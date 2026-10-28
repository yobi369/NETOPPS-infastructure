"""Explicitly scoped, read-only TCP reachability checks for inventory devices."""

from __future__ import annotations

import math
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

_MAX_TARGETS = 100
_MAX_TIMEOUT_SECONDS = 3.0
_MAX_WORKERS = 8


def check_connectivity(
    inventory: dict[str, Any],
    *,
    limit: int = 20,
    timeout: float = 1.0,
) -> dict[str, Any]:
    """Check only listed management endpoints; send no application payload."""
    if not isinstance(inventory, dict):
        raise TypeError("inventory must be a JSON object")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= _MAX_TARGETS:
        raise ValueError(f"limit must be an integer from 1 to {_MAX_TARGETS}")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout):
        raise TypeError("timeout must be a finite number")
    if not 0.1 <= timeout <= _MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout must be between 0.1 and {_MAX_TIMEOUT_SECONDS} seconds")

    devices = inventory.get("devices")
    if not isinstance(devices, list):
        raise ValueError("inventory devices must be an array")
    selected = devices[:limit]

    def check(device: dict[str, Any]) -> dict[str, Any]:
        identifier = str(device["id"])
        address = device["management_ip"]
        port = device.get("management_port", 22)
        started = time.monotonic()
        reason: str | None = None
        status = "reachable"
        connection = None
        try:
            connection = socket.create_connection((address, port), timeout=float(timeout))
        except TimeoutError:
            status, reason = "unreachable", "timeout"
        except ConnectionRefusedError:
            status, reason = "unreachable", "connection_refused"
        except OSError:
            status, reason = "unreachable", "network_error"
        finally:
            if connection is not None:
                connection.close()

        result: dict[str, Any] = {
            "device_id": identifier,
            "management_ip": address,
            "port": port,
            "status": status,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
        }
        if reason:
            result["reason"] = reason
        return result

    # executor.map preserves inventory order while limiting concurrent connection attempts.
    with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, max(1, len(selected)))) as executor:
        results = list(executor.map(check, selected))

    return {
        "mode": "read-only-tcp-check",
        "checked_count": len(results),
        "total_devices": len(devices),
        "scope_truncated": len(results) < len(devices),
        "timeout_seconds": float(timeout),
        "results": results,
        "all_reachable": all(item["status"] == "reachable" for item in results),
        "configuration_changed": False,
    }
