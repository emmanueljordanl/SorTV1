import unittest

from app.transport import ProtocolError, StreamParser, crc16, decode, encode

SORT = {"v": 1, "boot": "b17", "cycle": 42, "request": 7, "cmd": "SORT", "dest": 2}


class WireTests(unittest.TestCase):
    def test_known_crc_vector(self):
        self.assertEqual(crc16(b"123456789"), 0x29B1)

    def test_round_trip_at_every_fragment_boundary(self):
        line = encode(SORT)
        for boundary in range(len(line) + 1):
            parser = StreamParser()
            result = parser.feed(line[:boundary], 0) + parser.feed(line[boundary:], 1)
            self.assertEqual(result, [SORT])

    def test_bad_crc_is_rejected_and_next_line_recovers(self):
        parser = StreamParser()
        line = encode(SORT)
        bad = line[:-5] + b"0000\n"
        self.assertEqual(parser.feed(bad + line, 0), [SORT])
        self.assertTrue(parser.errors)

    def test_oversize_discards_to_newline(self):
        parser = StreamParser()
        self.assertEqual(parser.feed(b"x" * 513 + encode(SORT), 0), [])
        self.assertEqual(parser.feed(encode(SORT), 1), [SORT])
        self.assertLessEqual(len(parser.buffer), 512)

    def test_partial_timeout_discards_suffix(self):
        parser = StreamParser()
        line = encode(SORT)
        self.assertEqual(parser.feed(line[:10], 0), [])
        self.assertEqual(parser.feed(line[10:] + line, 251), [SORT])
        self.assertIn("PARTIAL_TIMEOUT", parser.errors)

    def test_boolean_destination_and_arbitrary_motion_are_rejected(self):
        for message in [{**SORT, "dest": True}, {**SORT, "dest": 4}, {**SORT, "steps": 400}]:
            with self.assertRaises(ProtocolError):
                encode(message)

    def test_duplicate_json_keys_are_rejected(self):
        payload = b'{"v":1,"boot":"b","cmd":"QUERY","cmd":"SORT"}'
        line = payload + f"|{crc16(payload):04X}\n".encode()
        with self.assertRaises(ProtocolError):
            decode(line)

    def test_non_object_and_unhashable_command_are_rejected(self):
        for payload in [b"[]", b'{"v":1,"boot":"b","cmd":[]}']:
            with self.assertRaises(ProtocolError):
                decode(payload + f"|{crc16(payload):04X}\n".encode())
