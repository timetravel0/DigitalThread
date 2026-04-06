# Use Cases — Who Is Digital Thread For?

> This document illustrates concrete use cases for the Digital Thread platform across two broad audiences: **individuals managing personal or home projects** and **small and medium-sized manufacturing businesses (SMBs)**. Each example shows how the platform vocabulary maps to the real-world context of that user.

---

## The Common Thread

Regardless of the domain, every use case in this document shares the same underlying structure:

```
Goals / Specifications  →  Elements / Components  →  Verifications / Quality Checks
         ↓                          ↓                           ↓
    Why it matters           What realizes it           How you prove it works
         ↓                          ↓                           ↓
                        Connections + Evidence + Snapshots
```

The platform adapts its vocabulary to your context. You never need to know what "MBSE" or "SysML" means to build a complete, traceable thread around your project.

---

## Personal Use Cases

These examples use the **Personal** domain profile. The platform will show: **Goals · Elements · Verifications · Connections · Snapshots · Updates · Issues**.

---

### Use Case P-1: Home Lab Infrastructure

**Context:** You are setting up a home server environment — a NAS, a VPN gateway, monitoring dashboards, and automatic backups. Equipment and software accumulate over months. Decisions get forgotten. When something breaks, you cannot remember what was changed last week or whether that component was ever tested properly.

**Why Digital Thread helps:** It gives your home infrastructure the same traceability discipline used in production systems — without the complexity. Every device and service is connected to the goal it serves. Every verification is recorded. When something breaks, you follow the thread back to find the cause.

**Example thread:**

| Layer | Examples |
|---|---|
| **Goals** | "NAS accessible from LAN and VPN", "Automated nightly backup of critical data", "Monitoring dashboard always available", "Container updates with safe rollback" |
| **Elements** | Raspberry Pi 5, OpenMediaVault, WireGuard VPN, Rclone + cron, Grafana + Prometheus, Watchtower |
| **Connections** | WireGuard → realizes → "NAS accessible from VPN"; Rclone → realizes → "Nightly backup" |
| **Verifications** | "SMB mount from external IP in ≤ 30s", "Rclone log: 0 errors over 7 nights", "Grafana responds on port 3000 for 30 days" |
| **Snapshots** | "v1.0 — Initial setup April 2026" — frozen before adding Nextcloud |
| **Updates** | When the NAS is replaced: open an Update, record the decision rationale, re-run affected Verifications |

**The real value:** Six months later, when the VPN stops working, you do not need to remember anything. Open the thread, find the Verification "SMB mount from external IP" marked as failed, check the last Update — it touched the router configuration. The thread leads you directly to the cause.

---

### Use Case P-2: Home Renovation Project

**Context:** You are renovating a bathroom. You have requirements (yours, or from a contractor), materials chosen, appointments with tradespeople, and inspections to pass. Everything lives on WhatsApp, scattered PDFs, and memory. When the project is finished — or when a problem emerges two years later — nothing is traceable.

**Why Digital Thread helps:** It creates a structured digital dossier of every decision and every verification performed. It works as both a project management tool during execution and a permanent record after completion.

**Example thread:**

| Layer | Examples |
|---|---|
| **Goals** | "Flush floor-level shower drain", "Electrical system compliant with CEI 64-8", "Mechanical heat recovery ventilation ≥ 40 m³/h" |
| **Elements** | Kaldewei shower tray, Electrical system (contractor Rossi), Zehnder VMC unit |
| **Connections** | Kaldewei tray → realizes → "Flush floor-level drain" |
| **Verifications** | "Hydraulic pressure test at 3 bar", "Electrical compliance certificate", "VMC airflow test at 40 m³/h" |
| **Snapshots** | "Shell complete — February", "Final handover — May" |
| **Updates** | Plumber changes tile material: open an Update, record the decision, adjust the Verification if needed |
| **Issues** | Grout cracking found at 6 months: log as Issue, link to the Element and Verification, track resolution |

**The real value:** At project end, you have a structured digital dossier with every decision made and every verification performed — useful for warranty claims, future maintenance, and property transfer documentation.

---

### Use Case P-3: Personal Software Project or Home Automation

**Context:** You are building a home automation system using Home Assistant, or developing a personal software tool (a bot, a self-hosted service, a custom script suite). Features grow incrementally. Over time, you lose track of which feature was added for what reason, what is currently working, and what broke after the last update.

**Why Digital Thread helps:** It provides lightweight requirements management and verification tracking for solo developers — giving personal projects the same discipline as professional ones, without heavyweight process.

**Example thread:**

| Layer | Examples |
|---|---|
| **Goals** | "Lights turn off automatically when no motion for 10 min", "Morning routine triggered at sunrise ± 15 min", "All automations recoverable after power loss" |
| **Elements** | Home Assistant core, Motion sensor (Aqara), Zigbee2MQTT, Automation scripts |
| **Connections** | Aqara sensor + HA automation → realizes → "Lights off on no motion" |
| **Verifications** | "Motion timeout test: lights off after 10 min", "Sunrise trigger accuracy over 7 days", "Power cycle recovery test" |
| **Snapshots** | "Stable config v2 — March 2026" |
| **Updates** | Upgrading Home Assistant to a new major version: open an Update, re-run Verifications after upgrade |

---

## Manufacturing SMB Use Cases

These examples use the **Manufacturing** domain profile. The platform will show: **Specifications · Components · Quality Checks · Dependencies · Approved Revisions · Change Orders · Non-Conformances · Production Records**.

---

### Use Case M-1: Custom Mechanical Component Production (Job Shop)

**Context:** A small CNC machining shop produces parts on commission. Specifications arrive as drawings or verbal instructions via email. Inspection results are written in paper logbooks. When a non-conformance arrives from the customer three months later, there is no traceable record of which machine produced the part, which operator ran the inspection, or what the acceptance criteria were at the time.

**Why Digital Thread helps:** Every specification is captured, every component (machine, operator, fixture) is linked to it, and every Quality Check is recorded with its result. The complete production history is navigable in seconds.

**Example thread:**

| Layer | Examples |
|---|---|
| **Specifications** | "Shaft diameter Ø25h6 ±0.013mm", "Surface roughness Ra ≤ 0.8 μm", "Material: C45 normalized and tempered" |
| **Components** | Mazak QT-200 CNC lathe, Mitutoyo micrometer, Operator Mario Bianchi |
| **Quality Checks** | "Dimensional check with micrometer — 100% sampling", "Roughness measurement at 3 points per part", "Material certificate verification" |
| **Production Records** | Batch 24/03: 50 parts, result 48/50 conforming, 2 rejected. Linked to Mazak QT-200 and operator. |
| **Approved Revisions** | "Rev. B — April 2026" after customer updated tolerance to ±0.010mm |
| **Change Orders** | Customer requests Ra ≤ 0.4 instead of Ra ≤ 0.8: Change Order tracks impact on cycle time and tooling cost |
| **Non-Conformances** | Part SN-0412: diameter out of tolerance → scrapped → root cause: worn tooling on Mazak station 2 |

**The real value:** When the non-conformance arrives, in under 30 seconds you identify that Batch 12 was machined on the Mazak with tool T-07 and the roughness check was performed by operator Bianchi using instrument MIT-003. Full traceability without Excel reconstruction.

---

### Use Case M-2: New Product Development (NPD)

**Context:** An SMB is developing a new machine or industrial device. Product requirements exist in email threads. Components are managed in CAD. Test results are in the technician's notebook. When the CE marking audit arrives, no one can produce a structured record proving that each requirement was verified — because the information was never connected.

**Why Digital Thread helps:** The CE technical file is built as a natural byproduct of the development process — not reconstructed from scratch for the audit.

**Example thread:**

| Layer | Examples |
|---|---|
| **Specifications** | "Operating temperature: −10°C to +55°C", "Protection rating: IP54 minimum", "Compliance: Machinery Directive 2006/42/EC" |
| **Components** | Control board rev. 3, IP54 enclosure, Brushless motor, Firmware v2.1 |
| **Quality Checks** | "Thermal cycle test −10/+55°C (48h)", "IP54 dust and water ingress test", "Risk assessment per EN ISO 12100" |
| **Test Reports** | External lab report, internal measurement sheets, declaration of conformity — each linked to its Quality Check |
| **Approved Revisions** | "Design Freeze Rev. 1.0 — March 2026" before pilot production |
| **Change Orders** | Motor supplier changes model: Change Order with impact analysis on all previously executed tests |

**The real value:** The technical dossier for CE marking is not created from scratch for the audit — it is already structured in the thread. Export it, present it.

---

### Use Case M-3: Assembly Line Quality Management

**Context:** A manufacturing line has work instructions, intermediate inspections, and final functional tests. When a field defect is reported, tracing the serial number back to the assembly station, operator, and shift requires hours of searching through paper records, with no guarantee of completeness.

**Why Digital Thread helps:** Every serial number's production history — which station, which operator, which tool, which inspection result — is linked together in the thread. Recall scope identification takes seconds instead of hours.

**Example thread:**

| Layer | Examples |
|---|---|
| **Specifications** | "M8 bolt torque: 25 Nm ±2", "Bearing axial play: 0.05–0.10 mm", "Functional test: 500 on/off cycles without error" |
| **Components** | Station S1 (press), Station S3 (torque), Final test bench |
| **Quality Checks** | "Torque check with calibrated wrench", "Axial play measurement with dial gauge", "500-cycle automatic on/off test" |
| **Production Runs** | Each shift: serial numbers produced, inspection results, operators on duty, machines used |
| **Non-Conformances** | "SN-00412: axial play out of tolerance → scrapped → root cause: bearing batch B-2203 from supplier X" |
| **Change Orders** | Bearing supplier change: Change Order with tolerance update and Quality Check re-validation |

**The real value:** In a product recall scenario, isolate all serial numbers from the affected batch in seconds and immediately know which inspections were — or were not — performed on each unit.

---

### Use Case M-4: Supplier and Subcontract Management

**Context:** An SMB delegates machining, surface treatment, or welding to subcontractors. Specifications are sent by email. Compliance certificates arrive as unstructured PDFs. When a supplier is replaced, no one knows exactly which specifications the previous supplier was qualified against, and which the new one must meet.

**Why Digital Thread helps:** Every specification is linked to the supplier component that must satisfy it, and every compliance certificate is recorded as evidence against the corresponding Quality Check. Supplier qualification history is fully traceable.

**Example thread:**

| Layer | Examples |
|---|---|
| **Specifications** | "Weld class B per EN ISO 5817", "Heat treatment: quench and temper 28–34 HRC", "Material certificate type 3.1 required" |
| **Components** | Supplier Alpha (welding), Supplier Beta (heat treatment) |
| **Quality Checks** | "Visual weld inspection per EN ISO 5817", "Hardness measurement HRC at 3 points", "Material certificate verification" |
| **Inspection Reports** | PDFs from Alpha and Beta, each linked to the corresponding Quality Check and Specification |
| **Approved Revisions** | Each revision of the supplier technical specification document |
| **Change Orders** | Replacing Supplier Alpha with Gamma: Change Order with re-qualification scope and new Inspection Reports |

**The real value:** During a customer qualification audit or a supplier review, present the complete thread: every specification has its conformity evidence, every supplier has its qualification history. Nothing needs to be reconstructed.

---

### Use Case M-5: ISO 9001 / Quality Management System Support

**Context:** A small manufacturer is working toward or maintaining ISO 9001 certification. The QMS requires documented procedures, records of inspections, traceability of non-conformances, and evidence of corrective actions. Maintaining this in spreadsheets and shared drives creates duplication, version confusion, and audit preparation nightmares.

**Why Digital Thread helps:** The platform's data model maps naturally onto the ISO 9001 process approach: specifications are the quality objectives, Quality Checks are the monitoring and measurement activities, Non-Conformances are recorded with their root causes, and Change Orders track corrective actions. The thread is the QMS record.

**Example mapping:**

| ISO 9001 Concept | Digital Thread Element |
|---|---|
| Quality objective / requirement | Specification |
| Process / equipment | Component |
| Monitoring & measurement activity | Quality Check |
| Record of inspection results | Production Record / Inspection Report |
| Non-conformance | Non-Conformance |
| Corrective action | Change Order |
| Document revision control | Approved Revision |
| Management review snapshot | Baseline / Approved Revision |

---

## Cross-Domain Value Summary

The platform delivers the same core value in every context above — expressed differently depending on who is using it:

| Audience | The question it answers |
|---|---|
| Home lab owner | "Why did I set this up, and does it still work as intended?" |
| DIY / renovation | "What decisions were made, who verified them, and what changed?" |
| Job shop | "Which machine, operator, and tool produced this part, and what were the inspection results?" |
| NPD team | "Which requirement was verified by which test, and what is the evidence?" |
| Assembly line | "Which serial numbers are affected, and were they inspected?" |
| Supply chain | "Which supplier is qualified against which specification, and what is the evidence?" |

In every case, the answer is a thread — a connected path from need to realization to proof. That is what this platform builds.
