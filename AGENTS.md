# Delivery preference

- After requested code changes and relevant verification, deploy changed AIOps services to the existing Kubernetes environment by default; the user performs acceptance testing in the frontend.
- Report deployed versions, rollout/health checks, and any incomplete verification. If tests or deployment fail, report the failure rather than claiming the change is live.
- Preserve existing credentials, PVC data and unrelated configuration. Updating code does not authorize automatic Git commits or pushes without a separate request.
- Explanation-only or review-only requests do not authorize application changes or redeployment.

# Design before implementation

- Before any development or behavior change, first inspect the relevant current implementation and explain the proposed design: objective, control flow, component responsibilities, impact on existing behavior, and verification criteria. Do not start coding merely to make a requested feature work.
- For meaningful technical choices involving architecture, routing, permissions, safety controls, approval/execution boundaries, data handling, or compatibility, present the recommendation and material tradeoffs, ask the user to decide, and wait for confirmation before implementation or deployment. Do not interpret a broad feature request as approval of a particular control mechanism.
- Ask concise questions when requirements are ambiguous or alternative implementations materially change how the system behaves. Do not invent the user's preferred design. Clearly bounded changes with no material design choice may proceed after a brief design explanation; avoid unnecessary approval rounds for routine implementation details.
- Implement only the agreed design. If investigation reveals a need to depart from it or expand scope, pause and explain the new decision before making the change.
- Keep agent autonomy separate from generic engineering safeguards. Do not introduce fault-specific scripts, mandatory evidence collection, or hidden fallback behavior without discussing the design and obtaining approval.
- Verify both the requested capability and preservation of existing behavior. Report tests, deployment status, known failures, and unverified areas separately; passing unit tests or health checks is not proof of full end-to-end acceptance.
