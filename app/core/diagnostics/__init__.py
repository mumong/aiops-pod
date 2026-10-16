"""Run diagnostics: a per-call ledger, engineering findings and a run report.

The ledger is derived from the events every agent call already emits; findings
are deterministic classifications of *how the run behaved* (bursts, repeats,
stalls, provider errors, deliveries) - never of the Kubernetes fault itself.
"""
