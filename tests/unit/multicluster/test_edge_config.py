"""Cluster configuration and xnet identifiers (research R3)."""

import pytest

from aiops_edge import clusters


def test_absent_config_is_single_local_cluster(tmp_path):
    cfg = clusters.load_config(str(tmp_path / "missing.yaml"))
    assert cfg.multi is False
    assert cfg.resolve(None).name == "local"
    assert cfg.resolve("local").access == "local"


def test_uuid_and_node_name_round_trip():
    uuid = "99eea57d-4cbe-4047-a7a0-ced9c658316c"
    assert clusters.uuid_to_node_name(uuid) == "vc-942nkkozc8o5fyb9q3bznb1ws"
    assert clusters.node_name_to_uuid("vc-942nkkozc8o5fyb9q3bznb1ws") == uuid
    assert clusters.node_name_to_uuid("vc-xnet-management") == "xnet-management"


def test_node_name_to_uuid_rejects_garbage():
    with pytest.raises(ValueError):
        clusters.node_name_to_uuid("edge-88")


CONFIG = """
clusters:
  default: null
  center: vc-xnet-management
  items:
    - name: vc-xnet-management
      aliases: [center]
      access: local
      observability: victoria
    - name: vc-942nkkozc8o5fyb9q3bznb1ws
      aliases: [edge-88, Edge88]
      access: xnet
      observability: victoria
  access:
    xnet:
      proxy_url: https://xnet-management.xnet.svc:9090/proxy
      cert_file: /etc/aiops-xnet/cert.pem
      key_file: /etc/aiops-xnet/key.pem
      ca_file: /etc/aiops-xnet/ca.pem
      runner_url: http://aiops-edge-runner.aiops.svc:8090
      signing_key_file: /etc/aiops-edge-key/key
"""


@pytest.fixture
def cfg(tmp_path):
    path = tmp_path / "clusters.yaml"
    path.write_text(CONFIG)
    return clusters.load_config(str(path))


def test_multi_cluster_resolution(cfg):
    assert cfg.multi is True
    assert cfg.resolve("edge-88").name == "vc-942nkkozc8o5fyb9q3bznb1ws"
    assert (
        cfg.resolve("EDGE88").name == "vc-942nkkozc8o5fyb9q3bznb1ws"
    )  # aliases are case-insensitive
    assert cfg.resolve("center").access == "local"
    assert cfg.resolve("edge-99") is None


def test_multi_cluster_has_no_implicit_default(cfg):
    assert cfg.resolve(None) is None
    assert cfg.resolve("") is None


def test_xnet_cluster_uuid_derived_from_name(cfg):
    assert cfg.resolve("edge-88").uuid == "99eea57d-4cbe-4047-a7a0-ced9c658316c"
    assert cfg.xnet.runner_url == "http://aiops-edge-runner.aiops.svc:8090"


def test_local_alias_maps_to_center_in_multi_mode(cfg):
    # The center's own tools run in-cluster; "local" names it in both modes.
    assert cfg.resolve("local").name == "vc-xnet-management"


def test_xnet_cluster_requires_access_block(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "clusters:\n  items:\n    - name: vc-942nkkozc8o5fyb9q3bznb1ws\n      access: xnet\n"
    )
    with pytest.raises(ValueError, match="access.xnet"):
        clusters.load_config(str(path))
