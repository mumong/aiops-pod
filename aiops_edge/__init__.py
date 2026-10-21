"""Multi-cluster access for AIOps (specs/008-multi-cluster).

Standard library only, so the same files run in the AIOps image, the MCP image
(synced copy) and the edge runner image. Edge clusters are reached solely
through the xnet tunnel and our edge runner; nothing here reads a kubeconfig
for an edge cluster.
"""
