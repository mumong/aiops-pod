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
# pip inside `docker build` needs the host's network/proxy on this build host:
# the default bridge network reported "Network is unreachable" and broke releases.
BUILD_NETWORK ?= host
DOCKER_BUILD := docker build --network=$(BUILD_NETWORK) \
	$(if $(http_proxy),--build-arg http_proxy=$(http_proxy),) \
	$(if $(https_proxy),--build-arg https_proxy=$(https_proxy),) \
	$(if $(no_proxy),--build-arg no_proxy=$(no_proxy),)
A2A_PUBLIC_HOST ?= $(shell kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
A2A_PUBLIC_URL ?= http://$(A2A_PUBLIC_HOST):30801

.PHONY: build release build-main build-a2a build-a2a-test-agent build-all push push-main push-a2a push-a2a-test-agent push-all test-a2a deploy deploy-master deploy-slave delete restart logs sync-version \
	case-list case-list-variants case-render case-deploy case-validate case-ask case-deploy-errors case-deploy-all case-clean case-clean-variants

.PHONY: help test-unit check check-syntax lint format format-check

help:
	@echo "build-main / build-a2a: container artifacts (Python service, no native binary)"
	@echo "test-unit: isolated unit tests and Runbook contracts"
	@echo "check: syntax + lint + format-check + unit; lint: ruff E9/F/I/B; format: ruff format"
	@echo "Docs: README.md, docs/ARCHITECTURE.md"

test-unit:
	$(PYTHON) -m pytest -q

check-syntax:
	$(PYTHON) scripts/check_syntax.py

LINT_PATHS := app tests scripts a2a_adapter a2a_test_agent tools

lint:
	$(RUFF) check $(LINT_PATHS)

format:
	$(RUFF) format $(LINT_PATHS)

format-check:
	$(RUFF) format --check $(LINT_PATHS)

check: check-syntax lint format-check test-unit

build: build-main build-a2a

# Release = build and push both images, then a rolling `deploy` (no delete):
# the old Pod keeps serving until the new one is Ready, and a failed rollout is
# undone automatically. `make delete` stays available for manual resets.
release: build push deploy

build-main:
	@echo "Building $(DOCKER_NAME):$(DOCKER_TAG)..."
	$(DOCKER_BUILD) -t $(DOCKER_NAME):$(DOCKER_TAG) .

build-a2a:
	@echo "Building $(A2A_DOCKER_NAME):$(DOCKER_TAG)..."
	$(DOCKER_BUILD) --build-arg VERSION=$(DOCKER_TAG) -f Dockerfile.a2a -t $(A2A_DOCKER_NAME):$(DOCKER_TAG) .

build-a2a-test-agent:
	@echo "Building $(A2A_TEST_AGENT_DOCKER_NAME):$(DOCKER_TAG)..."
	$(DOCKER_BUILD) --build-arg VERSION=$(DOCKER_TAG) -f Dockerfile.a2a-test-agent -t $(A2A_TEST_AGENT_DOCKER_NAME):$(DOCKER_TAG) .

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
	@kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s || { \
		echo "Rollout failed; rolling back to the previous ReplicaSet..."; \
		kubectl -n aiops logs deployment/aiops-copilot -c aiops-copilot --tail=40 2>/dev/null | tail -40; \
		kubectl rollout undo deployment/aiops-copilot -n aiops; \
		kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s; \
		exit 1; }
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

# ============================================================================
# 多集群（specs/008-multi-cluster）
# 运维与测试用的 kubeconfig 只在本机（MC_KUBE_DIR），不进入镜像、ConfigMap 或 Secret。
# ============================================================================
MC_KUBE_DIR ?= $(HOME)/.kube/aiops-mc
MC_KEY_FILE ?= $(MC_KUBE_DIR)/runner.key
CENTER_KUBECONFIG ?= $(MC_KUBE_DIR)/center
RUNNER_VERSION ?= $(shell cat deploy-edge/VERSION)
RUNNER_IMAGE := $(IMAGE_REPOSITORY)/$(PROJECT)/aiops-edge-runner
# 测试环境用自己的 Harbor（无推送权限），镜像经 SSH 导入节点缓存：MC_PULL_POLICY=IfNotPresent MC_LOAD_HOSTS=10.2.5.88
MC_PULL_POLICY ?= Always
MC_LOAD_HOSTS ?=
.PHONY: runner-build runner-push mc-keygen edge-deploy edge-delete sync-xnet-cert test-multicluster deploy-mc

runner-build:
	$(DOCKER_BUILD) --build-arg VERSION=$(RUNNER_VERSION) -f Dockerfile.edge-runner -t $(RUNNER_IMAGE):$(RUNNER_VERSION) .

runner-push:
	docker push $(RUNNER_IMAGE):$(RUNNER_VERSION)

# 中心与边缘共用的 runner 签名密钥，只生成一次，保存在本机运维目录。
mc-keygen:
	@test -f $(MC_KEY_FILE) || { umask 077; python3 -c 'import secrets; print(secrets.token_hex(32))' > $(MC_KEY_FILE); echo "generated $(MC_KEY_FILE)"; }

# 在边缘集群本地部署 runner：make edge-deploy EDGE_KUBECONFIG=~/.kube/aiops-mc/edge-88
edge-deploy: mc-keygen
	@test -n "$(EDGE_KUBECONFIG)" || { echo "EDGE_KUBECONFIG 未设置" >&2; exit 1; }
	@KUBECONFIG=$(EDGE_KUBECONFIG) kubectl create namespace aiops --dry-run=client -o yaml | KUBECONFIG=$(EDGE_KUBECONFIG) kubectl apply -f -
	@$(PYTHON) deploy-edge/render_policy.py deploy/configmap/config.yaml > /tmp/aiops-edge-policy.$$$$.json \
		&& KUBECONFIG=$(EDGE_KUBECONFIG) kubectl -n aiops create configmap aiops-edge-runner-policy \
			--from-file=policy.json=/tmp/aiops-edge-policy.$$$$.json --dry-run=client -o yaml | KUBECONFIG=$(EDGE_KUBECONFIG) kubectl apply -f - ; \
		rm -f /tmp/aiops-edge-policy.$$$$.json
	@KUBECONFIG=$(EDGE_KUBECONFIG) kubectl -n aiops create secret generic aiops-edge-key --from-file=key=$(MC_KEY_FILE) \
		--dry-run=client -o yaml | KUBECONFIG=$(EDGE_KUBECONFIG) kubectl apply -f -
	@if test -n "$(MC_LOAD_HOSTS)"; then deploy-edge/load_image.sh $(RUNNER_IMAGE):$(RUNNER_VERSION) $(MC_LOAD_HOSTS); fi
	sed -e 's|image: $(RUNNER_IMAGE):.*|image: $(RUNNER_IMAGE):$(RUNNER_VERSION)|' \
		-e 's|imagePullPolicy: Always|imagePullPolicy: $(MC_PULL_POLICY)|' deploy-edge/runner.yaml | KUBECONFIG=$(EDGE_KUBECONFIG) kubectl apply -f -
	KUBECONFIG=$(EDGE_KUBECONFIG) kubectl -n aiops rollout restart deployment/aiops-edge-runner
	KUBECONFIG=$(EDGE_KUBECONFIG) kubectl -n aiops rollout status deployment/aiops-edge-runner --timeout=180s

edge-delete:
	@test -n "$(EDGE_KUBECONFIG)" || { echo "EDGE_KUBECONFIG 未设置" >&2; exit 1; }
	KUBECONFIG=$(EDGE_KUBECONFIG) kubectl delete -f deploy-edge/runner.yaml --ignore-not-found
	KUBECONFIG=$(EDGE_KUBECONFIG) kubectl -n aiops delete configmap aiops-edge-runner-policy secret aiops-edge-key --ignore-not-found

# 部署时把 xnet 的隧道客户端证书复制到我们的命名空间（只读 xnet，不在 xnet 命名空间创建任何对象），
# 并下发 runner 签名密钥。make sync-xnet-cert CENTER_KUBECONFIG=...
sync-xnet-cert: mc-keygen
	@set -e; d=$$(mktemp -d); trap 'rm -rf $$d' EXIT; \
	K="kubectl --kubeconfig $(CENTER_KUBECONFIG)"; \
	$$K -n xnet get secret xnet-client-cert -o jsonpath='{.data.cert\.pem}' | base64 -d > $$d/cert.pem; \
	$$K -n xnet get secret xnet-client-cert -o jsonpath='{.data.key\.pem}' | base64 -d > $$d/key.pem; \
	$$K -n xnet get secret xnet-ca-cert -o jsonpath='{.data.cert\.pem}' | base64 -d > $$d/ca.pem; \
	for ns in mcp aiops; do \
		$$K create namespace $$ns --dry-run=client -o yaml | $$K apply -f - >/dev/null; \
		$$K -n $$ns create secret generic aiops-xnet-client-cert --from-file=$$d/cert.pem --from-file=$$d/key.pem \
			--from-file=$$d/ca.pem --dry-run=client -o yaml | $$K apply -f -; \
		$$K -n $$ns create secret generic aiops-edge-key --from-file=key=$(MC_KEY_FILE) --dry-run=client -o yaml | $$K apply -f -; \
	done; \
	echo "xnet 客户端证书有效期：$$(openssl x509 -noout -enddate -in $$d/cert.pem)"

test-multicluster:
	$(PYTHON) -m pytest -q tests/unit/multicluster

# 中心部署 AIOps（测试环境）：make deploy-mc MC_LOAD_HOSTS=10.2.5.85
# 运行时只依赖集群配置、复制的 xnet 证书和 runner 密钥；不含任何边缘 kubeconfig。
MC_CLUSTERS_FILE ?= deploy-edge/clusters.mc.yaml
deploy-mc:
	@if test -n "$(MC_LOAD_HOSTS)"; then \
		for image in $(DOCKER_NAME):$(DOCKER_TAG) $(A2A_DOCKER_NAME):$(DOCKER_TAG) \
			xnet.registry.io:8443/caopeng/docker.io/library/busybox:1.36; do \
			deploy-edge/load_image.sh $$image $(MC_LOAD_HOSTS); done; fi
	@K="kubectl --kubeconfig $(CENTER_KUBECONFIG)"; set -e; \
	$$K create namespace aiops --dry-run=client -o yaml | $$K apply -f -; \
	$$K apply -f deploy/secrets/core.yaml; \
	$$K -n aiops create configmap aiops-clusters --from-file=clusters.yaml=$(MC_CLUSTERS_FILE) \
		--dry-run=client -o yaml | $$K apply -f -; \
	$(PYTHON) deploy-edge/render_center_config.py deploy/configmap/config.yaml deploy-edge/center/overrides.yaml | $$K apply -f -; \
	kubectl kustomize --load-restrictor=LoadRestrictionsNone deploy-edge/center \
		| sed -e 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME):.*|image: $(DOCKER_NAME):$(DOCKER_TAG)|' \
		      -e 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(A2A_IMAGE_NAME):.*|image: $(A2A_DOCKER_NAME):$(DOCKER_TAG)|' \
		| $$K apply -f -; \
	$$K -n aiops rollout restart deployment/aiops-copilot; \
	$$K -n aiops rollout status deployment/aiops-copilot --timeout=600s
