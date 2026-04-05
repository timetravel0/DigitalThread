export type DomainProfile = "engineering" | "manufacturing" | "personal" | "custom";

export interface LabelSet {
  requirement: string;
  requirements: string;
  requirement_description: string;
  block: string;
  blocks: string;
  block_description: string;
  testCase: string;
  testCases: string;
  testCase_description: string;
  link: string;
  links: string;
  baseline: string;
  baselines: string;
  changeRequest: string;
  changeRequests: string;
  verificationEvidence: string;
  simulationEvidence: string;
  operationalEvidence: string;
  operationalRun: string;
  nonConformity: string;
  nonConformities: string;
  kpi_verified: string;
  kpi_coverage: string;
  kpi_open_changes: string;
}

const LABELS: Record<DomainProfile, LabelSet> = {
  engineering: {
    requirement: "Requirement",
    requirements: "Requirements",
    requirement_description: "State the need or constraint this requirement addresses.",
    block: "Block",
    blocks: "Blocks",
    block_description: "Describe this subsystem or structural element.",
    testCase: "Test Case",
    testCases: "Test Cases",
    testCase_description: "Describe the procedure and acceptance criteria.",
    link: "Traceability Link",
    links: "Traceability Links",
    baseline: "Baseline",
    baselines: "Baselines",
    changeRequest: "Change Request",
    changeRequests: "Change Requests",
    verificationEvidence: "Verification Evidence",
    simulationEvidence: "Simulation Evidence",
    operationalEvidence: "Operational Evidence",
    operationalRun: "Operational Run",
    nonConformity: "Non-Conformity",
    nonConformities: "Non-Conformities",
    kpi_verified: "Verified",
    kpi_coverage: "Coverage",
    kpi_open_changes: "Open Change Requests",
  },
  manufacturing: {
    requirement: "Specification",
    requirements: "Specifications",
    requirement_description: "Describe the product specification or quality constraint.",
    block: "Component",
    blocks: "Components",
    block_description: "Describe this part, assembly, or production station.",
    testCase: "Quality Check",
    testCases: "Quality Checks",
    testCase_description: "Describe the inspection procedure and acceptance criteria.",
    link: "Dependency",
    links: "Dependencies",
    baseline: "Approved Revision",
    baselines: "Approved Revisions",
    changeRequest: "Change Order",
    changeRequests: "Change Orders",
    verificationEvidence: "Inspection Report",
    simulationEvidence: "Test Report",
    operationalEvidence: "Production Record",
    operationalRun: "Production Run",
    nonConformity: "Non-Conformance",
    nonConformities: "Non-Conformances",
    kpi_verified: "Passed Checks",
    kpi_coverage: "Specification Coverage",
    kpi_open_changes: "Open Change Orders",
  },
  personal: {
    requirement: "Goal",
    requirements: "Goals",
    requirement_description: "Describe the goal or constraint for this project.",
    block: "Element",
    blocks: "Elements",
    block_description: "Describe this device, service, or system element.",
    testCase: "Verification",
    testCases: "Verifications",
    testCase_description: "Describe how you will check this element is working correctly.",
    link: "Connection",
    links: "Connections",
    baseline: "Snapshot",
    baselines: "Snapshots",
    changeRequest: "Update",
    changeRequests: "Updates",
    verificationEvidence: "Verification Log",
    simulationEvidence: "Test Log",
    operationalEvidence: "Field Log",
    operationalRun: "Run Log",
    nonConformity: "Issue",
    nonConformities: "Issues",
    kpi_verified: "Completed",
    kpi_coverage: "Goal Coverage",
    kpi_open_changes: "Open Updates",
  },
  custom: {
    requirement: "Requirement",
    requirements: "Requirements",
    requirement_description: "Describe the need or constraint for this project.",
    block: "Block",
    blocks: "Blocks",
    block_description: "Describe this system element.",
    testCase: "Test Case",
    testCases: "Test Cases",
    testCase_description: "Describe how this item will be checked.",
    link: "Traceability Link",
    links: "Traceability Links",
    baseline: "Baseline",
    baselines: "Baselines",
    changeRequest: "Change Request",
    changeRequests: "Change Requests",
    verificationEvidence: "Verification Evidence",
    simulationEvidence: "Simulation Evidence",
    operationalEvidence: "Operational Evidence",
    operationalRun: "Operational Run",
    nonConformity: "Non-Conformity",
    nonConformities: "Non-Conformities",
    kpi_verified: "Verified",
    kpi_coverage: "Coverage",
    kpi_open_changes: "Open Change Requests",
  },
};

export function getLabels(profile: DomainProfile | null | undefined): LabelSet {
  return LABELS[profile ?? "engineering"] ?? LABELS.engineering;
}
