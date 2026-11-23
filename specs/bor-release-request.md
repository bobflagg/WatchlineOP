# Request to the BOR developers: publish the graphs in the release (draft 2026-11-14)

From WatchlineOP, a consumer of release v0.2.1 (run 2026-05-29-149e871f). Superseded: BOR built release v0.3.0 (graph_edges.csv) on 2026-11-15, so this request is not sent. Kept as the record of the gap.

## Ask

Publish each layer's graph itself: the nodes, every edge BOR used, the evidence for each edge, and the group each node belongs to.
Today we read the groups and a spanning-tree witness, and rebuild the evidence from several tables.

## What v0.2.1 gives, and the gap

| Layer, stage | Present as | Gap |
| --- | --- | --- |
| Operational Network: name, address, identity | `network_edges` (57,202 pairs, three weights) | Complete, but the stage is implied by which weight is above 0; the masked address edges are not listed |
| Owner Portfolio: `identity.splink_base`, `splink_feedback` | `node_cluster` (a cluster per node) | The pairwise edges, and the hub-and-spoke stars above 150 nodes, are not written out |
| Owner Portfolio: `identity.registered_llc`, `identity.curated` | `link_sets`, `link_set_members` | Sets only; the shared entity name is reached through `decision_support` |
| Owner Portfolio: `deed.held_since`, `deed.linked_successor` | `evidence_items`, `evidence_members` | The deed hub cap (nodes on more than 20 joint deeds) removes edges that cannot be seen |
| Portfolio witness | `group_witness` (9,100 steps) | One representative tree, "not unique, strongest or shortest" |

## Requested files

- `graph_nodes.csv`: layer, node_id, group_id.
- `graph_edges.csv`: layer, edge_id, node_a, node_b, stage, weight (blank for portfolio), kept (true or false), drop_reason (for example `address_mask`, `deed_hub_cap`, `star_spoke`), evidence_id.
- `graph_evidence.csv`: evidence_id, stage, rule, rule_version, and the cited object (document, shared company observation, cluster, link set).
- Keep `groups.csv`, `group_members.csv` and `group_bbls.csv` as the partition. Say in the manifest that groups are connected components of the kept edges of `graph_edges.csv`, so a consumer can check it.

## Why

Evidence for "why are these two landlords grouped" should be traceable in one place, including edges BOR set aside (masked address, hub cap) and why.
