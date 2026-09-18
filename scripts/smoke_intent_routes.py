"""Read-only live smoke test in an isolated Python process inside an existing Pod.

Loads current app sources in memory, not into the serving process or Pod files.
Uses the Pod's existing model/MCP configuration without exporting credentials.
Run: .venv/bin/python scripts/smoke_intent_routes.py --pod <backend-pod>
"""
import argparse
import base64
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pod', required=True)
    parser.add_argument('--question', action='append')
    parser.add_argument('--routing-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    # Include all application modules so the tested process matches the worktree,
    # not a mixture of new callers and old deployed dependencies.
    sources = {'.'.join(p.relative_to(root).with_suffix('').parts): p.read_text()
               for p in (root / 'app').rglob('*.py') if p.name != '__init__.py'}
    questions = args.question or [
        '我的 xnet 命名空间有哪些 Pod？只列名称和状态。',
        '这些 Pod 有什么异常需要排查？分析原因。',
        '查询这些 Pod 当前的 CPU 和内存使用情况。',
        '分析 aiops-case-08/workload-5c9c7b6489-s7p79 频繁重启的根因。',
    ]
    bundle = base64.b64encode(json.dumps({'sources': sources, 'questions': questions, 'routing_only': args.routing_only}).encode()).decode()
    remote = '''
import base64, json, importlib.abc, importlib.util, sys, logging, uuid, os
logging.basicConfig(level=logging.CRITICAL, force=True)
bundle = json.loads(base64.b64decode(BUNDLE))
class Loader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path=None, target=None):
        if name in bundle['sources']: return importlib.util.spec_from_loader(name, self)
    def create_module(self, spec): return None
    def exec_module(self, module):
        module.__file__ = '/app/' + module.__name__.replace('.', '/') + '.py'
        exec(compile(bundle['sources'][module.__name__], module.__file__, 'exec'), module.__dict__)
sys.meta_path.insert(0, Loader())
from app.core.service import HolmesService
from app.core.workflow.executor import WorkflowExecutor
service = HolmesService()
service.initialize()
print(json.dumps({'context_window': os.getenv('MODEL_CONTEXT_WINDOW'), 'tools': len(service.mcp_tools)}, ensure_ascii=False), flush=True)
session = ('isolated-smoke', uuid.uuid4().hex)
for question in bundle['questions']:
    if bundle.get('routing_only'):
        from app.core.workflow.nodes.request_router import RequestRouterNode
        node = RequestRouterNode()
        node.ai_call = service._build_request_scoped_ai_call()
        print(json.dumps({'question': question, 'result': node.execute({'question': question})}, ensure_ascii=False), flush=True)
        continue
    executor = WorkflowExecutor(service)
    executor.ai_call = service._build_request_scoped_ai_call()
    executor.mcp_tools = service.mcp_tools
    run_id = 'intent-smoke-' + uuid.uuid4().hex[:12]
    print(json.dumps({'run_id': run_id, 'question': question}, ensure_ascii=False), flush=True)
    completed = False
    for event in executor.execute_stream(question, run_id=run_id, workflow_overrides={
        'query_mode': 'auto', '_query_session_key': session, 'remediation': {'enabled': False},
    }):
        if event.get('type') == 'node_start':
            print('NODE ' + event['node'], flush=True)
        elif event.get('thinking_type') == 'tool_result':
            print(json.dumps({k:event.get(k) for k in ('node','tool_name','tool_args','status')}, ensure_ascii=False), flush=True)
        elif event.get('type') == 'final':
            completed = True
            print(json.dumps({k:event.get(k) for k in ('request_route','request_contract','query_answer','session_memory','elapsed_seconds')}, ensure_ascii=False), flush=True)
        elif event.get('type') == 'error':
            print(json.dumps(event, ensure_ascii=False), flush=True)
    if not completed: raise RuntimeError('Smoke run did not produce final result')
'''.replace('BUNDLE', repr(bundle))
    subprocess.run(['kubectl', '-n', 'aiops', 'exec', '-i', args.pod,
                    '-c', 'aiops-copilot', '--', 'python3', '-'], input=remote, text=True, check=True)


if __name__ == '__main__':
    main()
