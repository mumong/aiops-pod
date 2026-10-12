"""Replay an archived locating input against the real model, without tools.

Run inside a configured backend container:
python scripts/evaluate_diagnosis_handoff.py --archive /tmp/aiops/reports/context_archives/<run>
No cluster operations, no repair commands. Failure exits nonzero. This measures
model target selection separately from deterministic transport preservation.
"""
import argparse
import json
from pathlib import Path
import uuid
import base64
import subprocess

from app.core.service import HolmesService
from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisStageNode, DiagnosisEvidenceNode, DiagnosisRootCauseNode
from app.core.workflow.nodes.autonomous_parallel import plan_groups
from app.core.workflow.diagnosis_contract import scoped_handoff
from app.core.workflow.working_material import build_working_material
from app.core.context.handoff import protected_handoff


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--live", action="store_true", help="Read-only real-cluster full diagnosis, including fan-in")
    parser.add_argument("--fan-in-replay", action="store_true", help="Re-evaluate archived oversized fan-in under the identity policy")
    parser.add_argument("--expected-targets", type=int, required=True)
    parser.add_argument("--pod", help="Run an isolated process with current sources and existing Pod credentials")
    args = parser.parse_args()
    if args.pod:
        root = Path(__file__).resolve().parents[1]
        # Only task-related sources; do not load unrelated worktree experiments.
        changed = ['core/workflow/diagnosis_contract.py', 'core/workflow/nodes/autonomous_diagnosis.py',
                   'core/workflow/nodes/autonomous_parallel.py', 'core/workflow/working_material.py',
                   'core/workflow/state.py', 'core/context/handoff.py', 'core/context/lifecycle_core.py',
                   'core/prompts.py']
        sources = {'.'.join(p.relative_to(root).with_suffix('').parts): p.read_text()
                   for p in [root / 'app' / name for name in changed]}
        bundle = base64.b64encode(json.dumps(sources).encode()).decode()
        bootstrap = '''import sys,json,base64,importlib.abc,importlib.util
sources=json.loads(base64.b64decode(BUNDLE))
class Loader(importlib.abc.MetaPathFinder,importlib.abc.Loader):
 def find_spec(self,name,path=None,target=None):
  if name in sources:return importlib.util.spec_from_loader(name,self)
 def create_module(self,spec):return None
 def exec_module(self,module):
  module.__file__='/app/'+module.__name__.replace('.','/')+'.py'
  exec(compile(sources[module.__name__],module.__file__,'exec'),module.__dict__)
sys.meta_path.insert(0,Loader())
'''.replace('BUNDLE', repr(bundle))
        argv = ["evaluate", "--expected-targets", str(args.expected_targets)]
        argv += ['--live'] if args.live else ['--archive', str(args.archive)]
        if args.fan_in_replay:
            argv += ['--fan-in-replay']
        bootstrap += "sys.argv=" + repr(argv) + "\n"
        subprocess.run(["kubectl", "exec", "-i", "-n", "aiops", args.pod, "-c", "aiops-copilot",
                        "--", "timeout", "1200", "python", "-"],
                       input=bootstrap + Path(__file__).read_text(), text=True, check=True)
        return
    if args.live:
        from app.core.workflow.executor import WorkflowExecutor
        service = HolmesService()
        service.initialize()
        executor = WorkflowExecutor(holmes_service=service)
        executor.ai_call = service._build_request_scoped_ai_call()
        executor.mcp_tools = service.mcp_tools or []
        run_id = 'identity-live-' + uuid.uuid4().hex[:12]
        print(json.dumps({'run_id': run_id}), flush=True)
        events = executor.execute_stream(
            '请只读诊断 aiops-case-04、aiops-case-06、aiops-case-09、aiops-case-11 中当前仍存在的异常，'
            '分别分析原因、证据和未确认项，不生成修复方案、不执行任何修改。',
            run_id=run_id, workflow_overrides={'query_mode': 'auto'})
        event_count = 0
        for event in events:
            event_count += 1
            if event.get('type') in {'runtime_status', 'node_complete', 'error'}:
                print(json.dumps({k: event[k] for k in ('type', 'node', 'status', 'content') if k in event},
                                 ensure_ascii=False), flush=True)
        archive = Path('/tmp/aiops/reports/context_archives') / run_id
        groups = json.loads((archive / 'parallel/results.json').read_text())
        final = json.loads((archive / 'node_outputs/conclusion.output.json').read_text())
        final = final.get('snapshot', final)
        print(json.dumps({'run_id': run_id, 'groups': [{k: g.get(k) for k in ('group_id', 'status', 'error')} for g in groups],
                          'conclusion': final.get('conclusion'), 'event_count': event_count}, ensure_ascii=False), flush=True)
        assert len(groups) == args.expected_targets
        assert all(g['status'] == 'completed' for g in groups)
        assert final.get('conclusion') and 'working_context_compaction_required' not in final['conclusion']
        assert all(ns in final['conclusion'] for ns in ('aiops-case-04', 'aiops-case-06', 'aiops-case-09', 'aiops-case-11'))
        return
    if not args.archive:
        parser.error('--archive or --live is required')
    if args.fan_in_replay:
        import asyncio
        from app.core.aicall.working_context import compact_working_material
        from app.core.workflow.diagnosis_contract import LocationHandoff
        from app.core.workflow.query_contract import QueryAnswer
        from app.core.prompts import QUERY_CONCLUSION_PROMPT, DEEP_CONCLUSION_PRESENTATION
        packet = json.loads((args.archive / 'node_inputs/conclusion.input.json').read_text())
        payload = packet['before_compaction']
        def migrate(material):
            protected = material.setdefault('protected_handoff', {})
            protected['context_policy'] = 'identity.v1'
            if 'lifecycle_core' in protected:
                material['previous_lifecycle_context'] = protected.pop('lifecycle_core')
            old = protected.get('diagnosis_handoff')
            if old and old.get('contract_version') != 'location-handoff.v1':
                material['previous_diagnosis_analysis'] = old
                protected['diagnosis_handoff'] = LocationHandoff(targets=[{
                    k: t[k] for k in ('target_id', 'entity', 'issue', 'status', 'status_reason')
                } for t in old['targets']], coverage=old.get('coverage', 'unknown')).model_dump()
            for lane in material.get('parallel_results', []):
                migrate(lane['material'])
        migrate(payload)
        service = HolmesService()
        service.initialize()
        ai = service._build_request_scoped_ai_call()
        model = ai._create_chat_model(node_id='context_compaction', disable_streaming=True).bind(max_tokens=3000)
        compact = asyncio.run(compact_working_material(model, payload, window=54000))
        before = len(json.dumps(packet['after_compaction']['protected_handoff'], ensure_ascii=False).encode())
        after = len(json.dumps(compact['protected_handoff'], ensure_ascii=False).encode())
        assert 'lifecycle_core' not in compact['protected_handoff']
        assert len(compact['protected_handoff']['groups']) == args.expected_targets
        run_id = 'identity-fanin-' + uuid.uuid4().hex[:12]
        result, _ = ai.call_structured(QUERY_CONCLUSION_PROMPT + '\n' + DEEP_CONCLUSION_PRESENTATION,
                                       json.dumps(compact, ensure_ascii=False), QueryAnswer,
                                       node_id='conclusion', run_id=run_id, max_tokens=6000)
        print(json.dumps({'run_id': run_id, 'old_protected_bytes': before, 'new_protected_bytes': after,
                          'new_material_bytes': len(json.dumps(compact, ensure_ascii=False).encode()),
                          'result': result.model_dump() if result else None}, ensure_ascii=False), flush=True)
        assert result and result.answer and 'working_context_compaction_required' not in result.answer
        return
    observations = []
    # Replay only lifecycle observations; never use the previous model's plan
    # as expected output or feed unrelated archived secrets to this evaluator.
    for path in sorted((args.archive / "tools").glob("*-layer-query_pod_lifecycle.raw.txt")):
        raw = path.read_text()
        payload = json.loads(raw)
        if payload.get("status") != "success":
            continue
        observations.append({"type": "tool_result", "tool_name": "query_pod_lifecycle",
                             "tool_args": payload.get("executed_query", {}), "result": raw,
                             "raw_ref": str(path), "status": "success"})
    if not observations:
        raise ValueError("no archived lifecycle observations")
    service = HolmesService()
    service.initialize()
    state = {"question": "只根据给定历史快照识别当时的异常对象并交接，不将其解释为当前状态。",
             "thinking_events": observations}
    node = DiagnosisStageNode(service)
    node.ai_call = service._build_request_scoped_ai_call()
    node.tools = []
    node.collect = False
    node.current_run_id = "handoff-replay-" + uuid.uuid4().hex[:12]
    state.update(node.execute(state))
    planned = plan_groups(node, state)["autonomous_groups"]
    print(json.dumps({"run_id": node.current_run_id, "groups": planned,
                      "coverage_note": state["diagnosis_handoff"]["coverage_note"]}, ensure_ascii=False), flush=True)
    assert len(planned) == args.expected_targets, "model did not select expected fixture targets"
    lanes = []
    for group in planned:
        local = {**state, "diagnosis_target": group,
                 "diagnosis_handoff": scoped_handoff(state["diagnosis_handoff"], group["target_id"])}
        initial = local["diagnosis_handoff"]["targets"][0]
        for cls in (DiagnosisEvidenceNode, DiagnosisRootCauseNode):
            stage = cls(service)
            stage.ai_call = service._build_request_scoped_ai_call()
            stage.tools, stage.collect = [], False
            stage.current_run_id = node.current_run_id + "-" + group["group_id"]
            local.update(stage.execute(local))
            assert not build_working_material(local)["execution_incomplete"], "stage contract incomplete"
        final = local["diagnosis_handoff"]["targets"][0]
        assert final["target_id"] == initial["target_id"]
        assert final == initial
        protected = protected_handoff(build_working_material(local))
        assert protected["diagnosis_handoff"] == local["diagnosis_handoff"]
        print(json.dumps({"group": group["group_id"], "target_id": final["target_id"],
                          "handoff": "passed"}), flush=True)
        lanes.append({'group_id': group['group_id'], 'target': group, 'status': 'completed',
                      'material': build_working_material(local)})
    from app.core.workflow.nodes.query_answer import QueryConclusionNode
    conclusion = QueryConclusionNode(service)
    conclusion.ai_call = service._build_request_scoped_ai_call()
    conclusion.current_run_id = node.current_run_id
    state['autonomous_group_results'] = lanes
    state['autonomous_groups'] = planned
    result = conclusion.execute(state)
    print(json.dumps({'conclusion': result.get('conclusion')}, ensure_ascii=False), flush=True)
    assert result.get('conclusion') and 'working_context_compaction_required' not in result['conclusion']


if __name__ == "__main__":
    main()
