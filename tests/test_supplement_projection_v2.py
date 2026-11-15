"""Closed cell markers and whole-asset geometry refusal for #2930, 2026-11-15."""

import json
import zipfile

import pytest

from tests.test_supplement_source_locator import (
    assert_positive, checked, sha, source_case, write_json,  # noqa: F401
)


@pytest.mark.parametrize("change", ["old_format", "unknown_reason", "partial_text", "missing_status"])
def test_rehashed_projection_cannot_relax_closed_cell_contract(request, change):
    case = request.getfixturevalue("source_case")
    root, _, _ = case
    assert_positive(case)
    original = {p: p.read_bytes() for p in root.iterdir() if p.is_file()}
    projection = json.loads((root / "s1.json").read_bytes())
    if change == "old_format":
        projection["format"] = "docx-table-cells-v1"
    elif change == "unknown_reason":
        projection["tables"][0][1][1] = {"status": "unsupported", "reason": "ignore"}
    elif change == "partial_text":
        projection["tables"][0][1][1] = {
            "status": "unsupported", "reason": "unsupported_cell_rendering", "text": "OAE516",
        }
    else:
        del projection["tables"][0][1][1]["status"]
    write_json(root / "s1.json", projection)
    catalog = json.loads((root / "catalog.json").read_bytes())
    catalog["sources"][0]["extraction_sha256"] = sha((root / "s1.json").read_bytes())
    write_json(root / "catalog.json", catalog)
    result = checked(case)
    assert not result.is_valid and result.match_result is None
    for path, raw in original.items():
        path.write_bytes(raw)
    assert_positive(case)


@pytest.mark.parametrize("change,reason", [
    ("malformed_xml", "Invalid selected source"), ("malformed_zip", "Invalid selected source"),
    ("merged", "merged cells"), ("nested", "nested or non-body"),
    ("row_wrapper", "row alignment"), ("cell_wrapper", "cell alignment"),
])
def test_asset_or_geometry_failure_cannot_become_opaque_cell(request, change, reason):
    case = request.getfixturevalue("source_case")
    root, _, _ = case
    assert_positive(case)
    original = {p: p.read_bytes() for p in root.iterdir() if p.is_file()}
    asset = root / "s1.docx"
    with zipfile.ZipFile(asset) as archive:
        xml = archive.read("word/document.xml").decode()
    if change == "malformed_xml":
        xml = xml[:-12]
    elif change == "merged":
        xml = xml.replace("<w:tc>", "<w:tc><w:tcPr><w:gridSpan w:val='2'/></w:tcPr>", 1)
    elif change == "nested":
        xml = xml.replace("<w:tc>", "<w:tc><w:tbl><w:tr><w:tc><w:p/></w:tc></w:tr></w:tbl>", 1)
    elif change == "row_wrapper":
        xml = xml.replace("<w:tr>", "<w:sdt><w:sdtContent><w:tr>", 1)
        xml = xml.replace("</w:tr>", "</w:tr></w:sdtContent></w:sdt>", 1)
    elif change == "cell_wrapper":
        xml = xml.replace("<w:tc>", "<w:sdt><w:sdtContent><w:tc>", 1)
        xml = xml.replace("</w:tc>", "</w:tc></w:sdtContent></w:sdt>", 1)
    with zipfile.ZipFile(asset, "w") as archive:
        archive.writestr("word/document.xml", xml)
    if change == "malformed_zip":
        asset.write_bytes(b"Not a ZIP")
    projection = json.loads((root / "s1.json").read_bytes())
    projection["asset_sha256"] = sha(asset.read_bytes())
    write_json(root / "s1.json", projection)
    catalog = json.loads((root / "catalog.json").read_bytes())
    catalog["sources"][0].update(asset_sha256=sha(asset.read_bytes()),
                                 extraction_sha256=sha((root / "s1.json").read_bytes()))
    write_json(root / "catalog.json", catalog)
    result = checked(case)
    assert not result.is_valid and result.match_result is None
    assert reason in result.message
    for path, raw in original.items():
        path.write_bytes(raw)
    assert_positive(case)
