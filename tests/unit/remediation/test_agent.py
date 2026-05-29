from app.core.remediation.agent import AgentDecision, RemediationAgentConfig, RemediationAgentExecutor
from app.core.remediation.approval import ApprovalStore
from app.core.remediation.models import RemediationAction, RemediationPlan


def _plan():
    return RemediationPlan(
        remediation_available=True,
        fix_type="patch_workload_resources",
        risk_level="low",
        basis=["OOMKilled", "memory limit too low"],
        actions=[
            RemediationAction(
                id="a1",
                type="kubectl_set",
                description="increase memory",
                dry_run_command="kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi --dry-run=server",
                execute_command="kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi",
                verify_command="kubectl get pod -l app=memhog -n aiops-e2e",
            )
        ],
    )


def test_agent_mode_stops_failed_when_pod_still_unhealthy_after_iterations():
    calls = []

    def runner(command):
        calls.append(command)
        if "get pod" in command:
            return "memhog 0/1 CrashLoopBackOff OOMKilled"
        return "ok"

    decisions = [
        AgentDecision(
            decision="run_command",
            description="increase memory",
            dry_run_command="kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi --dry-run=server",
            command="kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi",
            verify_command="kubectl get pod -l app=memhog -n aiops-e2e",
        ),
        AgentDecision(decision="finish", status="failed", reason="Pod still OOMKilled after resource update"),
    ]

    executor = RemediationAgentExecutor(
        approval_store=ApprovalStore(),
        command_runner=runner,
        decision_provider=lambda **_: decisions.pop(0),
    )

    events = list(
        executor.run(
            run_id="run1",
            plan=_plan(),
            report="report",
            approval_mode="auto",
            config=RemediationAgentConfig(max_iterations=3, max_write_actions=2),
        )
    )

    assert calls == [
        "kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi --dry-run=server",
        "kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi",
        "kubectl get pod -l app=memhog -n aiops-e2e",
    ]
    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "failed"
    assert "still OOMKilled" in events[-1]["reason"]


def test_agent_mode_does_not_auto_succeed_from_single_ready_observation():
    def runner(command):
        return "memhog 1/1 Running restartCount=0 Ready=True"

    executor = RemediationAgentExecutor(
        approval_store=ApprovalStore(),
        command_runner=runner,
        decision_provider=lambda **_: AgentDecision(
            decision="run_command",
            description="verify pod health",
            command="kubectl get pod -l app=memhog -n aiops-e2e",
        ),
    )

    events = list(
        executor.run(
            run_id="run1",
            plan=_plan(),
            report="report",
            approval_mode="auto",
            config=RemediationAgentConfig(max_iterations=2, max_write_actions=1),
        )
    )

    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "failed"
    assert "iteration limit" in events[-1]["reason"].lower()


def test_agent_mode_succeeds_when_agent_finishes_after_verification():
    decisions = [
        AgentDecision(
            decision="run_command",
            description="verify pod health",
            command="kubectl get pod -l app=memhog -n aiops-e2e",
        ),
        AgentDecision(
            decision="finish",
            status="success",
            reason="g1 OOMKilled group verified Running and Ready with restartCount stable",
        ),
    ]

    executor = RemediationAgentExecutor(
        approval_store=ApprovalStore(),
        command_runner=lambda command: "memhog 1/1 Running restartCount=0 Ready=True",
        decision_provider=lambda **_: decisions.pop(0),
    )

    events = list(
        executor.run(
            run_id="run1",
            plan=_plan(),
            report="report",
            approval_mode="auto",
            config=RemediationAgentConfig(max_iterations=3, max_write_actions=1),
        )
    )

    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "success"
    assert "g1" in events[-1]["reason"]


def test_agent_mode_ignores_empty_command_decision_after_field_verify():
    plan = RemediationPlan(
        remediation_available=True,
        fix_type="patch_workload_resources",
        risk_level="low",
        issue_groups=[
            {
                "group_id": "g1",
                "problem_type": "CreateContainerConfigError",
                "target": "aiops-e2e/Deployment/appconfigfail",
                "auto_fixable": True,
            }
        ],
        basis=["missing APP_BOOT_MODE"],
        actions=[
            RemediationAction(
                id="a1",
                type="kubectl_set",
                description="为 Deployment appconfigfail 添加缺失的环境变量 APP_BOOT_MODE。",
                dry_run_command=(
                    "kubectl set env deployment/appconfigfail -n aiops-e2e "
                    "APP_BOOT_MODE=local --dry-run=server"
                ),
                execute_command="kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=local",
                verify_command=(
                    "kubectl get deployment appconfigfail -n aiops-e2e "
                    "-o jsonpath='{.spec.template.spec.containers[0].env}'"
                ),
                metadata={"group_id": "g1"},
            )
        ],
    )
    decisions = [
        AgentDecision(
            decision="run_command",
            description="为 Deployment appconfigfail 添加缺失的环境变量 APP_BOOT_MODE。",
            dry_run_command=(
                "kubectl set env deployment/appconfigfail -n aiops-e2e "
                "APP_BOOT_MODE=local --dry-run=server"
            ),
            command="kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=local",
            verify_command=(
                "kubectl get deployment appconfigfail -n aiops-e2e "
                "-o jsonpath='{.spec.template.spec.containers[0].env}'"
            ),
        ),
        AgentDecision(
            decision="run_command",
            description="bad follow-up dry-run only decision",
            dry_run_command=(
                "kubectl set env deployment/appconfigfail -n aiops-e2e "
                "APP_BOOT_MODE=local --dry-run=server"
            ),
            command="",
            reason="field verification is not terminal health verification",
        ),
        AgentDecision(
            decision="finish",
            status="failed",
            reason="field update succeeded but workload health still requires rollout or pod verification",
        ),
    ]

    def runner(command):
        if "jsonpath" in command:
            return '[{"name":"APP_BOOT_MODE","value":"local"}]'
        return "deployment.apps/appconfigfail env updated"

    executor = RemediationAgentExecutor(
        approval_store=ApprovalStore(),
        command_runner=runner,
        decision_provider=lambda **_: decisions.pop(0),
    )

    events = list(
        executor.run(
            run_id="run1",
            plan=plan,
            report="report",
            approval_mode="auto",
            config=RemediationAgentConfig(max_iterations=3, max_write_actions=1),
        )
    )

    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "failed"
    assert "workload health" in events[-1]["reason"]
    assert decisions == []


def test_agent_mode_auto_finishes_after_planned_action_terminal_health_verify_success():
    plan = RemediationPlan(
        remediation_available=True,
        fix_type="restart_workload",
        risk_level="low",
        issue_groups=[
            {
                "group_id": "g1",
                "problem_type": "CrashLoopBackOff",
                "target": "aiops-e2e/Deployment/appconfigfail",
                "auto_fixable": True,
            }
        ],
        basis=["workload needs restart"],
        actions=[
            RemediationAction(
                id="a1",
                type="kubectl_rollout",
                description="restart deployment",
                execute_command="kubectl rollout restart deployment/appconfigfail -n aiops-e2e",
                verify_command="kubectl rollout status deployment/appconfigfail -n aiops-e2e --timeout=60s",
                metadata={"group_id": "g1"},
            )
        ],
    )
    decisions = [
        AgentDecision(
            decision="run_command",
            description="restart deployment",
            command="kubectl rollout restart deployment/appconfigfail -n aiops-e2e",
            verify_command="kubectl rollout status deployment/appconfigfail -n aiops-e2e --timeout=60s",
        ),
        AgentDecision(decision="run_command", command="", reason="should not be called after terminal verification"),
    ]

    def runner(command):
        if "rollout status" in command:
            return 'deployment "appconfigfail" successfully rolled out'
        return "deployment.apps/appconfigfail restarted"

    executor = RemediationAgentExecutor(
        approval_store=ApprovalStore(),
        command_runner=runner,
        decision_provider=lambda **_: decisions.pop(0),
    )

    events = list(
        executor.run(
            run_id="run1",
            plan=plan,
            report="report",
            approval_mode="auto",
            config=RemediationAgentConfig(max_iterations=3, max_write_actions=1),
        )
    )

    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "success"
    assert "a1" in events[-1]["reason"]
    assert len(decisions) == 1


def test_agent_mode_preserves_multiple_issue_groups_in_plan_payload():
    store = ApprovalStore()
    plan = RemediationPlan(
        remediation_available=True,
        fix_type="patch_workload_resources",
        risk_level="medium",
        requires_human_approval=True,
        issue_groups=[
            {"group_id": "g1", "problem_type": "OOMKilled", "target": "aiops-e2e/deployment/memhog"},
            {"group_id": "g2", "problem_type": "ImagePullFailed", "target": "default/statefulset/test-redis"},
        ],
        basis=["multi issue"],
        actions=[],
    )
    executor = RemediationAgentExecutor(
        approval_store=store,
        decision_provider=lambda **_: AgentDecision(decision="finish", status="failed", reason="manual only"),
    )

    events = executor.run(run_id="run1", plan=plan, report="report", approval_timeout_seconds=0.01)
    approval_event = next(events)

    assert approval_event["type"] == "remediation_approval_required"
    assert approval_event["payload"]["issue_groups"][0]["group_id"] == "g1"
    assert approval_event["payload"]["issue_groups"][1]["group_id"] == "g2"


def test_agent_mode_reports_failed_tool_result_when_command_runner_raises():
    executor = RemediationAgentExecutor(
        approval_store=ApprovalStore(),
        command_runner=lambda command: (_ for _ in ()).throw(RuntimeError("forbidden")),
        decision_provider=lambda **_: AgentDecision(
            decision="run_command",
            description="patch pod finalizer",
            command="kubectl patch pod terminating-stuck -n aiops-e2e --type=merge",
        ),
    )

    events = list(
        executor.run(
            run_id="run1",
            plan=_plan(),
            report="report",
            approval_mode="auto",
            config=RemediationAgentConfig(max_iterations=1, max_write_actions=1),
        )
    )

    assert events[-2]["type"] == "remediation_tool_result"
    assert events[-2]["status"] == "failed"
    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "failed"
    assert "forbidden" in events[-1]["reason"]


def test_agent_mode_treats_verify_not_found_as_success_for_finalizer_remediation():
    decisions = [
        AgentDecision(
            decision="run_command",
            description="移除 Pod finalizer 以解除 Terminating",
            command="kubectl patch pod terminating-stuck -n aiops-e2e --type=merge",
            verify_command="kubectl get pod terminating-stuck -n aiops-e2e",
        ),
        AgentDecision(
            decision="finish",
            status="success",
            reason="g1 verified: Pod NotFound after finalizer removal",
        ),
    ]

    def runner(command):
        if command.startswith("kubectl get pod"):
            raise RuntimeError('Error from server (NotFound): pods "terminating-stuck" not found')
        return "pod/terminating-stuck patched"

    executor = RemediationAgentExecutor(
        approval_store=ApprovalStore(),
        command_runner=runner,
        decision_provider=lambda **_: decisions.pop(0),
    )

    events = list(
        executor.run(
            run_id="run1",
            plan=_plan(),
            report="report",
            approval_mode="auto",
            config=RemediationAgentConfig(max_iterations=2, max_write_actions=1),
        )
    )

    verify_event = next(event for event in events if event.get("stage") == "verify")
    assert verify_event["status"] == "success"
    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "success"


def test_agent_review_mode_requires_plan_approval_before_finalizer_patch_action():
    store = ApprovalStore()
    calls = []
    plan = RemediationPlan(
        remediation_available=True,
        fix_type="remove_finalizer",
        risk_level="medium",
        requires_human_approval=True,
        issue_groups=[
            {
                "group_id": "g1",
                "problem_type": "TerminatingStuck",
                "target": "pod/terminating-stuck",
                "auto_fixable": True,
            }
        ],
        basis=["deletionTimestamp exists", "finalizers non-empty"],
        actions=[
            RemediationAction(
                id="remove-finalizer-g1",
                type="kubectl",
                description="Remove confirmed blocking finalizer",
                dry_run_command="kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
                execute_command=(
                    "kubectl patch pod terminating-stuck -n aiops-e2e "
                    "-p '{\"metadata\":{\"finalizers\":null}}' --type=merge"
                ),
                verify_command="kubectl get pod terminating-stuck -n aiops-e2e",
                metadata={"group_id": "g1"},
            )
        ],
    )

    def runner(command):
        calls.append(command)
        if command.startswith("kubectl get pod") and any(call.startswith("kubectl patch pod") for call in calls):
            raise RuntimeError('Error from server (NotFound): pods "terminating-stuck" not found')
        if command.startswith("kubectl get pod"):
            return "finalizers: aiops.e2e/hold"
        return "pod/terminating-stuck patched"

    executor = RemediationAgentExecutor(
        approval_store=store,
        command_runner=runner,
        decision_provider=lambda **_: AgentDecision(
            decision="run_command",
            description="Remove confirmed blocking finalizer",
            dry_run_command="kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
            command=(
                "kubectl patch pod terminating-stuck -n aiops-e2e "
                "-p '{\"metadata\":{\"finalizers\":null}}' --type=merge"
            ),
            verify_command="kubectl get pod terminating-stuck -n aiops-e2e",
        ),
    )

    events = executor.run(run_id="run-review-finalizer", plan=plan, report="report", approval_mode="review")

    plan_approval = next(events)
    assert plan_approval["type"] == "remediation_approval_required"
    assert plan_approval["approval_kind"] == "plan"
    assert calls == []
    store.resolve("run-review-finalizer", plan_approval["approval_id"], approved=True, reviewer="tester")

    action_approval = next(events)
    assert action_approval["type"] == "remediation_approval_required"
    assert action_approval["approval_kind"] == "action"
    assert calls == []
    store.resolve("run-review-finalizer", action_approval["approval_id"], approved=True, reviewer="tester")

    remaining = list(events)
    assert any(event.get("stage") == "execute" for event in remaining)
    assert calls[0].startswith("kubectl get pod")
    assert calls[1].startswith("kubectl patch pod terminating-stuck")


def test_agent_auto_mode_runs_finalizer_patch_without_approval_events():
    calls = []
    plan = RemediationPlan(
        remediation_available=True,
        fix_type="remove_finalizer",
        risk_level="medium",
        requires_human_approval=True,
        issue_groups=[
            {
                "group_id": "g1",
                "problem_type": "TerminatingStuck",
                "target": "pod/terminating-stuck",
                "auto_fixable": True,
            }
        ],
        basis=["deletionTimestamp exists", "finalizers non-empty"],
        actions=[
            RemediationAction(
                id="remove-finalizer-g1",
                type="kubectl",
                description="Remove confirmed blocking finalizer",
                dry_run_command="kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
                execute_command=(
                    "kubectl patch pod terminating-stuck -n aiops-e2e "
                    "-p '{\"metadata\":{\"finalizers\":null}}' --type=merge"
                ),
                verify_command="kubectl get pod terminating-stuck -n aiops-e2e",
                metadata={"group_id": "g1"},
            )
        ],
    )

    def runner(command):
        calls.append(command)
        if command.startswith("kubectl get pod") and any(call.startswith("kubectl patch pod") for call in calls):
            raise RuntimeError('Error from server (NotFound): pods "terminating-stuck" not found')
        if command.startswith("kubectl get pod"):
            return "finalizers: aiops.e2e/hold"
        return "pod/terminating-stuck patched"

    executor = RemediationAgentExecutor(
        approval_store=ApprovalStore(),
        command_runner=runner,
        decision_provider=lambda **_: AgentDecision(
            decision="run_command",
            description="Remove confirmed blocking finalizer",
            dry_run_command="kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
            command=(
                "kubectl patch pod terminating-stuck -n aiops-e2e "
                "-p '{\"metadata\":{\"finalizers\":null}}' --type=merge"
            ),
            verify_command="kubectl get pod terminating-stuck -n aiops-e2e",
        ),
    )

    events = list(
        executor.run(
            run_id="run-auto-finalizer",
            plan=plan,
            report="report",
            approval_mode="auto",
            config=RemediationAgentConfig(max_iterations=2, max_write_actions=1),
        )
    )

    assert all(event["type"] != "remediation_approval_required" for event in events)
    assert calls[0].startswith("kubectl get pod")
    assert calls[1].startswith("kubectl patch pod terminating-stuck")
    assert any(event.get("stage") == "verify" and event["status"] == "success" for event in events)
    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "success"
