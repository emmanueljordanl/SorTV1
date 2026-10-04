import queue
import time
import unittest
from types import SimpleNamespace
from app.transport import encode
from app.transport.serial_transport import SerialTransport

class FakeSerial:
    def __init__(self,**kwargs):self.incoming=queue.Queue();self.writes=[];self.closed=False
    def reset_input_buffer(self):pass
    def read(self,n):
        if self.closed:raise OSError('disconnected')
        try:return self.incoming.get(timeout=0.02)
        except queue.Empty:return b''
    def write(self,data):
        if self.closed:raise OSError('disconnected')
        self.writes.append(data);return len(data)
    def close(self):self.closed=True

class SerialTests(unittest.TestCase):
    def test_heartbeat_independent_and_no_replay(self):
        connections=[]
        def factory(**kwargs):
            s=FakeSerial(**kwargs);connections.append(s);s.incoming.put(encode({'v':1,'boot':'b'+str(len(connections)),'cmd':'HELLO'}));return s
        port=SimpleNamespace(vid=11914,pid=10,serial_number='unique',device='TEST')
        link=SerialTransport({'vid':11914,'pid':10,'serial_number':'unique'},serial_factory=factory,ports_factory=lambda:[port]);link.start()
        try:
            hello=link.events.get(timeout=1);self.assertEqual(hello['boot'],'b1')
            link.send(dict(v=1,boot='b1',cmd='SORT',cycle=1,request=1,dest=0));time.sleep(0.45)
            self.assertTrue(any(b'HEARTBEAT' in w for w in connections[0].writes))
            connections[0].closed=True
            limit=time.monotonic()+2
            while len(connections)<2 and time.monotonic()<limit:time.sleep(0.05)
            self.assertGreaterEqual(len(connections),2)
            self.assertFalse(any(b'SORT' in w for w in connections[1].writes))
            with self.assertRaises(OSError):link.send(dict(v=1,boot='b1',cmd='SORT',cycle=1,request=1,dest=0))
        finally:link.close()
    def test_ambiguous_device_refused(self):
        p=SimpleNamespace(vid=1,pid=2,serial_number='s',device='x')
        link=SerialTransport({'vid':1,'pid':2},ports_factory=lambda:[p,p])
        with self.assertRaises(OSError):link.select_port()
if __name__=='__main__':unittest.main()
