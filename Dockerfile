# ============================================================================
# K8s AIOps Copilot - Dockerfile
# ============================================================================
# 构建: docker build -t k8s-aiops-copilot:latest .
# ============================================================================

FROM python:3.12-slim

# 构建参数
ARG VERSION=1.0.0
ARG COMMIT_HASH=unknown
ARG BUILD_TIME=unknown
ARG KUBECTL_VERSION=v1.29.0
ARG HELM_VERSION=v3.14.0

# 设置工作目录
WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖和诊断工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础工具
    curl \
    ca-certificates \
    # 网络诊断工具
    net-tools \
    iproute2 \
    dnsutils \
    iputils-ping \
    netcat-openbsd \
    # 系统诊断工具
    procps \
    lsof \
    # 文本处理工具
    jq \
    && rm -rf /var/lib/apt/lists/*

# 安装 kubectl
RUN curl -fsSL --retry 3 --retry-all-errors --connect-timeout 15 \
        -o /usr/local/bin/kubectl \
        "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod +x /usr/local/bin/kubectl


# 安装 Helm（二进制本体即可，repo 初始化放到运行时按需执行）
RUN curl -fsSL --retry 3 --retry-all-errors --connect-timeout 15 \
        "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz" | tar -xzf - \
    && mv linux-amd64/helm /usr/local/bin/helm \
    && rm -rf linux-amd64
    
# 复制依赖文件
COPY requirements.runtime.txt .

# 安装运行时依赖。
# holmesgpt 使用 --no-deps，避免把未使用的多云/数据库 toolset 依赖整体带入镜像。
RUN pip install --no-cache-dir --no-compile --no-deps holmesgpt==0.21.0 \
    && pip install --no-cache-dir --no-compile -r requirements.runtime.txt \
    && find /usr/local/lib/python3.12/site-packages \
        \( -type d \( -name tests -o -name test -o -name __pycache__ \) \
        -o -type f \( -name '*.pyc' -o -name '*.pyo' \) \) -exec rm -rf '{}' + \
    && rm -rf /root/.cache /tmp/*

# 创建非 root 用户
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/config \
    && chown appuser:appuser /app /app/config

# 复制应用代码
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser run.py .
COPY --chown=appuser:appuser VERSION .

USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    APP_VERSION=${VERSION} \
    APP_COMMIT=${COMMIT_HASH} \
    APP_BUILD_TIME=${BUILD_TIME}

# 版本标签
LABEL version="${VERSION}" \
      commit="${COMMIT_HASH}" \
      build_time="${BUILD_TIME}" \
      maintainer="HuHu" \
      description="K8s AIOps Copilot - 智能运维助手"

# 启动命令
CMD ["python", "run.py"]
