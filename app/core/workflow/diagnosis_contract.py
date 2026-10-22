"""Stage-owned diagnosis handoff, independent of symptoms and tool selection.

Models select targets and evidence. Code preserves identity and previously
published facts; it does not decide whether an observation is a fault.
"""

from copy import deepcopy
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.workflow.contract_coercion import TextItems
from app.core.workflow.pod_detection import PodAssessment


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DiagnosisEntity(ContractModel):
    kind: str = Field(min_length=1)
    namespace: str = ""
    name: str = Field(min_length=1)
    uid: str = ""

    @field_validator("kind")
    @classmethod
    def canonical_pod_kind(cls, value):
        # Kubernetes Kind spelling, not fault inference. Keep other resource
        # kinds unchanged so this does not broaden Pod-only branch scope.
        return "Pod" if value.strip().casefold() == "pod" else value


class LocationTarget(ContractModel):
    target_id: str = Field(min_length=1, max_length=120)
    entity: DiagnosisEntity
    issue: str = Field(min_length=1, max_length=320, description="简短异常现象，不写完整分析")
    status: Literal["investigate", "assessed", "deferred", "excluded"] = "investigate"
    status_reason: str = Field(default="", max_length=240)
    evidence_refs: Annotated[list[str], TextItems] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def disposition(self):
        if self.status in {"deferred", "excluded"} and not self.status_reason.strip():
            raise ValueError("deferred/excluded targets require a reason")
        return self


class LocationHandoff(ContractModel):
    pod_assessment: PodAssessment | None = None
    contract_version: Literal["location-handoff.v1"] = "location-handoff.v1"
    targets: list[LocationTarget]
    coverage: Literal["complete", "partial", "unknown"] = "unknown"
    coverage_note: str = Field(default="", max_length=320)

    @model_validator(mode="after")
    def identities(self):
        ids = [t.target_id for t in self.targets]
        entities = [(t.entity.kind, t.entity.namespace, t.entity.name) for t in self.targets]
        if len(ids) != len(set(ids)) or len(entities) != len(set(entities)):
            raise ValueError("duplicate target identity")
        return self


class LocationOutput(ContractModel):
    analysis: str = Field(description="定位分析文字，可按上下文策略摘要；不复制原始工具全文")
    handoff: LocationHandoff


class DiagnosisFact(ContractModel):
    fact_id: str = Field(min_length=1)
    summary: str = Field(
        min_length=1, description="关键原始事实，不复制完整工具正文；保留数值、单位或原始错误"
    )
    observed_at: str = Field(description="源端观测时间；无法确定时留空，不猜测")
    evidence_refs: list[str] = Field(
        min_length=1, description="实际工具返回或归档引用；不是 Runbook 判断"
    )
    previous_fact_id: str = Field(default="", description="由传递层记录版本关联；新增事实留空")


class DiagnosisFinding(ContractModel):
    summary: str
    certainty: Literal["hypothesis", "supported", "confirmed", "refuted"]
    fact_ids: list[str]


class DiagnosisTarget(ContractModel):
    target_id: str = Field(min_length=1, description="本次诊断稳定标识；下游原样沿用")
    entity: DiagnosisEntity
    issue: str = Field(min_length=1)
    status: Literal["investigate", "assessed", "deferred", "excluded"] = "investigate"
    status_reason: str = ""
    facts: list[DiagnosisFact] = Field(default_factory=list)
    findings: list[DiagnosisFinding] = Field(default_factory=list)
    unknowns: Annotated[list[str], TextItems] = Field(default_factory=list)
    next_questions: Annotated[list[str], TextItems] = Field(default_factory=list)
    runbook_refs: Annotated[list[str], TextItems] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_identity_and_disposition(self):
        ids = [f.fact_id for f in self.facts]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate fact_id within target")
        if self.status in {"deferred", "excluded"} and not self.status_reason.strip():
            raise ValueError("deferred/excluded targets require a reason")
        return self


class DiagnosisHandoff(ContractModel):
    pod_assessment: PodAssessment | None = None
    contract_version: Literal["diagnosis-handoff.v1"] = "diagnosis-handoff.v1"
    summary: str
    targets: list[DiagnosisTarget]
    coverage: Literal["complete", "partial", "unknown"] = "unknown"
    limitations: Annotated[list[str], TextItems] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_targets(self):
        ids = [t.target_id for t in self.targets]
        entities = [(t.entity.kind, t.entity.namespace, t.entity.name) for t in self.targets]
        if len(ids) != len(set(ids)) or len(entities) != len(set(entities)):
            raise ValueError("duplicate target identity")
        return self


def scoped_handoff(handoff, target_id):
    result = deepcopy(handoff)
    result["targets"] = [t for t in result["targets"] if t["target_id"] == target_id]
    if not result["targets"]:
        raise ValueError(f"unknown diagnosis target: {target_id}")
    # Global prose can refer to siblings; retain only this target's structured data.
    if "summary" in result:
        result["summary"] = result["targets"][0]["issue"]
    return result
