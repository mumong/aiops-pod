"""Structured remediation plan models.

These models are intentionally small and deterministic. The LLM may propose a
plan in the conclusion, but execution code only consumes this normalized shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RemediationAction:
    id: str
    type: str
    description: str
    risk: str = "medium"
    dry_run_command: Optional[str] = None
    execute_command: Optional[str] = None
    verify_command: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RemediationPlan:
    remediation_available: bool
    fix_type: str
    risk_level: str
    requires_human_approval: bool = True
    issue_groups: List[Dict[str, Any]] = field(default_factory=list)
    basis: List[str] = field(default_factory=list)
    actions: List[RemediationAction] = field(default_factory=list)
    stop_conditions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RemediationRuntimeConfig:
    executor: str = "deterministic"
    max_iterations: int = 4
    max_write_actions: int = 2
    max_duration_seconds: int = 900
    verify_settle_seconds: float = 0.0
