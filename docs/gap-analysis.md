# Gap Analysis

ThreadLite has moved beyond the original gap-analysis phase. The product now implements federation, configuration comparison, verification evidence, closed-loop evidence variants, non-conformity handling, change lifecycle, connector import/export, standards contracts, graph-based traceability, and the major UX hardening work needed for a usable first release.

This document now serves as a short record of the remaining product-hardening gaps rather than a broad implementation plan.

## Residual Gaps

1. **AST trust hardening**
   - The revision snapshot chain is visible and checkable, but the repository does not yet use cryptographic signatures or a stronger Zero Trust-style attestation model for the full history.

2. **Optional governance hardening**
   - Change, baseline, configuration-context, and non-conformity workflows are operational, but stricter governance rules can still be added later if the product needs them.

3. **Graph layout variants**
   - The graph explorer is usable, but additional layouts may still be helpful if future projects become denser.

4. **Physical realization specificity**
   - Physical part linkage is supported through the current component and AP242-style contract surfaces, but the underlying part model remains intentionally lightweight.

## Current Status

The core user-facing product is operational. Any further work should be treated as hardening, interoperability expansion, or domain-specific refinement rather than missing foundational functionality.
