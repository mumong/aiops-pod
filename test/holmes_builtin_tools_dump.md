# Holmes 内置工具导出
- 生成时间: **2026-01-22 05:54:44 UTC**
- Python: `3.10.12`
- holmes 版本: `0.18.5`
- holmes 包路径: `/usr/local/lib/python3.10/dist-packages/holmes`
- 输入配置: `/root/huhu/agent/robusta/deploy/configmap/config.yaml`

---
## 本次导出的 toolsets（按 config.yaml 中 enabled=true）
- `helm/core`
- `kubernetes/core`
- `kubernetes/kube-prometheus-stack`
- `core_investigation`
- `internet`
- `connectivity_check`
- `bash`
- `runbook`
- `prometheus/metrics`

---
## 原始 inner config.yaml（来自 ConfigMap.data['config.yaml']）
```yaml
# 内置工具集配置（Built-in Toolsets）
toolsets:
  # ✅ 下面这些是从你的启动日志确认“已启用并可用”的内置 toolsets
  #    这里显式写开关，方便你未来做多集群/权限控制时统一管理
  helm/core:
    enabled: true
  kubernetes/core:
    enabled: true
  kubernetes/kube-prometheus-stack:
    enabled: true
  core_investigation:
    enabled: true
  internet:
    enabled: true
  connectivity_check:
    enabled: true
  bash:
    enabled: true
  runbook:
    enabled: true

  prometheus/metrics:
    enabled: true
    config:
      prometheus_url: "http://observability-prometheus.xnet.svc:9090"
  docker/core:
    # 容器内通常没有 docker daemon / socket，开启会导致 `docker version` 报 127
    enabled: false
  kubernetes/logs:
    enabled: false

# 第三方 MCP 服务器配置（Remote MCP Servers）
mcp_servers:
  test_tool_server:
    description: "测试工具集临时输出 - 只有当用户需要测试的时候才运行"
    config:
      url: "http://mcp-server-manager.mcp:8091/sse"
      mode: "sse"
    llm_instructions: "只有当用户需要测试临时输出的时候才运行这个工具。"
    enabled: false
  
  elasticsearch:
    description: "Elasticsearch MCP 工具集 - 用于查询索引、搜索日志数据"
    config:
      url: "http://mcp-server-manager.mcp:8088/sse"
      mode: "sse"
    enabled: false
  helmcharts:
    description: "Helm MCP 工具集 - 用于查询 Helm 资源"
    config:
      url: "http://mcp-server-manager.mcp:8092/sse"
      mode: "sse"
    enabled: false
```

---
## Toolset: `helm/core`
- **类**: `YAMLToolset`
- **模块**: `holmes.core.tools`
- **enabled**: `True`
- **status**: `enabled`

### 已注册工具（8 个）
| tool | description | class | module |
|---|---|---|---|
| `helm_list` | Use to get all the current helm releases | `YAMLTool` | `holmes.core.tools` |
| `helm_values` | Use to gather Helm values or any released helm chart | `YAMLTool` | `holmes.core.tools` |
| `helm_status` | Check the status of a Helm release | `YAMLTool` | `holmes.core.tools` |
| `helm_history` | Get the revision history of a Helm release | `YAMLTool` | `holmes.core.tools` |
| `helm_manifest` | Fetch the generated Kubernetes manifest for a Helm release | `YAMLTool` | `holmes.core.tools` |
| `helm_hooks` | Get the hooks for a Helm release | `YAMLTool` | `holmes.core.tools` |
| `helm_chart` | Show the chart used to create a Helm release | `YAMLTool` | `holmes.core.tools` |
| `helm_notes` | Show the notes provided by the Helm chart | `YAMLTool` | `holmes.core.tools` |

### 工具输入参数（Schema）

#### `helm_list`
```json
{}
```

#### `helm_values`
```json
{
  "release_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `helm_status`
```json
{
  "release_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `helm_history`
```json
{
  "release_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `helm_manifest`
```json
{
  "release_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `helm_hooks`
```json
{
  "release_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `helm_chart`
```json
{
  "release_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `helm_notes`
```json
{
  "release_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

### 相关源码文件（holmes 包内，1 个）

#### `core/tools.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/core/tools.py`
```python
import fnmatch
import json
import logging
import os
import re
import shlex
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    OrderedDict,
    Tuple,
    Union,
)

from jinja2 import Template
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    PrivateAttr,
    model_validator,
)
from rich.console import Console
from rich.table import Table

from holmes.core.llm import LLM
from holmes.core.openai_formatting import format_tool_to_open_ai_standard
from holmes.core.transformers import (
    Transformer,
    TransformerError,
    registry,
)
from holmes.plugins.prompts import load_and_render_prompt
from holmes.utils.config_utils import merge_transformers
from holmes.utils.memory_limit import check_oom_and_append_hint, get_ulimit_prefix

if TYPE_CHECKING:
    from holmes.core.transformers import BaseTransformer

logger = logging.getLogger(__name__)


class StructuredToolResultStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    NO_DATA = "no_data"
    APPROVAL_REQUIRED = "approval_required"

    def to_color(self) -> str:
        if self == StructuredToolResultStatus.SUCCESS:
            return "green"
        elif self == StructuredToolResultStatus.ERROR:
            return "red"
        elif self == StructuredToolResultStatus.APPROVAL_REQUIRED:
            return "yellow"
        else:
            return "white"

    def to_emoji(self) -> str:
        if self == StructuredToolResultStatus.SUCCESS:
            return "✔"
        elif self == StructuredToolResultStatus.ERROR:
            return "❌"
        elif self == StructuredToolResultStatus.APPROVAL_REQUIRED:
            return "⚠️"
        else:
            return "⚪️"


class StructuredToolResult(BaseModel):
    schema_version: str = "robusta:v1.0.0"
    status: StructuredToolResultStatus
    error: Optional[str] = None
    return_code: Optional[int] = None
    data: Optional[Any] = None
    url: Optional[str] = None
    invocation: Optional[str] = None
    params: Optional[Dict] = None
    icon_url: Optional[str] = None

    def get_stringified_data(self) -> str:
        if self.data is None:
            return ""

        if isinstance(self.data, str):
            return self.data
        else:
            try:
                if isinstance(self.data, BaseModel):
                    return self.data.model_dump_json()
                else:
                    return json.dumps(
                        self.data, separators=(",", ":"), ensure_ascii=False
                    )
            except Exception:
                return str(self.data)


class ApprovalRequirement(BaseModel):
    needs_approval: bool
    reason: str = ""


def sanitize(param):
    # allow empty strings to be unquoted - useful for optional params
    # it is up to the user to ensure that the command they are using is ok with empty strings
    # and if not to take that into account via an appropriate jinja template
    if param == "":
        return ""

    return shlex.quote(str(param))


def sanitize_params(params):
    return {k: sanitize(str(v)) for k, v in params.items()}


class ToolsetStatusEnum(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"


class ToolsetTag(str, Enum):
    CORE = "core"
    CLUSTER = "cluster"
    CLI = "cli"


class ToolsetType(str, Enum):
    BUILTIN = "built-in"
    CUSTOMIZED = "custom"
    MCP = "mcp"


class ToolParameter(BaseModel):
    description: Optional[str] = None
    type: str = "string"
    required: bool = True
    properties: Optional[Dict[str, "ToolParameter"]] = None  # For object types
    items: Optional["ToolParameter"] = None  # For array item schemas
    enum: Optional[List[str]] = None  # For restricting to specific values


class ToolInvokeContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tool_number: Optional[int] = None
    user_approved: bool = False
    llm: LLM
    max_token_count: int
    tool_call_id: str
    tool_name: str


class Tool(ABC, BaseModel):
    name: str
    description: str
    parameters: Dict[str, ToolParameter] = {}
    user_description: Optional[str] = (
        None  # templated string to show to the user describing this tool invocation (not seen by llm)
    )
    additional_instructions: Optional[str] = None
    icon_url: Optional[str] = Field(
        default=None,
        description="The URL of the icon for the tool, if None will get toolset icon",
    )
    transformers: Optional[List[Transformer]] = None
    restricted: bool = Field(
        default=False,
        description="If True, tool requires runbook authorization or restricted_tools=true to use",
    )

    # Private attribute to store initialized transformer instances for performance
    _transformer_instances: Optional[List["BaseTransformer"]] = PrivateAttr(
        default=None
    )

    def model_post_init(self, __context) -> None:
        """Initialize transformer instances once during tool creation for better performance."""
        logger.debug(
            f"Tool '{self.name}' model_post_init: creating transformer instances"
        )

        if self.transformers:
            logger.debug(
                f"Tool '{self.name}' has {len(self.transformers)} transformers to initialize"
            )
            self._transformer_instances = []
            for transformer in self.transformers:
                if not transformer:
                    continue
                logger.debug(
                    f"  Initializing transformer '{transformer.name}' with config: {transformer.config}"
                )
                try:
                    # Create transformer instance once and cache it
                    transformer_instance = registry.create_transformer(
                        transformer.name, transformer.config
                    )
                    self._transformer_instances.append(transformer_instance)
                    logger.debug(
                        f"Initialized transformer '{transformer.name}' for tool '{self.name}'"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize transformer '{transformer.name}' for tool '{self.name}': {e}"
                    )
                    # Continue with other transformers, don't fail the entire initialization
                    continue
        else:
            logger.debug(f"Tool '{self.name}' has no transformers")
            self._transformer_instances = None

    def get_openai_format(self, target_model: str):

        return format_tool_to_open_ai_standard(
            tool_name=self.name,
            tool_description=self.description,
            tool_parameters=self.parameters,
            target_model=target_model,
        )

    def invoke(
        self,
        params: Dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        tool_number_str = f"#{context.tool_number} " if context.tool_number else ""
        logger.info(
            f"Running tool {tool_number_str}[bold]{self.name}[/bold]: {self.get_parameterized_one_liner(params)}"
        )

        if not context.user_approved:
            approval_check = self._get_approval_requirement(params, context)
            if approval_check and approval_check.needs_approval:
                logger.info(
                    f"  [yellow]Tool '{self.name}' requires approval: {approval_check.reason}[/yellow]"
                )
                return StructuredToolResult(
                    status=StructuredToolResultStatus.APPROVAL_REQUIRED,
                    error=approval_check.reason,
                    params=params,
                    invocation=self.get_parameterized_one_liner(params),
                )

        start_time = time.time()
        result = self._invoke(params=params, context=context)
        result.icon_url = self.icon_url

        transformed_result = self._apply_transformers(result)
        elapsed = time.time() - start_time
        output_str = (
            transformed_result.get_stringified_data()
            if hasattr(transformed_result, "get_stringified_data")
            else str(transformed_result)
        )
        show_hint = f"/show {context.tool_number}" if context.tool_number else "/show"
        line_count = output_str.count("\n") + 1 if output_str else 0
        logger.info(
            f"  [dim]Finished {tool_number_str}in {elapsed:.2f}s, output length: {len(output_str):,} characters ({line_count:,} lines) - {show_hint} to view contents[/dim]"
        )
        return transformed_result

    def _is_restricted(self) -> bool:
        if self.restricted:
            return True

        toolset = getattr(self, "toolset", None)
        if toolset:
            for pattern in getattr(toolset, "restricted_tools", []):
                if fnmatch.fnmatch(self.name, pattern):
                    return True

        return False

    def _get_approval_requirement(
        self, params: Dict, context: ToolInvokeContext
    ) -> Optional[ApprovalRequirement]:
        toolset_approval = self._check_approval_config()
        if toolset_approval and toolset_approval.needs_approval:
            return toolset_approval
        return self.requires_approval(params, context)

    def _check_approval_config(self) -> Optional[ApprovalRequirement]:
        toolset = getattr(self, "toolset", None)
        if not toolset:
            return None

        for pattern in getattr(toolset, "approval_required_tools", []):
            if fnmatch.fnmatch(self.name, pattern):
                return ApprovalRequirement(
                    needs_approval=True,
                    reason=f"Tool '{self.name}' matches approval pattern '{pattern}'",
                )
        return None

    def requires_approval(
        self, params: Dict, context: ToolInvokeContext
    ) -> Optional[ApprovalRequirement]:
        """Override to implement tool-specific approval logic."""
        return None

    def _apply_transformers(self, result: StructuredToolResult) -> StructuredToolResult:
        """
        Apply configured transformers to the tool result.

        Args:
            result: The original tool result

        Returns:
            The tool result with transformed data, or original result if transformation fails
        """
        if (
            not self._transformer_instances
            or result.status != StructuredToolResultStatus.SUCCESS
        ):
            return result

        # Get the output string to transform
        original_data = result.get_stringified_data()
        if not original_data:
            return result

        transformed_data = original_data
        transformers_applied = []

        # Use cached transformer instances instead of creating new ones
        for transformer_instance in self._transformer_instances:
            try:
                # Check if transformer should be applied
                if not transformer_instance.should_apply(transformed_data):
                    logger.debug(
                        f"Transformer '{transformer_instance.name}' skipped for tool '{self.name}' (conditions not met)"
                    )
                    continue

                # Apply transformation
                pre_transform_size = len(transformed_data)
                transform_start_time = time.time()
                original_data = transformed_data  # Keep a copy for potential reversion
                transformed_data = transformer_instance.transform(transformed_data)
                transform_elapsed = time.time() - transform_start_time

                # Check if this is llm_summarize and revert if summary is not smaller
                post_transform_size = len(transformed_data)
                if (
                    transformer_instance.name == "llm_summarize"
                    and post_transform_size >= pre_transform_size
                ):
                    # Revert to original data if summary is not smaller
                    transformed_data = original_data
                    logger.debug(
                        f"Transformer '{transformer_instance.name}' reverted for tool '{self.name}' "
                        f"(output size {post_transform_size:,} >= input size {pre_transform_size:,})"
                    )
                    continue  # Don't mark as applied

                transformers_applied.append(transformer_instance.name)

                # Generic logging - transformers can override this with their own specific metrics
                size_change = post_transform_size - pre_transform_size
                logger.info(
                    f"Applied transformer '{transformer_instance.name}' to tool '{self.name}' output "
                    f"in {transform_elapsed:.2f}s (size: {pre_transform_size:,} → {post_transform_size:,} chars, "
                    f"change: {size_change:+,})"
                )

            except TransformerError as e:
                logger.warning(
                    f"Transformer '{transformer_instance.name}' failed for tool '{self.name}': {e}"
                )
                # Continue with other transformers, don't fail the entire chain
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error applying transformer '{transformer_instance.name}' to tool '{self.name}': {e}"
                )
                # Continue with other transformers
                continue

        # If any transformers were applied, update the result
        if transformers_applied:
            # Create a copy of the result with transformed data
            result_dict = result.model_dump(exclude={"data"})
            result_dict["data"] = transformed_data
            return StructuredToolResult(**result_dict)

        return result

    @abstractmethod
    def _invoke(
        self,
        params: dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        """
        params: the tool params
        user_approved: whether the tool call is approved by the user. Can be used to confidently execute unsafe actions.
        """
        pass

    @abstractmethod
    def get_parameterized_one_liner(self, params: Dict) -> str:
        return ""


class YAMLTool(Tool, BaseModel):
    command: Optional[str] = None
    script: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.__infer_parameters()

    def __infer_parameters(self):
        # Find parameters that appear inside self.command or self.script but weren't declared in parameters
        template = self.command or self.script
        inferred_params = re.findall(r"\{\{\s*([\w]+)[\.\|]?.*?\s*\}\}", template)
        # TODO: if filters were used in template, take only the variable name
        # Regular expression to match Jinja2 placeholders with or without filters
        # inferred_params = re.findall(r'\{\{\s*(\w+)(\s*\|\s*[^}]+)?\s*\}\}', self.command)
        # for param_tuple in inferred_params:
        #    param = param_tuple[0]  # Extract the parameter name
        #    if param not in self.parameters:
        #        self.parameters[param] = ToolParameter()
        for param in inferred_params:
            if param not in self.parameters:
                self.parameters[param] = ToolParameter()

    def get_parameterized_one_liner(self, params) -> str:
        params = sanitize_params(params)
        if self.user_description:
            template = Template(self.user_description)
        else:
            cmd_or_script = self.command or self.script
            template = Template(cmd_or_script)  # type: ignore
        return template.render(params)

    def _build_context(self, params):
        params = sanitize_params(params)
        context = {**params}
        return context

    def _get_status(
        self, return_code: int, raw_output: str
    ) -> StructuredToolResultStatus:
        if return_code != 0:
            return StructuredToolResultStatus.ERROR
        if raw_output == "":
            return StructuredToolResultStatus.NO_DATA
        return StructuredToolResultStatus.SUCCESS

    def _invoke(
        self,
        params: dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        if self.command is not None:
            raw_output, return_code, invocation = self.__invoke_command(params)
        else:
            raw_output, return_code, invocation = self.__invoke_script(params)  # type: ignore

        if self.additional_instructions and return_code == 0:
            logger.info(
                f"Applying additional instructions: {self.additional_instructions}"
            )
            output_with_instructions = self.__apply_additional_instructions(raw_output)
        else:
            output_with_instructions = raw_output

        error = (
            None
            if return_code == 0
            else f"Command `{invocation}` failed with return code {return_code}\nOutput:\n{raw_output}"
        )
        status = self._get_status(return_code, raw_output)

        return StructuredToolResult(
            status=status,
            error=error,
            return_code=return_code,
            data=output_with_instructions,
            params=params,
            invocation=invocation,
        )

    def __apply_additional_instructions(self, raw_output: str) -> str:
        try:
            result = subprocess.run(
                self.additional_instructions,  # type: ignore
                input=raw_output,
                shell=True,
                text=True,
                capture_output=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to apply additional instructions: {self.additional_instructions}. "
                f"Error: {e.stderr}"
            )
            return f"Error applying additional instructions: {e.stderr}"

    def __invoke_command(self, params) -> Tuple[str, int, str]:
        context = self._build_context(params)
        command = os.path.expandvars(self.command)  # type: ignore
        template = Template(command)  # type: ignore
        rendered_command = template.render(context)
        output, return_code = self.__execute_subprocess(rendered_command)
        return output, return_code, rendered_command

    def __invoke_script(self, params) -> str:
        context = self._build_context(params)
        script = os.path.expandvars(self.script)  # type: ignore
        template = Template(script)  # type: ignore
        rendered_script = template.render(context)

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".sh"
        ) as temp_script:
            temp_script.write(rendered_script)
            temp_script_path = temp_script.name
        subprocess.run(["chmod", "+x", temp_script_path], check=True)

        try:
            output, return_code = self.__execute_subprocess(temp_script_path)
        finally:
            subprocess.run(["rm", temp_script_path])
        return output, return_code, rendered_script  # type: ignore

    def __execute_subprocess(self, cmd) -> Tuple[str, int]:
        try:
            logger.debug(f"Running `{cmd}`")
            protected_cmd = get_ulimit_prefix() + cmd
            result = subprocess.run(
                protected_cmd,
                shell=True,
                text=True,
                check=False,  # do not throw error, we just return the error code
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            output = result.stdout.strip()
            output = check_oom_and_append_hint(output, result.returncode)
            return output, result.returncode
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while running '{cmd}': {e}",
                exc_info=True,
            )
            output = f"Command execution failed with error: {e}"
            return output, 1


class StaticPrerequisite(BaseModel):
    enabled: bool
    disabled_reason: str


class CallablePrerequisite(BaseModel):
    callable: Callable[[dict[str, Any]], Tuple[bool, str]]


class ToolsetCommandPrerequisite(BaseModel):
    command: str  # must complete successfully (error code 0) for prereq to be satisfied
    expected_output: Optional[str] = None  # optional


class ToolsetEnvironmentPrerequisite(BaseModel):
    env: List[str] = []  # optional


class Toolset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experimental: bool = False

    enabled: bool = False
    name: str
    description: str
    docs_url: Optional[str] = None
    icon_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    additional_instructions: Optional[str] = ""
    prerequisites: List[
        Union[
            StaticPrerequisite,
            ToolsetCommandPrerequisite,
            ToolsetEnvironmentPrerequisite,
            CallablePrerequisite,
        ]
    ] = []
    tools: List[Tool]
    tags: List[ToolsetTag] = Field(
        default_factory=lambda: [ToolsetTag.CORE],
    )
    config: Optional[Any] = None
    is_default: bool = False
    llm_instructions: Optional[str] = None
    transformers: Optional[List[Transformer]] = None

    restricted_tools: List[str] = Field(
        default_factory=list,
        description="Tool names/patterns that require runbook authorization (use '*' for all tools)",
    )
    approval_required_tools: List[str] = Field(
        default_factory=list,
        description="Tool names/patterns that require user approval before execution (use '*' for all tools)",
    )

    # warning! private attributes are not copied, which can lead to subtle bugs.
    # e.g. l.extend([some_tool]) will reset these private attribute to None

    # status fields that be cached
    type: Optional[ToolsetType] = None
    path: Optional[FilePath] = None
    status: ToolsetStatusEnum = ToolsetStatusEnum.DISABLED
    error: Optional[str] = None

    def override_with(self, override: "Toolset") -> None:
        """
        Overrides the current attributes with values from the Toolset loaded from custom config
        if they are not None.
        """
        for field, value in override.model_dump(
            exclude_unset=True,
            exclude=("name"),  # type: ignore
        ).items():
            if field in self.__class__.model_fields and value not in (None, [], {}, ""):
                setattr(self, field, value)

    @model_validator(mode="before")
    def preprocess_tools(cls, values):
        additional_instructions = values.get("additional_instructions", "")
        transformers = values.get("transformers", None)
        tools_data = values.get("tools", [])

        # Convert raw dict transformers to Transformer objects BEFORE merging
        if transformers:
            converted_transformers = []
            for t in transformers:
                if isinstance(t, dict):
                    try:
                        transformer_obj = Transformer(**t)
                        # Check if transformer is registered
                        from holmes.core.transformers import registry

                        if not registry.is_registered(transformer_obj.name):
                            logger.warning(
                                f"Invalid toolset transformer configuration: Transformer '{transformer_obj.name}' is not registered"
                            )
                            continue  # Skip invalid transformer
                        converted_transformers.append(transformer_obj)
                    except Exception as e:
                        # Log warning and skip invalid transformer
                        logger.warning(
                            f"Invalid toolset transformer configuration: {e}"
                        )
                        continue
                else:
                    # Already a Transformer object
                    converted_transformers.append(t)
            transformers = converted_transformers if converted_transformers else None

        tools = []
        for tool in tools_data:
            if isinstance(tool, dict):
                tool["additional_instructions"] = additional_instructions

                # Convert tool-level transformers to Transformer objects
                tool_transformers = tool.get("transformers")
                if tool_transformers:
                    converted_tool_transformers = []
                    for t in tool_transformers:
                        if isinstance(t, dict):
                            try:
                                transformer_obj = Transformer(**t)
                                # Check if transformer is registered
                                from holmes.core.transformers import registry

                                if not registry.is_registered(transformer_obj.name):
                                    logger.warning(
                                        f"Invalid tool transformer configuration: Transformer '{transformer_obj.name}' is not registered"
                                    )
                                    continue  # Skip invalid transformer
                                converted_tool_transformers.append(transformer_obj)
                            except Exception as e:
                                # Log warning and skip invalid transformer
                                logger.warning(
                                    f"Invalid tool transformer configuration: {e}"
                                )
                                continue
                        else:
                            # Already a Transformer object
                            converted_tool_transformers.append(t)
                    tool_transformers = (
                        converted_tool_transformers
                        if converted_tool_transformers
                        else None
                    )

                # Merge toolset-level transformers with tool-level configs
                tool["transformers"] = merge_transformers(
                    base_transformers=transformers,
                    override_transformers=tool_transformers,
                )
            if isinstance(tool, Tool):
                tool.additional_instructions = additional_instructions
                # Merge toolset-level transformers with tool-level configs
                tool.transformers = merge_transformers(  # type: ignore
                    base_transformers=transformers,
                    override_transformers=tool.transformers,
                )
            tools.append(tool)
        values["tools"] = tools

        return values

    def get_environment_variables(self) -> List[str]:
        env_vars = set()

        for prereq in self.prerequisites:
            if isinstance(prereq, ToolsetEnvironmentPrerequisite):
                env_vars.update(prereq.env)
        return list(env_vars)

    def interpolate_command(self, command: str) -> str:
        interpolated_command = os.path.expandvars(command)

        return interpolated_command

    def check_prerequisites(self, silent: bool = False):
        self.status = ToolsetStatusEnum.ENABLED

        # Sort prerequisites by type to fail fast on missing env vars before
        # running slow commands (e.g., ArgoCD checks that timeout):
        # 1. Static checks (instant)
        # 2. Environment variable checks (instant, often required by commands)
        # 3. Callable checks (variable speed)
        # 4. Command checks (slowest - may timeout or hang)
        def prereq_priority(prereq):
            if isinstance(prereq, StaticPrerequisite):
                return 0
            elif isinstance(prereq, ToolsetEnvironmentPrerequisite):
                return 1
            elif isinstance(prereq, CallablePrerequisite):
                return 2
            elif isinstance(prereq, ToolsetCommandPrerequisite):
                return 3
            return 4  # Unknown types go last

        sorted_prereqs = sorted(self.prerequisites, key=prereq_priority)

        for prereq in sorted_prereqs:
            if isinstance(prereq, ToolsetCommandPrerequisite):
                try:
                    command = self.interpolate_command(prereq.command)
                    result = subprocess.run(
                        command,
                        shell=True,
                        check=True,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    if (
                        prereq.expected_output
                        and prereq.expected_output not in result.stdout
                    ):
                        self.status = ToolsetStatusEnum.FAILED
                        self.error = f"`{prereq.command}` did not include `{prereq.expected_output}`"
                except subprocess.CalledProcessError as e:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"`{prereq.command}` returned {e.returncode}"

            elif isinstance(prereq, ToolsetEnvironmentPrerequisite):
                for env_var in prereq.env:
                    if env_var not in os.environ:
                        self.status = ToolsetStatusEnum.FAILED
                        self.error = f"Environment variable {env_var} was not set"

            elif isinstance(prereq, StaticPrerequisite):
                if not prereq.enabled:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"{prereq.disabled_reason}"

            elif isinstance(prereq, CallablePrerequisite):
                try:
                    (enabled, error_message) = prereq.callable(self.config)
                    if not enabled:
                        self.status = ToolsetStatusEnum.FAILED
                    if error_message:
                        self.error = f"{error_message}"
                except Exception as e:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"Prerequisite call failed unexpectedly: {str(e)}"

            if (
                self.status == ToolsetStatusEnum.DISABLED
                or self.status == ToolsetStatusEnum.FAILED
            ):
                if not silent:
                    logger.info(f"❌ Toolset {self.name}: {self.error}")
                # no point checking further prerequisites if one failed
                return

        if not silent:
            logger.info(f"✅ Toolset {self.name}")

    @abstractmethod
    def get_example_config(self) -> Dict[str, Any]:
        return {}

    def _load_llm_instructions(self, jinja_template: str):
        tool_names = [t.name for t in self.tools]
        self.llm_instructions = load_and_render_prompt(
            prompt=jinja_template,
            context={"tool_names": tool_names, "config": self.config},
        )

    def _load_llm_instructions_from_file(self, file_dir: str, filename: str) -> None:
        """Helper method to load LLM instructions from a jinja2 template file.

        Args:
            file_dir: Directory where the template file is located (typically os.path.dirname(__file__))
            filename: Name of the jinja2 template file (e.g., "toolset_grafana_dashboard.jinja2")
        """
        template_file_path = os.path.abspath(os.path.join(file_dir, filename))
        self._load_llm_instructions(jinja_template=f"file://{template_file_path}")


class YAMLToolset(Toolset):
    tools: List[YAMLTool]  # type: ignore

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.llm_instructions:
            self._load_llm_instructions(self.llm_instructions)

    def get_example_config(self) -> Dict[str, Any]:
        return {}


class ToolsetYamlFromConfig(Toolset):
    """
    ToolsetYamlFromConfig represents a toolset loaded from a YAML configuration file.
    To override a build-in toolset fields, we don't have to explicitly set all required fields,
    instead, we only put the fields we want to override in the YAML file.
    ToolsetYamlFromConfig helps py-pass the pydantic validation of the required fields and together with
    `override_with` method, a build-in toolset object with new configurations is created.
    """

    name: str
    # YamlToolset is loaded from a YAML file specified by the user and should be enabled by default
    # Built-in toolsets are exception and should be disabled by default when loaded
    enabled: bool = True
    additional_instructions: Optional[str] = None
    prerequisites: List[
        Union[
            StaticPrerequisite,
            ToolsetCommandPrerequisite,
            ToolsetEnvironmentPrerequisite,
        ]
    ] = []  # type: ignore
    tools: Optional[List[YAMLTool]] = []  # type: ignore
    description: Optional[str] = None  # type: ignore
    docs_url: Optional[str] = None
    icon_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    config: Optional[Any] = None
    url: Optional[str] = None  # MCP toolset

    restricted_tools: List[str] = Field(default_factory=list)
    approval_required_tools: List[str] = Field(default_factory=list)

    def get_example_config(self) -> Dict[str, Any]:
        return {}


class ToolsetDBModel(BaseModel):
    account_id: str
    cluster_id: str
    toolset_name: str
    icon_url: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    description: Optional[str] = None
    docs_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    updated_at: str = Field(default_factory=datetime.now().isoformat)


def pretty_print_toolset_status(toolsets: list[Toolset], console: Console) -> None:
    status_fields = ["name", "enabled", "status", "type", "path", "error"]
    toolsets_status = []
    for toolset in sorted(toolsets, key=lambda ts: ts.status.value):
        toolset_status = json.loads(toolset.model_dump_json(include=status_fields))  # type: ignore

        status_value = toolset_status.get("status", "")
        error_value = toolset_status.get("error", "")
        if status_value == "enabled":
            toolset_status["status"] = "[green]enabled[/green]"
        elif status_value == "failed":
            toolset_status["status"] = "[red]failed[/red]"
            toolset_status["error"] = f"[red]{error_value}[/red]"
        else:
            toolset_status["status"] = f"[yellow]{status_value}[/yellow]"

        # Replace None with "" for Path and Error columns
        for field in ["path", "error"]:
            if toolset_status.get(field) is None:
                toolset_status[field] = ""

        order_toolset_status = OrderedDict(
            (k.capitalize(), toolset_status[k])
            for k in status_fields
            if k in toolset_status
        )
        toolsets_status.append(order_toolset_status)

    table = Table(show_header=True, header_style="bold")
    for col in status_fields:
        table.add_column(col.capitalize())

    for row in toolsets_status:
        table.add_row(*(str(row.get(col.capitalize(), "")) for col in status_fields))

    console.print(table)
```

---
## Toolset: `kubernetes/core`
- **类**: `YAMLToolset`
- **模块**: `holmes.core.tools`
- **enabled**: `True`
- **status**: `enabled`

### 已注册工具（10 个）
| tool | description | class | module |
|---|---|---|---|
| `kubectl_describe` | Run kubectl describe <kind> <name> -n <namespace>, call this when users ask for description, for example when a user asks   - 'describe pod xyz-123'   - 'show s… | `YAMLTool` | `holmes.core.tools` |
| `kubectl_get_by_name` | Run `kubectl get <kind> <name> --show-labels` | `YAMLTool` | `holmes.core.tools` |
| `kubectl_get_by_kind_in_namespace` | Run `kubectl get <kind> -n <namespace> --show-labels` to get all resources of a given type in namespace | `YAMLTool` | `holmes.core.tools` |
| `kubectl_get_by_kind_in_cluster` | Run `kubectl get -A <kind> --show-labels` to get all resources of a given type in the cluster | `YAMLTool` | `holmes.core.tools` |
| `kubectl_find_resource` | Run `kubectl get {{ kind }} -A --show-labels | grep {{ keyword }}` to find a resource where you know a substring of the name, IP, namespace, or labels | `YAMLTool` | `holmes.core.tools` |
| `kubectl_get_yaml` | Run `kubectl get -o yaml` on a single Kubernetes resource | `YAMLTool` | `holmes.core.tools` |
| `kubectl_events` | Retrieve the events for a specific Kubernetes resource. `resource_type` can be any kubernetes resource type: 'pod', 'service', 'deployment', 'job', 'node', etc. | `YAMLTool` | `holmes.core.tools` |
| `kubernetes_jq_query` | Use kubectl to get json for all resources of a specific kind and filter with jq. IMPORTANT: The 'kind' parameter must be the plural form of the resource type (e… | `YAMLTool` | `holmes.core.tools` |
| `kubernetes_tabular_query` | Extract specific fields from Kubernetes resources in tabular format with optional filtering. Memory-efficient way to query large clusters - only requested field… | `YAMLTool` | `holmes.core.tools` |
| `kubernetes_count` | Use kubectl to get apply a jq filter and then count the results. Use this whenever asked to count kubernetes resources. IMPORTANT: The 'kind' parameter must be … | `YAMLTool` | `holmes.core.tools` |

### 工具输入参数（Schema）

#### `kubectl_describe`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubectl_get_by_name`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubectl_get_by_kind_in_namespace`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubectl_get_by_kind_in_cluster`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubectl_find_resource`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "keyword": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubectl_get_yaml`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubectl_events`
```json
{
  "resource_type": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "resource_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubernetes_jq_query`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "jq_expr": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubernetes_tabular_query`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "columns": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "filter_pattern": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubernetes_count`
```json
{
  "kind": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "jq_expr": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

### 相关源码文件（holmes 包内，1 个）

#### `core/tools.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/core/tools.py`
```python
import fnmatch
import json
import logging
import os
import re
import shlex
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    OrderedDict,
    Tuple,
    Union,
)

from jinja2 import Template
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    PrivateAttr,
    model_validator,
)
from rich.console import Console
from rich.table import Table

from holmes.core.llm import LLM
from holmes.core.openai_formatting import format_tool_to_open_ai_standard
from holmes.core.transformers import (
    Transformer,
    TransformerError,
    registry,
)
from holmes.plugins.prompts import load_and_render_prompt
from holmes.utils.config_utils import merge_transformers
from holmes.utils.memory_limit import check_oom_and_append_hint, get_ulimit_prefix

if TYPE_CHECKING:
    from holmes.core.transformers import BaseTransformer

logger = logging.getLogger(__name__)


class StructuredToolResultStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    NO_DATA = "no_data"
    APPROVAL_REQUIRED = "approval_required"

    def to_color(self) -> str:
        if self == StructuredToolResultStatus.SUCCESS:
            return "green"
        elif self == StructuredToolResultStatus.ERROR:
            return "red"
        elif self == StructuredToolResultStatus.APPROVAL_REQUIRED:
            return "yellow"
        else:
            return "white"

    def to_emoji(self) -> str:
        if self == StructuredToolResultStatus.SUCCESS:
            return "✔"
        elif self == StructuredToolResultStatus.ERROR:
            return "❌"
        elif self == StructuredToolResultStatus.APPROVAL_REQUIRED:
            return "⚠️"
        else:
            return "⚪️"


class StructuredToolResult(BaseModel):
    schema_version: str = "robusta:v1.0.0"
    status: StructuredToolResultStatus
    error: Optional[str] = None
    return_code: Optional[int] = None
    data: Optional[Any] = None
    url: Optional[str] = None
    invocation: Optional[str] = None
    params: Optional[Dict] = None
    icon_url: Optional[str] = None

    def get_stringified_data(self) -> str:
        if self.data is None:
            return ""

        if isinstance(self.data, str):
            return self.data
        else:
            try:
                if isinstance(self.data, BaseModel):
                    return self.data.model_dump_json()
                else:
                    return json.dumps(
                        self.data, separators=(",", ":"), ensure_ascii=False
                    )
            except Exception:
                return str(self.data)


class ApprovalRequirement(BaseModel):
    needs_approval: bool
    reason: str = ""


def sanitize(param):
    # allow empty strings to be unquoted - useful for optional params
    # it is up to the user to ensure that the command they are using is ok with empty strings
    # and if not to take that into account via an appropriate jinja template
    if param == "":
        return ""

    return shlex.quote(str(param))


def sanitize_params(params):
    return {k: sanitize(str(v)) for k, v in params.items()}


class ToolsetStatusEnum(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"


class ToolsetTag(str, Enum):
    CORE = "core"
    CLUSTER = "cluster"
    CLI = "cli"


class ToolsetType(str, Enum):
    BUILTIN = "built-in"
    CUSTOMIZED = "custom"
    MCP = "mcp"


class ToolParameter(BaseModel):
    description: Optional[str] = None
    type: str = "string"
    required: bool = True
    properties: Optional[Dict[str, "ToolParameter"]] = None  # For object types
    items: Optional["ToolParameter"] = None  # For array item schemas
    enum: Optional[List[str]] = None  # For restricting to specific values


class ToolInvokeContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tool_number: Optional[int] = None
    user_approved: bool = False
    llm: LLM
    max_token_count: int
    tool_call_id: str
    tool_name: str


class Tool(ABC, BaseModel):
    name: str
    description: str
    parameters: Dict[str, ToolParameter] = {}
    user_description: Optional[str] = (
        None  # templated string to show to the user describing this tool invocation (not seen by llm)
    )
    additional_instructions: Optional[str] = None
    icon_url: Optional[str] = Field(
        default=None,
        description="The URL of the icon for the tool, if None will get toolset icon",
    )
    transformers: Optional[List[Transformer]] = None
    restricted: bool = Field(
        default=False,
        description="If True, tool requires runbook authorization or restricted_tools=true to use",
    )

    # Private attribute to store initialized transformer instances for performance
    _transformer_instances: Optional[List["BaseTransformer"]] = PrivateAttr(
        default=None
    )

    def model_post_init(self, __context) -> None:
        """Initialize transformer instances once during tool creation for better performance."""
        logger.debug(
            f"Tool '{self.name}' model_post_init: creating transformer instances"
        )

        if self.transformers:
            logger.debug(
                f"Tool '{self.name}' has {len(self.transformers)} transformers to initialize"
            )
            self._transformer_instances = []
            for transformer in self.transformers:
                if not transformer:
                    continue
                logger.debug(
                    f"  Initializing transformer '{transformer.name}' with config: {transformer.config}"
                )
                try:
                    # Create transformer instance once and cache it
                    transformer_instance = registry.create_transformer(
                        transformer.name, transformer.config
                    )
                    self._transformer_instances.append(transformer_instance)
                    logger.debug(
                        f"Initialized transformer '{transformer.name}' for tool '{self.name}'"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize transformer '{transformer.name}' for tool '{self.name}': {e}"
                    )
                    # Continue with other transformers, don't fail the entire initialization
                    continue
        else:
            logger.debug(f"Tool '{self.name}' has no transformers")
            self._transformer_instances = None

    def get_openai_format(self, target_model: str):

        return format_tool_to_open_ai_standard(
            tool_name=self.name,
            tool_description=self.description,
            tool_parameters=self.parameters,
            target_model=target_model,
        )

    def invoke(
        self,
        params: Dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        tool_number_str = f"#{context.tool_number} " if context.tool_number else ""
        logger.info(
            f"Running tool {tool_number_str}[bold]{self.name}[/bold]: {self.get_parameterized_one_liner(params)}"
        )

        if not context.user_approved:
            approval_check = self._get_approval_requirement(params, context)
            if approval_check and approval_check.needs_approval:
                logger.info(
                    f"  [yellow]Tool '{self.name}' requires approval: {approval_check.reason}[/yellow]"
                )
                return StructuredToolResult(
                    status=StructuredToolResultStatus.APPROVAL_REQUIRED,
                    error=approval_check.reason,
                    params=params,
                    invocation=self.get_parameterized_one_liner(params),
                )

        start_time = time.time()
        result = self._invoke(params=params, context=context)
        result.icon_url = self.icon_url

        transformed_result = self._apply_transformers(result)
        elapsed = time.time() - start_time
        output_str = (
            transformed_result.get_stringified_data()
            if hasattr(transformed_result, "get_stringified_data")
            else str(transformed_result)
        )
        show_hint = f"/show {context.tool_number}" if context.tool_number else "/show"
        line_count = output_str.count("\n") + 1 if output_str else 0
        logger.info(
            f"  [dim]Finished {tool_number_str}in {elapsed:.2f}s, output length: {len(output_str):,} characters ({line_count:,} lines) - {show_hint} to view contents[/dim]"
        )
        return transformed_result

    def _is_restricted(self) -> bool:
        if self.restricted:
            return True

        toolset = getattr(self, "toolset", None)
        if toolset:
            for pattern in getattr(toolset, "restricted_tools", []):
                if fnmatch.fnmatch(self.name, pattern):
                    return True

        return False

    def _get_approval_requirement(
        self, params: Dict, context: ToolInvokeContext
    ) -> Optional[ApprovalRequirement]:
        toolset_approval = self._check_approval_config()
        if toolset_approval and toolset_approval.needs_approval:
            return toolset_approval
        return self.requires_approval(params, context)

    def _check_approval_config(self) -> Optional[ApprovalRequirement]:
        toolset = getattr(self, "toolset", None)
        if not toolset:
            return None

        for pattern in getattr(toolset, "approval_required_tools", []):
            if fnmatch.fnmatch(self.name, pattern):
                return ApprovalRequirement(
                    needs_approval=True,
                    reason=f"Tool '{self.name}' matches approval pattern '{pattern}'",
                )
        return None

    def requires_approval(
        self, params: Dict, context: ToolInvokeContext
    ) -> Optional[ApprovalRequirement]:
        """Override to implement tool-specific approval logic."""
        return None

    def _apply_transformers(self, result: StructuredToolResult) -> StructuredToolResult:
        """
        Apply configured transformers to the tool result.

        Args:
            result: The original tool result

        Returns:
            The tool result with transformed data, or original result if transformation fails
        """
        if (
            not self._transformer_instances
            or result.status != StructuredToolResultStatus.SUCCESS
        ):
            return result

        # Get the output string to transform
        original_data = result.get_stringified_data()
        if not original_data:
            return result

        transformed_data = original_data
        transformers_applied = []

        # Use cached transformer instances instead of creating new ones
        for transformer_instance in self._transformer_instances:
            try:
                # Check if transformer should be applied
                if not transformer_instance.should_apply(transformed_data):
                    logger.debug(
                        f"Transformer '{transformer_instance.name}' skipped for tool '{self.name}' (conditions not met)"
                    )
                    continue

                # Apply transformation
                pre_transform_size = len(transformed_data)
                transform_start_time = time.time()
                original_data = transformed_data  # Keep a copy for potential reversion
                transformed_data = transformer_instance.transform(transformed_data)
                transform_elapsed = time.time() - transform_start_time

                # Check if this is llm_summarize and revert if summary is not smaller
                post_transform_size = len(transformed_data)
                if (
                    transformer_instance.name == "llm_summarize"
                    and post_transform_size >= pre_transform_size
                ):
                    # Revert to original data if summary is not smaller
                    transformed_data = original_data
                    logger.debug(
                        f"Transformer '{transformer_instance.name}' reverted for tool '{self.name}' "
                        f"(output size {post_transform_size:,} >= input size {pre_transform_size:,})"
                    )
                    continue  # Don't mark as applied

                transformers_applied.append(transformer_instance.name)

                # Generic logging - transformers can override this with their own specific metrics
                size_change = post_transform_size - pre_transform_size
                logger.info(
                    f"Applied transformer '{transformer_instance.name}' to tool '{self.name}' output "
                    f"in {transform_elapsed:.2f}s (size: {pre_transform_size:,} → {post_transform_size:,} chars, "
                    f"change: {size_change:+,})"
                )

            except TransformerError as e:
                logger.warning(
                    f"Transformer '{transformer_instance.name}' failed for tool '{self.name}': {e}"
                )
                # Continue with other transformers, don't fail the entire chain
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error applying transformer '{transformer_instance.name}' to tool '{self.name}': {e}"
                )
                # Continue with other transformers
                continue

        # If any transformers were applied, update the result
        if transformers_applied:
            # Create a copy of the result with transformed data
            result_dict = result.model_dump(exclude={"data"})
            result_dict["data"] = transformed_data
            return StructuredToolResult(**result_dict)

        return result

    @abstractmethod
    def _invoke(
        self,
        params: dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        """
        params: the tool params
        user_approved: whether the tool call is approved by the user. Can be used to confidently execute unsafe actions.
        """
        pass

    @abstractmethod
    def get_parameterized_one_liner(self, params: Dict) -> str:
        return ""


class YAMLTool(Tool, BaseModel):
    command: Optional[str] = None
    script: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.__infer_parameters()

    def __infer_parameters(self):
        # Find parameters that appear inside self.command or self.script but weren't declared in parameters
        template = self.command or self.script
        inferred_params = re.findall(r"\{\{\s*([\w]+)[\.\|]?.*?\s*\}\}", template)
        # TODO: if filters were used in template, take only the variable name
        # Regular expression to match Jinja2 placeholders with or without filters
        # inferred_params = re.findall(r'\{\{\s*(\w+)(\s*\|\s*[^}]+)?\s*\}\}', self.command)
        # for param_tuple in inferred_params:
        #    param = param_tuple[0]  # Extract the parameter name
        #    if param not in self.parameters:
        #        self.parameters[param] = ToolParameter()
        for param in inferred_params:
            if param not in self.parameters:
                self.parameters[param] = ToolParameter()

    def get_parameterized_one_liner(self, params) -> str:
        params = sanitize_params(params)
        if self.user_description:
            template = Template(self.user_description)
        else:
            cmd_or_script = self.command or self.script
            template = Template(cmd_or_script)  # type: ignore
        return template.render(params)

    def _build_context(self, params):
        params = sanitize_params(params)
        context = {**params}
        return context

    def _get_status(
        self, return_code: int, raw_output: str
    ) -> StructuredToolResultStatus:
        if return_code != 0:
            return StructuredToolResultStatus.ERROR
        if raw_output == "":
            return StructuredToolResultStatus.NO_DATA
        return StructuredToolResultStatus.SUCCESS

    def _invoke(
        self,
        params: dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        if self.command is not None:
            raw_output, return_code, invocation = self.__invoke_command(params)
        else:
            raw_output, return_code, invocation = self.__invoke_script(params)  # type: ignore

        if self.additional_instructions and return_code == 0:
            logger.info(
                f"Applying additional instructions: {self.additional_instructions}"
            )
            output_with_instructions = self.__apply_additional_instructions(raw_output)
        else:
            output_with_instructions = raw_output

        error = (
            None
            if return_code == 0
            else f"Command `{invocation}` failed with return code {return_code}\nOutput:\n{raw_output}"
        )
        status = self._get_status(return_code, raw_output)

        return StructuredToolResult(
            status=status,
            error=error,
            return_code=return_code,
            data=output_with_instructions,
            params=params,
            invocation=invocation,
        )

    def __apply_additional_instructions(self, raw_output: str) -> str:
        try:
            result = subprocess.run(
                self.additional_instructions,  # type: ignore
                input=raw_output,
                shell=True,
                text=True,
                capture_output=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to apply additional instructions: {self.additional_instructions}. "
                f"Error: {e.stderr}"
            )
            return f"Error applying additional instructions: {e.stderr}"

    def __invoke_command(self, params) -> Tuple[str, int, str]:
        context = self._build_context(params)
        command = os.path.expandvars(self.command)  # type: ignore
        template = Template(command)  # type: ignore
        rendered_command = template.render(context)
        output, return_code = self.__execute_subprocess(rendered_command)
        return output, return_code, rendered_command

    def __invoke_script(self, params) -> str:
        context = self._build_context(params)
        script = os.path.expandvars(self.script)  # type: ignore
        template = Template(script)  # type: ignore
        rendered_script = template.render(context)

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".sh"
        ) as temp_script:
            temp_script.write(rendered_script)
            temp_script_path = temp_script.name
        subprocess.run(["chmod", "+x", temp_script_path], check=True)

        try:
            output, return_code = self.__execute_subprocess(temp_script_path)
        finally:
            subprocess.run(["rm", temp_script_path])
        return output, return_code, rendered_script  # type: ignore

    def __execute_subprocess(self, cmd) -> Tuple[str, int]:
        try:
            logger.debug(f"Running `{cmd}`")
            protected_cmd = get_ulimit_prefix() + cmd
            result = subprocess.run(
                protected_cmd,
                shell=True,
                text=True,
                check=False,  # do not throw error, we just return the error code
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            output = result.stdout.strip()
            output = check_oom_and_append_hint(output, result.returncode)
            return output, result.returncode
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while running '{cmd}': {e}",
                exc_info=True,
            )
            output = f"Command execution failed with error: {e}"
            return output, 1


class StaticPrerequisite(BaseModel):
    enabled: bool
    disabled_reason: str


class CallablePrerequisite(BaseModel):
    callable: Callable[[dict[str, Any]], Tuple[bool, str]]


class ToolsetCommandPrerequisite(BaseModel):
    command: str  # must complete successfully (error code 0) for prereq to be satisfied
    expected_output: Optional[str] = None  # optional


class ToolsetEnvironmentPrerequisite(BaseModel):
    env: List[str] = []  # optional


class Toolset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experimental: bool = False

    enabled: bool = False
    name: str
    description: str
    docs_url: Optional[str] = None
    icon_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    additional_instructions: Optional[str] = ""
    prerequisites: List[
        Union[
            StaticPrerequisite,
            ToolsetCommandPrerequisite,
            ToolsetEnvironmentPrerequisite,
            CallablePrerequisite,
        ]
    ] = []
    tools: List[Tool]
    tags: List[ToolsetTag] = Field(
        default_factory=lambda: [ToolsetTag.CORE],
    )
    config: Optional[Any] = None
    is_default: bool = False
    llm_instructions: Optional[str] = None
    transformers: Optional[List[Transformer]] = None

    restricted_tools: List[str] = Field(
        default_factory=list,
        description="Tool names/patterns that require runbook authorization (use '*' for all tools)",
    )
    approval_required_tools: List[str] = Field(
        default_factory=list,
        description="Tool names/patterns that require user approval before execution (use '*' for all tools)",
    )

    # warning! private attributes are not copied, which can lead to subtle bugs.
    # e.g. l.extend([some_tool]) will reset these private attribute to None

    # status fields that be cached
    type: Optional[ToolsetType] = None
    path: Optional[FilePath] = None
    status: ToolsetStatusEnum = ToolsetStatusEnum.DISABLED
    error: Optional[str] = None

    def override_with(self, override: "Toolset") -> None:
        """
        Overrides the current attributes with values from the Toolset loaded from custom config
        if they are not None.
        """
        for field, value in override.model_dump(
            exclude_unset=True,
            exclude=("name"),  # type: ignore
        ).items():
            if field in self.__class__.model_fields and value not in (None, [], {}, ""):
                setattr(self, field, value)

    @model_validator(mode="before")
    def preprocess_tools(cls, values):
        additional_instructions = values.get("additional_instructions", "")
        transformers = values.get("transformers", None)
        tools_data = values.get("tools", [])

        # Convert raw dict transformers to Transformer objects BEFORE merging
        if transformers:
            converted_transformers = []
            for t in transformers:
                if isinstance(t, dict):
                    try:
                        transformer_obj = Transformer(**t)
                        # Check if transformer is registered
                        from holmes.core.transformers import registry

                        if not registry.is_registered(transformer_obj.name):
                            logger.warning(
                                f"Invalid toolset transformer configuration: Transformer '{transformer_obj.name}' is not registered"
                            )
                            continue  # Skip invalid transformer
                        converted_transformers.append(transformer_obj)
                    except Exception as e:
                        # Log warning and skip invalid transformer
                        logger.warning(
                            f"Invalid toolset transformer configuration: {e}"
                        )
                        continue
                else:
                    # Already a Transformer object
                    converted_transformers.append(t)
            transformers = converted_transformers if converted_transformers else None

        tools = []
        for tool in tools_data:
            if isinstance(tool, dict):
                tool["additional_instructions"] = additional_instructions

                # Convert tool-level transformers to Transformer objects
                tool_transformers = tool.get("transformers")
                if tool_transformers:
                    converted_tool_transformers = []
                    for t in tool_transformers:
                        if isinstance(t, dict):
                            try:
                                transformer_obj = Transformer(**t)
                                # Check if transformer is registered
                                from holmes.core.transformers import registry

                                if not registry.is_registered(transformer_obj.name):
                                    logger.warning(
                                        f"Invalid tool transformer configuration: Transformer '{transformer_obj.name}' is not registered"
                                    )
                                    continue  # Skip invalid transformer
                                converted_tool_transformers.append(transformer_obj)
                            except Exception as e:
                                # Log warning and skip invalid transformer
                                logger.warning(
                                    f"Invalid tool transformer configuration: {e}"
                                )
                                continue
                        else:
                            # Already a Transformer object
                            converted_tool_transformers.append(t)
                    tool_transformers = (
                        converted_tool_transformers
                        if converted_tool_transformers
                        else None
                    )

                # Merge toolset-level transformers with tool-level configs
                tool["transformers"] = merge_transformers(
                    base_transformers=transformers,
                    override_transformers=tool_transformers,
                )
            if isinstance(tool, Tool):
                tool.additional_instructions = additional_instructions
                # Merge toolset-level transformers with tool-level configs
                tool.transformers = merge_transformers(  # type: ignore
                    base_transformers=transformers,
                    override_transformers=tool.transformers,
                )
            tools.append(tool)
        values["tools"] = tools

        return values

    def get_environment_variables(self) -> List[str]:
        env_vars = set()

        for prereq in self.prerequisites:
            if isinstance(prereq, ToolsetEnvironmentPrerequisite):
                env_vars.update(prereq.env)
        return list(env_vars)

    def interpolate_command(self, command: str) -> str:
        interpolated_command = os.path.expandvars(command)

        return interpolated_command

    def check_prerequisites(self, silent: bool = False):
        self.status = ToolsetStatusEnum.ENABLED

        # Sort prerequisites by type to fail fast on missing env vars before
        # running slow commands (e.g., ArgoCD checks that timeout):
        # 1. Static checks (instant)
        # 2. Environment variable checks (instant, often required by commands)
        # 3. Callable checks (variable speed)
        # 4. Command checks (slowest - may timeout or hang)
        def prereq_priority(prereq):
            if isinstance(prereq, StaticPrerequisite):
                return 0
            elif isinstance(prereq, ToolsetEnvironmentPrerequisite):
                return 1
            elif isinstance(prereq, CallablePrerequisite):
                return 2
            elif isinstance(prereq, ToolsetCommandPrerequisite):
                return 3
            return 4  # Unknown types go last

        sorted_prereqs = sorted(self.prerequisites, key=prereq_priority)

        for prereq in sorted_prereqs:
            if isinstance(prereq, ToolsetCommandPrerequisite):
                try:
                    command = self.interpolate_command(prereq.command)
                    result = subprocess.run(
                        command,
                        shell=True,
                        check=True,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    if (
                        prereq.expected_output
                        and prereq.expected_output not in result.stdout
                    ):
                        self.status = ToolsetStatusEnum.FAILED
                        self.error = f"`{prereq.command}` did not include `{prereq.expected_output}`"
                except subprocess.CalledProcessError as e:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"`{prereq.command}` returned {e.returncode}"

            elif isinstance(prereq, ToolsetEnvironmentPrerequisite):
                for env_var in prereq.env:
                    if env_var not in os.environ:
                        self.status = ToolsetStatusEnum.FAILED
                        self.error = f"Environment variable {env_var} was not set"

            elif isinstance(prereq, StaticPrerequisite):
                if not prereq.enabled:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"{prereq.disabled_reason}"

            elif isinstance(prereq, CallablePrerequisite):
                try:
                    (enabled, error_message) = prereq.callable(self.config)
                    if not enabled:
                        self.status = ToolsetStatusEnum.FAILED
                    if error_message:
                        self.error = f"{error_message}"
                except Exception as e:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"Prerequisite call failed unexpectedly: {str(e)}"

            if (
                self.status == ToolsetStatusEnum.DISABLED
                or self.status == ToolsetStatusEnum.FAILED
            ):
                if not silent:
                    logger.info(f"❌ Toolset {self.name}: {self.error}")
                # no point checking further prerequisites if one failed
                return

        if not silent:
            logger.info(f"✅ Toolset {self.name}")

    @abstractmethod
    def get_example_config(self) -> Dict[str, Any]:
        return {}

    def _load_llm_instructions(self, jinja_template: str):
        tool_names = [t.name for t in self.tools]
        self.llm_instructions = load_and_render_prompt(
            prompt=jinja_template,
            context={"tool_names": tool_names, "config": self.config},
        )

    def _load_llm_instructions_from_file(self, file_dir: str, filename: str) -> None:
        """Helper method to load LLM instructions from a jinja2 template file.

        Args:
            file_dir: Directory where the template file is located (typically os.path.dirname(__file__))
            filename: Name of the jinja2 template file (e.g., "toolset_grafana_dashboard.jinja2")
        """
        template_file_path = os.path.abspath(os.path.join(file_dir, filename))
        self._load_llm_instructions(jinja_template=f"file://{template_file_path}")


class YAMLToolset(Toolset):
    tools: List[YAMLTool]  # type: ignore

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.llm_instructions:
            self._load_llm_instructions(self.llm_instructions)

    def get_example_config(self) -> Dict[str, Any]:
        return {}


class ToolsetYamlFromConfig(Toolset):
    """
    ToolsetYamlFromConfig represents a toolset loaded from a YAML configuration file.
    To override a build-in toolset fields, we don't have to explicitly set all required fields,
    instead, we only put the fields we want to override in the YAML file.
    ToolsetYamlFromConfig helps py-pass the pydantic validation of the required fields and together with
    `override_with` method, a build-in toolset object with new configurations is created.
    """

    name: str
    # YamlToolset is loaded from a YAML file specified by the user and should be enabled by default
    # Built-in toolsets are exception and should be disabled by default when loaded
    enabled: bool = True
    additional_instructions: Optional[str] = None
    prerequisites: List[
        Union[
            StaticPrerequisite,
            ToolsetCommandPrerequisite,
            ToolsetEnvironmentPrerequisite,
        ]
    ] = []  # type: ignore
    tools: Optional[List[YAMLTool]] = []  # type: ignore
    description: Optional[str] = None  # type: ignore
    docs_url: Optional[str] = None
    icon_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    config: Optional[Any] = None
    url: Optional[str] = None  # MCP toolset

    restricted_tools: List[str] = Field(default_factory=list)
    approval_required_tools: List[str] = Field(default_factory=list)

    def get_example_config(self) -> Dict[str, Any]:
        return {}


class ToolsetDBModel(BaseModel):
    account_id: str
    cluster_id: str
    toolset_name: str
    icon_url: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    description: Optional[str] = None
    docs_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    updated_at: str = Field(default_factory=datetime.now().isoformat)


def pretty_print_toolset_status(toolsets: list[Toolset], console: Console) -> None:
    status_fields = ["name", "enabled", "status", "type", "path", "error"]
    toolsets_status = []
    for toolset in sorted(toolsets, key=lambda ts: ts.status.value):
        toolset_status = json.loads(toolset.model_dump_json(include=status_fields))  # type: ignore

        status_value = toolset_status.get("status", "")
        error_value = toolset_status.get("error", "")
        if status_value == "enabled":
            toolset_status["status"] = "[green]enabled[/green]"
        elif status_value == "failed":
            toolset_status["status"] = "[red]failed[/red]"
            toolset_status["error"] = f"[red]{error_value}[/red]"
        else:
            toolset_status["status"] = f"[yellow]{status_value}[/yellow]"

        # Replace None with "" for Path and Error columns
        for field in ["path", "error"]:
            if toolset_status.get(field) is None:
                toolset_status[field] = ""

        order_toolset_status = OrderedDict(
            (k.capitalize(), toolset_status[k])
            for k in status_fields
            if k in toolset_status
        )
        toolsets_status.append(order_toolset_status)

    table = Table(show_header=True, header_style="bold")
    for col in status_fields:
        table.add_column(col.capitalize())

    for row in toolsets_status:
        table.add_row(*(str(row.get(col.capitalize(), "")) for col in status_fields))

    console.print(table)
```

---
## Toolset: `kubernetes/kube-prometheus-stack`
- **类**: `YAMLToolset`
- **模块**: `holmes.core.tools`
- **enabled**: `True`
- **status**: `enabled`

### 已注册工具（1 个）
| tool | description | class | module |
|---|---|---|---|
| `get_prometheus_target` | Fetch the definition of a Prometheus target | `YAMLTool` | `holmes.core.tools` |

### 工具输入参数（Schema）

#### `get_prometheus_target`
```json
{
  "prometheus_namespace": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "prometheus_service_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "target_name": {
    "description": null,
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

### 相关源码文件（holmes 包内，1 个）

#### `core/tools.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/core/tools.py`
```python
import fnmatch
import json
import logging
import os
import re
import shlex
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    OrderedDict,
    Tuple,
    Union,
)

from jinja2 import Template
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    PrivateAttr,
    model_validator,
)
from rich.console import Console
from rich.table import Table

from holmes.core.llm import LLM
from holmes.core.openai_formatting import format_tool_to_open_ai_standard
from holmes.core.transformers import (
    Transformer,
    TransformerError,
    registry,
)
from holmes.plugins.prompts import load_and_render_prompt
from holmes.utils.config_utils import merge_transformers
from holmes.utils.memory_limit import check_oom_and_append_hint, get_ulimit_prefix

if TYPE_CHECKING:
    from holmes.core.transformers import BaseTransformer

logger = logging.getLogger(__name__)


class StructuredToolResultStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    NO_DATA = "no_data"
    APPROVAL_REQUIRED = "approval_required"

    def to_color(self) -> str:
        if self == StructuredToolResultStatus.SUCCESS:
            return "green"
        elif self == StructuredToolResultStatus.ERROR:
            return "red"
        elif self == StructuredToolResultStatus.APPROVAL_REQUIRED:
            return "yellow"
        else:
            return "white"

    def to_emoji(self) -> str:
        if self == StructuredToolResultStatus.SUCCESS:
            return "✔"
        elif self == StructuredToolResultStatus.ERROR:
            return "❌"
        elif self == StructuredToolResultStatus.APPROVAL_REQUIRED:
            return "⚠️"
        else:
            return "⚪️"


class StructuredToolResult(BaseModel):
    schema_version: str = "robusta:v1.0.0"
    status: StructuredToolResultStatus
    error: Optional[str] = None
    return_code: Optional[int] = None
    data: Optional[Any] = None
    url: Optional[str] = None
    invocation: Optional[str] = None
    params: Optional[Dict] = None
    icon_url: Optional[str] = None

    def get_stringified_data(self) -> str:
        if self.data is None:
            return ""

        if isinstance(self.data, str):
            return self.data
        else:
            try:
                if isinstance(self.data, BaseModel):
                    return self.data.model_dump_json()
                else:
                    return json.dumps(
                        self.data, separators=(",", ":"), ensure_ascii=False
                    )
            except Exception:
                return str(self.data)


class ApprovalRequirement(BaseModel):
    needs_approval: bool
    reason: str = ""


def sanitize(param):
    # allow empty strings to be unquoted - useful for optional params
    # it is up to the user to ensure that the command they are using is ok with empty strings
    # and if not to take that into account via an appropriate jinja template
    if param == "":
        return ""

    return shlex.quote(str(param))


def sanitize_params(params):
    return {k: sanitize(str(v)) for k, v in params.items()}


class ToolsetStatusEnum(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"


class ToolsetTag(str, Enum):
    CORE = "core"
    CLUSTER = "cluster"
    CLI = "cli"


class ToolsetType(str, Enum):
    BUILTIN = "built-in"
    CUSTOMIZED = "custom"
    MCP = "mcp"


class ToolParameter(BaseModel):
    description: Optional[str] = None
    type: str = "string"
    required: bool = True
    properties: Optional[Dict[str, "ToolParameter"]] = None  # For object types
    items: Optional["ToolParameter"] = None  # For array item schemas
    enum: Optional[List[str]] = None  # For restricting to specific values


class ToolInvokeContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tool_number: Optional[int] = None
    user_approved: bool = False
    llm: LLM
    max_token_count: int
    tool_call_id: str
    tool_name: str


class Tool(ABC, BaseModel):
    name: str
    description: str
    parameters: Dict[str, ToolParameter] = {}
    user_description: Optional[str] = (
        None  # templated string to show to the user describing this tool invocation (not seen by llm)
    )
    additional_instructions: Optional[str] = None
    icon_url: Optional[str] = Field(
        default=None,
        description="The URL of the icon for the tool, if None will get toolset icon",
    )
    transformers: Optional[List[Transformer]] = None
    restricted: bool = Field(
        default=False,
        description="If True, tool requires runbook authorization or restricted_tools=true to use",
    )

    # Private attribute to store initialized transformer instances for performance
    _transformer_instances: Optional[List["BaseTransformer"]] = PrivateAttr(
        default=None
    )

    def model_post_init(self, __context) -> None:
        """Initialize transformer instances once during tool creation for better performance."""
        logger.debug(
            f"Tool '{self.name}' model_post_init: creating transformer instances"
        )

        if self.transformers:
            logger.debug(
                f"Tool '{self.name}' has {len(self.transformers)} transformers to initialize"
            )
            self._transformer_instances = []
            for transformer in self.transformers:
                if not transformer:
                    continue
                logger.debug(
                    f"  Initializing transformer '{transformer.name}' with config: {transformer.config}"
                )
                try:
                    # Create transformer instance once and cache it
                    transformer_instance = registry.create_transformer(
                        transformer.name, transformer.config
                    )
                    self._transformer_instances.append(transformer_instance)
                    logger.debug(
                        f"Initialized transformer '{transformer.name}' for tool '{self.name}'"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize transformer '{transformer.name}' for tool '{self.name}': {e}"
                    )
                    # Continue with other transformers, don't fail the entire initialization
                    continue
        else:
            logger.debug(f"Tool '{self.name}' has no transformers")
            self._transformer_instances = None

    def get_openai_format(self, target_model: str):

        return format_tool_to_open_ai_standard(
            tool_name=self.name,
            tool_description=self.description,
            tool_parameters=self.parameters,
            target_model=target_model,
        )

    def invoke(
        self,
        params: Dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        tool_number_str = f"#{context.tool_number} " if context.tool_number else ""
        logger.info(
            f"Running tool {tool_number_str}[bold]{self.name}[/bold]: {self.get_parameterized_one_liner(params)}"
        )

        if not context.user_approved:
            approval_check = self._get_approval_requirement(params, context)
            if approval_check and approval_check.needs_approval:
                logger.info(
                    f"  [yellow]Tool '{self.name}' requires approval: {approval_check.reason}[/yellow]"
                )
                return StructuredToolResult(
                    status=StructuredToolResultStatus.APPROVAL_REQUIRED,
                    error=approval_check.reason,
                    params=params,
                    invocation=self.get_parameterized_one_liner(params),
                )

        start_time = time.time()
        result = self._invoke(params=params, context=context)
        result.icon_url = self.icon_url

        transformed_result = self._apply_transformers(result)
        elapsed = time.time() - start_time
        output_str = (
            transformed_result.get_stringified_data()
            if hasattr(transformed_result, "get_stringified_data")
            else str(transformed_result)
        )
        show_hint = f"/show {context.tool_number}" if context.tool_number else "/show"
        line_count = output_str.count("\n") + 1 if output_str else 0
        logger.info(
            f"  [dim]Finished {tool_number_str}in {elapsed:.2f}s, output length: {len(output_str):,} characters ({line_count:,} lines) - {show_hint} to view contents[/dim]"
        )
        return transformed_result

    def _is_restricted(self) -> bool:
        if self.restricted:
            return True

        toolset = getattr(self, "toolset", None)
        if toolset:
            for pattern in getattr(toolset, "restricted_tools", []):
                if fnmatch.fnmatch(self.name, pattern):
                    return True

        return False

    def _get_approval_requirement(
        self, params: Dict, context: ToolInvokeContext
    ) -> Optional[ApprovalRequirement]:
        toolset_approval = self._check_approval_config()
        if toolset_approval and toolset_approval.needs_approval:
            return toolset_approval
        return self.requires_approval(params, context)

    def _check_approval_config(self) -> Optional[ApprovalRequirement]:
        toolset = getattr(self, "toolset", None)
        if not toolset:
            return None

        for pattern in getattr(toolset, "approval_required_tools", []):
            if fnmatch.fnmatch(self.name, pattern):
                return ApprovalRequirement(
                    needs_approval=True,
                    reason=f"Tool '{self.name}' matches approval pattern '{pattern}'",
                )
        return None

    def requires_approval(
        self, params: Dict, context: ToolInvokeContext
    ) -> Optional[ApprovalRequirement]:
        """Override to implement tool-specific approval logic."""
        return None

    def _apply_transformers(self, result: StructuredToolResult) -> StructuredToolResult:
        """
        Apply configured transformers to the tool result.

        Args:
            result: The original tool result

        Returns:
            The tool result with transformed data, or original result if transformation fails
        """
        if (
            not self._transformer_instances
            or result.status != StructuredToolResultStatus.SUCCESS
        ):
            return result

        # Get the output string to transform
        original_data = result.get_stringified_data()
        if not original_data:
            return result

        transformed_data = original_data
        transformers_applied = []

        # Use cached transformer instances instead of creating new ones
        for transformer_instance in self._transformer_instances:
            try:
                # Check if transformer should be applied
                if not transformer_instance.should_apply(transformed_data):
                    logger.debug(
                        f"Transformer '{transformer_instance.name}' skipped for tool '{self.name}' (conditions not met)"
                    )
                    continue

                # Apply transformation
                pre_transform_size = len(transformed_data)
                transform_start_time = time.time()
                original_data = transformed_data  # Keep a copy for potential reversion
                transformed_data = transformer_instance.transform(transformed_data)
                transform_elapsed = time.time() - transform_start_time

                # Check if this is llm_summarize and revert if summary is not smaller
                post_transform_size = len(transformed_data)
                if (
                    transformer_instance.name == "llm_summarize"
                    and post_transform_size >= pre_transform_size
                ):
                    # Revert to original data if summary is not smaller
                    transformed_data = original_data
                    logger.debug(
                        f"Transformer '{transformer_instance.name}' reverted for tool '{self.name}' "
                        f"(output size {post_transform_size:,} >= input size {pre_transform_size:,})"
                    )
                    continue  # Don't mark as applied

                transformers_applied.append(transformer_instance.name)

                # Generic logging - transformers can override this with their own specific metrics
                size_change = post_transform_size - pre_transform_size
                logger.info(
                    f"Applied transformer '{transformer_instance.name}' to tool '{self.name}' output "
                    f"in {transform_elapsed:.2f}s (size: {pre_transform_size:,} → {post_transform_size:,} chars, "
                    f"change: {size_change:+,})"
                )

            except TransformerError as e:
                logger.warning(
                    f"Transformer '{transformer_instance.name}' failed for tool '{self.name}': {e}"
                )
                # Continue with other transformers, don't fail the entire chain
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error applying transformer '{transformer_instance.name}' to tool '{self.name}': {e}"
                )
                # Continue with other transformers
                continue

        # If any transformers were applied, update the result
        if transformers_applied:
            # Create a copy of the result with transformed data
            result_dict = result.model_dump(exclude={"data"})
            result_dict["data"] = transformed_data
            return StructuredToolResult(**result_dict)

        return result

    @abstractmethod
    def _invoke(
        self,
        params: dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        """
        params: the tool params
        user_approved: whether the tool call is approved by the user. Can be used to confidently execute unsafe actions.
        """
        pass

    @abstractmethod
    def get_parameterized_one_liner(self, params: Dict) -> str:
        return ""


class YAMLTool(Tool, BaseModel):
    command: Optional[str] = None
    script: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.__infer_parameters()

    def __infer_parameters(self):
        # Find parameters that appear inside self.command or self.script but weren't declared in parameters
        template = self.command or self.script
        inferred_params = re.findall(r"\{\{\s*([\w]+)[\.\|]?.*?\s*\}\}", template)
        # TODO: if filters were used in template, take only the variable name
        # Regular expression to match Jinja2 placeholders with or without filters
        # inferred_params = re.findall(r'\{\{\s*(\w+)(\s*\|\s*[^}]+)?\s*\}\}', self.command)
        # for param_tuple in inferred_params:
        #    param = param_tuple[0]  # Extract the parameter name
        #    if param not in self.parameters:
        #        self.parameters[param] = ToolParameter()
        for param in inferred_params:
            if param not in self.parameters:
                self.parameters[param] = ToolParameter()

    def get_parameterized_one_liner(self, params) -> str:
        params = sanitize_params(params)
        if self.user_description:
            template = Template(self.user_description)
        else:
            cmd_or_script = self.command or self.script
            template = Template(cmd_or_script)  # type: ignore
        return template.render(params)

    def _build_context(self, params):
        params = sanitize_params(params)
        context = {**params}
        return context

    def _get_status(
        self, return_code: int, raw_output: str
    ) -> StructuredToolResultStatus:
        if return_code != 0:
            return StructuredToolResultStatus.ERROR
        if raw_output == "":
            return StructuredToolResultStatus.NO_DATA
        return StructuredToolResultStatus.SUCCESS

    def _invoke(
        self,
        params: dict,
        context: ToolInvokeContext,
    ) -> StructuredToolResult:
        if self.command is not None:
            raw_output, return_code, invocation = self.__invoke_command(params)
        else:
            raw_output, return_code, invocation = self.__invoke_script(params)  # type: ignore

        if self.additional_instructions and return_code == 0:
            logger.info(
                f"Applying additional instructions: {self.additional_instructions}"
            )
            output_with_instructions = self.__apply_additional_instructions(raw_output)
        else:
            output_with_instructions = raw_output

        error = (
            None
            if return_code == 0
            else f"Command `{invocation}` failed with return code {return_code}\nOutput:\n{raw_output}"
        )
        status = self._get_status(return_code, raw_output)

        return StructuredToolResult(
            status=status,
            error=error,
            return_code=return_code,
            data=output_with_instructions,
            params=params,
            invocation=invocation,
        )

    def __apply_additional_instructions(self, raw_output: str) -> str:
        try:
            result = subprocess.run(
                self.additional_instructions,  # type: ignore
                input=raw_output,
                shell=True,
                text=True,
                capture_output=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to apply additional instructions: {self.additional_instructions}. "
                f"Error: {e.stderr}"
            )
            return f"Error applying additional instructions: {e.stderr}"

    def __invoke_command(self, params) -> Tuple[str, int, str]:
        context = self._build_context(params)
        command = os.path.expandvars(self.command)  # type: ignore
        template = Template(command)  # type: ignore
        rendered_command = template.render(context)
        output, return_code = self.__execute_subprocess(rendered_command)
        return output, return_code, rendered_command

    def __invoke_script(self, params) -> str:
        context = self._build_context(params)
        script = os.path.expandvars(self.script)  # type: ignore
        template = Template(script)  # type: ignore
        rendered_script = template.render(context)

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".sh"
        ) as temp_script:
            temp_script.write(rendered_script)
            temp_script_path = temp_script.name
        subprocess.run(["chmod", "+x", temp_script_path], check=True)

        try:
            output, return_code = self.__execute_subprocess(temp_script_path)
        finally:
            subprocess.run(["rm", temp_script_path])
        return output, return_code, rendered_script  # type: ignore

    def __execute_subprocess(self, cmd) -> Tuple[str, int]:
        try:
            logger.debug(f"Running `{cmd}`")
            protected_cmd = get_ulimit_prefix() + cmd
            result = subprocess.run(
                protected_cmd,
                shell=True,
                text=True,
                check=False,  # do not throw error, we just return the error code
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            output = result.stdout.strip()
            output = check_oom_and_append_hint(output, result.returncode)
            return output, result.returncode
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while running '{cmd}': {e}",
                exc_info=True,
            )
            output = f"Command execution failed with error: {e}"
            return output, 1


class StaticPrerequisite(BaseModel):
    enabled: bool
    disabled_reason: str


class CallablePrerequisite(BaseModel):
    callable: Callable[[dict[str, Any]], Tuple[bool, str]]


class ToolsetCommandPrerequisite(BaseModel):
    command: str  # must complete successfully (error code 0) for prereq to be satisfied
    expected_output: Optional[str] = None  # optional


class ToolsetEnvironmentPrerequisite(BaseModel):
    env: List[str] = []  # optional


class Toolset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experimental: bool = False

    enabled: bool = False
    name: str
    description: str
    docs_url: Optional[str] = None
    icon_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    additional_instructions: Optional[str] = ""
    prerequisites: List[
        Union[
            StaticPrerequisite,
            ToolsetCommandPrerequisite,
            ToolsetEnvironmentPrerequisite,
            CallablePrerequisite,
        ]
    ] = []
    tools: List[Tool]
    tags: List[ToolsetTag] = Field(
        default_factory=lambda: [ToolsetTag.CORE],
    )
    config: Optional[Any] = None
    is_default: bool = False
    llm_instructions: Optional[str] = None
    transformers: Optional[List[Transformer]] = None

    restricted_tools: List[str] = Field(
        default_factory=list,
        description="Tool names/patterns that require runbook authorization (use '*' for all tools)",
    )
    approval_required_tools: List[str] = Field(
        default_factory=list,
        description="Tool names/patterns that require user approval before execution (use '*' for all tools)",
    )

    # warning! private attributes are not copied, which can lead to subtle bugs.
    # e.g. l.extend([some_tool]) will reset these private attribute to None

    # status fields that be cached
    type: Optional[ToolsetType] = None
    path: Optional[FilePath] = None
    status: ToolsetStatusEnum = ToolsetStatusEnum.DISABLED
    error: Optional[str] = None

    def override_with(self, override: "Toolset") -> None:
        """
        Overrides the current attributes with values from the Toolset loaded from custom config
        if they are not None.
        """
        for field, value in override.model_dump(
            exclude_unset=True,
            exclude=("name"),  # type: ignore
        ).items():
            if field in self.__class__.model_fields and value not in (None, [], {}, ""):
                setattr(self, field, value)

    @model_validator(mode="before")
    def preprocess_tools(cls, values):
        additional_instructions = values.get("additional_instructions", "")
        transformers = values.get("transformers", None)
        tools_data = values.get("tools", [])

        # Convert raw dict transformers to Transformer objects BEFORE merging
        if transformers:
            converted_transformers = []
            for t in transformers:
                if isinstance(t, dict):
                    try:
                        transformer_obj = Transformer(**t)
                        # Check if transformer is registered
                        from holmes.core.transformers import registry

                        if not registry.is_registered(transformer_obj.name):
                            logger.warning(
                                f"Invalid toolset transformer configuration: Transformer '{transformer_obj.name}' is not registered"
                            )
                            continue  # Skip invalid transformer
                        converted_transformers.append(transformer_obj)
                    except Exception as e:
                        # Log warning and skip invalid transformer
                        logger.warning(
                            f"Invalid toolset transformer configuration: {e}"
                        )
                        continue
                else:
                    # Already a Transformer object
                    converted_transformers.append(t)
            transformers = converted_transformers if converted_transformers else None

        tools = []
        for tool in tools_data:
            if isinstance(tool, dict):
                tool["additional_instructions"] = additional_instructions

                # Convert tool-level transformers to Transformer objects
                tool_transformers = tool.get("transformers")
                if tool_transformers:
                    converted_tool_transformers = []
                    for t in tool_transformers:
                        if isinstance(t, dict):
                            try:
                                transformer_obj = Transformer(**t)
                                # Check if transformer is registered
                                from holmes.core.transformers import registry

                                if not registry.is_registered(transformer_obj.name):
                                    logger.warning(
                                        f"Invalid tool transformer configuration: Transformer '{transformer_obj.name}' is not registered"
                                    )
                                    continue  # Skip invalid transformer
                                converted_tool_transformers.append(transformer_obj)
                            except Exception as e:
                                # Log warning and skip invalid transformer
                                logger.warning(
                                    f"Invalid tool transformer configuration: {e}"
                                )
                                continue
                        else:
                            # Already a Transformer object
                            converted_tool_transformers.append(t)
                    tool_transformers = (
                        converted_tool_transformers
                        if converted_tool_transformers
                        else None
                    )

                # Merge toolset-level transformers with tool-level configs
                tool["transformers"] = merge_transformers(
                    base_transformers=transformers,
                    override_transformers=tool_transformers,
                )
            if isinstance(tool, Tool):
                tool.additional_instructions = additional_instructions
                # Merge toolset-level transformers with tool-level configs
                tool.transformers = merge_transformers(  # type: ignore
                    base_transformers=transformers,
                    override_transformers=tool.transformers,
                )
            tools.append(tool)
        values["tools"] = tools

        return values

    def get_environment_variables(self) -> List[str]:
        env_vars = set()

        for prereq in self.prerequisites:
            if isinstance(prereq, ToolsetEnvironmentPrerequisite):
                env_vars.update(prereq.env)
        return list(env_vars)

    def interpolate_command(self, command: str) -> str:
        interpolated_command = os.path.expandvars(command)

        return interpolated_command

    def check_prerequisites(self, silent: bool = False):
        self.status = ToolsetStatusEnum.ENABLED

        # Sort prerequisites by type to fail fast on missing env vars before
        # running slow commands (e.g., ArgoCD checks that timeout):
        # 1. Static checks (instant)
        # 2. Environment variable checks (instant, often required by commands)
        # 3. Callable checks (variable speed)
        # 4. Command checks (slowest - may timeout or hang)
        def prereq_priority(prereq):
            if isinstance(prereq, StaticPrerequisite):
                return 0
            elif isinstance(prereq, ToolsetEnvironmentPrerequisite):
                return 1
            elif isinstance(prereq, CallablePrerequisite):
                return 2
            elif isinstance(prereq, ToolsetCommandPrerequisite):
                return 3
            return 4  # Unknown types go last

        sorted_prereqs = sorted(self.prerequisites, key=prereq_priority)

        for prereq in sorted_prereqs:
            if isinstance(prereq, ToolsetCommandPrerequisite):
                try:
                    command = self.interpolate_command(prereq.command)
                    result = subprocess.run(
                        command,
                        shell=True,
                        check=True,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    if (
                        prereq.expected_output
                        and prereq.expected_output not in result.stdout
                    ):
                        self.status = ToolsetStatusEnum.FAILED
                        self.error = f"`{prereq.command}` did not include `{prereq.expected_output}`"
                except subprocess.CalledProcessError as e:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"`{prereq.command}` returned {e.returncode}"

            elif isinstance(prereq, ToolsetEnvironmentPrerequisite):
                for env_var in prereq.env:
                    if env_var not in os.environ:
                        self.status = ToolsetStatusEnum.FAILED
                        self.error = f"Environment variable {env_var} was not set"

            elif isinstance(prereq, StaticPrerequisite):
                if not prereq.enabled:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"{prereq.disabled_reason}"

            elif isinstance(prereq, CallablePrerequisite):
                try:
                    (enabled, error_message) = prereq.callable(self.config)
                    if not enabled:
                        self.status = ToolsetStatusEnum.FAILED
                    if error_message:
                        self.error = f"{error_message}"
                except Exception as e:
                    self.status = ToolsetStatusEnum.FAILED
                    self.error = f"Prerequisite call failed unexpectedly: {str(e)}"

            if (
                self.status == ToolsetStatusEnum.DISABLED
                or self.status == ToolsetStatusEnum.FAILED
            ):
                if not silent:
                    logger.info(f"❌ Toolset {self.name}: {self.error}")
                # no point checking further prerequisites if one failed
                return

        if not silent:
            logger.info(f"✅ Toolset {self.name}")

    @abstractmethod
    def get_example_config(self) -> Dict[str, Any]:
        return {}

    def _load_llm_instructions(self, jinja_template: str):
        tool_names = [t.name for t in self.tools]
        self.llm_instructions = load_and_render_prompt(
            prompt=jinja_template,
            context={"tool_names": tool_names, "config": self.config},
        )

    def _load_llm_instructions_from_file(self, file_dir: str, filename: str) -> None:
        """Helper method to load LLM instructions from a jinja2 template file.

        Args:
            file_dir: Directory where the template file is located (typically os.path.dirname(__file__))
            filename: Name of the jinja2 template file (e.g., "toolset_grafana_dashboard.jinja2")
        """
        template_file_path = os.path.abspath(os.path.join(file_dir, filename))
        self._load_llm_instructions(jinja_template=f"file://{template_file_path}")


class YAMLToolset(Toolset):
    tools: List[YAMLTool]  # type: ignore

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.llm_instructions:
            self._load_llm_instructions(self.llm_instructions)

    def get_example_config(self) -> Dict[str, Any]:
        return {}


class ToolsetYamlFromConfig(Toolset):
    """
    ToolsetYamlFromConfig represents a toolset loaded from a YAML configuration file.
    To override a build-in toolset fields, we don't have to explicitly set all required fields,
    instead, we only put the fields we want to override in the YAML file.
    ToolsetYamlFromConfig helps py-pass the pydantic validation of the required fields and together with
    `override_with` method, a build-in toolset object with new configurations is created.
    """

    name: str
    # YamlToolset is loaded from a YAML file specified by the user and should be enabled by default
    # Built-in toolsets are exception and should be disabled by default when loaded
    enabled: bool = True
    additional_instructions: Optional[str] = None
    prerequisites: List[
        Union[
            StaticPrerequisite,
            ToolsetCommandPrerequisite,
            ToolsetEnvironmentPrerequisite,
        ]
    ] = []  # type: ignore
    tools: Optional[List[YAMLTool]] = []  # type: ignore
    description: Optional[str] = None  # type: ignore
    docs_url: Optional[str] = None
    icon_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    config: Optional[Any] = None
    url: Optional[str] = None  # MCP toolset

    restricted_tools: List[str] = Field(default_factory=list)
    approval_required_tools: List[str] = Field(default_factory=list)

    def get_example_config(self) -> Dict[str, Any]:
        return {}


class ToolsetDBModel(BaseModel):
    account_id: str
    cluster_id: str
    toolset_name: str
    icon_url: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    description: Optional[str] = None
    docs_url: Optional[str] = None
    installation_instructions: Optional[str] = None
    updated_at: str = Field(default_factory=datetime.now().isoformat)


def pretty_print_toolset_status(toolsets: list[Toolset], console: Console) -> None:
    status_fields = ["name", "enabled", "status", "type", "path", "error"]
    toolsets_status = []
    for toolset in sorted(toolsets, key=lambda ts: ts.status.value):
        toolset_status = json.loads(toolset.model_dump_json(include=status_fields))  # type: ignore

        status_value = toolset_status.get("status", "")
        error_value = toolset_status.get("error", "")
        if status_value == "enabled":
            toolset_status["status"] = "[green]enabled[/green]"
        elif status_value == "failed":
            toolset_status["status"] = "[red]failed[/red]"
            toolset_status["error"] = f"[red]{error_value}[/red]"
        else:
            toolset_status["status"] = f"[yellow]{status_value}[/yellow]"

        # Replace None with "" for Path and Error columns
        for field in ["path", "error"]:
            if toolset_status.get(field) is None:
                toolset_status[field] = ""

        order_toolset_status = OrderedDict(
            (k.capitalize(), toolset_status[k])
            for k in status_fields
            if k in toolset_status
        )
        toolsets_status.append(order_toolset_status)

    table = Table(show_header=True, header_style="bold")
    for col in status_fields:
        table.add_column(col.capitalize())

    for row in toolsets_status:
        table.add_row(*(str(row.get(col.capitalize(), "")) for col in status_fields))

    console.print(table)
```

---
## Toolset: `core_investigation`
- **类**: `CoreInvestigationToolset`
- **模块**: `holmes.plugins.toolsets.investigator.core_investigation`
- **enabled**: `True`
- **status**: `enabled`

### 已注册工具（1 个）
| tool | description | class | module |
|---|---|---|---|
| `TodoWrite` | Save investigation tasks to break down complex problems into manageable sub-tasks. ALWAYS provide the COMPLETE list of all tasks, not just the ones being update… | `TodoWriteTool` | `holmes.plugins.toolsets.investigator.core_investigation` |

### 工具输入参数（Schema）

#### `TodoWrite`
```json
{
  "todos": {
    "description": "COMPLETE list of ALL tasks on the task list. Each task should have: id (string), content (string), status (pending/in_progress/completed/failed)",
    "type": "array",
    "required": true,
    "properties": null,
    "items": {
      "description": null,
      "type": "object",
      "required": true,
      "properties": {
        "id": {
          "description": null,
          "type": "string",
          "required": true,
          "properties": null,
          "items": null,
          "enum": null
        },
        "content": {
          "description": null,
          "type": "string",
          "required": true,
          "properties": null,
          "items": null,
          "enum": null
        },
        "status": {
          "description": null,
          "type": "string",
          "required": true,
          "properties": null,
          "items": null,
          "enum": [
            "pending",
            "in_progress",
            "completed",
            "failed"
          ]
        }
      },
      "items": null,
      "enum": null
    },
    "enum": null
  }
}
```

### 相关源码文件（holmes 包内，1 个）

#### `plugins/toolsets/investigator/core_investigation.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/plugins/toolsets/investigator/core_investigation.py`
```python
import logging
import os
from typing import Any, Dict
from uuid import uuid4

from holmes.core.todo_tasks_formatter import format_tasks
from holmes.core.tools import (
    StructuredToolResult,
    StructuredToolResultStatus,
    Tool,
    ToolInvokeContext,
    ToolParameter,
    Toolset,
    ToolsetTag,
)
from holmes.plugins.toolsets.investigator.model import Task, TaskStatus

TODO_WRITE_TOOL_NAME = "TodoWrite"


def parse_tasks(todos_data: Any) -> list[Task]:
    tasks = []

    for todo_item in todos_data:
        if isinstance(todo_item, dict):
            task = Task(
                id=todo_item.get("id", str(uuid4())),
                content=todo_item.get("content", ""),
                status=TaskStatus(todo_item.get("status", "pending")),
            )
            tasks.append(task)

    return tasks


class TodoWriteTool(Tool):
    name: str = TODO_WRITE_TOOL_NAME
    description: str = "Save investigation tasks to break down complex problems into manageable sub-tasks. ALWAYS provide the COMPLETE list of all tasks, not just the ones being updated."
    parameters: Dict[str, ToolParameter] = {
        "todos": ToolParameter(
            description="COMPLETE list of ALL tasks on the task list. Each task should have: id (string), content (string), status (pending/in_progress/completed/failed)",
            type="array",
            required=True,
            items=ToolParameter(
                type="object",
                properties={
                    "id": ToolParameter(type="string", required=True),
                    "content": ToolParameter(type="string", required=True),
                    "status": ToolParameter(
                        type="string",
                        required=True,
                        enum=["pending", "in_progress", "completed", "failed"],
                    ),
                },
            ),
        ),
    }

    # Print a nice table to console/log
    def print_tasks_table(self, tasks):
        if not tasks:
            logging.info("No tasks in the investigation plan.")
            return

        status_icons = {
            "pending": "[ ]",
            "in_progress": "[~]",
            "completed": "[✓]",
            "failed": "[✗]",
        }

        max_id_width = max(len(str(task.id)) for task in tasks)
        max_content_width = max(len(task.content) for task in tasks)
        max_status_display_width = max(
            len(f"{status_icons[task.status.value]} {task.status.value}")
            for task in tasks
        )

        id_width = max(max_id_width, len("ID"))
        content_width = max(max_content_width, len("Content"))
        status_width = max(max_status_display_width, len("Status"))

        separator = f"+{'-' * (id_width + 2)}+{'-' * (content_width + 2)}+{'-' * (status_width + 2)}+"
        header = f"| {'ID':<{id_width}} | {'Content':<{content_width}} | {'Status':<{status_width}} |"
        tasks_to_display = []

        for task in tasks:
            status_display = f"{status_icons[task.status.value]} {task.status.value}"
            row = f"| {task.id:<{id_width}} | {task.content:<{content_width}} | {status_display:<{status_width}} |"
            tasks_to_display.append(row)

        logging.info(
            f"Task List:\n{separator}\n{header}\n{separator}\n"
            + "\n".join(tasks_to_display)
            + f"\n{separator}"
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        try:
            todos_data = params.get("todos", [])

            tasks = parse_tasks(todos_data=todos_data)

            logging.debug(f"Tasks: {len(tasks)}")

            self.print_tasks_table(tasks)
            formatted_tasks = format_tasks(tasks)

            response_data = f"✅ Investigation plan updated with {len(tasks)} tasks. Tasks are now stored in session and will appear in subsequent prompts.\n\n"
            if formatted_tasks:
                response_data += formatted_tasks
            else:
                response_data += "No tasks currently in the investigation plan."

            return StructuredToolResult(
                status=StructuredToolResultStatus.SUCCESS,
                data=response_data,
                params=params,
            )

        except Exception as e:
            logging.exception("error using todowrite tool")
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Failed to process tasks: {str(e)}",
                params=params,
            )

    def get_parameterized_one_liner(self, params: Dict) -> str:
        return "Update investigation tasks"


class CoreInvestigationToolset(Toolset):
    """Core toolset for investigation management and task planning."""

    def __init__(self):
        super().__init__(
            name="core_investigation",
            description="Core investigation tools for task management and planning",
            enabled=True,
            tools=[TodoWriteTool()],
            tags=[ToolsetTag.CORE],
            is_default=True,
        )

    def get_example_config(self) -> Dict[str, Any]:
        return {}

    def _reload_instructions(self):
        template_file_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "investigator_instructions.jinja2")
        )
        self._load_llm_instructions(jinja_template=f"file://{template_file_path}")
```

---
## Toolset: `internet`
- **类**: `InternetToolset`
- **模块**: `holmes.plugins.toolsets.internet.internet`
- **enabled**: `True`
- **status**: `enabled`

### 已注册工具（1 个）
| tool | description | class | module |
|---|---|---|---|
| `fetch_webpage` | Fetch a webpage. Use this to fetch runbooks if they are present before starting your investigation (if no other tool like confluence is more appropriate) | `FetchWebpage` | `holmes.plugins.toolsets.internet.internet` |

### 工具输入参数（Schema）

#### `fetch_webpage`
```json
{
  "url": {
    "description": "The URL to fetch",
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

### 相关源码文件（holmes 包内，1 个）

#### `plugins/toolsets/internet/internet.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/plugins/toolsets/internet/internet.py`
```python
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests  # type: ignore
from bs4 import BeautifulSoup
from markdownify import markdownify
from requests import RequestException, Timeout  # type: ignore

from holmes.core.tools import (
    CallablePrerequisite,
    StructuredToolResult,
    StructuredToolResultStatus,
    Tool,
    ToolInvokeContext,
    ToolParameter,
    Toolset,
    ToolsetTag,
)
from holmes.plugins.toolsets.utils import toolset_name_for_one_liner

# TODO: change and make it holmes
INTERNET_TOOLSET_USER_AGENT = os.environ.get(
    "INTERNET_TOOLSET_USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0; holmesgpt;) Gecko/20100101 Firefox/128.0",
)
INTERNET_TOOLSET_TIMEOUT_SECONDS = int(
    os.environ.get("INTERNET_TOOLSET_TIMEOUT_SECONDS", "5")
)

SELECTORS_TO_REMOVE = [
    "script",
    "style",
    "link",
    "noscript",
    "header",
    "footer",
    "nav",
    "iframe",
    "svg",
    "img",
    "button",
    "menu",
    "sidebar",
    "aside",
    ".header",
    ".footer",
    ".navigation",
    ".nav",
    ".menu",
    ".sidebar",
    ".ad",
    ".advertisement",
    ".social",
    ".popup",
    ".modal",
    ".banner",
    ".cookie-notice",
    ".social-share",
    ".related-articles",
    ".recommended",
    "#header",
    "#footer",
    "#navigation",
    "#nav",
    "#menu",
    "#sidebar",
    "#ad",
    "#advertisement",
    "#social",
    "#popup",
    "#modal",
    "#banner",
    "#cookie-notice",
    "#social-share",
    "#related-articles",
    "#recommended",
]


def scrape(url: str, headers: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    response = None
    content = None
    mime_type = None
    if not headers:
        headers = {}
    headers["User-Agent"] = INTERNET_TOOLSET_USER_AGENT
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=INTERNET_TOOLSET_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except Timeout:
        error_message = f"Failed to load {url}. Timeout after {INTERNET_TOOLSET_TIMEOUT_SECONDS} seconds"
        logging.error(
            error_message,
            exc_info=True,
        )
        return error_message, None
    except RequestException as e:
        error_message = f"Failed to load {url}: {str(e)}"
        logging.warning(error_message, exc_info=True)
        return error_message, None

    if response:
        content = response.text
        try:
            content_type = response.headers["content-type"]
            if content_type:
                mime_type = content_type.split(";")[0]
        except Exception:
            logging.info(
                f"Failed to parse content type from headers {response.headers}"
            )

    return (content, mime_type)


def cleanup(soup: BeautifulSoup):
    """Remove all elements that are irrelevant to the textual representation of a web page.
    This includes images, extra data, even links as there is no intention to navigate from that page.
    """

    for selector in SELECTORS_TO_REMOVE:
        for element in soup.select(selector):
            element.decompose()

    for tag in soup.find_all(True):
        for attr in list(tag.attrs):  # type: ignore
            if attr != "href":
                tag.attrs.pop(attr, None)  # type: ignore

    return soup


def html_to_markdown(page_source: str):
    soup = BeautifulSoup(page_source, "html.parser")
    soup = cleanup(soup)
    page_source = str(soup)

    try:
        md = markdownify(page_source)
    except OSError as e:
        logging.error(
            f"There was an error in converting the HTML to markdown. Falling back to returning the raw HTML. Error: {str(e)}"
        )
        return page_source

    md = re.sub(r"</div>", "      ", md)
    md = re.sub(r"<div>", "     ", md)

    md = re.sub(r"\n\s*\n", "\n\n", md)

    return md


def looks_like_html(content):
    """
    Check if the content looks like HTML.
    """
    if isinstance(content, str):
        # Check for common HTML tags
        html_patterns = [r"<!DOCTYPE\s+html", r"<html", r"<head", r"<body"]
        return any(
            re.search(pattern, content, re.IGNORECASE) for pattern in html_patterns
        )
    return False


class FetchWebpage(Tool):
    toolset: "InternetToolset"

    def __init__(self, toolset: "InternetToolset"):
        super().__init__(
            name="fetch_webpage",
            description="Fetch a webpage. Use this to fetch runbooks if they are present before starting your investigation (if no other tool like confluence is more appropriate)",
            parameters={
                "url": ToolParameter(
                    description="The URL to fetch",
                    type="string",
                    required=True,
                ),
            },
            toolset=toolset,  # type: ignore
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        url: str = params["url"]

        additional_headers = (
            self.toolset.additional_headers if self.toolset.additional_headers else {}
        )
        content, mime_type = scrape(url, additional_headers)

        if not content:
            logging.error(f"Failed to retrieve content from {url}")
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Failed to retrieve content from {url}",
                params=params,
            )

        # Check if the content is HTML based on MIME type or content
        if (mime_type and mime_type.startswith("text/html")) or (
            mime_type is None and looks_like_html(content)
        ):
            content = html_to_markdown(content)

        return StructuredToolResult(
            status=StructuredToolResultStatus.SUCCESS,
            data=content,
            params=params,
        )

    def get_parameterized_one_liner(self, params) -> str:
        url: str = params.get("url", "<missing url>")
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Fetch Webpage {url}"


class InternetBaseToolset(Toolset):
    additional_headers: Dict[str, str] = {}

    def __init__(
        self,
        name: str,
        description: str,
        icon_url: str,
        tools: list[Tool],
        is_default: bool,
        tags: List[ToolsetTag],
        docs_url: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=icon_url,
            prerequisites=[
                CallablePrerequisite(callable=self.prerequisites_callable),
            ],
            tools=tools,
            tags=tags,
            is_default=is_default,
            docs_url=docs_url,
        )

    def prerequisites_callable(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        if not config:
            return True, ""
        self.additional_headers = config.get("additional_headers", {})
        return True, ""

    def get_example_config(self) -> Dict[str, Any]:
        return {
            "additional_headers": {"Authorization": "Basic <base_64_encoded_string>"}
        }


class InternetToolset(InternetBaseToolset):
    additional_headers: Dict[str, str] = {}

    def __init__(self):
        super().__init__(
            name="internet",
            description="Fetch webpages",
            icon_url="https://platform.robusta.dev/demos/internet-access.svg",
            tools=[
                FetchWebpage(self),
            ],
            docs_url="https://holmesgpt.dev/data-sources/builtin-toolsets/internet/",
            tags=[
                ToolsetTag.CORE,
            ],
            is_default=True,
        )
```

---
## Toolset: `connectivity_check`
- **类**: `ConnectivityCheckToolset`
- **模块**: `holmes.plugins.toolsets.connectivity_check`
- **enabled**: `True`
- **status**: `disabled`

### 已注册工具（0 个）
- （此 toolset 未注册任何工具，或加载失败）

### 相关源码文件（holmes 包内，1 个）

#### `plugins/toolsets/connectivity_check.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/plugins/toolsets/connectivity_check.py`
```python
import socket
from typing import Any, Dict, Literal

from holmes.core.tools import (
    StructuredToolResult,
    StructuredToolResultStatus,
    Tool,
    ToolInvokeContext,
    ToolParameter,
    Toolset,
    ToolsetTag,
)
from holmes.plugins.toolsets.utils import toolset_name_for_one_liner

BROWSER_LIKE_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

UserAgentMode = Literal["none", "browser"]


def tcp_check(host: str, port: int, timeout: float) -> Dict[str, Any]:
    if not (1 <= port <= 65535):
        return {
            "ok": False,
            "error": "invalid port (must be 1-65535)",
        }

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {
                "ok": True,
            }
    except (OSError, socket.timeout) as e:
        return {
            "ok": False,
            "error": str(e),
        }


class TcpCheckTool(Tool):
    toolset: "ConnectivityCheckToolset" = None  # type: ignore

    def __init__(self, toolset: "ConnectivityCheckToolset"):
        super().__init__(
            name="tcp_check",
            description="Check if a TCP socket can be opened to a host and port.",
            parameters={
                "host": ToolParameter(
                    description="The hostname or IP address to connect to",
                    type="string",
                    required=True,
                ),
                "port": ToolParameter(
                    description="The port to connect to",
                    type="integer",
                    required=True,
                ),
                "timeout": ToolParameter(
                    description="Timeout in seconds (default: 3.0)",
                    type="number",
                    required=False,
                ),
            },
        )
        self.toolset = toolset

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        host = params.get("host")
        port = params.get("port")
        if host is None:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                data={"error": "host parameter is required"},
                params=params,
            )
        if port is None:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                data={"error": "port parameter is required"},
                params=params,
            )

        result = tcp_check(
            host=host,
            port=int(port),
            timeout=float(params.get("timeout", 3.0)),
        )
        return StructuredToolResult(
            status=StructuredToolResultStatus.SUCCESS,
            data=result,
            params=params,
        )

    def get_parameterized_one_liner(self, params) -> str:
        host = params.get("host", "<missing host>")
        port = params.get("port", "<missing port>")
        return (
            f"{toolset_name_for_one_liner(self.toolset.name)}: "
            f"TCP check {host}:{port}"
        )


class ConnectivityCheckToolset(Toolset):
    def __init__(self):
        super().__init__(
            name="connectivity_check",
            description="Check TCP connectivity to endpoints",
            icon_url="https://platform.robusta.dev/demos/internet-access.svg",
            tools=[
                TcpCheckTool(self),
            ],
            tags=[
                ToolsetTag.CORE,
            ],
            is_default=True,
            enabled=True,
            docs_url="https://holmesgpt.dev/data-sources/builtin-toolsets/connectivity-check/",
        )

    def get_example_config(self) -> Dict[str, Any]:
        return {}
```

---
## Toolset: `bash`
- **类**: `BashExecutorToolset`
- **模块**: `holmes.plugins.toolsets.bash.bash_toolset`
- **enabled**: `True`
- **status**: `enabled`

### 已注册工具（2 个）
| tool | description | class | module |
|---|---|---|---|
| `run_bash_command` | Executes a given bash command and returns its standard output, standard error, and exit code.The command is executed via 'bash -c "<command>"'.Only some command… | `RunBashCommand` | `holmes.plugins.toolsets.bash.bash_toolset` |
| `kubectl_run_image` | Executes `kubectl run <name> --image=<image> ... -- <command>` return the result | `KubectlRunImageCommand` | `holmes.plugins.toolsets.bash.bash_toolset` |

### 工具输入参数（Schema）

#### `run_bash_command`
```json
{
  "command": {
    "description": "The bash command string to execute.",
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "timeout": {
    "description": "Optional timeout in seconds for the command execution. Defaults to 60s.",
    "type": "integer",
    "required": false,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

#### `kubectl_run_image`
```json
{
  "image": {
    "description": "The image to run",
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "command": {
    "description": "The command to execute on the deployed pod",
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  },
  "namespace": {
    "description": "The namespace in which to deploy the temporary pod",
    "type": "string",
    "required": false,
    "properties": null,
    "items": null,
    "enum": null
  },
  "timeout": {
    "description": "Optional timeout in seconds for the command execution. Defaults to 60s.",
    "type": "integer",
    "required": false,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

### 相关源码文件（holmes 包内，1 个）

#### `plugins/toolsets/bash/bash_toolset.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/plugins/toolsets/bash/bash_toolset.py`
```python
import argparse
import logging
import os
import random
import re
import string
from typing import Any, Dict, Optional

import sentry_sdk

from holmes.common.env_vars import (
    BASH_TOOL_UNSAFE_ALLOW_ALL,
)
from holmes.core.tools import (
    ApprovalRequirement,
    CallablePrerequisite,
    StructuredToolResult,
    StructuredToolResultStatus,
    Tool,
    ToolInvokeContext,
    ToolParameter,
    Toolset,
    ToolsetTag,
)
from holmes.plugins.toolsets.bash.common.bash import execute_bash_command
from holmes.plugins.toolsets.bash.common.config import BashExecutorConfig
from holmes.plugins.toolsets.bash.kubectl.constants import SAFE_NAMESPACE_PATTERN
from holmes.plugins.toolsets.bash.kubectl.kubectl_run import validate_image_and_commands
from holmes.plugins.toolsets.bash.parse_command import make_command_safe
from holmes.plugins.toolsets.utils import get_param_or_raise


class BaseBashExecutorToolset(Toolset):
    config: Optional[BashExecutorConfig] = None

    def get_example_config(self):
        example_config = BashExecutorConfig()
        return example_config.model_dump()


class BaseBashTool(Tool):
    toolset: BaseBashExecutorToolset


class KubectlRunImageCommand(BaseBashTool):
    def __init__(self, toolset: BaseBashExecutorToolset):
        super().__init__(
            name="kubectl_run_image",
            description=(
                "Executes `kubectl run <name> --image=<image> ... -- <command>` return the result"
            ),
            parameters={
                "image": ToolParameter(
                    description="The image to run",
                    type="string",
                    required=True,
                ),
                "command": ToolParameter(
                    description="The command to execute on the deployed pod",
                    type="string",
                    required=True,
                ),
                "namespace": ToolParameter(
                    description="The namespace in which to deploy the temporary pod",
                    type="string",
                    required=False,
                ),
                "timeout": ToolParameter(
                    description=(
                        "Optional timeout in seconds for the command execution. "
                        "Defaults to 60s."
                    ),
                    type="integer",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def _build_kubectl_command(self, params: dict, pod_name: str) -> str:
        namespace = params.get("namespace", "default")
        image = get_param_or_raise(params, "image")
        command_str = get_param_or_raise(params, "command")
        return f"kubectl run {pod_name} --image={image} --namespace={namespace} --rm --attach --restart=Never -i -- {command_str}"

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        timeout = params.get("timeout", 60)

        image = get_param_or_raise(params, "image")
        command_str = get_param_or_raise(params, "command")

        namespace = params.get("namespace")

        if namespace and not re.match(SAFE_NAMESPACE_PATTERN, namespace):
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Error: The namespace is invalid. Valid namespaces must match the following regexp: {SAFE_NAMESPACE_PATTERN}",
                params=params,
            )

        try:
            validate_image_and_commands(
                image=image, container_command=command_str, config=self.toolset.config
            )
        except ValueError as e:
            # Report unsafe kubectl run command attempt to Sentry
            sentry_sdk.capture_event(
                {
                    "message": f"Unsafe kubectl run command attempted: {image}",
                    "level": "warning",
                    "extra": {
                        "image": image,
                        "command": command_str,
                        "namespace": namespace,
                        "error": str(e),
                    },
                }
            )
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=str(e),
                params=params,
            )

        pod_name = (
            "holmesgpt-debug-pod-"
            + "".join(random.choices(string.ascii_letters, k=8)).lower()
        )
        full_kubectl_command = self._build_kubectl_command(params, pod_name)
        return execute_bash_command(
            cmd=full_kubectl_command, timeout=timeout, params=params
        )

    def get_parameterized_one_liner(self, params: Dict[str, Any]) -> str:
        return self._build_kubectl_command(params, "<pod_name>")


class RunBashCommand(BaseBashTool):
    def __init__(self, toolset: BaseBashExecutorToolset):
        super().__init__(
            name="run_bash_command",
            description=(
                "Executes a given bash command and returns its standard output, "
                "standard error, and exit code."
                "The command is executed via 'bash -c \"<command>\"'."
                "Only some commands are allowed."
            ),
            parameters={
                "command": ToolParameter(
                    description="The bash command string to execute.",
                    type="string",
                    required=True,
                ),
                "timeout": ToolParameter(
                    description=(
                        "Optional timeout in seconds for the command execution. "
                        "Defaults to 60s."
                    ),
                    type="integer",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def requires_approval(
        self, params: Dict[str, Any], context: ToolInvokeContext
    ) -> Optional[ApprovalRequirement]:
        """Check if bash command requires approval based on safety validation."""
        command_str = params.get("command", "")

        if not command_str:
            return None  # Let _invoke() handle validation error

        try:
            make_command_safe(command_str, self.toolset.config)
            return None  # Command passed safety check, no approval needed
        except (argparse.ArgumentError, ValueError) as e:
            # Report to Sentry for monitoring unsafe command attempts
            with sentry_sdk.configure_scope() as scope:
                scope.set_extra("command", command_str)
                scope.set_extra("error", str(e))
                scope.set_extra("unsafe_allow_all", BASH_TOOL_UNSAFE_ALLOW_ALL)
                sentry_sdk.capture_exception(e)

            if BASH_TOOL_UNSAFE_ALLOW_ALL:
                return None  # UNSAFE_ALLOW_ALL bypasses approval

            logging.info(f"Refusing LLM tool call {command_str}")
            return ApprovalRequirement(
                needs_approval=True,
                reason=f"Refusing to execute bash command. {str(e)}",
            )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        command_str = params.get("command")
        timeout = params.get("timeout", 60)

        if not command_str:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="The 'command' parameter is required and was not provided.",
                params=params,
            )

        if not isinstance(command_str, str):
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"The 'command' parameter must be a string, got {type(command_str).__name__}.",
                params=params,
            )

        if context.user_approved:
            command_to_execute = command_str
        else:
            try:
                command_to_execute = make_command_safe(command_str, self.toolset.config)
            except (argparse.ArgumentError, ValueError) as e:
                return StructuredToolResult(
                    status=StructuredToolResultStatus.ERROR,
                    error=f"Command failed safety validation: {e}",
                    params=params,
                )

        return execute_bash_command(
            cmd=command_to_execute, timeout=timeout, params=params
        )

    def get_parameterized_one_liner(self, params: Dict[str, Any]) -> str:
        command = params.get("command", "N/A")
        display_command = command[:200] + "..." if len(command) > 200 else command
        return display_command


class BashExecutorToolset(BaseBashExecutorToolset):
    def __init__(self):
        super().__init__(
            name="bash",
            enabled=False,
            description=(
                "Toolset for executing arbitrary bash commands on the system where Holmes is running. "
                "WARNING: This toolset provides powerful capabilities and should be "
                "enabled and used with extreme caution due to significant security risks. "
                "Ensure that only trusted users have access to this tool."
            ),
            docs_url="",  # TODO: Add relevant documentation URL
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Bash_Logo_Colored.svg/120px-Bash_Logo_Colored.svg.png",  # Example Bash icon
            prerequisites=[CallablePrerequisite(callable=self.prerequisites_callable)],
            tools=[RunBashCommand(self), KubectlRunImageCommand(self)],
            tags=[ToolsetTag.CORE],
            is_default=False,
        )

        self._reload_llm_instructions()

    def _reload_llm_instructions(self):
        template_file_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "bash_instructions.jinja2")
        )
        self._load_llm_instructions(jinja_template=f"file://{template_file_path}")

    def prerequisites_callable(self, config: dict[str, Any]) -> tuple[bool, str]:
        if config:
            self.config = BashExecutorConfig(**config)
        else:
            self.config = BashExecutorConfig()
        return True, ""
```

---
## Toolset: `runbook`
- **类**: `RunbookToolset`
- **模块**: `holmes.plugins.toolsets.runbook.runbook_fetcher`
- **enabled**: `True`
- **status**: `enabled`

### 已注册工具（1 个）
| tool | description | class | module |
|---|---|---|---|
| `fetch_runbook` | Get runbook content by runbook link. Use this to get troubleshooting steps for incidents | `RunbookFetcher` | `holmes.plugins.toolsets.runbook.runbook_fetcher` |

### 工具输入参数（Schema）

#### `fetch_runbook`
```json
{
  "runbook_id": {
    "description": "The runbook_id: either a UUID or a .md filename. Must be one of: \"networking/dns_troubleshooting_instructions.md\", \"upgrade/upgrade_troubleshooting_instructions.md\"",
    "type": "string",
    "required": true,
    "properties": null,
    "items": null,
    "enum": null
  }
}
```

### 相关源码文件（holmes 包内，1 个）

#### `plugins/toolsets/runbook/runbook_fetcher.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/plugins/toolsets/runbook/runbook_fetcher.py`
```python
import logging
import os
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from holmes.core.supabase_dal import SupabaseDal
from holmes.core.tools import (
    StructuredToolResult,
    StructuredToolResultStatus,
    Tool,
    ToolInvokeContext,
    ToolParameter,
    Toolset,
    ToolsetTag,
)
from holmes.plugins.runbooks import (
    DEFAULT_RUNBOOK_SEARCH_PATH,
    get_runbook_by_path,
    load_runbook_catalog,
)
from holmes.plugins.toolsets.utils import toolset_name_for_one_liner


class RunbookFetcher(Tool):
    toolset: "RunbookToolset"
    available_runbooks: List[str] = []
    additional_search_paths: Optional[List[str]] = None
    _dal: Optional[SupabaseDal] = None

    def __init__(
        self,
        toolset: "RunbookToolset",
        additional_search_paths: Optional[List[str]] = None,
        dal: Optional[SupabaseDal] = None,
        custom_catalog_paths: Optional[List[Union[str, Path]]] = None,
    ):
        catalog = load_runbook_catalog(
            dal=dal, custom_catalog_paths=custom_catalog_paths
        )
        available_runbooks = []
        if catalog:
            available_runbooks = catalog.list_available_runbooks()

        if additional_search_paths:
            for search_path in additional_search_paths:
                if not os.path.isdir(search_path):
                    continue

                for file in os.listdir(search_path):
                    if file.endswith(".md") and file not in available_runbooks:
                        available_runbooks.append(f"{file}")

        runbook_list = ", ".join([f'"{rb}"' for rb in available_runbooks])

        super().__init__(
            name="fetch_runbook",
            description="Get runbook content by runbook link. Use this to get troubleshooting steps for incidents",
            parameters={
                "runbook_id": ToolParameter(
                    description=f"The runbook_id: either a UUID or a .md filename. Must be one of: {runbook_list}",
                    type="string",
                    required=True,
                ),
            },
            toolset=toolset,  # type: ignore[call-arg]
            available_runbooks=available_runbooks,  # type: ignore[call-arg]
            additional_search_paths=additional_search_paths,  # type: ignore[call-arg]
        )
        self._dal = dal

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        runbook_id: str = params.get("runbook_id", "")
        is_md_file: bool = True if runbook_id.endswith(".md") else False

        # Validate link is not empty
        if not runbook_id or not runbook_id.strip():
            err_msg = (
                "Runbook link cannot be empty. Please provide a valid runbook path."
            )
            logging.error(err_msg)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=err_msg,
                params=params,
            )

        if is_md_file:
            return self._get_md_runbook(runbook_id, params)
        else:
            return self._get_robusta_runbook(runbook_id, params)

    def _get_robusta_runbook(self, link: str, params: dict) -> StructuredToolResult:
        if self._dal and self._dal.enabled:
            try:
                runbook_content = self._dal.get_runbook_content(link)
                if runbook_content:
                    return StructuredToolResult(
                        status=StructuredToolResultStatus.SUCCESS,
                        data=runbook_content.pretty(),
                        params=params,
                    )
                else:
                    err_msg = f"Runbook with UUID '{link}' not found in remote storage."
                    logging.error(err_msg)
                    return StructuredToolResult(
                        status=StructuredToolResultStatus.ERROR,
                        error=err_msg,
                        params=params,
                    )
            except Exception as e:
                err_msg = f"Failed to fetch runbook with UUID '{link}': {str(e)}"
                logging.error(err_msg)
                return StructuredToolResult(
                    status=StructuredToolResultStatus.ERROR,
                    error=err_msg,
                    params=params,
                )
        else:
            err_msg = "Runbook link appears to be a UUID, but no remote data access layer (dal) is enabled."
            logging.error(err_msg)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=err_msg,
                params=params,
            )

    def _get_md_runbook(self, link: str, params: dict) -> StructuredToolResult:
        search_paths = [DEFAULT_RUNBOOK_SEARCH_PATH]
        if self.additional_search_paths:
            search_paths.extend(self.additional_search_paths)
        # Validate link is in the available runbooks list OR is a valid path within allowed directories
        if link not in self.available_runbooks:
            # Check if the link would resolve to a valid path within allowed directories
            # This prevents path traversal attacks like ../../secret.md
            is_valid_path = False
            for search_path in search_paths:
                candidate_path = os.path.join(search_path, link)
                # Canonicalize both paths to resolve any .. or . components
                real_search_path = os.path.realpath(search_path)
                real_candidate_path = os.path.realpath(candidate_path)

                # Check if the resolved path is within the allowed directory
                if (
                    real_candidate_path.startswith(real_search_path + os.sep)
                    or real_candidate_path == real_search_path
                ):
                    if os.path.isfile(real_candidate_path):
                        is_valid_path = True
                        break

            if not is_valid_path:
                err_msg = f"Invalid runbook link '{link}'. Must be one of: {', '.join(self.available_runbooks) if self.available_runbooks else 'No runbooks available'}"
                logging.error(err_msg)
                return StructuredToolResult(
                    status=StructuredToolResultStatus.ERROR,
                    error=err_msg,
                    params=params,
                )

        runbook_path = get_runbook_by_path(link, search_paths)
        if runbook_path is None:
            err_msg = (
                f"Runbook '{link}' not found in any of the search paths: {search_paths}"
            )
            logging.error(err_msg)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=err_msg,
                params=params,
            )
        try:
            with open(runbook_path, "r") as file:
                content = file.read()
                wrapped_content = textwrap.dedent(f"""\
                    <runbook>
{textwrap.indent(content, " " * 20)}
                    </runbook>
                    Note: the above are DIRECTIONS not ACTUAL RESULTS. You now need to follow the steps outlined in the runbook yourself USING TOOLS.
                    Anything that looks like an actual result in the above <runbook> is just an EXAMPLE.
                    Now follow those steps and report back what you find.
                    You must follow them by CALLING TOOLS YOURSELF.
                    If you are missing tools, follow your general instructions on how to enable them as present in your system prompt.

                    Assuming the above runbook is relevant, you MUST start your response (after calling tools to investigate) with:
                    "I found a runbook named [runbook name/description] and used it to troubleshoot:"

                    Then list each step with ✅ for completed steps and ❌ for steps you couldn't complete.

                    <example>
                        I found a runbook named **Troubleshooting Erlang Issues** and used it to troubleshoot:

                        1. ✅ *Check BEAM VM memory usage* - 87% allocated (3.2GB used of 4GB limit)
                        2. ✅ *Review GC logs* - 15 full GC cycles in last 30 minutes, avg pause time 2.3s
                        3. ✅ *Verify Erlang application logs* - `** exception error: out of memory in process <0.139.0> called by gen_server:handle_msg/6`
                        4. ❌ *Could not analyze process mailbox sizes* - Observer tool not enabled in container. Enable remote shell or observer_cli for process introspection.
                        5. ✅ *Check pod memory limits* - container limit 4Gi, requests 2Gi
                        6. ✅ *Verify BEAM startup arguments* - `+S 4:4 +P 1048576`, no memory instrumentation flags enabled
                        7. ❌ *Could not retrieve APM traces* - Datadog traces toolset is disabled. You can enable it by following https://holmesgpt.dev/data-sources/builtin-toolsets/datadog/
                        8. ❌ *Could not query Erlang metrics* - Prometheus integration is not connected. Enable it via https://holmesgpt.dev/data-sources/builtin-toolsets/prometheus/
                        9. ✅ *Examine recent deployments* - app version 2.1.3 deployed 4 hours ago, coincides with memory spike
                        10. ❌ *Could not check Stripe API status* - No toolset for Stripe integration exists. To monitor Stripe or similar third-party APIs, add a [custom toolset](https://holmesgpt.dev/data-sources/custom-toolsets/) or use a [remote MCP server](https://holmesgpt.dev/data-sources/remote-mcp-servers/)

                        **Root cause:** Memory leak in `gen_server` logic introduced in v2.1.3. BEAM VM hitting memory limit, causing out-of-memory crashes.

                        **Fix:** Roll back to v2.1.2 or increase memory limit to 6GB as a temporary workaround.
                    </example>
                """)
                return StructuredToolResult(
                    status=StructuredToolResultStatus.SUCCESS,
                    data=wrapped_content,
                    params=params,
                )
        except Exception as e:
            err_msg = f"Failed to read runbook {runbook_path}: {str(e)}"
            logging.error(err_msg)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=err_msg,
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        path: str = params.get("runbook_id", "")
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Fetch Runbook {path}"


class RunbookToolset(Toolset):
    def __init__(
        self,
        dal: Optional[SupabaseDal],
        additional_search_paths: Optional[List[str]] = None,
    ):
        # Store additional search paths in config for RunbookFetcher to access
        config = {}
        if additional_search_paths:
            config["additional_search_paths"] = additional_search_paths

        # Compute custom catalog paths from additional search paths
        custom_catalog_paths = None
        if additional_search_paths:
            custom_catalog_paths = [
                os.path.join(search_path, "catalog.json")
                for search_path in additional_search_paths
                if os.path.isfile(os.path.join(search_path, "catalog.json"))
            ]

        super().__init__(
            name="runbook",
            description="Fetch runbooks",
            icon_url="https://platform.robusta.dev/demos/runbook.svg",
            tools=[
                RunbookFetcher(
                    self,
                    additional_search_paths,
                    dal,
                    cast(Optional[List[Union[str, Path]]], custom_catalog_paths),
                ),
            ],
            docs_url="https://holmesgpt.dev/data-sources/",
            tags=[
                ToolsetTag.CORE,
            ],
            is_default=True,
            config=config,
            enabled=True,
        )

    def get_example_config(self) -> Dict[str, Any]:
        return {}
```

---
## Toolset: `prometheus/metrics`
- **类**: `PrometheusToolset`
- **模块**: `holmes.plugins.toolsets.prometheus.prometheus`
- **enabled**: `True`
- **status**: `failed`
- **error**: `Failed to initialize using url=http://observability-prometheus.xnet.svc:9090/api/v1/query?query=up. Unexpected error: HTTPConnectionPool(host='observability-prometheus.xnet.svc', port=9090): Max retries exceeded with url: /api/v1/query?query=up (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7fa51a7d6110>: Failed to establish a new connection: [Errno -2] Name or servi`

### 已注册工具（0 个）
- （此 toolset 未注册任何工具，或加载失败）

### 相关源码文件（holmes 包内，1 个）

#### `plugins/toolsets/prometheus/prometheus.py`
- 绝对路径: `/usr/local/lib/python3.10/dist-packages/holmes/plugins/toolsets/prometheus/prometheus.py`
```python
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple, Type, Union
from urllib.parse import urljoin

import dateutil.parser
import requests  # type: ignore
from prometrix.auth import PrometheusAuthorization
from prometrix.connect.aws_connect import AWSPrometheusConnect
from prometrix.models.prometheus_config import (
    AzurePrometheusConfig as PrometrixAzureConfig,
)
from prometrix.models.prometheus_config import PrometheusConfig as BasePrometheusConfig
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from requests import RequestException
from requests.exceptions import SSLError  # type: ignore

from holmes.common.env_vars import IS_OPENSHIFT, MAX_GRAPH_POINTS
from holmes.common.openshift import load_openshift_token
from holmes.core.tools import (
    CallablePrerequisite,
    StructuredToolResult,
    StructuredToolResultStatus,
    Tool,
    ToolInvokeContext,
    ToolParameter,
    Toolset,
    ToolsetTag,
)
from holmes.core.tools_utils.token_counting import count_tool_response_tokens
from holmes.core.tools_utils.tool_context_window_limiter import get_pct_token_count
from holmes.plugins.toolsets.consts import STANDARD_END_DATETIME_TOOL_PARAM_DESCRIPTION
from holmes.plugins.toolsets.logging_utils.logging_api import (
    DEFAULT_GRAPH_TIME_SPAN_SECONDS,
)
from holmes.plugins.toolsets.prometheus.utils import parse_duration_to_seconds
from holmes.plugins.toolsets.service_discovery import PrometheusDiscovery
from holmes.plugins.toolsets.utils import (
    get_param_or_raise,
    process_timestamps_to_rfc3339,
    standard_start_datetime_tool_param_description,
    toolset_name_for_one_liner,
)
from holmes.utils.cache import TTLCache

PROMETHEUS_RULES_CACHE_KEY = "cached_prometheus_rules"
PROMETHEUS_METADATA_API_LIMIT = 100  # Default limit for Prometheus metadata APIs (series, labels, metadata) to prevent overwhelming responses
# Default timeout values for PromQL queries
DEFAULT_QUERY_TIMEOUT_SECONDS = 20
MAX_QUERY_TIMEOUT_SECONDS = 180
# Default timeout for metadata API calls (discovery endpoints)
DEFAULT_METADATA_TIMEOUT_SECONDS = 20
MAX_METADATA_TIMEOUT_SECONDS = 60
# Default time window for metadata APIs (in hours)
DEFAULT_METADATA_TIME_WINDOW_HRS = 1


def format_ssl_error_message(prometheus_url: str, error: SSLError) -> str:
    """Format a clear SSL error message with remediation steps."""
    return (
        f"SSL certificate verification failed when connecting to Prometheus at {prometheus_url}. "
        f"Error: {str(error)}. "
        f"To disable SSL verification, set 'verify_ssl: false' in your configuration. "
        f"For Helm deployments, add this to your values.yaml:\n"
        f"  toolsets:\n"
        f"    prometheus/metrics:\n"
        f"      config:\n"
        f"        verify_ssl: false"
    )


class PrometheusConfig(BaseModel):
    """Prometheus toolset configuration.

    Deprecated config names (still accepted but not in schema):
    - default_metadata_time_window_hrs -> discover_metrics_from_last_hours
    - default_query_timeout_seconds -> query_timeout_seconds_default
    - max_query_timeout_seconds -> query_timeout_seconds_hard_max
    - default_metadata_timeout_seconds -> metadata_timeout_seconds_default
    - max_metadata_timeout_seconds -> metadata_timeout_seconds_hard_max
    - metrics_labels_time_window_hrs -> discover_metrics_from_last_hours
    - prometheus_ssl_enabled -> verify_ssl
    - metrics_labels_cache_duration_hrs (no longer used)
    - fetch_labels_with_labels_api (no longer used)
    - fetch_metadata_with_series_api (no longer used)
    """

    model_config = ConfigDict(extra="allow")

    # URL is optional because it can be set with an env var
    prometheus_url: Optional[str] = None

    # Discovery API time window - only return metrics with data in the last N hours
    discover_metrics_from_last_hours: int = DEFAULT_METADATA_TIME_WINDOW_HRS

    # Query timeout configuration
    query_timeout_seconds_default: int = DEFAULT_QUERY_TIMEOUT_SECONDS
    query_timeout_seconds_hard_max: int = MAX_QUERY_TIMEOUT_SECONDS

    # Metadata API timeout configuration
    metadata_timeout_seconds_default: int = DEFAULT_METADATA_TIMEOUT_SECONDS
    metadata_timeout_seconds_hard_max: int = MAX_METADATA_TIMEOUT_SECONDS

    tool_calls_return_data: bool = True
    headers: Dict = Field(default_factory=dict)
    rules_cache_duration_seconds: Optional[int] = 1800  # 30 minutes
    additional_labels: Optional[Dict[str, str]] = None
    verify_ssl: bool = True

    # Custom limit to the max number of tokens that a query result can take to proactively
    #   prevent token limit issues. Expressed in % of the model's context window.
    # This limit only overrides the global limit for all tools  (TOOL_MAX_ALLOCATED_CONTEXT_WINDOW_PCT)
    #   if it is lower.
    query_response_size_limit_pct: Optional[int] = None

    @field_validator("prometheus_url")
    def ensure_trailing_slash(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.endswith("/"):
            return v + "/"
        return v

    @model_validator(mode="after")
    def validate_prom_config(self):
        # Handle deprecated config names passed as extra fields
        # These are accepted via extra="allow" but not defined in schema
        extra = self.model_extra or {}
        deprecated_with_replacement = []

        # Map of old names -> new names
        deprecated_mappings = {
            "default_metadata_time_window_hrs": "discover_metrics_from_last_hours",
            "default_query_timeout_seconds": "query_timeout_seconds_default",
            "max_query_timeout_seconds": "query_timeout_seconds_hard_max",
            "default_metadata_timeout_seconds": "metadata_timeout_seconds_default",
            "max_metadata_timeout_seconds": "metadata_timeout_seconds_hard_max",
            "metrics_labels_time_window_hrs": "discover_metrics_from_last_hours",
            "prometheus_ssl_enabled": "verify_ssl",
        }

        for old_name, new_name in deprecated_mappings.items():
            if old_name in extra:
                setattr(self, new_name, extra[old_name])
                deprecated_with_replacement.append(f"{old_name} -> {new_name}")

        if deprecated_with_replacement:
            logging.warning(
                f"Prometheus config uses deprecated names. Please update: "
                f"{', '.join(deprecated_with_replacement)}"
            )

        # Check for deprecated config values that no longer have any effect
        deprecated_no_effect = [
            name
            for name in [
                "metrics_labels_cache_duration_hrs",
                "fetch_labels_with_labels_api",
                "fetch_metadata_with_series_api",
            ]
            if name in extra
        ]

        if deprecated_no_effect:
            logging.warning(
                f"The following Prometheus config values are deprecated and have no effect: "
                f"{', '.join(deprecated_no_effect)}"
            )

        # If openshift is enabled, and the user didn't configure auth headers, we will try to load the token from the service account.
        if IS_OPENSHIFT:
            if self.headers.get("Authorization"):
                return self

            openshift_token = load_openshift_token()
            if openshift_token:
                logging.info("Using openshift token for prometheus toolset auth")
                self.headers["Authorization"] = f"Bearer {openshift_token}"

        return self

    def is_amp(self) -> bool:
        return False


class AMPConfig(PrometheusConfig):
    aws_access_key: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str
    aws_service_name: str = "aps"
    verify_ssl: bool = False
    assume_role_arn: Optional[str] = None

    # Refresh the AWS client (and its STS creds) every N seconds (default: 15 minutes)
    refresh_interval_seconds: int = 900

    _aws_client: Optional[AWSPrometheusConnect] = None
    _aws_client_created_at: float = 0.0

    def is_amp(self) -> bool:
        return True

    def _should_refresh_client(self) -> bool:
        if not self._aws_client:
            return True
        return (
            time.time() - self._aws_client_created_at
        ) >= self.refresh_interval_seconds

    def get_aws_client(self) -> Optional[AWSPrometheusConnect]:
        if not self._aws_client or self._should_refresh_client():
            try:
                base_config = BasePrometheusConfig(
                    url=self.prometheus_url,
                    disable_ssl=not self.verify_ssl,
                    additional_labels=self.additional_labels,
                )
                self._aws_client = AWSPrometheusConnect(
                    access_key=self.aws_access_key,
                    secret_key=self.aws_secret_access_key,
                    token=None,
                    region=self.aws_region,
                    service_name=self.aws_service_name,
                    assume_role_arn=self.assume_role_arn,
                    config=base_config,
                )
                self._aws_client_created_at = time.time()
            except Exception:
                logging.exception("Failed to create/refresh AWS client")
                return self._aws_client
        return self._aws_client


class AzurePrometheusConfig(PrometheusConfig):
    azure_resource: Optional[str] = None
    azure_metadata_endpoint: Optional[str] = None
    azure_token_endpoint: Optional[str] = None
    azure_use_managed_id: bool = False
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    verify_ssl: bool = True

    # Refresh the Azure bearer token every N seconds (default: 15 minutes)
    refresh_interval_seconds: int = 900

    _prometrix_config: Optional[PrometrixAzureConfig] = None
    _token_created_at: float = 0.0

    @staticmethod
    def _load_from_env_or_default(
        config_value: Optional[str], env_var: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Load value from config, environment variable, or use default."""
        if config_value:
            return config_value
        return os.environ.get(env_var, default)

    def __init__(self, **data):
        super().__init__(**data)
        # Load from environment variables if not provided in config
        self.azure_client_id = self._load_from_env_or_default(
            self.azure_client_id, "AZURE_CLIENT_ID"
        )
        self.azure_tenant_id = self._load_from_env_or_default(
            self.azure_tenant_id, "AZURE_TENANT_ID"
        )
        self.azure_client_secret = self._load_from_env_or_default(
            self.azure_client_secret, "AZURE_CLIENT_SECRET"
        )

        # Set defaults from environment if not provided
        self.azure_resource = self._load_from_env_or_default(
            self.azure_resource,
            "AZURE_RESOURCE",
            "https://prometheus.monitor.azure.com",
        )
        # from https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-to-use-vm-token
        self.azure_metadata_endpoint = self._load_from_env_or_default(
            self.azure_metadata_endpoint,
            "AZURE_METADATA_ENDPOINT",
            "http://169.254.169.254/metadata/identity/oauth2/token",
        )
        self.azure_token_endpoint = self._load_from_env_or_default(
            self.azure_token_endpoint, "AZURE_TOKEN_ENDPOINT"
        )
        if not self.azure_token_endpoint and self.azure_tenant_id:
            self.azure_token_endpoint = (
                f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/token"
            )

        # Check if managed identity should be used
        if not self.azure_use_managed_id:
            self.azure_use_managed_id = os.environ.get(
                "AZURE_USE_MANAGED_ID", "false"
            ).lower() in ("true", "1")

        # Convert None to empty string for prometrix compatibility (prometrix checks != "")
        azure_client_id = self.azure_client_id or ""
        azure_tenant_id = self.azure_tenant_id or ""
        azure_client_secret = self.azure_client_secret or ""
        azure_resource = self.azure_resource or ""
        azure_metadata_endpoint = self.azure_metadata_endpoint or ""
        azure_token_endpoint = self.azure_token_endpoint or ""

        # Create prometrix Azure config
        self._prometrix_config = PrometrixAzureConfig(
            url=self.prometheus_url,
            azure_resource=azure_resource,
            azure_metadata_endpoint=azure_metadata_endpoint,
            azure_token_endpoint=azure_token_endpoint,
            azure_use_managed_id=self.azure_use_managed_id,
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
            azure_tenant_id=azure_tenant_id,
            disable_ssl=not self.verify_ssl,
            additional_labels=self.additional_labels,
        )
        # Ensure promtrix gets a real bool (not string) for managed identity
        # fixing internal prometrix config issue
        object.__setattr__(
            self._prometrix_config,
            "azure_use_managed_id",
            bool(self.azure_use_managed_id),
        )

        PrometheusAuthorization.azure_authorization(self._prometrix_config)

    @staticmethod
    def is_azure_config(config: dict[str, Any]) -> bool:
        """Check if config dict or environment variables indicate Azure Prometheus config."""
        # Check for explicit Azure fields in config
        if (
            "azure_client_id" in config
            or "azure_tenant_id" in config
            or "azure_use_managed_id" in config
        ):
            return True

        # Check for Azure environment variables
        if os.environ.get("AZURE_CLIENT_ID") or os.environ.get("AZURE_TENANT_ID"):
            return True

        return False

    def is_amp(self) -> bool:
        return False

    def _should_refresh_token(self) -> bool:
        if not PrometheusAuthorization.bearer_token:
            return True
        return (time.time() - self._token_created_at) >= self.refresh_interval_seconds

    def request_new_token(self) -> bool:
        """Request a new Azure access token using prometrix."""
        success = PrometheusAuthorization.request_new_token(self._prometrix_config)
        if success:
            self._token_created_at = time.time()
        return success

    def get_authorization_headers(self) -> Dict[str, str]:
        # Request new token if needed
        if self._should_refresh_token():
            if not self.request_new_token():
                logging.error("Failed to request new Azure access token")
                return {}
            self._token_created_at = time.time()

        headers = PrometheusAuthorization.get_authorization_headers(
            self._prometrix_config
        )
        if not headers.get("Authorization"):
            logging.warning("No authorization header generated for Azure Prometheus")
        return headers


class BasePrometheusTool(Tool):
    toolset: "PrometheusToolset"


def do_request(
    config,  # PrometheusConfig | AMPConfig | AzurePrometheusConfig
    url: str,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    timeout: int = 60,
    verify: Optional[bool] = None,
    headers: Optional[Dict] = None,
    method: str = "GET",
) -> requests.Response:
    """
    Route a request through either:
      - AWSPrometheusConnect (SigV4) when config is AMPConfig
      - Azure bearer token auth when config is AzurePrometheusConfig
      - plain requests otherwise

    method defaults to GET so callers can omit it for reads.
    """
    if verify is None:
        verify = config.verify_ssl
    if headers is None:
        headers = config.headers or {}

    if isinstance(config, AMPConfig):
        client = config.get_aws_client()  # cached AWSPrometheusConnect
        # Note: timeout parameter is not supported by prometrix's signed_request
        # AWS/AMP requests will not respect the timeout setting
        return client.signed_request(  # type: ignore
            method=method,
            url=url,
            data=data,
            params=params,
            verify=verify,
            headers=headers,
        )

    if isinstance(config, AzurePrometheusConfig):
        # Merge Azure authorization headers with provided headers
        azure_headers = config.get_authorization_headers()
        headers = {**azure_headers, **headers}
        return requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            timeout=timeout,
            verify=verify,
        )

    # Non-AMP, Non-Azure: plain HTTP
    return requests.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        data=data,
        timeout=timeout,
        verify=verify,
    )


def result_has_data(result: Dict) -> bool:
    data = result.get("data", {})
    if len(data.get("result", [])) > 0:
        return True
    return False


def adjust_step_for_max_points(
    start_timestamp: str,
    end_timestamp: str,
    step: Optional[float] = None,
    max_points_override: Optional[float] = None,
) -> float:
    """
    Adjusts the step parameter to ensure the number of data points doesn't exceed max_points.

    Args:
        start_timestamp: RFC3339 formatted start time
        end_timestamp: RFC3339 formatted end time
        step: The requested step duration in seconds (None for auto-calculation)
        max_points_override: Optional override for max points (must be <= MAX_GRAPH_POINTS)

    Returns:
        Adjusted step value in seconds that ensures points <= max_points
    """
    # Use override if provided and valid, otherwise use default
    max_points = MAX_GRAPH_POINTS
    if max_points_override is not None:
        if max_points_override > MAX_GRAPH_POINTS:
            logging.warning(
                f"max_points override ({max_points_override}) exceeds system limit ({MAX_GRAPH_POINTS}), using {MAX_GRAPH_POINTS}"
            )
            max_points = MAX_GRAPH_POINTS
        elif max_points_override < 1:
            logging.warning(
                f"max_points override ({max_points_override}) is invalid, using default {MAX_GRAPH_POINTS}"
            )
            max_points = MAX_GRAPH_POINTS
        else:
            max_points = max_points_override
            logging.debug(f"Using max_points override: {max_points}")

    start_dt = dateutil.parser.parse(start_timestamp)
    end_dt = dateutil.parser.parse(end_timestamp)

    time_range_seconds = (end_dt - start_dt).total_seconds()

    # If no step provided, calculate a reasonable default
    # Aim for ~60 data points across the time range (1 per minute for hourly, etc)
    if step is None:
        step = max(1, time_range_seconds / 60)
        logging.debug(
            f"No step provided, defaulting to {step}s for {time_range_seconds}s range"
        )

    current_points = time_range_seconds / step

    # If current points exceed max, adjust the step
    if current_points > max_points:
        adjusted_step = time_range_seconds / max_points
        logging.info(
            f"Adjusting step from {step}s to {adjusted_step}s to limit points from {current_points:.0f} to {max_points}"
        )
        return adjusted_step

    return step


def add_prometheus_auth(prometheus_auth_header: Optional[str]) -> Dict[str, Any]:
    results = {}
    if prometheus_auth_header:
        results["Authorization"] = prometheus_auth_header
    return results


def create_data_summary_for_large_result(
    result_data: Dict, query: str, data_size_tokens: int, is_range_query: bool = False
) -> Dict[str, Any]:
    """
    Create a summary for large Prometheus results instead of returning full data.

    Args:
        result_data: The Prometheus data result
        query: The original PromQL query
        data_size_tokens: Size of the data in tokens
        is_range_query: Whether this is a range query (vs instant query)

    Returns:
        Dictionary with summary information and suggestions
    """
    if is_range_query:
        series_list = result_data.get("result", [])
        num_items = len(series_list)

        # Calculate exact total data points across all series
        total_points = 0
        for series in series_list:  # Iterate through ALL series for exact count
            points = len(series.get("values", []))
            total_points += points

        # Analyze label keys and their cardinality
        label_cardinality: Dict[str, set] = {}
        for series in series_list:
            metric = series.get("metric", {})
            for label_key, label_value in metric.items():
                if label_key not in label_cardinality:
                    label_cardinality[label_key] = set()
                label_cardinality[label_key].add(label_value)

        # Convert sets to counts for the summary
        label_summary = {
            label: len(values) for label, values in label_cardinality.items()
        }
        # Sort by cardinality (highest first) for better insights
        label_summary = dict(
            sorted(label_summary.items(), key=lambda x: x[1], reverse=True)
        )

        return {
            "message": f"Data too large to return ({data_size_tokens:,} tokens). Query returned {num_items} time series with {total_points:,} total data points.",
            "series_count": num_items,
            "total_data_points": total_points,
            "data_size_tokens": data_size_tokens,
            "label_cardinality": label_summary,
            "suggestion": f'Consider using topk({min(5, num_items)}, {query}) to limit results to the top {min(5, num_items)} series. To also capture remaining data as \'other\': topk({min(5, num_items)}, {query}) or label_replace((sum({query}) - sum(topk({min(5, num_items)}, {query}))), "pod", "other", "", "")',
        }
    else:
        # Instant query
        result_type = result_data.get("resultType", "")
        result_list = result_data.get("result", [])
        num_items = len(result_list)

        # Analyze label keys and their cardinality
        instant_label_cardinality: Dict[str, set] = {}
        for item in result_list:
            if isinstance(item, dict):
                metric = item.get("metric", {})
                for label_key, label_value in metric.items():
                    if label_key not in instant_label_cardinality:
                        instant_label_cardinality[label_key] = set()
                    instant_label_cardinality[label_key].add(label_value)

        # Convert sets to counts for the summary
        label_summary = {
            label: len(values) for label, values in instant_label_cardinality.items()
        }
        # Sort by cardinality (highest first) for better insights
        label_summary = dict(
            sorted(label_summary.items(), key=lambda x: x[1], reverse=True)
        )

        return {
            "message": f"Data too large to return ({data_size_tokens:,} tokens). Query returned {num_items} results.",
            "result_count": num_items,
            "result_type": result_type,
            "data_size_tokens": data_size_tokens,
            "label_cardinality": label_summary,
            "suggestion": f'Consider using topk({min(5, num_items)}, {query}) to limit results. To also capture remaining data as \'other\': topk({min(5, num_items)}, {query}) or label_replace((sum({query}) - sum(topk({min(5, num_items)}, {query}))), "instance", "other", "", "")',
        }


class MetricsBasedResponse(BaseModel):
    status: str
    error_message: Optional[str] = None
    data: Optional[str] = None
    tool_name: str
    description: str
    query: str
    start: Optional[str] = None
    end: Optional[str] = None
    step: Optional[float] = None
    output_type: Optional[str] = None
    data_summary: Optional[dict[str, Any]] = None


def create_structured_tool_result(
    params: dict, response: MetricsBasedResponse
) -> StructuredToolResult:
    status = StructuredToolResultStatus.SUCCESS
    error = None
    if response.error_message or response.status.lower() in ("failed", "error"):
        status = StructuredToolResultStatus.ERROR
        error = (
            response.error_message
            if response.error_message
            else "Unknown Prometheus error"
        )
    elif not response.data:
        status = StructuredToolResultStatus.NO_DATA

    return StructuredToolResult(
        status=status,
        data=response,
        params=params,
        error=error,
    )


class ListPrometheusRules(BasePrometheusTool):
    def __init__(self, toolset: "PrometheusToolset"):
        super().__init__(
            name="list_prometheus_rules",
            description="List all defined Prometheus rules (api/v1/rules). Will show the Prometheus rules description, expression and annotations",
            parameters={},
            toolset=toolset,
        )
        self._cache = None

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        if not self.toolset.config or not self.toolset.config.prometheus_url:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Prometheus is not configured. Prometheus URL is missing",
                params=params,
            )
        if self.toolset.config.is_amp():
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Tool not supported in AMP",
                params=params,
            )
        if not self._cache and self.toolset.config.rules_cache_duration_seconds:
            self._cache = TTLCache(self.toolset.config.rules_cache_duration_seconds)  # type: ignore
        try:
            if self._cache:
                cached_rules = self._cache.get(PROMETHEUS_RULES_CACHE_KEY)
                if cached_rules:
                    logging.debug("rules returned from cache")

                    return StructuredToolResult(
                        status=StructuredToolResultStatus.SUCCESS,
                        data=cached_rules,
                        params=params,
                    )

            prometheus_url = self.toolset.config.prometheus_url

            rules_url = urljoin(prometheus_url, "api/v1/rules")

            rules_response = do_request(
                config=self.toolset.config,
                url=rules_url,
                params=params,
                timeout=40,
                verify=self.toolset.config.verify_ssl,
                headers=self.toolset.config.headers,
                method="GET",
            )
            rules_response.raise_for_status()
            data = rules_response.json()["data"]

            if self._cache:
                self._cache.set(PROMETHEUS_RULES_CACHE_KEY, data)
            return StructuredToolResult(
                status=StructuredToolResultStatus.SUCCESS,
                data=data,
                params=params,
            )
        except requests.Timeout:
            logging.warning("Timeout while fetching prometheus rules", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Request timed out while fetching rules",
                params=params,
            )
        except SSLError as e:
            logging.warning("SSL error while fetching prometheus rules", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=format_ssl_error_message(self.toolset.config.prometheus_url, e),
                params=params,
            )
        except RequestException as e:
            logging.warning("Failed to fetch prometheus rules", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Network error while fetching rules: {str(e)}",
                params=params,
            )
        except Exception as e:
            logging.warning("Failed to process prometheus rules", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Fetch Rules"


class GetMetricNames(BasePrometheusTool):
    """Thin wrapper around /api/v1/label/__name__/values - the fastest way to discover metric names"""

    def __init__(self, toolset: "PrometheusToolset"):
        super().__init__(
            name="get_metric_names",
            description=(
                "Get list of metric names using /api/v1/label/__name__/values. "
                "FASTEST method for metric discovery when you need to explore available metrics. "
                f"Returns up to {PROMETHEUS_METADATA_API_LIMIT} unique metric names (limit={PROMETHEUS_METADATA_API_LIMIT}). If {PROMETHEUS_METADATA_API_LIMIT} results returned, more may exist - use a more specific filter. "
                f"ALWAYS use match[] parameter to filter metrics - without it you'll get random {PROMETHEUS_METADATA_API_LIMIT} metrics which is rarely useful. "
                "Note: Does not return metric metadata (type, description, labels). "
                "By default returns metrics active in the last 1 hour (configurable via default_metadata_time_window_hrs)."
            ),
            parameters={
                "match": ToolParameter(
                    description=(
                        "REQUIRED: PromQL selector to filter metrics. Use regex OR (|) to check multiple patterns in one call - much faster than multiple calls! Examples: "
                        "'{__name__=~\"node_cpu.*|node_memory.*|node_disk.*\"}' for all node resource metrics, "
                        "'{__name__=~\"container_cpu.*|container_memory.*|container_network.*\"}' for all container metrics, "
                        "'{__name__=~\"kube_pod.*|kube_deployment.*|kube_service.*\"}' for multiple Kubernetes object metrics, "
                        "'{__name__=~\".*cpu.*|.*memory.*|.*disk.*\"}' for all resource metrics, "
                        "'{namespace=~\"kube-system|default|monitoring\"}' for metrics from multiple namespaces, "
                        "'{job=~\"prometheus|node-exporter|kube-state-metrics\"}' for metrics from multiple jobs."
                    ),
                    type="string",
                    required=True,
                ),
                "start": ToolParameter(
                    description="Start timestamp (RFC3339 or Unix). Default: 1 hour ago",
                    type="string",
                    required=False,
                ),
                "end": ToolParameter(
                    description="End timestamp (RFC3339 or Unix). Default: now",
                    type="string",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        if not self.toolset.config or not self.toolset.config.prometheus_url:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Prometheus is not configured. Prometheus URL is missing",
                params=params,
            )
        try:
            match_param = params.get("match")
            if not match_param:
                return StructuredToolResult(
                    status=StructuredToolResultStatus.ERROR,
                    error="Match parameter is required to filter metrics",
                    params=params,
                )

            url = urljoin(
                self.toolset.config.prometheus_url, "api/v1/label/__name__/values"
            )
            query_params = {
                "limit": str(PROMETHEUS_METADATA_API_LIMIT),
                "match[]": match_param,
            }

            # Add time parameters - use provided values or defaults
            if params.get("end"):
                query_params["end"] = params["end"]
            else:
                query_params["end"] = str(int(time.time()))

            if params.get("start"):
                query_params["start"] = params["start"]
            elif self.toolset.config.discover_metrics_from_last_hours:
                # Use default time window
                query_params["start"] = str(
                    int(time.time())
                    - (self.toolset.config.discover_metrics_from_last_hours * 3600)
                )

            response = do_request(
                config=self.toolset.config,
                url=url,
                params=query_params,
                timeout=self.toolset.config.metadata_timeout_seconds_default,
                verify=self.toolset.config.verify_ssl,
                headers=self.toolset.config.headers,
                method="GET",
            )
            response.raise_for_status()
            data = response.json()

            # Check if results were truncated
            if (
                "data" in data
                and isinstance(data["data"], list)
                and len(data["data"]) == PROMETHEUS_METADATA_API_LIMIT
            ):
                data["_truncated"] = True
                data["_message"] = (
                    f"Results truncated at limit={PROMETHEUS_METADATA_API_LIMIT}. Use a more specific match filter to see additional metrics."
                )

            return StructuredToolResult(
                status=StructuredToolResultStatus.SUCCESS,
                data=data,
                params=params,
            )
        except Exception as e:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=str(e),
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Get Metric Names"


class GetLabelValues(BasePrometheusTool):
    """Get values for a specific label across all metrics"""

    def __init__(self, toolset: "PrometheusToolset"):
        super().__init__(
            name="get_label_values",
            description=(
                "Get all values for a specific label using /api/v1/label/{label}/values. "
                "Use this to discover pods, namespaces, jobs, instances, etc. "
                f"Returns up to {PROMETHEUS_METADATA_API_LIMIT} unique values (limit={PROMETHEUS_METADATA_API_LIMIT}). If {PROMETHEUS_METADATA_API_LIMIT} results returned, more may exist - use match[] to filter. "
                "Supports optional match[] parameter to filter. "
                "By default returns values from metrics active in the last 1 hour (configurable via default_metadata_time_window_hrs)."
            ),
            parameters={
                "label": ToolParameter(
                    description="Label name to get values for (e.g., 'pod', 'namespace', 'job', 'instance')",
                    type="string",
                    required=True,
                ),
                "match": ToolParameter(
                    description=(
                        "Optional PromQL selector to filter (e.g., '{__name__=~\"kube.*\"}', "
                        "'{namespace=\"default\"}')."
                    ),
                    type="string",
                    required=False,
                ),
                "start": ToolParameter(
                    description="Start timestamp (RFC3339 or Unix). Default: 1 hour ago",
                    type="string",
                    required=False,
                ),
                "end": ToolParameter(
                    description="End timestamp (RFC3339 or Unix). Default: now",
                    type="string",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        if not self.toolset.config or not self.toolset.config.prometheus_url:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Prometheus is not configured. Prometheus URL is missing",
                params=params,
            )
        try:
            label = params.get("label")
            if not label:
                return StructuredToolResult(
                    status=StructuredToolResultStatus.ERROR,
                    error="Label parameter is required",
                    params=params,
                )

            url = urljoin(
                self.toolset.config.prometheus_url, f"api/v1/label/{label}/values"
            )
            query_params = {"limit": str(PROMETHEUS_METADATA_API_LIMIT)}
            if params.get("match"):
                query_params["match[]"] = params["match"]

            # Add time parameters - use provided values or defaults
            if params.get("end"):
                query_params["end"] = params["end"]
            else:
                query_params["end"] = str(int(time.time()))

            if params.get("start"):
                query_params["start"] = params["start"]
            elif self.toolset.config.discover_metrics_from_last_hours:
                # Use default time window
                query_params["start"] = str(
                    int(time.time())
                    - (self.toolset.config.discover_metrics_from_last_hours * 3600)
                )

            response = do_request(
                config=self.toolset.config,
                url=url,
                params=query_params,
                timeout=self.toolset.config.metadata_timeout_seconds_default,
                verify=self.toolset.config.verify_ssl,
                headers=self.toolset.config.headers,
                method="GET",
            )
            response.raise_for_status()
            data = response.json()

            # Check if results were truncated
            if (
                "data" in data
                and isinstance(data["data"], list)
                and len(data["data"]) == PROMETHEUS_METADATA_API_LIMIT
            ):
                data["_truncated"] = True
                data["_message"] = (
                    f"Results truncated at limit={PROMETHEUS_METADATA_API_LIMIT}. Use match[] parameter to filter label '{label}' values."
                )

            return StructuredToolResult(
                status=StructuredToolResultStatus.SUCCESS,
                data=data,
                params=params,
            )
        except Exception as e:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=str(e),
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        label = params.get("label", "")
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Get {label} Values"


class GetAllLabels(BasePrometheusTool):
    """Get all label names that exist in Prometheus"""

    def __init__(self, toolset: "PrometheusToolset"):
        super().__init__(
            name="get_all_labels",
            description=(
                "Get list of all label names using /api/v1/labels. "
                "Use this to discover what labels are available across all metrics. "
                f"Returns up to {PROMETHEUS_METADATA_API_LIMIT} label names (limit={PROMETHEUS_METADATA_API_LIMIT}). If {PROMETHEUS_METADATA_API_LIMIT} results returned, more may exist - use match[] to filter. "
                "Supports optional match[] parameter to filter. "
                "By default returns labels from metrics active in the last 1 hour (configurable via default_metadata_time_window_hrs)."
            ),
            parameters={
                "match": ToolParameter(
                    description=(
                        "Optional PromQL selector to filter (e.g., '{__name__=~\"kube.*\"}', "
                        "'{job=\"prometheus\"}')."
                    ),
                    type="string",
                    required=False,
                ),
                "start": ToolParameter(
                    description="Start timestamp (RFC3339 or Unix). Default: 1 hour ago",
                    type="string",
                    required=False,
                ),
                "end": ToolParameter(
                    description="End timestamp (RFC3339 or Unix). Default: now",
                    type="string",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        if not self.toolset.config or not self.toolset.config.prometheus_url:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Prometheus is not configured. Prometheus URL is missing",
                params=params,
            )
        try:
            url = urljoin(self.toolset.config.prometheus_url, "api/v1/labels")
            query_params = {"limit": str(PROMETHEUS_METADATA_API_LIMIT)}
            if params.get("match"):
                query_params["match[]"] = params["match"]

            # Add time parameters - use provided values or defaults
            if params.get("end"):
                query_params["end"] = params["end"]
            else:
                query_params["end"] = str(int(time.time()))

            if params.get("start"):
                query_params["start"] = params["start"]
            elif self.toolset.config.discover_metrics_from_last_hours:
                # Use default time window
                query_params["start"] = str(
                    int(time.time())
                    - (self.toolset.config.discover_metrics_from_last_hours * 3600)
                )

            response = do_request(
                config=self.toolset.config,
                url=url,
                params=query_params,
                timeout=self.toolset.config.metadata_timeout_seconds_default,
                verify=self.toolset.config.verify_ssl,
                headers=self.toolset.config.headers,
                method="GET",
            )
            response.raise_for_status()
            data = response.json()

            # Check if results were truncated
            if (
                "data" in data
                and isinstance(data["data"], list)
                and len(data["data"]) == PROMETHEUS_METADATA_API_LIMIT
            ):
                data["_truncated"] = True
                data["_message"] = (
                    f"Results truncated at limit={PROMETHEUS_METADATA_API_LIMIT}. Use match[] parameter to filter labels."
                )

            return StructuredToolResult(
                status=StructuredToolResultStatus.SUCCESS,
                data=data,
                params=params,
            )
        except Exception as e:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=str(e),
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Get All Labels"


class GetSeries(BasePrometheusTool):
    """Get time series matching a selector"""

    def __init__(self, toolset: "PrometheusToolset"):
        super().__init__(
            name="get_series",
            description=(
                "Get time series using /api/v1/series. "
                "Returns label sets for all time series matching the selector. "
                "SLOWER than other discovery methods - use only when you need full label sets. "
                f"Returns up to {PROMETHEUS_METADATA_API_LIMIT} series (limit={PROMETHEUS_METADATA_API_LIMIT}). If {PROMETHEUS_METADATA_API_LIMIT} results returned, more series exist - use more specific selector. "
                "Requires match[] parameter with PromQL selector. "
                "By default returns series active in the last 1 hour (configurable via default_metadata_time_window_hrs)."
            ),
            parameters={
                "match": ToolParameter(
                    description=(
                        "PromQL selector to match series (e.g., 'up', 'node_cpu_seconds_total', "
                        "'{__name__=~\"node.*\"}', '{job=\"prometheus\"}', "
                        '\'{__name__="up",job="prometheus"}\').'
                    ),
                    type="string",
                    required=True,
                ),
                "start": ToolParameter(
                    description="Start timestamp (RFC3339 or Unix). Default: 1 hour ago",
                    type="string",
                    required=False,
                ),
                "end": ToolParameter(
                    description="End timestamp (RFC3339 or Unix). Default: now",
                    type="string",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        if not self.toolset.config or not self.toolset.config.prometheus_url:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Prometheus is not configured. Prometheus URL is missing",
                params=params,
            )
        try:
            match = params.get("match")
            if not match:
                return StructuredToolResult(
                    status=StructuredToolResultStatus.ERROR,
                    error="Match parameter is required",
                    params=params,
                )

            url = urljoin(self.toolset.config.prometheus_url, "api/v1/series")
            query_params = {
                "match[]": match,
                "limit": str(PROMETHEUS_METADATA_API_LIMIT),
            }

            # Add time parameters - use provided values or defaults
            if params.get("end"):
                query_params["end"] = params["end"]
            else:
                query_params["end"] = str(int(time.time()))

            if params.get("start"):
                query_params["start"] = params["start"]
            elif self.toolset.config.discover_metrics_from_last_hours:
                # Use default time window
                query_params["start"] = str(
                    int(time.time())
                    - (self.toolset.config.discover_metrics_from_last_hours * 3600)
                )

            response = do_request(
                config=self.toolset.config,
                url=url,
                params=query_params,
                timeout=self.toolset.config.metadata_timeout_seconds_default,
                verify=self.toolset.config.verify_ssl,
                headers=self.toolset.config.headers,
                method="GET",
            )
            response.raise_for_status()
            data = response.json()

            # Check if results were truncated
            if (
                "data" in data
                and isinstance(data["data"], list)
                and len(data["data"]) == PROMETHEUS_METADATA_API_LIMIT
            ):
                data["_truncated"] = True
                data["_message"] = (
                    f"Results truncated at limit={PROMETHEUS_METADATA_API_LIMIT}. Use a more specific match selector to see additional series."
                )

            return StructuredToolResult(
                status=StructuredToolResultStatus.SUCCESS,
                data=data,
                params=params,
            )
        except Exception as e:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=str(e),
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Get Series"


class GetMetricMetadata(BasePrometheusTool):
    """Get metadata (type, description, unit) for metrics"""

    def __init__(self, toolset: "PrometheusToolset"):
        super().__init__(
            name="get_metric_metadata",
            description=(
                "Get metric metadata using /api/v1/metadata. "
                "Returns type, help text, and unit for metrics. "
                "Use after discovering metric names to get their descriptions. "
                f"Returns up to {PROMETHEUS_METADATA_API_LIMIT} metrics (limit={PROMETHEUS_METADATA_API_LIMIT}). If {PROMETHEUS_METADATA_API_LIMIT} results returned, more may exist - filter by specific metric name. "
                "Supports optional metric name filter."
            ),
            parameters={
                "metric": ToolParameter(
                    description=(
                        "Optional metric name to filter (e.g., 'up', 'node_cpu_seconds_total'). "
                        "If not provided, returns metadata for all metrics."
                    ),
                    type="string",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        if not self.toolset.config or not self.toolset.config.prometheus_url:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Prometheus is not configured. Prometheus URL is missing",
                params=params,
            )
        try:
            url = urljoin(self.toolset.config.prometheus_url, "api/v1/metadata")
            query_params = {"limit": str(PROMETHEUS_METADATA_API_LIMIT)}

            if params.get("metric"):
                query_params["metric"] = params["metric"]

            response = do_request(
                config=self.toolset.config,
                url=url,
                params=query_params,
                timeout=self.toolset.config.metadata_timeout_seconds_default,
                verify=self.toolset.config.verify_ssl,
                headers=self.toolset.config.headers,
                method="GET",
            )
            response.raise_for_status()
            data = response.json()

            # Check if results were truncated (metadata endpoint returns a dict, not a list)
            if (
                "data" in data
                and isinstance(data["data"], dict)
                and len(data["data"]) == PROMETHEUS_METADATA_API_LIMIT
            ):
                data["_truncated"] = True
                data["_message"] = (
                    f"Results truncated at limit={PROMETHEUS_METADATA_API_LIMIT}. Use metric parameter to filter by specific metric name."
                )

            return StructuredToolResult(
                status=StructuredToolResultStatus.SUCCESS,
                data=data,
                params=params,
            )
        except Exception as e:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=str(e),
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        metric = params.get("metric", "all")
        return (
            f"{toolset_name_for_one_liner(self.toolset.name)}: Get Metadata ({metric})"
        )


class ExecuteInstantQuery(BasePrometheusTool):
    def __init__(self, toolset: "PrometheusToolset"):
        super().__init__(
            name="execute_prometheus_instant_query",
            description=(
                f"Execute an instant PromQL query (single point in time). "
                f"Default timeout is {DEFAULT_QUERY_TIMEOUT_SECONDS} seconds "
                f"but can be increased up to {MAX_QUERY_TIMEOUT_SECONDS} seconds for complex/slow queries."
            ),
            parameters={
                "query": ToolParameter(
                    description="The PromQL query",
                    type="string",
                    required=True,
                ),
                "description": ToolParameter(
                    description="Describes the query",
                    type="string",
                    required=True,
                ),
                "timeout": ToolParameter(
                    description=(
                        f"Query timeout in seconds. Default: {DEFAULT_QUERY_TIMEOUT_SECONDS}. "
                        f"Maximum: {MAX_QUERY_TIMEOUT_SECONDS}. "
                        f"Increase for complex queries that may take longer."
                    ),
                    type="number",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        if not self.toolset.config or not self.toolset.config.prometheus_url:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Prometheus is not configured. Prometheus URL is missing",
                params=params,
            )
        try:
            query = params.get("query", "")
            description = params.get("description", "")

            url = urljoin(self.toolset.config.prometheus_url, "api/v1/query")

            payload = {"query": query}

            # Get timeout parameter and enforce limits
            default_timeout = self.toolset.config.query_timeout_seconds_default
            max_timeout = self.toolset.config.query_timeout_seconds_hard_max
            timeout = params.get("timeout", default_timeout)
            if timeout > max_timeout:
                timeout = max_timeout
                logging.warning(
                    f"Timeout requested ({params.get('timeout')}) exceeds maximum ({max_timeout}s), using {max_timeout}s"
                )
            elif timeout < 1:
                timeout = default_timeout  # Min 1 second, but use default if invalid

            response = do_request(
                config=self.toolset.config,
                url=url,
                headers=self.toolset.config.headers,
                data=payload,
                timeout=timeout,
                verify=self.toolset.config.verify_ssl,
                method="POST",
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                error_message = None
                if status == "success" and not result_has_data(data):
                    status = "Failed"
                    error_message = (
                        "The prometheus query returned no result. Is the query correct?"
                    )
                response_data = MetricsBasedResponse(
                    status=status,
                    error_message=error_message,
                    tool_name=self.name,
                    description=description,
                    query=query,
                )
                structured_tool_result: StructuredToolResult
                # Check if data should be included based on size
                if self.toolset.config.tool_calls_return_data:
                    result_data = data.get("data", {})
                    response_data.data = result_data

                    structured_tool_result = create_structured_tool_result(
                        params=params, response=response_data
                    )
                    tool_call_id = context.tool_call_id
                    tool_name = context.tool_name
                    token_count = count_tool_response_tokens(
                        llm=context.llm,
                        structured_tool_result=structured_tool_result,
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                    )

                    token_limit = context.max_token_count
                    if self.toolset.config.query_response_size_limit_pct:
                        custom_token_limit = get_pct_token_count(
                            percent_of_total_context_window=self.toolset.config.query_response_size_limit_pct,
                            llm=context.llm,
                        )
                        if custom_token_limit < token_limit:
                            token_limit = custom_token_limit

                    # Provide summary if data is too large
                    if token_count > token_limit:
                        response_data.data = None
                        response_data.data_summary = (
                            create_data_summary_for_large_result(
                                result_data,
                                query,
                                token_count,
                                is_range_query=False,
                            )
                        )
                        logging.info(
                            f"Prometheus instant query returned large dataset: "
                            f"{response_data.data_summary.get('result_count', 0)} results, "
                            f"{token_count:,} tokens (limit: {token_limit:,}). "
                            f"Returning summary instead of full data."
                        )
                        # Also add token info to the summary for debugging
                        response_data.data_summary["_debug_info"] = (
                            f"Data size: {token_count:,} tokens exceeded limit of {token_limit:,} tokens"
                        )
                    else:
                        response_data.data = result_data

                structured_tool_result = create_structured_tool_result(
                    params=params, response=response_data
                )
                return structured_tool_result

            # Handle known Prometheus error status codes
            error_msg = "Unknown error occurred"
            if response.status_code in [400, 429]:
                try:
                    error_data = response.json()
                    error_msg = error_data.get(
                        "error", error_data.get("message", str(response.content))
                    )
                except json.JSONDecodeError:
                    pass
                return StructuredToolResult(
                    status=StructuredToolResultStatus.ERROR,
                    error=f"Query execution failed. HTTP {response.status_code}: {error_msg}",
                    params=params,
                )

            # For other status codes, just return the status code and content
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Query execution failed with unexpected status code: {response.status_code}. Response: {str(response.content)}",
                params=params,
            )

        except SSLError as e:
            logging.warning("SSL error while executing Prometheus query", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=format_ssl_error_message(self.toolset.config.prometheus_url, e),
                params=params,
            )
        except RequestException as e:
            logging.info("Failed to connect to Prometheus", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Connection error to Prometheus: {str(e)}",
                params=params,
            )
        except Exception as e:
            logging.info("Failed to connect to Prometheus", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Unexpected error executing query: {str(e)}",
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        description = params.get("description", "")
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Query ({description})"


class ExecuteRangeQuery(BasePrometheusTool):
    def __init__(self, toolset: "PrometheusToolset"):
        super().__init__(
            name="execute_prometheus_range_query",
            description=(
                f"Generates a graph and Execute a PromQL range query. "
                f"Default timeout is {DEFAULT_QUERY_TIMEOUT_SECONDS} seconds "
                f"but can be increased up to {MAX_QUERY_TIMEOUT_SECONDS} seconds for complex/slow queries. "
                f"Default time range is last 1 hour."
            ),
            parameters={
                "query": ToolParameter(
                    description="The PromQL query",
                    type="string",
                    required=True,
                ),
                "description": ToolParameter(
                    description="Describes the query",
                    type="string",
                    required=True,
                ),
                "start": ToolParameter(
                    description=standard_start_datetime_tool_param_description(
                        DEFAULT_GRAPH_TIME_SPAN_SECONDS
                    ),
                    type="string",
                    required=False,
                ),
                "end": ToolParameter(
                    description=STANDARD_END_DATETIME_TOOL_PARAM_DESCRIPTION,
                    type="string",
                    required=False,
                ),
                "step": ToolParameter(
                    description="Query resolution step width in duration format or float number of seconds",
                    type="number",
                    required=False,
                ),
                "output_type": ToolParameter(
                    description="Specifies how to interpret the Prometheus result. Use 'Plain' for raw values, 'Bytes' to format byte values, 'Percentage' to scale 0–1 values into 0–100%, or 'CPUUsage' to convert values to cores (e.g., 500 becomes 500m, 2000 becomes 2).",
                    type="string",
                    required=True,
                ),
                "timeout": ToolParameter(
                    description=(
                        f"Query timeout in seconds. Default: {DEFAULT_QUERY_TIMEOUT_SECONDS}. "
                        f"Maximum: {MAX_QUERY_TIMEOUT_SECONDS}. "
                        f"Increase for complex queries that may take longer."
                    ),
                    type="number",
                    required=False,
                ),
                "max_points": ToolParameter(
                    description=(
                        f"Maximum number of data points to return. Default: {int(MAX_GRAPH_POINTS)}. "
                        f"Can be reduced to get fewer data points (e.g., 50 for simpler graphs). "
                        f"Cannot exceed system limit of {int(MAX_GRAPH_POINTS)}. "
                        f"If your query would return more points than this limit, the step will be automatically adjusted."
                    ),
                    type="number",
                    required=False,
                ),
            },
            toolset=toolset,
        )

    def _invoke(self, params: dict, context: ToolInvokeContext) -> StructuredToolResult:
        if not self.toolset.config or not self.toolset.config.prometheus_url:
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error="Prometheus is not configured. Prometheus URL is missing",
                params=params,
            )

        try:
            url = urljoin(self.toolset.config.prometheus_url, "api/v1/query_range")

            query = get_param_or_raise(params, "query")
            (start, end) = process_timestamps_to_rfc3339(
                start_timestamp=params.get("start"),
                end_timestamp=params.get("end"),
                default_time_span_seconds=DEFAULT_GRAPH_TIME_SPAN_SECONDS,
            )
            step = parse_duration_to_seconds(params.get("step"))
            max_points = params.get(
                "max_points"
            )  # Get the optional max_points parameter

            # adjust_step_for_max_points handles None case and converts to float
            step = adjust_step_for_max_points(
                start_timestamp=start,
                end_timestamp=end,
                step=step,
                max_points_override=max_points,
            )

            description = params.get("description", "")
            output_type = params.get("output_type", "Plain")
            payload = {
                "query": query,
                "start": start,
                "end": end,
                "step": step,
            }

            # Get timeout parameter and enforce limits
            default_timeout = self.toolset.config.query_timeout_seconds_default
            max_timeout = self.toolset.config.query_timeout_seconds_hard_max
            timeout = params.get("timeout", default_timeout)
            if timeout > max_timeout:
                timeout = max_timeout
                logging.warning(
                    f"Timeout requested ({params.get('timeout')}) exceeds maximum ({max_timeout}s), using {max_timeout}s"
                )
            elif timeout < 1:
                timeout = default_timeout  # Min 1 second, but use default if invalid

            response = do_request(
                config=self.toolset.config,
                url=url,
                headers=self.toolset.config.headers,
                data=payload,
                timeout=timeout,
                verify=self.toolset.config.verify_ssl,
                method="POST",
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                error_message = None
                if status == "success" and not result_has_data(data):
                    status = "Failed"
                    error_message = (
                        "The prometheus query returned no result. Is the query correct?"
                    )
                response_data = MetricsBasedResponse(
                    status=status,
                    error_message=error_message,
                    tool_name=self.name,
                    description=description,
                    query=query,
                    start=start,
                    end=end,
                    step=step,
                    output_type=output_type,
                )

                structured_tool_result: StructuredToolResult

                # Check if data should be included based on size
                if self.toolset.config.tool_calls_return_data:
                    result_data = data.get("data", {})
                    response_data.data = result_data
                    structured_tool_result = create_structured_tool_result(
                        params=params, response=response_data
                    )

                    tool_call_id = context.tool_call_id
                    tool_name = context.tool_name
                    token_count = count_tool_response_tokens(
                        llm=context.llm,
                        structured_tool_result=structured_tool_result,
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                    )

                    token_limit = context.max_token_count
                    if self.toolset.config.query_response_size_limit_pct:
                        custom_token_limit = get_pct_token_count(
                            percent_of_total_context_window=self.toolset.config.query_response_size_limit_pct,
                            llm=context.llm,
                        )
                        if custom_token_limit < token_limit:
                            token_limit = custom_token_limit

                    # Provide summary if data is too large
                    if token_count > token_limit:
                        response_data.data = None
                        response_data.data_summary = (
                            create_data_summary_for_large_result(
                                result_data, query, token_count, is_range_query=True
                            )
                        )
                        logging.info(
                            f"Prometheus range query returned large dataset: "
                            f"{response_data.data_summary.get('series_count', 0)} series, "
                            f"{token_count:,} tokens (limit: {token_limit:,}). "
                            f"Returning summary instead of full data."
                        )
                        # Also add character info to the summary for debugging
                        response_data.data_summary["_debug_info"] = (
                            f"Data size: {token_count:,} tokens exceeded limit of {token_limit:,} tokens"
                        )
                    else:
                        response_data.data = result_data

                structured_tool_result = create_structured_tool_result(
                    params=params, response=response_data
                )

                return structured_tool_result

            error_msg = "Unknown error occurred"
            if response.status_code in [400, 429]:
                try:
                    error_data = response.json()
                    error_msg = error_data.get(
                        "error", error_data.get("message", str(response.content))
                    )
                except json.JSONDecodeError:
                    pass
                return StructuredToolResult(
                    status=StructuredToolResultStatus.ERROR,
                    error=f"Query execution failed. HTTP {response.status_code}: {error_msg}",
                    params=params,
                )

            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Query execution failed with unexpected status code: {response.status_code}. Response: {str(response.content)}",
                params=params,
            )

        except SSLError as e:
            logging.warning(
                "SSL error while executing Prometheus range query", exc_info=True
            )
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=format_ssl_error_message(self.toolset.config.prometheus_url, e),
                params=params,
            )
        except RequestException as e:
            logging.info("Failed to connect to Prometheus", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Connection error to Prometheus: {str(e)}",
                params=params,
            )
        except Exception as e:
            logging.info("Failed to connect to Prometheus", exc_info=True)
            return StructuredToolResult(
                status=StructuredToolResultStatus.ERROR,
                error=f"Unexpected error executing query: {str(e)}",
                params=params,
            )

    def get_parameterized_one_liner(self, params) -> str:
        description = params.get("description", "")
        return f"{toolset_name_for_one_liner(self.toolset.name)}: Query ({description})"


class PrometheusToolset(Toolset):
    config: Optional[Union[PrometheusConfig, AMPConfig, AzurePrometheusConfig]] = None

    def __init__(self):
        super().__init__(
            name="prometheus/metrics",
            description="Prometheus integration to fetch metadata and execute PromQL queries",
            docs_url="https://holmesgpt.dev/data-sources/builtin-toolsets/prometheus/",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/3/38/Prometheus_software_logo.svg",
            prerequisites=[CallablePrerequisite(callable=self.prerequisites_callable)],
            tools=[
                ListPrometheusRules(toolset=self),
                GetMetricNames(toolset=self),
                GetLabelValues(toolset=self),
                GetAllLabels(toolset=self),
                GetSeries(toolset=self),
                GetMetricMetadata(toolset=self),
                ExecuteInstantQuery(toolset=self),
                ExecuteRangeQuery(toolset=self),
            ],
            tags=[
                ToolsetTag.CORE,
            ],
        )
        self._reload_llm_instructions()

    def _reload_llm_instructions(self):
        template_file_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "prometheus_instructions.jinja2")
        )
        self._load_llm_instructions(jinja_template=f"file://{template_file_path}")

    def determine_prometheus_class(
        self, config: dict[str, Any]
    ) -> Type[Union[PrometheusConfig, AMPConfig, AzurePrometheusConfig]]:
        has_aws_fields = "aws_region" in config
        if has_aws_fields:
            return AMPConfig

        # Check for Azure config using static method
        is_azure = AzurePrometheusConfig.is_azure_config(config)
        if is_azure:
            logging.info("Detected Azure Managed Prometheus configuration")
        return AzurePrometheusConfig if is_azure else PrometheusConfig

    def _disable_azure_incompatible_tools(self):
        """
        Azure Managed Prometheus does not support some APIs.
        Remove unsupported tools.
        """
        incompatible = {
            "get_label_values",
            "get_metric_metadata",
            "list_prometheus_rules",
        }
        self.tools = [t for t in self.tools if t.name not in incompatible]

    def prerequisites_callable(self, config: dict[str, Any]) -> Tuple[bool, str]:
        try:
            if config:
                config_cls = self.determine_prometheus_class(config)
                self.config = config_cls(**config)  # type: ignore
                if isinstance(self.config, AzurePrometheusConfig):
                    self._disable_azure_incompatible_tools()
                self._reload_llm_instructions()
                return self._is_healthy()
        except Exception:
            logging.exception("Failed to create prometheus config")
            return False, "Failed to create prometheus config"
        try:
            prometheus_url = os.environ.get("PROMETHEUS_URL")
            if not prometheus_url:
                prometheus_url = self.auto_detect_prometheus_url()
                if not prometheus_url:
                    return (
                        False,
                        "Unable to auto-detect prometheus. Define prometheus_url in the configuration for tool prometheus/metrics",
                    )

            self.config = PrometheusConfig(
                prometheus_url=prometheus_url,
                headers=add_prometheus_auth(os.environ.get("PROMETHEUS_AUTH_HEADER")),
            )
            logging.info(f"Prometheus auto discovered at url {prometheus_url}")
            self._reload_llm_instructions()
            return self._is_healthy()
        except Exception as e:
            logging.exception("Failed to set up prometheus")
            return False, str(e)

    def auto_detect_prometheus_url(self) -> Optional[str]:
        url: Optional[str] = PrometheusDiscovery.find_prometheus_url()
        if not url:
            url = PrometheusDiscovery.find_vm_url()

        return url

    def _is_healthy(self) -> Tuple[bool, str]:
        if (
            not hasattr(self, "config")
            or not self.config
            or not self.config.prometheus_url
        ):
            return (
                False,
                f"Toolset {self.name} failed to initialize because prometheus is not configured correctly",
            )

        url = urljoin(self.config.prometheus_url, "api/v1/query?query=up")
        try:
            response = do_request(
                config=self.config,
                url=url,
                headers=self.config.headers,
                timeout=10,
                verify=self.config.verify_ssl,
                method="GET",
            )

            if response.status_code == 200:
                return True, ""
            else:
                return (
                    False,
                    f"Failed to connect to Prometheus at {url}: HTTP {response.status_code}",
                )

        except Exception as e:
            logging.debug("Failed to initialize Prometheus", exc_info=True)
            return (
                False,
                f"Failed to initialize using url={url}. Unexpected error: {str(e)}",
            )

    def get_example_config(self):
        example_config = PrometheusConfig(
            prometheus_url="http://prometheus-server.monitoring.svc.cluster.local:9090",
            headers={"Authorization": "Basic <base64_encoded_credentials>"},
            discover_metrics_from_last_hours=1,
            query_timeout_seconds_default=20,
            query_timeout_seconds_hard_max=180,
            verify_ssl=True,
        )
        return example_config.model_dump()
```
