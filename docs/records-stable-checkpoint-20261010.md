# Records integration checkpoint — 2026-10-10

This checkpoint saves the already deployed optional selection/counting capability,
not the pending evidence-view experiments or the follow-up audit recommendations.

## Release boundary

- Backend: `11.0.205-records-20261009`; only the record-result parser, lossless
  observation hook and SSE projection change serving behavior.
- Frontend: `0.1.39`; an alias of the tested `0.1.39-records-20261009` image,
  preserving the repository's numeric-version contract. Image content is unchanged.
- MCP: `7.0.34-records-20261009`; generic row operations, lifecycle adapter and tests.
- A2A remains `11.0.168-security-20260924`. Model, credentials and PVC data are unchanged.

The backend observation file is staged from the verified release source. Other
local evidence-view changes are deliberately left uncommitted. Build reproducible
artifacts from a clean checkout of this commit, not the experimental worktree.

VERSION and image references now identify the tested images. Redeployment reuses
those images without rebuilding or overwriting existing tags. The live cluster uses
locally imported images with `IfNotPresent`; source registry policy is preserved.
Do not run the backend's generic `make deploy` for this scoped release: it also
rewrites the A2A tag to the backend version and applies unrelated configuration.

## Verification and limitations

See [release verification](evidence-record-release-20261009.md) and
[full audit](../testreports/records-audit-20261009/report.md).

The prior audit recorded backend 1735 passed / 2 failed, MCP 263 passed, frontend
94 passed, and A2A 17 passed / 1 failed. Existing replay-contract and A2A failures
remain open. "Stable checkpoint" does not mean every diagnostic path is correct.

Checkpoint verification reran backend syntax and 1733 unit/Runbook tests, MCP
syntax and 263 tests, and frontend 94 tests/lint/TypeScript/build successfully.
Replay again returned 2 passed / 2 known failures. The backend's three changed
serving files and MCP's four changed serving files match the tested images by
SHA256; the frontend build output is byte-identical to the prior release output.
The frontend numeric image alias preserves the original image config ID.

No cache-delivery redesign, concurrent-evidence deduplication, legacy table-filter
fix, monitoring reconfiguration, prompt change or repair behavior change is part
of this checkpoint. Raw run archives, local credentials, virtual environments and
temporary experiment artifacts are not part of the commit.
