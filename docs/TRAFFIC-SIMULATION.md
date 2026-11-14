# Traffic Demand and Congestion Simulation

## Purpose

This milestone adds deterministic traffic-demand modelling to the simulation-only network digital twin. It assigns each demand to one lowest-latency path and estimates the load placed on each declared link.

## Demand contract

A separate JSON file contains schema_version 1 and a demands array. Each demand has a unique ID, source node, target node, and positive demand_mbps value. See examples/traffic-demands.json.

## CLI

    netopps topology-report examples/topology.json --traffic-file examples/traffic-demands.json

The result includes the selected path for each routable demand, unroutable demand count, carried Mbps per link, utilization percentage, and estimated overload in Mbps.

## Model assumptions

- Each demand is routed over one lowest-total-latency path; there is no multipath splitting or traffic engineering.
- Demands are aggregated independently on shared links.
- Congestion is flagged when modeled carried traffic exceeds declared link capacity.
- Capacity values and demand rates are scenario inputs, not measured throughput.
- The model does not estimate packet loss, queueing delay, protocol overhead, burst behavior, or convergence.
- A missing path is reported as unroutable; it is not silently rerouted through a failed or disabled link.

## Safety

The simulator performs local computation only. It does not generate traffic, open sockets, collect telemetry, or change device configuration. Its output is a scenario estimate, not an operational network measurement.
