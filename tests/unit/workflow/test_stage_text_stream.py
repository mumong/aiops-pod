"""Stage prose reaches the live stream (cc5f9fc7: 19 visible characters per stage).

Deep stages deliver their analysis inside the structured result, so the stream had
reasoning only. After delivery the node streams the same text once as ai_message;
lane queues tag it with the group/cluster like every other event.
"""

import queue
from types import SimpleNamespace

from app.core.aicall.client import AICall
from app.core.workflow.nodes.autonomous_diagnosis import (
    DiagnosisEvidenceNode,
    DiagnosisRootCauseNode,
    DiagnosisStageNode,
)
from app.core.workflow.nodes.autonomous_parallel import LaneQueue


def node(cls, q):
    n = cls.__new__(cls)
    n.ai_call = SimpleNamespace(_push=AICall._push)
    n._event_queue = q
    return n


def drained(q):
    out = []
    while not q.empty():
        out.append(q.get_nowait()[1])
    return out


def test_layer_and_evidence_stream_their_analysis():
    q = queue.Queue()
    node(DiagnosisStageNode, q)._publish_stage_text({}, "  发现 4 个异常 Pod  ")
    node(DiagnosisEvidenceNode, q)._publish_stage_text({}, "")  # nothing delivered: nothing shown
    (event,) = drained(q)
    assert event["type"] == "ai_message" and event["node"] == "layer"
    assert event["full_content"] == "发现 4 个异常 Pod"


def test_rca_streams_conclusion_and_cause_inside_its_lane():
    q = queue.Queue()
    lane = LaneQueue(q, group_id="g3", entities=[{"namespace": "aiops-case-09", "name": "w"}])
    case = {"summary": "探针端口配置错误", "cause": "readiness 探测 8081，应用监听 8080"}
    node(DiagnosisRootCauseNode, lane)._publish_stage_text(
        {"diagnosis_case_result": case}, "完整报告"
    )
    (event,) = drained(q)
    assert event["node"] == "parallel_evidence" and event["lane_stage"] == "rca"
    assert event["parallel_context"]["group_id"] == "g3"
    assert event["full_content"] == (
        "**诊断结论**：探针端口配置错误\n\n**原因**：readiness 探测 8081，应用监听 8080"
    )
