"""Per-request tool guards; constrain target scope without prescribing a plan."""

import json
import re

import promql_parser as promql

from langchain_core.tools import StructuredTool


def promql_scope_error(query, namespaces):
    """Validate every selector, including selectors nested in joins/subqueries.

    Never rewrite a query: doing so could silently change joins, absence tests,
    or aggregate denominators. Regex scopes are accepted only when their finite
    literal alternatives are provably inside the request's namespace set.
    """
    allowed = set(namespaces)
    try:
        tree = promql.parse(query)
    except (ValueError, TypeError) as exc:
        return f"Invalid PromQL: {exc}"
    errors = []

    def confined(matcher):
        if matcher.name != "namespace":
            return False
        if matcher.op == promql.MatchOp.Equal:
            return matcher.value in allowed
        if matcher.op == promql.MatchOp.Re:
            # Kubernetes namespace names cannot contain regex metacharacters.
            pattern = matcher.value.removeprefix("^").removesuffix("$")
            if pattern.startswith("(?:") and pattern.endswith(")"):
                pattern = pattern[3:-1]
            elif pattern.startswith("(") and pattern.endswith(")"):
                pattern = pattern[1:-1]
            return bool(re.fullmatch(r"[a-z0-9-]+(?:\|[a-z0-9-]+)*", pattern)) and set(pattern.split("|")) <= allowed
        return False

    def visit(node):
        if not isinstance(node, promql.VectorSelector):
            return
        groups = node.matchers.or_matchers or [node.matchers.matchers]
        for matchers in groups:
            if any(confined(matcher) for matcher in matchers):
                continue
            # Related host evidence is allowed, but must name a host rather
            # than quietly querying every node in a namespace-scoped task.
            if (node.name or "").startswith(("node_", "kube_node_")) and any(
                matcher.name in {"node", "instance"} and matcher.op == promql.MatchOp.Equal
                and matcher.value for matcher in matchers
            ):
                continue
            errors.append(f"Selector {node.name or str(node.matchers)} needs namespace restricted to {sorted(allowed)}")

    promql.walk(tree, pre_visit=visit)
    return "; ".join(errors) if errors else None


def scope_tool(tool, namespaces):
    """Guard explicit namespace arguments on a cloned tool, never shared state.

    Cluster-scoped node/namespace lookups remain possible for related evidence.
    This is a task boundary, not a substitute for backend authorization.
    """
    if not namespaces or not getattr(tool, "args_schema", None):
        return tool
    schema = tool.args_schema
    schema_dict = schema if isinstance(schema, dict) else schema.model_json_schema()
    query_key = {
        "execute_prometheus_instant_query": "query",
        "execute_prometheus_range_query": "query",
        "get_series": "match",
    }.get(tool.name)
    if "namespace" not in schema_dict.get("properties", {}) and not query_key:
        return tool
    allowed = frozenset(namespaces)

    def error(args):
        if query_key:
            reason = promql_scope_error(args.get(query_key, ""), allowed)
            if reason:
                return json.dumps({"status": "tool_error", "semantic_success": False, "error": reason}, ensure_ascii=False)
            return None
        kind = str(args.get("kind") or args.get("resource_type") or "").lower()
        if kind in {"node", "nodes", "namespace", "namespaces", "ns"}:
            return None
        if args.get("namespace") not in allowed:
            return json.dumps({
                "status": "tool_error", "semantic_success": False,
                "error": "Namespace outside request scope or missing; choose an explicit requested namespace.",
                "allowed_namespaces": sorted(allowed),
            }, ensure_ascii=False)
        return None

    async def invoke_async(**kwargs):
        denied = error(kwargs)
        return denied if denied else await tool.ainvoke(kwargs)

    def invoke_sync(**kwargs):
        denied = error(kwargs)
        return denied if denied else tool.invoke(kwargs)

    return StructuredTool.from_function(
        func=invoke_sync, coroutine=invoke_async, name=tool.name,
        description=tool.description, args_schema=tool.args_schema,
    )
