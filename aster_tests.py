"""Allow to control an Aster command file during tests.
If this module import 'aster', it will be the static module built with
the Aster solver (see asteru or asterd).
"""
import socket
import threading


class Cnt(object):
    """Send message from an Aster case to a test.
    """

    def __init__(self, port, host=''):
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.connect((host, port))
        self._sck = sck

    def wait_srv(self):
        """Block until the server release the connection"""
        self._sck.send("WAITING")
        self._sck.recv(1024)

    def close(self):
        """Close the connection"""
        self._sck.close()


class Srv(object):
    """Listen to the Cnt connection and reply.
    """

    def __init__(self, port, host=''):
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port
        sck.bind((host, port))
        sck.listen(1)
        self._sck = sck
        self._cnt = None
        thread = threading.Thread(target=self._start_listening)
        thread.start()
        self._thread = thread

    def _start_listening(self):
        """Start to wait for a connection"""
        self._cnt = self._sck.accept()[0]

    def wait_cnt(self, timeout=120.):
        """Wait until the server has received a connection.
        If the timeout is reached, return False."""
        self._thread.join(timeout)
        return (not self._thread.isAlive())

    def release_cnt(self):
        """Release the connection waiting for the server"""
        if self.has_cnt():
            assert self._cnt.recv(1024) == "WAITING"
            self._cnt.send("RELEASE")

    def has_cnt(self):
        """Tell if the server has a connection"""
        return (self._cnt is not None)

    def close(self):
        """Close the server"""
        if not self.has_cnt():
            cnt = Cnt(self.port)
            self.wait_cnt()
            cnt.close()
        self._sck.close()


def build_srv(start_port=50007, stop_port=50027):
    """Build a socket server. Try to build the first one with 
    start_port and then increment values until stop_port."""
    srv = None
    port = start_port
    while (srv is None) and (port <= stop_port):
        try:
            srv = Srv(port)
        except socket.error:
            port += 1
    if srv is None:
        mess = "No server could be built from %i to %i"
        raise ValueError(mess % (start_port, stop_port))
    return srv


