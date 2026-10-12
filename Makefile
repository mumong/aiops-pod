# K8s AIOps Copilot Makefile
.DEFAULT_GOAL := build

IMAGE_REPOSITORY := xnet.registry.io:8443
PROJECT := xnet-cloud
IMAGE_NAME := aiops-copilot
DOCKER_NAME := $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME)
A2A_IMAGE_NAME := aiops-a2a-adapter
A2A_DOCKER_NAME := $(IMAGE_REPOSITORY)/$(PROJECT)/$(A2A_IMAGE_NAME)
A2A_TEST_AGENT_IMAGE_NAME := aiops-a2a-test-agent
A2A_TEST_AGENT_DOCKER_NAME := $(IMAGE_REPOSITORY)/$(PROJECT)/$(A2A_TEST_AGENT_IMAGE_NAME)

VERSION ?= $(shell cat VERSION)
PYTHON ?= .venv/bin/python
RUFF ?= .venv-quality/bin/ruff
DOCKER_TAG := $(VERSION)
A2A_PUBLIC_HOST ?= $(shell kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
A2A_PUBLIC_URL ?= http://$(A2A_PUBLIC_HOST):30801

.PHONY: build build-main build-a2a build-a2a-test-agent build-all push push-main push-a2a push-a2a-test-agent push-all test-a2a deploy deploy-master deploy-slave delete restart logs sync-version \
	case-list case-list-variants case-render case-deploy case-validate case-ask case-deploy-errors case-deploy-all case-clean case-clean-variants

.PHONY: help test-unit test-replay check check-syntax lint

help:
	@echo "build-main / build-a2a: container artifacts (Python service, no native binary)"
	@echo "test-unit: isolated unit tests and Runbook contracts"
	@echo "test-replay: historical evidence replay; known failures are documented"
	@echo "check: syntax + unit + replay; lint: static correctness checks"
	@echo "Setup: CONTRIBUTING.md; baseline: docs/maintenance-normalization.md"

test-unit:
	$(PYTHON) -m pytest tests/unit test/workflow/test_runbook_remediation_guidance.py -q

test-replay:
	$(PYTHON) -m pytest tests/replay -q

check-syntax:
	$(PYTHON) scripts/check_syntax.py

lint:
	$(RUFF) check app tests scripts

check: check-syntax test-unit test-replay

build: build-main build-a2a

build-main:
	@echo "Building $(DOCKER_NAME):$(DOCKER_TAG)..."
	docker build -t $(DOCKER_NAME):$(DOCKER_TAG) .

build-a2a:
	@echo "Building $(A2A_DOCKER_NAME):$(DOCKER_TAG)..."
	docker build --build-arg VERSION=$(DOCKER_TAG) -f Dockerfile.a2a -t $(A2A_DOCKER_NAME):$(DOCKER_TAG) .

build-a2a-test-agent:
	@echo "Building $(A2A_TEST_AGENT_DOCKER_NAME):$(DOCKER_TAG)..."
	docker build --build-arg VERSION=$(DOCKER_TAG) -f Dockerfile.a2a-test-agent -t $(A2A_TEST_AGENT_DOCKER_NAME):$(DOCKER_TAG) .

build-all: build build-a2a-test-agent

push: push-main push-a2a

push-main:
	@echo "Pushing $(DOCKER_NAME):$(DOCKER_TAG)..."
	docker push $(DOCKER_NAME):$(DOCKER_TAG)

push-a2a:
	@echo "Pushing $(A2A_DOCKER_NAME):$(DOCKER_TAG)..."
	docker push $(A2A_DOCKER_NAME):$(DOCKER_TAG)

push-a2a-test-agent:
	@echo "Pushing $(A2A_TEST_AGENT_DOCKER_NAME):$(DOCKER_TAG)..."
	docker push $(A2A_TEST_AGENT_DOCKER_NAME):$(DOCKER_TAG)

push-all: push push-a2a-test-agent

test-a2a:
	@test -x .venv-a2a/bin/python || (echo "先执行: python3 -m venv .venv-a2a && .venv-a2a/bin/pip install -r requirements.a2a-dev.txt" && exit 1)
	.venv-a2a/bin/python -m pytest -q tests/a2a

# 通用部署（不修改 federation 配置，直接应用当前 configmap）
deploy:
	@test -n "$(A2A_PUBLIC_HOST)" || (echo "无法自动获取 Node InternalIP；请设置 A2A_PUBLIC_HOST=<可访问IP>" && exit 1)
	@echo "Deploying AIOps Pod (main container + A2A sidecar) with version $(DOCKER_TAG)..."
	@sed -i 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME):.*|image: $(DOCKER_NAME):$(DOCKER_TAG)|' deploy/k8s-simple.yaml
	@sed -i 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(A2A_IMAGE_NAME):.*|image: $(A2A_DOCKER_NAME):$(DOCKER_TAG)|' deploy/k8s-simple.yaml
	@sed -i '/- name: A2A_PUBLIC_URL/{n;s|^\([[:space:]]*\)value:.*|\1value: "$(A2A_PUBLIC_URL)"|;}' deploy/k8s-simple.yaml
	@kubectl create namespace aiops --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f deploy/ --recursive
	@echo "Waiting for rollout to complete..."
	kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s
	@if kubectl get deployment/aiops-copilot-frontend -n aiops >/dev/null 2>&1; then \
		echo "Refreshing frontend DNS after backend Service recreation..."; \
		kubectl rollout restart deployment/aiops-copilot-frontend -n aiops; \
		kubectl rollout status deployment/aiops-copilot-frontend -n aiops --timeout=300s; \
	fi

# 主集群部署：federation.enabled = true，然后 deploy
deploy-master:
	@echo "Deploying as MASTER cluster (federation enabled)..."
	@sed -i '/^    federation:/,/^    [^ ]/{s/enabled: false/enabled: true/}' deploy/configmap/config.yaml
	$(MAKE) deploy
	@echo "✅ Master cluster deployed successfully!"

# 子集群部署：federation.enabled = false，然后 deploy
deploy-slave:
	@echo "Deploying as SLAVE cluster (federation disabled)..."
	@sed -i '/^    federation:/,/^    [^ ]/{s/enabled: true/enabled: false/}' deploy/configmap/config.yaml
	$(MAKE) deploy
	@echo "✅ Slave cluster deployed successfully!"

delete:
	@echo "Deleting app resources only (keeping namespace, PVC and PV)..."
	kubectl delete deployment/aiops-copilot service/aiops-copilot -n aiops --ignore-not-found
	kubectl delete -f deploy/rbac.yaml --ignore-not-found
	kubectl delete -f deploy/secrets/ --recursive --ignore-not-found
	kubectl delete -f deploy/configmap/ --recursive --ignore-not-found

restart:
	@echo "Restarting pods..."
	kubectl rollout restart deployment/aiops-copilot -n aiops
	kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s

logs:
	kubectl logs -f deployment/aiops-copilot -n aiops

sync-version:
	@echo "Syncing version to $(DOCKER_TAG)..."
	sed -i 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME):.*|image: $(DOCKER_NAME):$(DOCKER_TAG)|' deploy/k8s-simple.yaml
	sed -i 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(A2A_IMAGE_NAME):.*|image: $(A2A_DOCKER_NAME):$(DOCKER_TAG)|' deploy/k8s-simple.yaml

# ============================================================
# Pod 异常测试 Case 库（test/pod-anomaly-cases，源自 aiopsdata 仓库）
# 用法:
#   make case-list                  # 列出全部 case（id/名称/维度覆盖）
#   make case-deploy CASE=c07       # 部署单个 case
#   make case-validate CASE=c07     # 等待异常成立并验收遥测
#   make case-ask CASE=c07          # 对该 case 的 namespace 跑 /ask 定向诊断并保存报告
#   make case-deploy-errors         # 只部署 c01-c11 并精确触发 c11，不执行遥测验收
#   make case-deploy-all            # 部署全部非破坏性 case
#   make case-clean                 # 清理全部 case namespace（先安全释放 c11 finalizer）
# ============================================================
CASES_DIR := test/pod-anomaly-cases
CASE_MANAGER := python3 $(CASES_DIR)/scripts/manage_cases.py

case-list:
	@$(CASE_MANAGER) list

case-list-variants:
	@$(CASE_MANAGER) list --variants

case-render:
	@$(CASE_MANAGER) render --case "$(CASE)"

case-deploy:
	@test -n "$(CASE)" || (echo "用法: make case-deploy CASE=c07" && exit 1)
	@$(CASE_MANAGER) deploy --case "$(CASE)"

case-validate:
	@test -n "$(CASE)" || (echo "用法: make case-validate CASE=c07" && exit 1)
	@$(CASE_MANAGER) validate --case "$(CASE)"

case-ask:
	@test -n "$(CASE)" || (echo "用法: make case-ask CASE=c07" && exit 1)
	@ns=$$($(CASE_MANAGER) namespace --case "$(CASE)") || exit 1; \
	pod=$$(kubectl get pods -n aiops -l app=aiops-copilot -o jsonpath='{.items[0].metadata.name}'); \
	q=$$(python3 -c "import urllib.parse; print(urllib.parse.quote('请诊断 $$ns 命名空间中的异常 Pod，为什么异常？'))"); \
	out=reports/case-$(CASE)-$$(date +%Y%m%d_%H%M%S).txt; mkdir -p reports; \
	echo "🩺 对 $$ns 执行 /ask，报告将保存到 $$out"; \
	kubectl exec -n aiops $$pod -- sh -c "curl -s --max-time 1500 'http://localhost:8000/ask?q='$$q'&format=text&stream=true'" | tee $$out | tail -80

case-deploy-errors:
	@deletion_timestamp=$$(kubectl -n aiops-case-11 get pod workload \
		-o jsonpath='{.metadata.deletionTimestamp}' 2>/dev/null || true); \
	if test -n "$$deletion_timestamp"; then \
		echo "释放上一次 c11 finalizer..."; \
		kubectl -n aiops-case-11 patch pod workload --type=json \
			-p='[{"op":"remove","path":"/metadata/finalizers"}]' || true; \
		kubectl -n aiops-case-11 wait --for=delete pod/workload --timeout=120s; \
	fi
	kubectl apply -k $(CASES_DIR)/safe
	kubectl -n aiops-case-11 wait --for=condition=Ready pod/workload --timeout=180s
	@telemetry_ready=false; \
	for _attempt in $$(seq 1 30); do \
		if kubectl -n aiops-case-11 logs pod/workload --tail=20 2>/dev/null | grep -q '"event":"http_request"'; then \
			telemetry_ready=true; \
			break; \
		fi; \
		sleep 2; \
	done; \
	if test "$$telemetry_ready" != true; then \
		echo "c11 在触发删除前没有产生 traced request" >&2; \
		exit 1; \
	fi
	kubectl -n aiops-case-11 delete pod workload --wait=false
	@echo "c01-c11 已部署；c11 已触发 Terminating。请等待约 3 分钟后再执行遥测验收。"

case-deploy-all:
	$(CASES_DIR)/scripts/deploy-safe.sh

case-clean:
	@if test -n "$(CASE)"; then \
		$(CASE_MANAGER) clean --case "$(CASE)"; \
	else \
		$(CASES_DIR)/scripts/cleanup.sh; \
	fi

case-clean-variants:
	@$(CASE_MANAGER) clean --variants

# 专属自动修复验收：仅 c04、c06、c09、c11
.PHONY: repair-cases-reset repair-cases-clean repair-cases-status
repair-cases-reset:
	@python3 $(CASES_DIR)/scripts/repair_cases.py reset

repair-cases-clean:
	@python3 $(CASES_DIR)/scripts/repair_cases.py clean

repair-cases-status:
	@python3 $(CASES_DIR)/scripts/repair_cases.py status
