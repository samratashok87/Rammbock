import unittest
import time
import socket
from threading import Timer
from Networking import UDPServer, TCPServer, UDPClient, TCPClient
from templates.containers import Protocol
from templates.primitives import UInt, PDU

LOCAL_IP = '127.0.0.1'
SERVER_PORT = 12345
SERVER_PORT_2 = 12346
CLIENT_PORT = 54321
CLIENT_PORT_2 = 64321
CONNECTION_ALIAS = "Connection alias"


class TestNetwork(unittest.TestCase):

    def setUp(self):
        self.sockets = []

    def tearDown(self, *args, **kwargs):
        for sock in self.sockets:
            sock.close()
        return unittest.TestCase.tearDown(self, *args, **kwargs)

    def test_send_and_receive_udp(self):
        server, client = self._udp_server_and_client(SERVER_PORT, CLIENT_PORT)
        client.send('foofaa')
        self._assert_receive(server, 'foofaa')

    def test_server_send_udp(self):
        server, client = self._udp_server_and_client(SERVER_PORT, CLIENT_PORT)
        server.send_to('foofaa', LOCAL_IP, CLIENT_PORT)
        self._assert_receive(client, 'foofaa')

    def test_server_send_tcp(self):
        server, client = self._tcp_server_and_client(SERVER_PORT, CLIENT_PORT)
        server.accept_connection()
        server.send('foofaa')
        self._assert_receive(client, 'foofaa')

    def test_send_and_receive_tcp(self):
        server, client = self._tcp_server_and_client(SERVER_PORT, CLIENT_PORT)
        client.send('foofaa')
        server.accept_connection()
        self._assert_receive(server, 'foofaa')

    def test_tcp_server_with_queued_connections(self):
        server, client = self._tcp_server_and_client(SERVER_PORT, CLIENT_PORT)
        TCPClient().connect_to(LOCAL_IP, SERVER_PORT)
        server.accept_connection()
        server.accept_connection()

    def test_tcp_server_with_named_connection(self):
        server = TCPServer(LOCAL_IP, 1337)
        client = TCPClient().connect_to(LOCAL_IP, 1337)
        server.accept_connection(alias=CONNECTION_ALIAS + "1")
        self.assertTrue(server._connections.get(CONNECTION_ALIAS + "1"))

    def test_setting_port_no_ip(self):
        server, client = self._udp_server_and_client(SERVER_PORT, CLIENT_PORT, client_ip='')
        server.send_to('foofaa', LOCAL_IP, client.get_address()[1])
        self._assert_receive(client, 'foofaa')

    def test_setting_ip_no_port(self):
        server, client = self._udp_server_and_client(SERVER_PORT, '')
        server.send_to('foofaa', *client.get_address())
        self._assert_receive(client, 'foofaa')

    def test_setting_client_default_timeout(self):
        _, client = self._udp_server_and_client(SERVER_PORT, CLIENT_PORT, timeout=0.1)
        self._assert_timeout(client)

    def test_overriding_client_read_timeout(self):
        _, client = self._udp_server_and_client(SERVER_PORT, CLIENT_PORT, timeout=5)
        self._assert_timeout(client, 0.1)

    def test_overriding_server_read_timeout(self):
        server, _ = self._udp_server_and_client(SERVER_PORT, CLIENT_PORT, timeout=5)
        self._assert_timeout(server, 0.1)

    def test_setting_server_default_timeout(self):
        server, _ = self._udp_server_and_client(SERVER_PORT, CLIENT_PORT, timeout=0.1)
        self._assert_timeout(server)

    def test_blocking_timeout(self):
        server, client = self._udp_server_and_client(SERVER_PORT, CLIENT_PORT, timeout=0.1)
        t = Timer(0.2, client.send, args=['foofaa'])
        t.start()
        self.assertEquals(server.receive(timeout='blocking'), 'foofaa')

    def _assert_timeout(self, node, timeout=None):
        start_time = time.time()
        self.assertRaises(socket.timeout, node.receive, timeout)
        self.assertTrue(time.time() - 0.5 < start_time)

    def _assert_receive(self, receiver, msg):
        self.assertEquals(receiver.receive(), msg)

    def _udp_server_and_client(self, server_port, client_port, client_ip=LOCAL_IP, timeout=None):
        server = UDPServer(LOCAL_IP, server_port, timeout=timeout)
        client = UDPClient(timeout=timeout)
        client.set_own_ip_and_port(client_ip, client_port)
        client.connect_to(LOCAL_IP, server_port)
        self.sockets.append(server)
        self.sockets.append(client)
        return server, client

    def _tcp_server_and_client(self, port, timeout=None):
        server = TCPServer(LOCAL_IP, port, timeout=timeout)
        client = TCPClient(timeout=timeout).connect_to(LOCAL_IP, port)
        self.sockets.append(server)
        self.sockets.append(client)
        return server, client

    def _server_gets(self, name, text):
        msg = self.net.server_receive(name)
        self.assertEquals(text, msg)


def _get_template():
    protocol = Protocol('Test')
    protocol.add(UInt(1, 'id', 1))
    protocol.add(UInt(2, 'length', None))
    protocol.add(PDU('length-2'))
    return protocol

if __name__ == "__main__":
    unittest.main()