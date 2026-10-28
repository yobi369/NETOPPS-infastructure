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

    occupied: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for index, item in enumerate(raw_networks):
        if not isinstance(item, dict) or not isinstance(item.get("cidr"), str):
            raise TypeError(f"inventory network at index {index} has no valid cidr field")
        try:
            network = ipaddress.ip_network(item["cidr"], strict=True)
        except ValueError as exc:
            raise ValueError(f"inventory network at index {index} has an invalid cidr: {exc}") from exc
        if network.version == pool.version and network.overlaps(pool):
            occupied.append(network)

    allocated: list[str] = []
    for candidate in pool.subnets(new_prefix=new_prefix):
        if any(candidate.overlaps(existing) for existing in occupied):
            continue
        allocated.append(str(candidate))
        occupied.append(candidate)
        if len(allocated) == count:
            break
    return allocated
