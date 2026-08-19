# K8s AIOps Copilot Makefile

IMAGE_REPOSITORY := xnet.registry.io:8443
PROJECT := xnet-cloud
IMAGE_NAME := aiops-copilot
DOCKER_NAME := $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME)

VERSION ?= $(shell cat VERSION)
DOCKER_TAG := $(VERSION)

.PHONY: build push deploy deploy-master deploy-slave delete restart logs sync-version \
	case-list case-deploy case-validate case-ask case-deploy-errors case-deploy-all case-clean

build:
	@echo "Building $(DOCKER_NAME):$(DOCKER_TAG)..."
	docker build -t $(DOCKER_NAME):$(DOCKER_TAG) .

push:
	@echo "Pushing $(DOCKER_NAME):$(DOCKER_TAG)..."
	docker push $(DOCKER_NAME):$(DOCKER_TAG)

# 通用部署（不修改 federation 配置，直接应用当前 configmap）
deploy:
	@echo "Deploying $(DOCKER_NAME):$(DOCKER_TAG)..."
	@sed -i 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME):.*|image: $(DOCKER_NAME):$(DOCKER_TAG)|' deploy/k8s-simple.yaml
	@kubectl create namespace aiops --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f deploy/ --recursive
	@echo "Waiting for rollout to complete..."
	kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s

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

case-list:
	@python3 -c "import json; cases=json.load(open('$(CASES_DIR)/catalog.yaml'))['cases']; \
	print(f\"{'ID':<5}{'名称':<32}{'NS':<15}{'runtime':<9}覆盖(k8s/prom/es/deepflow/tempo)\"); \
	[print(f\"{c['id']:<5}{c['name']:<32}{c['namespace']:<15}{str(c['runtime']):<9}\" \
	+ '/'.join(c['coverage'][k] for k in ('kubernetes','prometheus','elasticsearch','deepflow','tempo'))) for c in cases]"

case-deploy:
	@test -n "$(CASE)" || (echo "用法: make case-deploy CASE=c07" && exit 1)
	@dir=$$(python3 -c "import json; cases=json.load(open('$(CASES_DIR)/catalog.yaml'))['cases']; \
	print(next(c['directory'] for c in cases if c['id']=='$(CASE)'))"); \
	echo "🚀 部署 $(CASE): $$dir"; kubectl apply -k $(CASES_DIR)/$$dir

case-validate:
	@test -n "$(CASE)" || (echo "用法: make case-validate CASE=c07" && exit 1)
	$(CASES_DIR)/scripts/validate.sh --case $(CASE) --wait

case-ask:
	@test -n "$(CASE)" || (echo "用法: make case-ask CASE=c07" && exit 1)
	@ns=$$(python3 -c "import json; cases=json.load(open('$(CASES_DIR)/catalog.yaml'))['cases']; \
	print(next(c['namespace'] for c in cases if c['id']=='$(CASE)'))"); \
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
	$(CASES_DIR)/scripts/cleanup.sh
