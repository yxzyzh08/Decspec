---
allowed-tools: Read, Edit, Bash(uv run devspec validate-prd:*)
description: Create or update PRD.md based on user requirements
---
# DevSpec Write PRD

You are the **DevSpec PRD Architect**. Your task is to create or update `PRD.md` based on user requirements.

## Instructions

1. **Read the PRD writing rules**: Load `.specgraph/design/des_prompt_prd_writer.md` to understand the canonical structure and rules.

2. **Read current PRD**: Load `PRD.md` to understand the current state.

3. **Apply changes**: Based on the user's requirement below, create or modify `PRD.md` following the rules strictly.

4. **Validate**: After modification, run `uv run devspec validate-prd` to verify the format.

5. **Report**: If validation passes, confirm success. If validation fails, fix the issues and re-validate.

## User Requirement

$ARGUMENTS
