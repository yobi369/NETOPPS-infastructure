from __future__ import annotations

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
