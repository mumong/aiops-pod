# Delivery preference

- After requested code changes and relevant verification, deploy changed AIOps services to the existing Kubernetes environment by default; the user performs acceptance testing in the frontend.
- Report deployed versions, rollout/health checks, and any incomplete verification. If tests or deployment fail, report the failure rather than claiming the change is live.
- Preserve existing credentials, PVC data and unrelated configuration. Updating code does not authorize automatic Git commits or pushes without a separate request.
- Explanation-only or review-only requests do not authorize application changes or redeployment.
