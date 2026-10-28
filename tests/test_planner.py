from __future__ import annotations

import random
import ipaddress
import unittest

from netopps.planner import allocate_subnets


class SubnetPlannerTests(unittest.TestCase):
    def test_allocates_first_free_subnets_deterministically(self) -> None:
        inventory = {"networks": [{"id": "used", "cidr": "10.0.0.0/24"}]}
        result = allocate_subnets(inventory, "10.0.0.0/16", 24, 3)
        self.assertEqual(["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"], result)

    def test_existing_parent_network_blocks_candidates(self) -> None:
        inventory = {"networks": [{"id": "reserved", "cidr": "10.0.0.0/16"}]}
        self.assertEqual([], allocate_subnets(inventory, "10.0.0.0/16", 24, 1))

    def test_ipv6_allocation(self) -> None:
        result = allocate_subnets({"networks": []}, "2001:db8::/48", 64, 2)
        self.assertEqual(["2001:db8::/64", "2001:db8:0:1::/64"], result)

    def test_rejects_non_object_inventory(self) -> None:
        with self.assertRaisesRegex(TypeError, "inventory must be a JSON object"):
            allocate_subnets([], "10.0.0.0/16", 24, 1)  # type: ignore[arg-type]

    def test_more_specific_occupied_range_blocks_candidate_subnet(self) -> None:
        inventory = {"networks": [{"id": "reserved", "cidr": "10.0.0.64/27"}]}
        result = allocate_subnets(inventory, "10.0.0.0/24", 26, 3)
        self.assertEqual(["10.0.0.0/26", "10.0.0.128/26", "10.0.0.192/26"], result)

    def test_deterministic_randomized_allocations_never_overlap_reservations(self) -> None:
        rng = random.Random(20261028)
        pool = ipaddress.ip_network("10.0.0.0/24")
        candidates = list(pool.subnets(new_prefix=26))
        for case in range(100):
            occupied_indexes = set(rng.sample(range(4), rng.randint(0, 4)))
            occupied = [candidates[index] for index in occupied_indexes]
            inventory = {
                "networks": [
                    {"id": f"reserved-{index}", "cidr": str(network)}
                    for index, network in enumerate(occupied)
                ]
            }
            result = allocate_subnets(inventory, str(pool), 26, 4)
            expected = [str(candidate) for candidate in candidates if candidate not in occupied]
            self.assertEqual(expected, result, msg=f"case {case}")
            parsed_result = [ipaddress.ip_network(value) for value in result]
            self.assertTrue(all(candidate.subnet_of(pool) for candidate in parsed_result))
            for index, candidate in enumerate(parsed_result):
                self.assertFalse(any(candidate.overlaps(reserved) for reserved in occupied))
                self.assertFalse(any(candidate.overlaps(other) for other in parsed_result[index + 1 :]))

    def test_rejects_prefix_smaller_than_pool(self) -> None:
        with self.assertRaisesRegex(ValueError, "prefix must be between"):
            allocate_subnets({"networks": []}, "10.0.0.0/24", 16, 1)

    def test_rejects_invalid_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "count must be"):
            allocate_subnets({"networks": []}, "10.0.0.0/24", 25, 0)

    def test_rejects_unbounded_candidate_space(self) -> None:
        with self.assertRaisesRegex(ValueError, "planning limit"):
            allocate_subnets({"networks": []}, "10.0.0.0/8", 32, 1, max_candidates=1000)

    def test_does_not_mutate_inventory(self) -> None:
        inventory = {"networks": [{"id": "used", "cidr": "10.0.0.0/24"}]}
        before = {"networks": list(inventory["networks"])}
        allocate_subnets(inventory, "10.0.0.0/16", 24, 1)
        self.assertEqual(before, inventory)


if __name__ == "__main__":
    unittest.main()
