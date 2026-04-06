# Data Model

## Core entities
- `Project` - top-level container and domain-profile holder
- `Requirement` - authored need, goal, or specification
- `Block` - logical or physical system element
- `Component` - realization element, including software modules
- `TestCase` - verification definition
- `TestRun` - execution record for a test case
- `OperationalRun` - field or operational record
- `VerificationEvidence` - evidence linked to requirements or test cases
- `SimulationEvidence` - simulation record, optionally linked to an FMI contract
- `OperationalEvidence` - aggregated operational evidence batch
- `Baseline` and `BaselineItem` - frozen approved versions
- `ChangeRequest` and `ChangeImpact` - change-control workflow and impact records
- `NonConformity` - issue / NCR-like record with disposition
- `ConnectorDefinition` - external system registration
- `ExternalArtifact` and `ExternalArtifactVersion` - authoritative external references
- `ArtifactLink` - link between internal objects and external artifacts
- `ConfigurationContext` and `ConfigurationItemMapping` - review or release context
- `RevisionSnapshot` - history snapshot for authored changes
- `ApprovalActionLog` - workflow history entry
- `Link` - generic relationship between internal objects
- `SysMLRelation` - SysML-style relation between internal objects
- `BlockContainment` - parent/child block relation
- `FMIContract` - simulation model reference contract

## Relationship highlights
- Requirements can be satisfied by blocks and verified by test cases.
- Requirements can have verification criteria, evidence, and revision history.
- Blocks can contain other blocks and participate in logical or physical abstraction layers.
- Components are linked to requirements and evidence where the realization is software or physical part based.
- Baselines capture approved object versions.
- Change requests and non-conformities carry review and disposition history.
- External artifacts and configuration contexts bridge ThreadLite to external authoritative sources.

## Notes and limitations
- The model is intentionally broad because the app serves a full digital-thread workflow.
- Some interoperability entities are projection-oriented rather than native external-system clones.
- The model is normalized enough for the current MVP, but richer graph or standards-native semantics may need further refinement later.
