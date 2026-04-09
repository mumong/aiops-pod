import os
import tempfile
from app.core.config import AppConfig, ConfigLoader


def test_app_config_defaults():
    c = AppConfig()
    assert c.llm_model == "deepseek/deepseek-chat"
    assert c.llm_api_key == ""


def test_config_loader_missing_file():
    c = ConfigLoader.load("/nonexistent/path.yaml")
    assert isinstance(c, AppConfig)


def test_config_loader_yaml(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("llm:\n  model: test-model\nmcp_servers:\n  test:\n    enabled: true\n")
    c = ConfigLoader.load(str(cfg_file))
    assert c.llm_model == "test-model"
    assert "test" in c.mcp_servers


def test_env_var_substitution():
    os.environ["TEST_VAR_XYZ"] = "hello"
    result = ConfigLoader._substitute_env_vars("${TEST_VAR_XYZ:-default}")
    assert result == "hello"
    del os.environ["TEST_VAR_XYZ"]


def test_env_var_default():
    result = ConfigLoader._substitute_env_vars("${NONEXISTENT_VAR_ABC:-fallback}")
    assert result == "fallback"
