"""Deterministic, local-only checks for a JSON network inventory."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
_HOST_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_ROLES = {"router", "switch", "firewall", "server", "access_point", "load_balancer", "other"}
_MAX_DEVICES = 10_000
_MAX_NETWORKS = 10_000
_MAX_OVERLAP_FINDINGS = 10_000


def _valid_hostname(value: str) -> bool:
    """Accept ASCII DNS hostnames, including a single trailing root dot."""
    normalized = value[:-1] if value.endswith(".") else value
    if not normalized or len(normalized) > 253:
        return False
    labels = normalized.split(".")
    return all(_HOST_LABEL_PATTERN.fullmatch(label) for label in labels)


def validate_inventory(data: Any) -> list[dict[str, str]]:
    """Return stable validation findings; an empty list means the input passed checks."""
    findings: list[dict[str, str]] = []

    def add(code: str, path: str, message: str) -> None:
        findings.append({"code": code, "path": path, "message": message})

    if not isinstance(data, dict):
        return [{"code": "inventory.type", "path": "$", "message": "Inventory must be a JSON object."}]

    allowed_root_keys = {"schema_version", "devices", "networks"}
    for key in sorted(set(data) - allowed_root_keys, key=str):
        add("inventory.unknown_property", "$", f"Unknown top-level property: {key!r}.")

    version = data.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        add("inventory.schema_version", "$.schema_version", "schema_version must be the integer 1.")

    devices = data.get("devices")
    networks = data.get("networks")
    if not isinstance(devices, list):
        add("devices.type", "$.devices", "devices must be an array.")
        devices = []
    if not isinstance(networks, list):
        add("networks.type", "$.networks", "networks must be an array.")
        networks = []
    if len(devices) > _MAX_DEVICES:
        add("devices.limit", "$.devices", f"devices exceeds the {_MAX_DEVICES:,}-item safety limit.")
        devices = devices[:_MAX_DEVICES]
    if len(networks) > _MAX_NETWORKS:
        add("networks.limit", "$.networks", f"networks exceeds the {_MAX_NETWORKS:,}-item safety limit.")
        networks = networks[:_MAX_NETWORKS]

    seen_device_ids: set[str] = set()
    seen_management_ips: dict[str, str] = {}
    seen_hostnames: dict[str, str] = {}
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
        if not isinstance(hostname, str) or not hostname.strip() or any(ch.isspace() for ch in hostname) or not _valid_hostname(hostname):
            add("device.hostname", f"{path}.hostname", "hostname must be a non-empty string without whitespace.")
        else:
            normalized_hostname = hostname.rstrip(".").casefold()
            if normalized_hostname in seen_hostnames:
                add(
                    "device.duplicate_hostname",
                    f"{path}.hostname",
                    f"Hostname {hostname!r} duplicates device {seen_hostnames[normalized_hostname]!r} (case-insensitive).",
                )
            else:
                seen_hostnames[normalized_hostname] = str(device.get("id"))

        address = device.get("management_ip")
        try:
            if not isinstance(address, str):
                raise TypeError("management_ip must be a string")
            parsed_address = ipaddress.ip_address(address)
            canonical_address = str(parsed_address)
            if canonical_address in seen_management_ips:
                add(
                    "device.duplicate_management_ip",
                    f"{path}.management_ip",
                    f"Management IP {canonical_address} is also assigned to device {seen_management_ips[canonical_address]!r}.",
                )
            else:
                seen_management_ips[canonical_address] = str(identifier)
        except (ValueError, TypeError):
            add("device.management_ip", f"{path}.management_ip", "management_ip must be a valid IPv4 or IPv6 address.")

        port = device.get("management_port", 22)
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            add("device.management_port", f"{path}.management_port", "management_port must be an integer from 1 to 65535.")

        if "site" in device and (not isinstance(device["site"], str) or not device["site"].strip()):
            add("device.site", f"{path}.site", "site must be a non-empty string when provided.")

        role = device.get("role")
        if not isinstance(role, str) or role not in _ROLES:
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

        if "site" in network and (not isinstance(network["site"], str) or not network["site"].strip()):
            add("network.site", f"{path}.site", "site must be a non-empty string when provided.")

        cidr = network.get("cidr")
        try:
            if not isinstance(cidr, str):
                raise TypeError("cidr must be a string")
            parsed = ipaddress.ip_network(cidr, strict=True)
            parsed_networks.append((str(identifier), parsed))
        except (ValueError, TypeError):
            add("network.cidr", f"{path}.cidr", "cidr must be a valid network address with its correct prefix boundary.")

    ordered_networks = sorted(
        parsed_networks,
        key=lambda item: (
            item[1].version,
            int(item[1].network_address),
            int(item[1].broadcast_address),
            item[0],
        ),
    )
    active: list[tuple[str, ipaddress.IPv4Network | ipaddress.IPv6Network]] = []
    active_version: int | None = None
    overlap_count = 0
    overlap_limit_reached = False
    for right_id, right in ordered_networks:
        if active_version != right.version:
            active = []
            active_version = right.version
        right_start = int(right.network_address)
        active = [(left_id, left) for left_id, left in active if int(left.broadcast_address) >= right_start]
        for left_id, left in active:
            if overlap_count >= _MAX_OVERLAP_FINDINGS:
                overlap_limit_reached = True
                break
            add(
                "network.overlap",
                "$.networks",
                f"Networks {left_id!r} ({left}) and {right_id!r} ({right}) overlap.",
            )
            overlap_count += 1
        if overlap_limit_reached:
            break
        active.append((right_id, right))

    if overlap_limit_reached:
        add(
            "network.overlap_limit",
            "$.networks",
            f"Additional overlap findings were suppressed after {_MAX_OVERLAP_FINDINGS:,} pairs.",
        )

    return sorted(findings, key=lambda item: (item["path"], item["code"], item["message"]))
