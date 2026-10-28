from __future__ import annotations

import socket
import threading
import unittest

from netopps.health import check_connectivity


class LoopbackConnectivityIntegrationTests(unittest.TestCase):
    def test_tcp_check_connects_to_explicit_local_listener(self) -> None:
        accepted = threading.Event()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]

            def accept_once() -> None:
                try:
                    connection, _ = server.accept()
                    with connection:
                        accepted.set()
                except OSError:
                    return

            worker = threading.Thread(target=accept_once, daemon=True)
            worker.start()
            inventory = {
                "devices": [{
                    "id": "loopback-test",
                    "hostname": "localhost",
                    "management_ip": "127.0.0.1",
                    "management_port": port,
                    "role": "server",
                }],
                "networks": [],
            }
            report = check_connectivity(inventory, limit=1, timeout=1.0)
            worker.join(timeout=1.0)

        self.assertTrue(report["all_reachable"])
        self.assertTrue(accepted.is_set())
        self.assertEqual("reachable", report["results"][0]["status"])
        self.assertFalse(report["configuration_changed"])


if __name__ == "__main__":
    unittest.main()
