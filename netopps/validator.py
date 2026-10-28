"""Deterministic, local-only checks for a JSON network inventory."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
_ROLES = {"router", "switch", "firewall", "server", "access_point", "load_balancer", "other"}


def validate_inventory(data: Any) -> list[dict[str, str]]:
    """Return stable validation findings; an empty list means the input passed checks."""
    findings: list[dict[str, str]] = []

    def add(code: str, path: str, message: str) -> None:
        findings.append({"code": code, "path": path, "message": message})

    if not isinstance(data, dict):
        return [{"code": "inventory.type", "path": "$", "message": "Inventory must be a JSON object."}]

    if data.get("schema_version") != 1:
        add("inventory.schema_version", "$.schema_version", "schema_version must be the integer 1.")

    devices = data.get("devices")
    networks = data.get("networks")
    if not isinstance(devices, list):
        add("devices.type", "$.devices", "devices must be an array.")
        devices = []
    if not isinstance(networks, list):
        add("networks.type", "$.networks", "networks must be an array.")
        networks = []

    seen_device_ids: set[str] = set()
    for index, device in enumerate(devices):
        path = f"$.devices[{index}]"
        if not isinstance(device, dict):
            add("device.type", path, "Each device must be an object.")
            continue
        identifier = device.get("id")
        if not isinstance(identifier, str) or not _ID_PATTERN.fullmatch(identifier):
            add("device.id", f"{path}.id", "id must be 1-63 safe letters, digits, dots, underscores, or hyphens.")
        elif identifier in seen_device_ids:
            add("device.duplicate_id", f"{path}.id", f"Duplicate device id: {identifier}.")
        else:
            seen_device_ids.add(identifier)

        hostname = device.get("hostname")
        if not isinstance(hostname, str) or not hostname.strip() or any(ch.isspace() for ch in hostname):
            add("device.hostname", f"{path}.hostname", "hostname must be a non-empty string without whitespace.")

        address = device.get("management_ip")
        try:
            if not isinstance(address, str):
                raise ValueError
            ipaddress.ip_address(address)
        except ValueError:
            add("device.management_ip", f"{path}.management_ip", "management_ip must be a valid IPv4 or IPv6 address.")

        port = device.get("management_port", 22)
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            add("device.management_port", f"{path}.management_port", "management_port must be an integer from 1 to 65535.")

        role = device.get("role")
        if role not in _ROLES:
            add("device.role", f"{path}.role", f"role must be one of: {', '.join(sorted(_ROLES))}.")

    parsed_networks: list[tuple[str, ipaddress.IPv4Network | ipaddress.IPv6Network]] = []
    seen_network_ids: set[str] = set()
    for index, network in enumerate(networks):
        path = f"$.networks[{index}]"
        if not isinstance(network, dict):
            add("network.type", path, "Each network must be an object.")
            continue
        identifier = network.get("id")
        if not isinstance(identifier, str) or not _ID_PATTERN.fullmatch(identifier):
            add("network.id", f"{path}.id", "id must be 1-63 safe letters, digits, dots, underscores, or hyphens.")
        elif identifier in seen_network_ids:
            add("network.duplicate_id", f"{path}.id", f"Duplicate network id: {identifier}.")
        else:
            seen_network_ids.add(identifier)

        cidr = network.get("cidr")
        try:
            if not isinstance(cidr, str):
                raise ValueError
            parsed = ipaddress.ip_network(cidr, strict=True)
            parsed_networks.append((str(identifier), parsed))
        except ValueError:
            add("network.cidr", f"{path}.cidr", "cidr must be a valid network address with its correct prefix boundary.")

    for index, (left_id, left) in enumerate(parsed_networks):
        for right_id, right in parsed_networks[index + 1 :]:
            if left.version == right.version and left.overlaps(right):
                add(
                    "network.overlap",
                    "$.networks",
                    f"Networks {left_id!r} ({left}) and {right_id!r} ({right}) overlap.",
                )

    return sorted(findings, key=lambda item: (item["path"], item["code"], item["message"]))
