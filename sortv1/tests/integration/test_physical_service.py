"""PhysicalService end-to-end con enlace USB falso (sin cámara, sin Pico, sin motores).

Cubre el orquestador que corre en operación: INSPECT -> decisión -> SORT -> ACK/DONE -> evidencia,
más los caminos de seguridad que deben terminar en REVIEW sin enviar SORT.
"""
import queue
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.controller.physical import PhysicalService, MAX_INSPECTION_DEADLINE_MS, MIN_DECISION_MARGIN_MS, PICO_DECISION_TIMEOUT_MS
from app.operator_ui import create_server
from app.utils import write_json


class Stop(BaseException):
    """Termina run() sin pasar por `except Exception` del servicio."""


class StoppableQueue(queue.Queue):
    stopped = False

    def get(self, block=True, timeout=None):
        if self.stopped:
            raise Stop()
        return super().get(block, timeout)


class FakeLink:
    def __init__(self, boot="b1"):
        self.events = StoppableQueue()
        self.sent = []
        self.boot = boot  # el transporte real lo fija al recibir HELLO/STATUS
        self.closed = False

    def start(self):
        pass

    def send(self, message):
        self.sent.append(message)

    def close(self):
        self.closed = True


BOOT = "b1"
STATUS = {"cmd": "STATUS", "boot": BOOT, "state": "WAIT_DECISION", "reason": "OK", "cycle": 1, "request": 0,
          "lid": True, "service": True, "power": True, "presence": True, "fill": ["AVAILABLE"] * 4}


def make_service(test, *, enable=True, dest=2, **settings):
    temp = TemporaryDirectory()
    test.addCleanup(temp.cleanup)
    root = Path(temp.name)
    write_json(root / "config/physical.json", {
        "serial": {"vid": 11914, "pid": 10, "serial_number": None, "port": None},
        "model_package": "models/active", "operator": "tester", "admission_record": None,
        "admission_max_age_s": 120, "journal": "evidence/experiments/physical.jsonl", "ui_port": 0, **settings})
    service = PhysicalService(root, diagnostic=True, enable_actuators=enable, destination=dest)
    test.addCleanup(service.pool.shutdown, wait=True, cancel_futures=True)
    return service


class Harness:
    def __init__(self, test, *, feed_status=True, **kwargs):
        self.test = test
        self.service = make_service(test, **kwargs)
        self.link = FakeLink()
        self.service.link = self.link
        self.error = None
        self.feed = feed_status
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.feeder = threading.Thread(target=self._feed, daemon=True)
        test.addCleanup(self.finish)

    def _run(self):
        try:
            self.service.run()
        except Stop:
            pass
        except BaseException as error:  # noqa: BLE001 - se reporta en finish()
            self.error = error

    def _feed(self):
        # El Pico real emite STATUS cada 250 ms; el servicio exige datos < 500 ms.
        while not self.link.events.stopped:
            self.push(**STATUS)
            time.sleep(0.1)

    def start(self):
        self.push(cmd="HELLO", boot=BOOT, firmware="test")
        self.push(**STATUS)
        self.thread.start()
        if self.feed:
            self.feeder.start()
        return self

    def push(self, **message):
        self.link.events.put({"v": 1, **message})

    def wait_for(self, predicate, timeout=5.0):
        limit = time.monotonic() + timeout
        while time.monotonic() < limit:
            if predicate():
                return True
            time.sleep(0.01)
        return False

    def sorts(self):
        return [m for m in self.link.sent if m["cmd"] == "SORT"]

    def review_reasons(self):
        return [e["data"]["decision"]["reason"] for e in self.service.journal.events if e["event"] == "REVIEW"]

    def wait_review(self):
        self.test.assertTrue(self.wait_for(lambda: self.review_reasons()), "no se registró REVIEW")
        return self.review_reasons()[-1]

    def finish(self):
        self.link.events.stopped = True
        if self.thread.is_alive():
            self.thread.join(5)
        if self.feeder.is_alive():
            self.feeder.join(2)
        self.test.assertFalse(self.thread.is_alive(), 'PhysicalService thread abandoned')
        self.test.assertFalse(self.feeder.is_alive(), 'status feeder thread abandoned')
        if self.error:
            raise self.error


class PhysicalServiceTests(unittest.TestCase):
    def test_forced_diagnostic_cycle_sends_one_sort_and_counts_done_once(self):
        h = Harness(self, enable=True, dest=2).start()
        h.push(cmd="INSPECT", boot=BOOT, cycle=1)
        self.assertTrue(h.wait_for(h.sorts), "no se envió SORT")
        self.assertEqual(h.sorts(), [{"v": 1, "boot": BOOT, "cycle": 1, "request": 1, "cmd": "SORT", "dest": 2}])
        h.push(cmd="ACK", boot=BOOT, cycle=1, request=1)
        self.assertTrue(h.wait_for(lambda: any(e['event'] == 'ACK' for e in h.service.journal.events)))
        self.assertEqual(h.service.journal.counts('DIAGNOSTIC'), [0, 0, 0, 0], 'ACK must not count')
        done = {"cmd": "DONE", "boot": BOOT, "cycle": 1, "request": 1, "seq": 1, "confirmed_bin": 2}
        h.push(**done)
        h.push(**done)  # duplicado idéntico
        self.assertTrue(h.wait_for(lambda: h.service.journal.counts("DIAGNOSTIC") == [0, 0, 1, 0]))
        h.push(cmd='DONE', boot='stale-marker', cycle=1, request=1, seq=1, confirmed_bin=2)
        self.assertTrue(h.wait_for(lambda: any(e['event'] == 'IGNORED_STALE_BOOT' for e in h.service.journal.events)))
        self.assertEqual(h.service.journal.counts("DIAGNOSTIC"), [0, 0, 1, 0])
        self.assertEqual(len(h.sorts()), 1)
        self.assertEqual(sum(e['event'] == 'DONE' for e in h.service.journal.events), 1)
        self.assertEqual(h.service.journal.pending_cycles(), set())

    def test_diagnostic_without_enable_flag_never_sorts(self):
        h = Harness(self, enable=False, dest=2).start()
        h.push(cmd="INSPECT", boot=BOOT, cycle=1)
        self.assertEqual(h.wait_review(), "ACTUATORS_NOT_ENABLED")
        self.assertEqual(h.sorts(), [])
        self.assertTrue(h.service.controller.blocked)
        self.assertEqual(h.service.snapshot()["estado"], "REVISIÓN")

    def test_stale_sensor_status_forces_review(self):
        h = Harness(self, enable=True, dest=1, feed_status=False).start()
        time.sleep(0.6)  # el único STATUS queda más viejo que 500 ms
        h.push(cmd="INSPECT", boot=BOOT, cycle=1)
        self.assertEqual(h.wait_review(), "STALE_SENSORS")
        self.assertEqual(h.sorts(), [])

    def test_inspection_past_deadline_is_review_and_late_result_is_discarded(self):
        h = Harness(self, enable=True, dest=1, inspection_deadline_ms=150)
        original = h.service.inspect

        def slow(cycle, status):
            time.sleep(0.5)
            return original(cycle, status)

        h.service.inspect = slow
        h.start()
        h.push(cmd="INSPECT", boot=BOOT, cycle=1)
        self.assertEqual(h.wait_review(), "INSPECTION_TIMEOUT")
        self.assertTrue(h.wait_for(lambda: h.service.future is None), "el trabajador no terminó")
        self.assertEqual(h.sorts(), [], "un resultado tardío no puede producir SORT")

    def test_inspection_within_configured_deadline_is_not_discarded(self):
        # El Pico espera 2 s; con un plazo configurado de 1.5 s una inspección de 1.2 s es válida.
        h = Harness(self, enable=True, dest=3, inspection_deadline_ms=1500)
        original = h.service.inspect

        def slow(cycle, status):
            time.sleep(1.2)
            return original(cycle, status)

        h.service.inspect = slow
        h.start()
        h.push(cmd="INSPECT", boot=BOOT, cycle=1)
        self.assertTrue(h.wait_for(h.sorts, timeout=4), "una inspección dentro del plazo fue descartada")
        self.assertEqual(h.sorts()[0]["dest"], 3)

    def test_default_deadline_matches_plan_and_stays_below_pico_timeout(self):
        service = make_service(self)
        self.assertEqual(service.inspection_deadline_s, 1.75)
        self.assertEqual(MAX_INSPECTION_DEADLINE_MS, PICO_DECISION_TIMEOUT_MS - MIN_DECISION_MARGIN_MS)

    def test_1750_deadline_is_valid_and_preserves_usb_margin(self):
        self.assertEqual(make_service(self, inspection_deadline_ms=1750).inspection_deadline_s, 1.75)

    def test_invalid_deadline_is_rejected(self):
        for value in (0, -1, -5, 1751, 1800, 1999, 2000, 5000, 1.5, "1000", True, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                make_service(self, inspection_deadline_ms=value)

    def test_stale_boot_message_is_ignored(self):
        h = Harness(self, enable=True, dest=0).start()
        h.push(cmd="DONE", boot="otro-arranque", cycle=1, request=1, seq=1, confirmed_bin=0)
        self.assertTrue(h.wait_for(lambda: any(e["event"] == "IGNORED_STALE_BOOT" for e in h.service.journal.events)))
        self.assertEqual(h.service.journal.counts("DIAGNOSTIC"), [0, 0, 0, 0])

    def test_shutdown_stops_ui_and_releases_same_port(self):
        servers = []
        def factory(service, port):
            server = create_server(service, port); servers.append(server); return server
        with patch('app.controller.physical.create_server', side_effect=factory):
            h = Harness(self).start()
            self.assertTrue(h.wait_for(lambda: bool(servers)))
            port = servers[0].server_address[1]
            h.finish()
        self.assertTrue(h.link.closed)
        self.assertEqual(servers[0].fileno(), -1)
        self.assertFalse(any(t.name == 'SorTV1OperatorUI' for t in threading.enumerate()))
        replacement = create_server(h.service, port)
        replacement.server_close()

    def test_ui_bind_failure_closes_link_and_pool(self):
        service = make_service(self); link = FakeLink(); service.link = link
        with patch('app.controller.physical.create_server', side_effect=OSError('fixture bind failure')):
            with self.assertRaises(OSError): service.run()
        self.assertTrue(link.closed)
        with self.assertRaises(RuntimeError): service.pool.submit(lambda: None)

    def test_inspection_exception_closes_ui_and_joins_threads(self):
        servers = []
        def factory(service, port):
            server = create_server(service, port); servers.append(server); return server
        with patch('app.controller.physical.create_server', side_effect=factory):
            h = Harness(self)
            def failed_inspection(cycle, status): raise ValueError('fixture inspection failure')
            h.service.inspect = failed_inspection
            h.start(); h.push(cmd='INSPECT', boot=BOOT, cycle=1)
            self.assertTrue(h.wait_for(lambda: not h.thread.is_alive()))
            self.assertIsInstance(h.error, ValueError)
            h.error = None
        self.assertTrue(h.link.closed)
        self.assertEqual(servers[0].fileno(), -1)
        self.assertTrue(h.service.controller.blocked)
        self.assertTrue(any(e['event']=='SERVICE_FAULT' for e in h.service.journal.events))
        self.assertFalse(any(t.name == 'SorTV1OperatorUI' for t in threading.enumerate()))

    def test_cleanup_failure_still_closes_ui_and_joins_worker(self):
        servers = []
        def factory(service, port):
            server = create_server(service, port); servers.append(server); return server
        with patch('app.controller.physical.create_server', side_effect=factory):
            h = Harness(self)
            def failed_close():
                h.link.closed = True
                raise OSError('fixture close failure')
            h.link.close = failed_close
            h.start()
            self.assertTrue(h.wait_for(lambda: bool(servers)))
            h.link.events.stopped = True
            self.assertTrue(h.wait_for(lambda: not h.thread.is_alive()))
            self.assertIsInstance(h.error, OSError)
            h.error = None  # expected error was asserted; cleanup must still check all threads.
        self.assertEqual(servers[0].fileno(), -1)
        self.assertFalse(any(t.name == 'SorTV1OperatorUI' for t in threading.enumerate()))
        with self.assertRaises(RuntimeError): h.service.pool.submit(lambda: None)


if __name__ == "__main__":
    unittest.main()
