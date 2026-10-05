#!/usr/bin/env python3
# gpsd-nmea-relay — serve gpsd's raw NMEA on a plain TCP port for PyGPSClient
#
# PyGPSClient has no gpsd client: it reads raw NMEA/UBX from a serial port or a socket it
# connects to, and gpsd's port 2947 speaks JSON until told otherwise. Each client that connects
# here gets its own gpsd session with ?WATCH={"nmea":true}; only NMEA sentences are forwarded.
# gpsd keeps sole ownership of /dev/serial0, so Kismet etc. are unaffected.
#
# Install:
#   install -m 755 gpsd-nmea-relay.py ~/.local/bin/gpsd-nmea-relay
# Run (normally started by ~/.local/bin/pygpsclient-gpsd):
#   gpsd-nmea-relay            # listens on 127.0.0.1:50010 (PyGPSClient's default socket port)
# Verify:
#   timeout 3 nc 127.0.0.1 50010 | head -3     # expect $GNGGA / $GNRMC ...
# PyGPSClient: Socket -> TCP IPv4, localhost, 50010 (the defaults), connect.
# Roll back:
#   rm ~/.local/bin/gpsd-nmea-relay     # nothing else to undo; gpsd is never reconfigured

import socket
import socketserver
import sys
import threading

GPSD = ("127.0.0.1", 2947)
LISTEN = ("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 50010)
WATCH = b'?WATCH={"enable":true,"nmea":true};\n'


class Relay(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.create_connection(GPSD, timeout=10) as gpsd:
            gpsd.settimeout(None)
            gpsd.sendall(WATCH)
            # Drain anything the client sends (PyGPSClient may poll the receiver); gpsd is
            # read-only here, so it is discarded.
            threading.Thread(target=self._drain, daemon=True).start()
            for line in gpsd.makefile("rb"):
                if line[:1] in (b"$", b"!"):  # skip gpsd's JSON (VERSION, DEVICES, WATCH)
                    self.request.sendall(line)

    def _drain(self):
        try:
            while self.request.recv(4096):
                pass
        except OSError:
            pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass  # a client disconnecting mid-send is normal, not worth a traceback


if __name__ == "__main__":
    with Server(LISTEN, Relay) as srv:
        srv.serve_forever()
