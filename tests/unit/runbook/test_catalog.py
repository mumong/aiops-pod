import json
from app.core.runbook.catalog import RunbookCatalog, RunbookEntry


def test_runbook_catalog_empty():
    c = RunbookCatalog()
    assert len(c) == 0
    assert not c
    assert c.to_prompt_text() == ""


def test_runbook_catalog_from_json(tmp_path):
    catalog_file = tmp_path / "catalog.json"
    catalog_file.write_text(json.dumps([
        {"id": "l0-disk", "description": "Disk full", "link": "l0-disk.md"},
        {"id": "l3-image", "description": "ImagePull", "link": "l3-image.md"},
    ]))
    c = RunbookCatalog.from_json(str(catalog_file))
    assert len(c) == 2
    assert c.catalog[0].id == "l0-disk"


def test_runbook_catalog_to_prompt():
    c = RunbookCatalog([RunbookEntry(id="test", description="Test RB", link="test.md")])
    text = c.to_prompt_text()
    assert "test.md" in text
    assert "Test RB" in text
