# Docs

Project-level design notes, user guidance, and architecture writeups live here.

The documentation set is intentionally small and English-only:

- [Root README](../README.md) - product overview, setup, and documentation entry point
- [User Guide](user-guide.md) - how to use each module and feature
- [Platform Logic Guide](platform-logic.md) - how the platform works logically
- [Target Architecture](target-architecture.md) - where the product is heading
- [Implementation Backlog](implementation-backlog.md) - planned stories and epics
- [Gap Analysis](gap-analysis.md) - current state versus target capabilities

Documentation policy:

- update the root README when product behavior changes
- update the user guide whenever a module or user flow changes
- update the logic guide whenever the data model, workflow, or platform rules change
- keep feature documentation aligned for contract-shaped interoperability surfaces such as AP242 and FMI
- keep all documentation in English

The same documentation set is also available from inside the application through the `Documentation` navigation item, including the Validation cockpit guidance added for the simplified SidSat-style review flow and the authoritative-source integrity summary now visible in the registry view.
