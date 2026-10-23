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
# 开发机用项目虚拟环境；部署机没有 .venv 时用系统 python3（部署脚本只需 PyYAML）
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
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

.PHONY: build release build-main build-a2a build-a2a-test-agent build-all push push-main push-a2a push-a2a-test-agent push-all test-a2a deploy delete restart logs sync-version \
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

# 单集群部署：应用当前 configmap 并滚动更新
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
# 中心：有 $(MC_KUBE_DIR)/center 就用它，否则用当前 kubectl 上下文（直接在中心节点上执行时）
CENTER_KUBECONFIG ?= $(wildcard $(MC_KUBE_DIR)/center)
CENTER_KUBECTL = kubectl $(if $(CENTER_KUBECONFIG),--kubeconfig $(CENTER_KUBECONFIG))
# 边缘：EDGE=edge-88 → $(MC_KUBE_DIR)/edge-88；EDGE=local → 当前上下文（在边缘节点上执行时）
EDGE ?=
EDGE_KUBECONFIG ?= $(if $(filter-out local,$(EDGE)),$(MC_KUBE_DIR)/$(EDGE))
EDGE_KUBECTL = kubectl $(if $(EDGE_KUBECONFIG),--kubeconfig $(EDGE_KUBECONFIG))
# runner 权限等级：1 只读（只诊断）；2 标准（默认，读全部、写常见修复对象）；3 管理员。见 deploy-edge/rbac/
RUNNER_LEVEL ?= 2
# 历史版本与各等级用过的绑定名；切换等级前先删除（ClusterRoleBinding 的 roleRef 不能原地修改）
RUNNER_BINDINGS := aiops-edge-runner-read aiops-edge-runner-read-view aiops-edge-runner-write aiops-edge-runner-view aiops-edge-runner-read-cluster
MC_CLUSTERS_FILE ?= deploy-edge/clusters.mc.yaml
# 交付时可由运维提供 AIOps 专用的 xnet 客户端证书：目录内含 cert.pem、key.pem、ca.pem；
# 不设则从中心 xnet 命名空间复制 xnet-management 的客户端证书（见设计文档 §18.2）
XNET_CERT_DIR ?=
RUNNER_VERSION ?= $(shell cat deploy-edge/VERSION)
RUNNER_IMAGE := $(IMAGE_REPOSITORY)/$(PROJECT)/aiops-edge-runner
# 测试环境用自己的 Harbor（无推送权限），镜像经 SSH 导入节点缓存：MC_PULL_POLICY=IfNotPresent MC_LOAD_HOSTS=10.2.5.88
MC_PULL_POLICY ?= Always
MC_A2A_PUBLIC_URL ?=
# 中心的模型配置：有 deploy-edge/center/secret.yaml（不入库）就用它，否则与单集群共用 deploy/secrets/core.yaml。
# 同一台机器同时部署单集群和多集群中心、两边模型不同时，把中心的放进前者，不用来回替换。
MC_SECRET_FILE ?= $(or $(wildcard deploy-edge/center/secret.yaml),deploy/secrets/core.yaml)
MC_LOAD_HOSTS ?=
.PHONY: runner-build runner-push mc-keygen mc-discover mc-init edge-target edge-deploy edge-delete sync-xnet-cert test-multicluster deploy-mc

runner-build:
	$(DOCKER_BUILD) --build-arg VERSION=$(RUNNER_VERSION) -f Dockerfile.edge-runner -t $(RUNNER_IMAGE):$(RUNNER_VERSION) .

runner-push:
	docker push $(RUNNER_IMAGE):$(RUNNER_VERSION)

# 中心与边缘共用的 runner 签名密钥，保存在本机运维目录。本机没有时先从中心已有的 Secret 取回
# （换一台机器部署不会生成新密钥、导致边缘 runner 验签失败），中心也没有才新生成。
mc-keygen:
	@test -f $(MC_KEY_FILE) || { set -e; umask 077; mkdir -p $(dir $(MC_KEY_FILE)); \
		$(CENTER_KUBECTL) -n aiops get secret aiops-edge-key -o jsonpath='{.data.key}' 2>/dev/null | base64 -d > $(MC_KEY_FILE) || true; \
		if test -s $(MC_KEY_FILE); then echo "从中心 Secret aiops/aiops-edge-key 取回签名密钥 → $(MC_KEY_FILE)"; \
		else python3 -c 'import secrets; print(secrets.token_hex(32))' > $(MC_KEY_FILE); echo "生成新的签名密钥 → $(MC_KEY_FILE)"; fi; }

edge-target:
	@case "$(RUNNER_LEVEL)" in 1|2|3) ;; *) echo "RUNNER_LEVEL 只能是 1、2、3（当前：$(RUNNER_LEVEL)）" >&2; exit 1;; esac
	@test -n "$(EDGE)$(EDGE_KUBECONFIG)" || { echo "请指定边缘：EDGE=edge-88（用 $(MC_KUBE_DIR)/edge-88）或 EDGE=local（当前 kubectl 上下文）" >&2; exit 1; }
	@test -z "$(EDGE_KUBECONFIG)" || test -f "$(EDGE_KUBECONFIG)" || { echo "找不到 $(EDGE_KUBECONFIG)" >&2; exit 1; }
	@echo "边缘目标：$$($(EDGE_KUBECTL) config view --minify -o jsonpath='{.clusters[0].cluster.server}' 2>/dev/null || echo '?')（$(if $(EDGE_KUBECONFIG),$(EDGE_KUBECONFIG),当前上下文)）"

# 列出 xnet 已接入的集群（虚拟 Node），输出可直接粘贴进集群配置的条目；只读
mc-discover:
	@$(CENTER_KUBECTL) get nodes -l node-role.kubernetes.io/xnet-agent -o json | $(PYTHON) deploy-edge/discover_clusters.py

# 在边缘集群部署 runner：make edge-deploy EDGE=edge-88（用 $(MC_KUBE_DIR)/edge-88）或 EDGE=local（当前上下文）
# 签名密钥来自本机 $(MC_KEY_FILE)：在边缘节点上执行时，先把中心生成的这个文件拷过去
edge-deploy: edge-target
	@test -f $(MC_KEY_FILE) || { echo "缺少签名密钥 $(MC_KEY_FILE)：先在中心执行 make mc-init，再把该文件拷到这台机器" >&2; exit 1; }
	@$(EDGE_KUBECTL) create namespace aiops --dry-run=client -o yaml | $(EDGE_KUBECTL) apply -f -
	@$(PYTHON) deploy-edge/render_policy.py deploy/configmap/config.yaml > /tmp/aiops-edge-policy.$$$$.json \
		&& $(EDGE_KUBECTL) -n aiops create configmap aiops-edge-runner-policy \
			--from-file=policy.json=/tmp/aiops-edge-policy.$$$$.json --dry-run=client -o yaml | $(EDGE_KUBECTL) apply -f - ; \
		rm -f /tmp/aiops-edge-policy.$$$$.json
	@$(EDGE_KUBECTL) -n aiops create secret generic aiops-edge-key --from-file=key=$(MC_KEY_FILE) \
		--dry-run=client -o yaml | $(EDGE_KUBECTL) apply -f -
	@if test -n "$(MC_LOAD_HOSTS)"; then deploy-edge/load_image.sh $(RUNNER_IMAGE):$(RUNNER_VERSION) $(MC_LOAD_HOSTS); fi
	sed -e 's|image: $(RUNNER_IMAGE):.*|image: $(RUNNER_IMAGE):$(RUNNER_VERSION)|' \
		-e 's|imagePullPolicy: Always|imagePullPolicy: $(MC_PULL_POLICY)|' \
		-e 's|{name: RUNNER_LEVEL, value: "[0-9]"}|{name: RUNNER_LEVEL, value: "$(RUNNER_LEVEL)"}|' deploy-edge/runner.yaml | $(EDGE_KUBECTL) apply -f -
	@$(EDGE_KUBECTL) delete clusterrolebinding $(RUNNER_BINDINGS) --ignore-not-found >/dev/null
	$(EDGE_KUBECTL) apply -f deploy-edge/rbac/level-$(RUNNER_LEVEL).yaml
	@echo "runner 权限等级：$(RUNNER_LEVEL)"
	$(EDGE_KUBECTL) -n aiops rollout restart deployment/aiops-edge-runner
	$(EDGE_KUBECTL) -n aiops rollout status deployment/aiops-edge-runner --timeout=180s

edge-delete: edge-target
	$(EDGE_KUBECTL) delete -f deploy-edge/runner.yaml --ignore-not-found
	$(EDGE_KUBECTL) delete clusterrolebinding $(RUNNER_BINDINGS) --ignore-not-found
	$(EDGE_KUBECTL) delete clusterrole aiops-edge-runner-read-l1 aiops-edge-runner-read-l2 aiops-edge-runner-write-l2 aiops-edge-runner-read-l3 aiops-edge-runner-write aiops-edge-runner-read-cluster --ignore-not-found
	$(EDGE_KUBECTL) -n aiops delete configmap aiops-edge-runner-policy secret aiops-edge-key --ignore-not-found

# 中心的共享对象，MCP（mcp）和 AIOps（aiops）两个命名空间各一份，可重复执行：
#   Secret aiops-xnet-client-cert（xnet 客户端证书）、Secret aiops-edge-key（runner 签名密钥）、
#   ConfigMap aiops-clusters（集群配置 $(MC_CLUSTERS_FILE)）
# 只读 xnet，不在 xnet 命名空间创建任何对象。集群配置或证书变化后重新执行，再重启 MCP 和 AIOps。
mc-init: mc-keygen
	@test -f $(MC_CLUSTERS_FILE) || { echo "缺少集群配置 $(MC_CLUSTERS_FILE)（make mc-discover 可列出已接入的集群）" >&2; exit 1; }
	@set -e; d=$$(mktemp -d); trap 'rm -rf $$d' EXIT; K="$(CENTER_KUBECTL)"; \
	if test -n "$(XNET_CERT_DIR)"; then \
		cp $(XNET_CERT_DIR)/cert.pem $(XNET_CERT_DIR)/key.pem $(XNET_CERT_DIR)/ca.pem $$d/; \
	else \
		$$K -n xnet get secret xnet-client-cert -o jsonpath='{.data.cert\.pem}' | base64 -d > $$d/cert.pem; \
		$$K -n xnet get secret xnet-client-cert -o jsonpath='{.data.key\.pem}' | base64 -d > $$d/key.pem; \
		$$K -n xnet get secret xnet-ca-cert -o jsonpath='{.data.cert\.pem}' | base64 -d > $$d/ca.pem; \
	fi; \
	for ns in mcp aiops; do \
		$$K create namespace $$ns --dry-run=client -o yaml | $$K apply -f - >/dev/null; \
		$$K -n $$ns create secret generic aiops-xnet-client-cert --from-file=$$d/cert.pem --from-file=$$d/key.pem \
			--from-file=$$d/ca.pem --dry-run=client -o yaml | $$K apply -f - >/dev/null; \
		$$K -n $$ns create secret generic aiops-edge-key --from-file=key=$(MC_KEY_FILE) \
			--dry-run=client -o yaml | $$K apply -f - >/dev/null; \
		$$K -n $$ns create configmap aiops-clusters --from-file=clusters.yaml=$(MC_CLUSTERS_FILE) \
			--dry-run=client -o yaml | $$K apply -f - >/dev/null; \
	done; \
	echo "mc-init: mcp、aiops 命名空间已更新（xnet 证书、签名密钥、集群配置）；证书有效期至 $$(openssl x509 -noout -enddate -in $$d/cert.pem | cut -d= -f2)"

# 旧名称，等同 mc-init
sync-xnet-cert: mc-init

test-multicluster:
	$(PYTHON) -m pytest -q tests/unit/multicluster

# 中心部署 AIOps（测试环境）：make deploy-mc MC_LOAD_HOSTS=10.2.5.85
# A2A 对外地址用中心自己的节点（跳过 xnet 虚拟 Node），不沿用单集群 make deploy 写进清单的地址；
# 有域名时用 MC_A2A_PUBLIC_URL=https://… 指定。
# 运行时只依赖集群配置、复制的 xnet 证书和 runner 密钥；不含任何边缘 kubeconfig。
deploy-mc: mc-init
	@if test -n "$(MC_LOAD_HOSTS)"; then \
		for image in $(DOCKER_NAME):$(DOCKER_TAG) $(A2A_DOCKER_NAME):$(DOCKER_TAG) \
			xnet.registry.io:8443/caopeng/docker.io/library/busybox:1.36; do \
			deploy-edge/load_image.sh $$image $(MC_LOAD_HOSTS); done; fi
	@test -f $(MC_SECRET_FILE) || { echo "缺少 $(MC_SECRET_FILE)（模型配置，见 docs/GUIDE.md）" >&2; exit 1; }
	@K="$(CENTER_KUBECTL)"; set -e; \
	U="$(MC_A2A_PUBLIC_URL)"; test -n "$$U" || U="http://$$($$K get nodes -l '!node-role.kubernetes.io/xnet-agent' \
		-o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}'):30801"; \
	echo "A2A 对外地址：$$U"; \
	echo "模型配置：$(MC_SECRET_FILE)"; $$K apply -f $(MC_SECRET_FILE); \
	$(PYTHON) deploy-edge/render_center_config.py deploy/configmap/config.yaml deploy-edge/center/overrides.yaml | $$K apply -f -; \
	kubectl kustomize --load-restrictor=LoadRestrictionsNone deploy-edge/center \
		| sed -e 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME):.*|image: $(DOCKER_NAME):$(DOCKER_TAG)|' \
		      -e 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(A2A_IMAGE_NAME):.*|image: $(A2A_DOCKER_NAME):$(DOCKER_TAG)|' \
		      -e "/- name: A2A_PUBLIC_URL/{n;s|value:.*|value: $$U|;}" \
		| $$K apply -f -; \
	$$K -n aiops rollout restart deployment/aiops-copilot; \
	$$K -n aiops rollout status deployment/aiops-copilot --timeout=600s
