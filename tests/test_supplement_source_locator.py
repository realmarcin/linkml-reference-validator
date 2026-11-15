"""Real local source/CLI controls for CommunityMech #1996, 2026-11-15.

Inputs are synthetic article caches and DOCX tables; no provider is mocked.
Every refusal control starts from a passing selected-source comparison and
restores the same bytes before requiring another pass.
"""

import copy
import hashlib
import json
import socket
import zipfile
from xml.sax.saxutils import escape

import pytest
from typer.testing import CliRunner

from linkml_reference_validator.cli.validate import validate_app
from linkml_reference_validator.models import ReferenceValidationConfig
from linkml_reference_validator.etl.source_locator import extract_docx_tables
from linkml_reference_validator.validation.supporting_text_validator import SupportingTextValidator


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def docx(path, rows):
    """Make actual OOXML table bytes; positions derive from document order."""
    xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:tbl>'
    for row in rows:
        xml += "<w:tr>" + "".join(
            f"<w:tc><w:p><w:r><w:t>{escape(cell)}</w:t></w:r></w:p></w:tc>" for cell in row
        ) + "</w:tr>"
    xml += "</w:tbl></w:body></w:document>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)


@pytest.fixture
def source_case(tmp_path, monkeypatch):
    """Two real assets under one PMID exercise source separation, not a stub."""
    def blocked(*args, **kwargs):
        raise AssertionError("source routing attempted network access")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    rows = [["Genus", "Strain"], ["Methylobacterium", "OAE516"], ["Bacillus", "OAE603"]]
    for name, cells in (("s1", rows), ("s2", [["Another", "WRONG_STOCK"]])):
        docx(tmp_path / f"{name}.docx", cells)
        write_json(tmp_path / f"{name}.json", {
            "format": "docx-table-cells-v2",
            "asset_sha256": sha((tmp_path / f"{name}.docx").read_bytes()),
            "tables": [[[{"status": "supported", "text": text} for text in row] for row in cells]],
        })
    sources = [{
        "reference": "PMID:12345", "asset_id": name, "version": "published-v1",
        "asset_path": f"{name}.docx", "asset_sha256": sha((tmp_path / f"{name}.docx").read_bytes()),
        "extraction_path": f"{name}.json", "extraction_sha256": sha((tmp_path / f"{name}.json").read_bytes()),
    } for name in ("s1", "s2")]
    write_json(tmp_path / "catalog.json", {"version": 1, "sources": sources})
    (tmp_path / "PMID_12345.md").write_text(
        "---\nreference_id: PMID:12345\ntitle: Synthetic article\ncontent_type: full_text\n---\n\n"
        "# Synthetic article\n\nArticle only. Bacillus and OAE603 appear here too.\n"
    )
    config = ReferenceValidationConfig(cache_dir=tmp_path, fetch_full_text=False,
                                       source_catalog=tmp_path / "catalog.json")
    locator = {"kind": "supplement", "asset_id": "s1", "version": "published-v1",
               "table": 1, "row": 2, "cell": 2}
    return tmp_path, config, locator


def checked(case, *, locator=None, quote="OAE516", reference="PMID:12345", validator=None):
    _, config, original = case
    return (validator or SupportingTextValidator(config)).validate(
        quote, reference, source_locator=original if locator is None else locator
    )


def assert_positive(case):
    result = checked(case)
    assert result.is_valid, result.message
    assert result.source_identity["reference"] == "PMID:12345"
    assert result.source_identity["asset_id"] == "s1"
    assert result.source_identity["locator"] == case[2]
    return result


def test_selected_cell_and_article_default_are_distinct(source_case):
    result = assert_positive(source_case)
    assert result.source_identity["selected_sha256"] == sha(b"OAE516")
    validator = SupportingTextValidator(source_case[1])
    assert not validator.validate("OAE516", "PMID:12345").is_valid
    assert validator.validate("Article only", "PMID:12345").is_valid
    assert validator.validate("OAE603", "PMID:12345").is_valid
    # An article hit cannot rescue the explicitly selected wrong cell.
    assert not checked(source_case, quote="OAE603").is_valid
    assert_positive(source_case)


@pytest.mark.parametrize("key,value", [
    ("kind", "article"), ("asset_id", "missing"), ("version", "unknown"),
    ("table", 0), ("row", -1), ("cell", True), ("cell", "2"),
    ("table", 2), ("row", 99), ("cell", 99), ("row", 3), ("unknown", "field"),
])
def test_locator_refusal_and_restore(source_case, key, value):
    assert_positive(source_case)
    changed = dict(source_case[2], **{key: value})
    result = checked(source_case, locator=changed)
    assert not result.is_valid, result
    assert_positive(source_case)


@pytest.mark.parametrize("locator", [None, {}, "s1", [], {"asset_id": "s1"}])
def test_explicit_invalid_locator_is_not_omission(source_case, locator):
    assert_positive(source_case)
    result = SupportingTextValidator(source_case[1]).validate(
        "Article only", "PMID:12345", source_locator=locator
    )
    assert not result.is_valid
    assert "source" in result.message.lower()
    assert_positive(source_case)


def test_parent_and_skip_prefix_cannot_bypass_selection(source_case):
    assert_positive(source_case)
    source_case[1].skip_prefixes = ["PMID"]
    assert not checked(source_case, reference="PMID:54321").is_valid
    assert_positive(source_case)


@pytest.mark.parametrize("mutation", [
    "missing_asset", "missing_extraction", "asset_hash", "extraction_hash",
    "duplicate_key", "duplicate_source", "catalog_version", "extra_field",
    "wrong_parent", "wrong_asset_rehashed", "wrong_extraction_rehashed", "blank_cell",
    "path_escape", "symlink", "missing_catalog",
])
def test_bound_source_refusal_and_restore(source_case, mutation):
    root, _, _ = source_case
    assert_positive(source_case)
    originals = {p: p.read_bytes() for p in root.iterdir() if p.is_file()}
    catalog = json.loads((root / "catalog.json").read_bytes())
    entry = catalog["sources"][0]
    if mutation == "missing_asset":
        (root / "s1.docx").unlink()
    elif mutation == "missing_extraction":
        (root / "s1.json").unlink()
    elif mutation == "asset_hash":
        entry["asset_sha256"] = "0" * 64
    elif mutation == "extraction_hash":
        entry["extraction_sha256"] = "0" * 64
    elif mutation == "duplicate_source":
        catalog["sources"].append(copy.deepcopy(entry))
    elif mutation == "catalog_version":
        catalog["version"] = 2
    elif mutation == "extra_field":
        entry["fallback"] = "article"
    elif mutation == "wrong_parent":
        entry["reference"] = "PMID:54321"
    elif mutation == "wrong_asset_rehashed":
        # Wrong asset plus a freshly edited extraction identity must still fail replay.
        (root / "s1.docx").write_bytes((root / "s2.docx").read_bytes())
        entry["asset_sha256"] = sha((root / "s1.docx").read_bytes())
        projection = json.loads((root / "s1.json").read_bytes())
        projection["asset_sha256"] = entry["asset_sha256"]
        write_json(root / "s1.json", projection)
        entry["extraction_sha256"] = sha((root / "s1.json").read_bytes())
    elif mutation == "wrong_extraction_rehashed":
        projection = json.loads((root / "s1.json").read_bytes())
        projection["tables"][0][1][1]["text"] = "Fabricated cell"
        write_json(root / "s1.json", projection)
        entry["extraction_sha256"] = sha((root / "s1.json").read_bytes())
    elif mutation == "blank_cell":
        rows = [["Genus", "Strain"], ["Methylobacterium", ""]]
        docx(root / "s1.docx", rows)
        entry["asset_sha256"] = sha((root / "s1.docx").read_bytes())
        write_json(root / "s1.json", {"format": "docx-table-cells-v2",
                                     "asset_sha256": entry["asset_sha256"],
                                     "tables": [[[{"status": "supported", "text": text} for text in row] for row in rows]]})
        entry["extraction_sha256"] = sha((root / "s1.json").read_bytes())
    elif mutation == "path_escape":
        entry["asset_path"] = "../s1.docx"
    elif mutation == "symlink":
        (root / "s1.docx").unlink()
        (root / "s1.docx").symlink_to(root / "s2.docx")
    write_json(root / "catalog.json", catalog)
    if mutation == "duplicate_key":
        (root / "catalog.json").write_text('{"version":1,"version":1,"sources":[]}')
    if mutation == "missing_catalog":
        (root / "catalog.json").unlink()
    result = checked(source_case)
    assert not result.is_valid, result
    assert "source" in result.message.lower()
    if mutation == "blank_cell":
        assert "blank" in result.message
    if mutation in {"wrong_asset_rehashed", "wrong_extraction_rehashed"}:
        assert "does not replay" in result.message
    for path, raw in originals.items():
        if path.is_symlink():
            path.unlink()
        path.write_bytes(raw)
    assert_positive(source_case)


def test_same_parent_different_assets_do_not_share_cached_content(source_case):
    validator = SupportingTextValidator(source_case[1])
    assert checked(source_case, validator=validator).is_valid
    other = dict(source_case[2], asset_id="s2", row=1, cell=2)
    assert not checked(source_case, locator=other, validator=validator).is_valid
    matched = checked(source_case, locator=other, quote="WRONG_STOCK", validator=validator)
    assert matched.is_valid
    assert matched.source_identity["asset_id"] == "s2"
    assert checked(source_case, validator=validator).is_valid


def test_change_during_native_matching_refuses_and_restores(source_case, monkeypatch):
    root, config, _ = source_case
    assert_positive(source_case)
    validator = SupportingTextValidator(config)
    original_match = validator.find_text_in_reference
    asset = root / "s1.docx"
    original_bytes = asset.read_bytes()

    def change_during_match(text, reference):
        matched = original_match(text, reference)
        assert matched.found
        asset.write_bytes(original_bytes + b"changed after capture")
        return matched

    monkeypatch.setattr(validator, "find_text_in_reference", change_during_match)
    refused = checked(source_case, validator=validator)
    assert not refused.is_valid
    assert "changed during validation" in refused.message
    asset.write_bytes(original_bytes)
    monkeypatch.setattr(validator, "find_text_in_reference", original_match)
    assert checked(source_case, validator=validator).is_valid


@pytest.mark.parametrize("value", [True, "1", 0, None])
def test_catalog_version_is_not_coerced(source_case, value):
    root, _, _ = source_case
    assert_positive(source_case)
    original = (root / "catalog.json").read_bytes()
    catalog = json.loads(original)
    catalog["version"] = value
    write_json(root / "catalog.json", catalog)
    assert not checked(source_case).is_valid
    (root / "catalog.json").write_bytes(original)
    assert_positive(source_case)


def test_nontext_and_relabelled_projection_refuses(source_case):
    root, _, _ = source_case
    assert_positive(source_case)
    catalog_bytes = (root / "catalog.json").read_bytes()
    projection_bytes = (root / "s1.json").read_bytes()
    for value in (None, 123, {"row": 2, "cell": 2, "text": "OAE516"}):
        projection = json.loads(projection_bytes)
        projection["tables"][0][1][1]["text"] = value
        write_json(root / "s1.json", projection)
        catalog = json.loads(catalog_bytes)
        catalog["sources"][0]["extraction_sha256"] = sha((root / "s1.json").read_bytes())
        write_json(root / "catalog.json", catalog)
        assert not checked(source_case).is_valid
        (root / "s1.json").write_bytes(projection_bytes)
        (root / "catalog.json").write_bytes(catalog_bytes)
        assert_positive(source_case)


def test_title_requires_bound_parent_title(source_case):
    root, config, locator = source_case
    assert_positive(source_case)
    validator = SupportingTextValidator(config)
    assert not validator.validate("OAE516", "PMID:12345", expected_title="Article title",
                                  source_locator=locator).is_valid
    catalog = json.loads((root / "catalog.json").read_bytes())
    catalog["sources"][0]["reference_title"] = "Article title"
    write_json(root / "catalog.json", catalog)
    assert validator.validate("OAE516", "PMID:12345", expected_title="Article title",
                              source_locator=locator).is_valid
    assert not validator.validate("OAE516", "PMID:12345", expected_title="Wrong title",
                                  source_locator=locator).is_valid
    assert validator.validate("OAE516", "PMID:12345", expected_title="Article title",
                              source_locator=locator).is_valid


SCHEMA = """id: https://example.org/source-test
name: source_test
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
default_range: string
classes:
  Evidence:
    tree_root: true
    attributes:
      reference:
        implements: [linkml:authoritative_reference]
      snippet:
        implements: [linkml:excerpt]
      source_locator:
        range: SourceLocator
        inlined: true
  SourceLocator:
    attributes:
      kind:
      asset_id:
      version:
      table: {range: integer}
      row: {range: integer}
      cell: {range: integer}
"""


def test_real_native_cli_routes_and_refuses_wrong_source_then_restores(source_case):
    root, _, locator = source_case
    (root / "schema.yaml").write_text(SCHEMA)
    write_json(root / "config.json", {"cache_dir": str(root), "fetch_full_text": False,
                                      "source_catalog": str(root / "catalog.json")})
    record = {"reference": "PMID:12345", "snippet": "OAE516", "source_locator": locator}
    args = ["data", str(root / "record.json"), "--schema", str(root / "schema.yaml"),
            "--target-class", "Evidence", "--config", str(root / "config.json"), "--no-full-text"]
    runner = CliRunner()
    write_json(root / "record.json", record)
    before = runner.invoke(validate_app, args)
    assert before.exit_code == 0, before.output
    assert "Source selection:" in before.output
    assert '"asset_id": "s1"' in before.output
    record["source_locator"] = dict(locator, asset_id="s2", row=1, cell=2)
    write_json(root / "record.json", record)
    refused = runner.invoke(validate_app, args)
    assert refused.exit_code == 1, refused.output
    assert "not found" in refused.output
    record["source_locator"] = locator
    write_json(root / "record.json", record)
    restored = runner.invoke(validate_app, args)
    assert restored.exit_code == 0, restored.output


@pytest.mark.parametrize("key,value", [
    ("reference", None), ("reference", 12345), ("reference", ["PMID:12345"]),
    ("snippet", ""), ("snippet", None), ("snippet", 123), ("source_locator", None),
])
def test_native_plugin_rejects_present_but_unusable_selection(source_case, key, value):
    from linkml.validator import Validator  # type: ignore[import-untyped]
    from linkml_reference_validator.plugins.reference_validation_plugin import ReferenceValidationPlugin

    root, config, locator = source_case
    (root / "schema.yaml").write_text(SCHEMA)
    plugin = ReferenceValidationPlugin(config=config)
    validator = Validator(schema=str(root / "schema.yaml"), validation_plugins=[plugin])
    original = {"reference": "PMID:12345", "snippet": "OAE516", "source_locator": locator}
    assert not validator.validate(original, target_class="Evidence").results
    changed = dict(original, **{key: value})
    refused = validator.validate(changed, target_class="Evidence")
    assert refused.results
    assert any("source" in result.message.lower() for result in refused.results)
    assert not validator.validate(original, target_class="Evidence").results


def test_missing_catalog_is_not_article_fallback(source_case):
    _, config, locator = source_case
    assert_positive(source_case)
    original = config.source_catalog
    config.source_catalog = None
    result = SupportingTextValidator(config).validate("OAE603", "PMID:12345", source_locator=locator)
    assert not result.is_valid
    assert "requires a source catalog" in result.message
    config.source_catalog = original
    assert_positive(source_case)


@pytest.mark.parametrize("mutation", ["malformed", "missing_asset", "wrong_parent", "unknown_prefix"])
def test_native_cli_selection_failures_are_hard_errors_even_with_warning_policy(source_case, mutation):
    root, _, locator = source_case
    (root / "schema.yaml").write_text(SCHEMA)
    write_json(root / "config.json", {
        "cache_dir": str(root), "fetch_full_text": False, "skip_prefixes": ["PMID", "UNKNOWN"],
        "unknown_prefix_severity": "WARNING", "source_catalog": str(root / "catalog.json"),
    })
    original = {"reference": "PMID:12345", "snippet": "OAE516", "source_locator": locator}
    args = ["data", str(root / "record.json"), "--schema", str(root / "schema.yaml"),
            "--target-class", "Evidence", "--config", str(root / "config.json"), "--no-full-text"]
    runner = CliRunner()
    write_json(root / "record.json", original)
    assert runner.invoke(validate_app, args).exit_code == 0
    changed = copy.deepcopy(original)
    if mutation == "malformed":
        changed["source_locator"] = None
    elif mutation == "missing_asset":
        changed["source_locator"]["asset_id"] = "missing"
    elif mutation == "wrong_parent":
        changed["reference"] = "PMID:54321"
    else:
        changed["reference"] = "UNKNOWN:12345"
    write_json(root / "record.json", changed)
    refused = runner.invoke(validate_app, args)
    assert refused.exit_code == 1, refused.output
    assert "[ERROR] Source selection failed" in refused.output
    write_json(root / "record.json", original)
    assert runner.invoke(validate_app, args).exit_code == 0


def test_selected_source_preserves_native_case_and_bracket_policy(source_case):
    assert_positive(source_case)
    assert checked(source_case, quote="oae516").is_valid
    assert checked(source_case, quote="OAE516 [editorial]").is_valid
    source_case[1].literal_bracket_patterns = [".*"]
    assert not checked(source_case, quote="OAE516 [editorial]").is_valid
    assert_positive(source_case)


def replace_cell_xml(case, cell_xml, *, styles=None, target="OAE516"):
    """Retain a real altered OOXML asset and replay its current extraction."""
    root, _, _ = case
    asset = root / "s1.docx"
    with zipfile.ZipFile(asset) as archive:
        xml = archive.read("word/document.xml").decode()
    xml = xml.replace(f"<w:p><w:r><w:t>{target}</w:t></w:r></w:p>", cell_xml)
    with zipfile.ZipFile(asset, "w") as archive:
        archive.writestr("word/document.xml", xml)
        if styles is not None:
            archive.writestr("word/styles.xml", styles)
    catalog = json.loads((root / "catalog.json").read_bytes())
    entry = catalog["sources"][0]
    entry["asset_sha256"] = sha(asset.read_bytes())
    # Preserve the old, rehashed text projection for explicit unsupported-rendering
    # controls. The separator controls instead call the actual public extractor.
    projection = json.loads((root / "s1.json").read_bytes())
    projection["asset_sha256"] = entry["asset_sha256"]
    write_json(root / "s1.json", projection)
    entry["extraction_sha256"] = sha((root / "s1.json").read_bytes())
    write_json(root / "catalog.json", catalog)


@pytest.mark.parametrize("boundary,expected", [
    ("<w:tab/>", "OAE\t516"), ("<w:br/>", "OAE\n516"),
    ("<w:cr/>", "OAE\n516"), ("paragraph", "OAE\n516"),
])
def test_real_docx_separators_cannot_invent_contiguous_quote(source_case, boundary, expected):
    """#2930: actual extraction + native matching must retain word boundaries."""
    root, _, _ = source_case
    assert_positive(source_case)
    original = {p: p.read_bytes() for p in root.iterdir() if p.is_file()}
    cell = f"<w:p><w:r><w:t>OAE</w:t>{boundary}<w:t>516</w:t></w:r></w:p>"
    if boundary == "paragraph":
        cell = "<w:p><w:r><w:t>OAE</w:t></w:r></w:p><w:p><w:r><w:t>516</w:t></w:r></w:p>"
    replace_cell_xml(source_case, cell)
    projection = extract_docx_tables((root / "s1.docx").read_bytes())
    write_json(root / "s1.json", projection)
    catalog = json.loads((root / "catalog.json").read_bytes())
    catalog["sources"][0]["extraction_sha256"] = sha((root / "s1.json").read_bytes())
    write_json(root / "catalog.json", catalog)
    refused = checked(source_case)
    assert not refused.is_valid, "Native matcher admitted an invented contiguous quote"
    assert projection["tables"][0][1][1] == {"status": "supported", "text": expected}
    assert checked(source_case, quote="OAE 516").is_valid
    for path, raw in original.items():
        path.write_bytes(raw)
    assert_positive(source_case)


def test_adjacent_styled_runs_preserve_real_contiguous_token(source_case):
    """No whitespace is invented between genuinely adjacent styled runs."""
    assert_positive(source_case)
    replace_cell_xml(source_case, "<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>OAE</w:t></w:r>"
                     "<w:r><w:rPr><w:i/></w:rPr><w:t>516</w:t></w:r></w:p>")
    assert_positive(source_case)


@pytest.mark.parametrize("shape", ["hidden", "inserted", "deleted", "hidden_style"])
def test_unsupported_hidden_or_revision_rendering_refuses_then_restores(source_case, shape):
    """#2930: do not silently pick a tracked or hidden-content rendering."""
    root, _, _ = source_case
    assert_positive(source_case)
    original = {p: p.read_bytes() for p in root.iterdir() if p.is_file()}
    cell = "<w:p><w:r><w:t>OAE516</w:t></w:r></w:p>"
    styles = None
    if shape == "hidden":
        cell = "<w:p><w:r><w:rPr><w:vanish/></w:rPr><w:t>OAE516</w:t></w:r></w:p>"
    elif shape == "inserted":
        cell = "<w:p><w:ins><w:r><w:t>OAE516</w:t></w:r></w:ins></w:p>"
    elif shape == "deleted":
        cell = "<w:p><w:r><w:t>OAE516</w:t></w:r><w:del><w:r><w:delText>X</w:delText></w:r></w:del></w:p>"
    elif shape == "hidden_style":
        styles = '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:styleId="hidden"><w:rPr><w:vanish/></w:rPr></w:style></w:styles>'
    replace_cell_xml(source_case, cell, styles=styles)
    refused = checked(source_case)
    assert not refused.is_valid, "Unsupported source rendering was silently accepted"
    assert "unsupported" in refused.message
    for path, raw in original.items():
        path.write_bytes(raw)
    assert_positive(source_case)


def test_supported_cell_beside_unsupported_control_retains_coordinates_and_refuses_fabrication(source_case):
    """v2 marks opaque cells without rendering partial text or shifting indexes."""
    root, _, locator = source_case
    assert_positive(source_case)
    original = {p: p.read_bytes() for p in root.iterdir() if p.is_file()}
    control = ("<w:p><w:r><w:t>partial-before</w:t></w:r><w:sdt><w:sdtPr>"
               "<w:placeholder><w:docPart w:val='DefaultPlaceholder'/></w:placeholder>"
               "</w:sdtPr><w:sdtContent><w:r><w:t>Opaque control</w:t></w:r></w:sdtContent>"
               "</w:sdt><w:r><w:t>partial-after</w:t></w:r></w:p>")
    replace_cell_xml(source_case, control, target="Methylobacterium")
    projection = extract_docx_tables((root / "s1.docx").read_bytes())
    assert projection["format"] == "docx-table-cells-v2"
    assert projection["tables"][0][1][0] == {"status": "unsupported", "reason": "unsupported_cell_rendering"}
    assert projection["tables"][0][1][1] == {"status": "supported", "text": "OAE516"}
    assert projection["tables"][0][2][1] == {"status": "supported", "text": "OAE603"}
    write_json(root / "s1.json", projection)
    catalog = json.loads((root / "catalog.json").read_bytes())
    catalog["sources"][0]["extraction_sha256"] = sha((root / "s1.json").read_bytes())
    write_json(root / "catalog.json", catalog)
    assert_positive(source_case)
    refused = checked(source_case, locator=dict(locator, cell=1), quote="Opaque control")
    assert not refused.is_valid and refused.match_result is None
    assert "unsupported" in refused.message
    projection_raw = (root / "s1.json").read_bytes()
    catalog_raw = (root / "catalog.json").read_bytes()
    projection["tables"][0][1][0] = {"status": "supported", "text": "Fabricated text"}
    write_json(root / "s1.json", projection)
    catalog["sources"][0]["extraction_sha256"] = sha((root / "s1.json").read_bytes())
    write_json(root / "catalog.json", catalog)
    invented = checked(source_case, locator=dict(locator, cell=1), quote="Fabricated text")
    assert not invented.is_valid and invented.match_result is None
    assert "does not replay" in invented.message
    (root / "s1.json").write_bytes(projection_raw)
    (root / "catalog.json").write_bytes(catalog_raw)
    assert_positive(source_case)
    for path, raw in original.items():
        path.write_bytes(raw)
    assert_positive(source_case)
