"""Deterministic, read-only subnet allocation planning."""

from __future__ import annotations

import ipaddress
from typing import Any


def allocate_subnets(
    inventory: dict[str, Any],
    pool_cidr: str,
    new_prefix: int,
    count: int,
    *,
    max_candidates: int = 1_000_000,
) -> list[str]:
    """Return the first available subnets from a pool without modifying inventory."""
    pool = ipaddress.ip_network(pool_cidr, strict=True)
    if isinstance(new_prefix, bool) or not isinstance(new_prefix, int):
        raise TypeError("prefix must be an integer")
    if not pool.prefixlen <= new_prefix <= pool.max_prefixlen:
        raise ValueError(f"prefix must be between {pool.prefixlen} and {pool.max_prefixlen} for pool {pool}")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 256:
        raise ValueError("count must be an integer from 1 to 256")
    if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or max_candidates < 1:
        raise ValueError("max_candidates must be a positive integer")

    candidate_count = 1 << (new_prefix - pool.prefixlen)
    if candidate_count > max_candidates:
        raise ValueError(
            f"pool would contain {candidate_count:,} candidate subnets; "
            f"the planning limit is {max_candidates:,}. Use a narrower pool."
        )

    raw_networks = inventory.get("networks", [])
    if not isinstance(raw_networks, list):
        raise TypeError("inventory networks must be an array")

    pool_start = int(pool.network_address)
    pool_end = int(pool.broadcast_address)
    candidate_size = 1 << (pool.max_prefixlen - new_prefix)
    blocked_ranges: list[tuple[int, int]] = []

    for index, item in enumerate(raw_networks):
        if not isinstance(item, dict) or not isinstance(item.get("cidr"), str):
            raise TypeError(f"inventory network at index {index} has no valid cidr field")
        try:
            network = ipaddress.ip_network(item["cidr"], strict=True)
        except ValueError as exc:
            raise ValueError(f"inventory network at index {index} has an invalid cidr: {exc}") from exc

        if network.version != pool.version or not network.overlaps(pool):
            continue

        first_address = max(pool_start, int(network.network_address))
        last_address = min(pool_end, int(network.broadcast_address))
        first_index = (first_address - pool_start) // candidate_size
        last_index = (last_address - pool_start) // candidate_size
        blocked_ranges.append((first_index, last_index))

    merged_ranges: list[list[int]] = []
    for start, end in sorted(blocked_ranges):
        if merged_ranges and start <= merged_ranges[-1][1] + 1:
            merged_ranges[-1][1] = max(merged_ranges[-1][1], end)
        else:
            merged_ranges.append([start, end])

    network_class = ipaddress.IPv4Network if pool.version == 4 else ipaddress.IPv6Network
    allocated: list[str] = []
    range_index = 0
    for candidate_index in range(candidate_count):
        while range_index < len(merged_ranges) and candidate_index > merged_ranges[range_index][1]:
            range_index += 1
        if range_index < len(merged_ranges):
            start, end = merged_ranges[range_index]
            if start <= candidate_index <= end:
                continue
        address = pool_start + candidate_index * candidate_size
        allocated.append(str(network_class((address, new_prefix))))
        if len(allocated) == count:
            break
    return allocated
