# K8s AIOps Copilot Makefile

IMAGE_REPOSITORY := xnet.registry.io:8443
PROJECT := xnet-cloud
IMAGE_NAME := aiops-copilot
DOCKER_NAME := $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME)

VERSION ?= $(shell cat VERSION)
DOCKER_TAG := $(VERSION)

.PHONY: build push deploy deploy-master deploy-slave delete restart logs sync-version

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
	kubectl rollout status deployment/aiops-copilot -n aiops --timeout=120s

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
	@echo "Deleting (keeping namespace)..."
	kubectl delete -f deploy/k8s-simple.yaml --ignore-not-found
	kubectl delete -f deploy/rbac.yaml --ignore-not-found
	kubectl delete -f deploy/secrets/ --recursive --ignore-not-found
	kubectl delete -f deploy/configmap/ --recursive --ignore-not-found

restart:
	@echo "Restarting pods..."
	kubectl rollout restart deployment/aiops-copilot -n aiops
	kubectl rollout status deployment/aiops-copilot -n aiops --timeout=120s

logs:
	kubectl logs -f deployment/aiops-copilot -n aiops

sync-version:
	@echo "Syncing version to $(DOCKER_TAG)..."
	sed -i 's|image: $(IMAGE_REPOSITORY)/$(PROJECT)/$(IMAGE_NAME):.*|image: $(DOCKER_NAME):$(DOCKER_TAG)|' deploy/k8s-simple.yaml
