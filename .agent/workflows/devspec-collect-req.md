---
description: decompose user requirements without modifying the code.
---

---
allowed-tools: Read, Edit, Bash(uv run devspec validate-prd:*)
description: Collect, analyze and decompose user requirements
---
## Instructions

1. **Log Raw Input**: Append the user's raw requirement to `origin_req/raw_requirements.md` with a timestamp.

2. **Vision Check**: Check if the requirement aligns with the Product Vision in `PRD.md`.
   - If NOT aligned: Stop and explain why. Do not update any documentation.
   - If aligned: Proceed to decomposition.

3. **Decomposition & Doc Update**:
   - **Cross-Domain**: Generate Domain-level subtasks. Update `product.yaml`.
   - **Domain-Level**: Generate Feature-level subtasks. Update `product.yaml` and create/update `feat_*.yaml`.
   - **Feature-Level**: Generate Component-level subtasks. Update `feat_*.yaml` and create/update `comp_*.yaml`.
   - **Component-Level**: Update `comp_*.yaml`.

4. **Report**: Generate a summary report in `reports/` folder with timestamp.

## User Requirement

$ARGUMENTS
