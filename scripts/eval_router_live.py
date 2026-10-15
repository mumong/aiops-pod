"""Opt-in real-model intent evaluation. Classifies only; never runs cluster tools."""
import argparse
import ast
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CASES = [
    ('我的集群pod有什么问题？', 'full_diagnosis', 'cluster'),
    ('看看集群里的 Pod 有没有异常，帮我排查一下', 'full_diagnosis', 'cluster'),
    ('检查一下 xnet 命名空间的 Pod 是否健康', 'full_diagnosis', 'namespace'),
    ('xnet/api 为什么未就绪？', 'full_diagnosis', 'pod'),
    ('分析 xnet/api 最近10分钟重启的原因', 'full_diagnosis', 'pod'),
    ('帮我调查 xnet/api 启动失败的问题', 'full_diagnosis', 'pod'),
    ('查 xnet/api 的日志并分析为什么请求失败', 'full_diagnosis', 'pod'),
    ('查询我各个节点的cpu和内存使用率', 'focused', 'cluster'),
    ('列出非 Running 的 Pod，不分析原因', 'focused', 'cluster'),
    ('xnet/api 当前的状态是什么？', 'focused', 'pod'),
    ('查看 xnet/api 最近10分钟的日志，不做诊断', 'focused', 'pod'),
    ('统计 xnet 命名空间未就绪的 Pod 数量', 'focused', 'namespace'),
    ('查 xnet/api 的累计重启次数', 'focused', 'pod'),
    ('解释 CPU 使用率的计算口径', 'focused', None),
    ('解释 CrashLoopBackOff 是什么意思', 'focused', None),
    ('如何修改 readinessProbe？只解释，不执行', 'focused', None),
    ('在 xnet 创建一个 nginx 测试 Pod', 'focused', 'namespace'),
    ('帮我修复 xnet/api 的启动故障，先生成方案', 'remediation', 'pod'),
    ('刚才的修复执行了吗？', 'focused', None),
]


def literal(path, name):
    for n in ast.parse(path.read_text()).body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return ast.literal_eval(n.value)
    raise ValueError(name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', required=True)
    parser.add_argument('--prompts-file', type=Path, required=True)
    parser.add_argument('--baseline-file', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from app.core.aicall.client import AICall
    from app.core.workflow.nodes.request_router import RequestContract
    history = [{'question': '检查 xnet/api', 'answer': 'xnet/api 未就绪，原因待查',
                'request_contract': {'scope': 'pod', 'namespaces': ['xnet'], 'pod_names': ['api']}}]
    cases = [{'question': q, 'route': r, 'scope': s} for q, r, s in CASES]
    cases += [{'question': '只查它的内存使用量', 'history': history, 'route': 'focused', 'scope': 'pod'},
              {'question': '继续分析它为什么失败', 'history': history, 'route': 'full_diagnosis', 'scope': 'pod'},
              {'question': '帮我修复刚才那个 Pod', 'history': history, 'route': 'remediation', 'scope': 'pod'}]
    results = {}
    for label, path in [('baseline', args.baseline_file), ('candidate', args.prompts_file)]:
        if not path:
            continue
        prompt = literal(path, 'REQUEST_ROUTER_PROMPT')
        def evaluate(case, prompt=prompt):
            client = AICall(model=os.environ['LLM_MODEL'], api_key=os.environ['LLM_API_KEY'],
                            api_base=os.environ['LLM_API_BASE'])
            q = json.dumps({'question': case['question'], 'history': case.get('history', [])}, ensure_ascii=False)
            try:
                contract, _ = client.call_structured(system_prompt=prompt, question=q, schema=RequestContract,
                    node_id='request_router', max_tokens=1200, raise_on_error=True)
                actual = contract.model_dump()
                passed = actual['route'] == case['route'] and (case['scope'] is None or actual['scope'] == case['scope'])
                return {**case, 'actual': actual, 'passed': passed}
            except Exception as exc:
                return {**case, 'passed': False, 'error_type': type(exc).__name__}
        with ThreadPoolExecutor(max_workers=2) as pool:
            rows = list(pool.map(evaluate, cases))
        results[label] = rows
        args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print(json.dumps({'variant': label, 'passed': sum(r['passed'] for r in rows),
                          'total': len(rows), 'failures': [r for r in rows if not r['passed']]}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
