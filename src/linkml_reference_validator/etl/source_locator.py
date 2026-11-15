"""Select one retained supplementary DOCX cell without article fallback.

The v2 contract numbers top-level body tables, direct rows and direct cells
from one, in OOXML document order (including header rows). Merged cells and
nested tables are refused. Adjacent styled runs concatenate, explicit tabs are
tabs, and breaks/paragraph boundaries are newlines. Hidden/revised content
refuses the whole asset. Unsupported cell rendering becomes an explicit marker with no partial text.
Selecting a marked cell fails before matching. A retained JSON
projection is accepted only when it equals a fresh extraction of the pinned
DOCX bytes. This module performs no network access or writes.
"""

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Callable, Literal
from zipfile import BadZipFile, ZipFile

from lxml import etree  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field


ABSENT = object()
FORMAT = "docx-table-cells-v2"
MAX_BYTES = 20 * 1024 * 1024
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Nonblank = Annotated[str, Field(min_length=1, pattern=r"\S")]
Position = Annotated[int, Field(strict=True, ge=1)]


class SourceSelectionError(ValueError):
    """An explicitly requested source cannot be established."""


class CellRenderingUnsupported(SourceSelectionError):
    """Only this known rendering boundary can become an opaque cell marker."""


class ClosedModel(BaseModel):
    """Unknown fields and coercions cannot change the routing contract."""

    model_config = ConfigDict(extra="forbid", strict=True)


class SourceLocator(ClosedModel):
    """One cell in one identified supplementary asset version."""

    kind: Literal["supplement"]
    asset_id: Nonblank
    version: Nonblank
    table: Position
    row: Position
    cell: Position


class SourceEntry(ClosedModel):
    """A publisher asset and its exact, mechanically replayable projection."""

    reference: Nonblank
    asset_id: Nonblank
    version: Nonblank
    asset_path: Nonblank
    asset_sha256: Digest
    extraction_path: Nonblank
    extraction_sha256: Digest
    reference_title: str | None = None


class SourceCatalog(ClosedModel):
    """A closed list; duplicate normalized reference/asset/version keys fail."""

    version: Annotated[int, Field(strict=True, ge=1, le=1)]
    sources: list[SourceEntry]


class SupportedCell(ClosedModel):
    """Exact supported cell text, including its structural whitespace."""

    status: Literal["supported"]
    text: str


class UnsupportedCell(ClosedModel):
    """Opaque cell retains its position but contains no usable partial text."""

    status: Literal["unsupported"]
    reason: Literal["unsupported_cell_rendering"]


Cell = Annotated[SupportedCell | UnsupportedCell, Field(discriminator="status")]


class TableProjection(ClosedModel):
    """Positional arrays avoid manually invented or duplicate row labels."""

    format: Literal["docx-table-cells-v2"]
    asset_sha256: Digest
    tables: list[list[list[Cell]]]


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceSelectionError(f"Duplicate source JSON key: {key}")
        result[key] = value
    return result


def _json(raw: bytes) -> Any:
    return json.loads(raw, object_pairs_hook=_unique_pairs)


def _xml(raw: bytes):
    """Parse bounded XML without entities, DTDs or external access."""
    if len(raw) > MAX_BYTES:
        raise SourceSelectionError("Source DOCX XML exceeds the bounded size")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    root = etree.fromstring(raw, parser)
    if root.getroottree().docinfo.doctype:
        raise SourceSelectionError("Source DOCX DTD declarations are unsupported")
    return root


def _cell_text(cell) -> str:
    """Render only simple text paragraphs; never discard a token boundary."""
    namespace = "{" + NS["w"] + "}"

    def paragraph_part(element):
        if element.tag == namespace + "r":
            pieces = []
            for node in element:
                if node.tag == namespace + "rPr":
                    continue
                if node.tag == namespace + "t":
                    pieces.append(node.text or "")
                elif node.tag == namespace + "tab":
                    pieces.append("\t")
                elif node.tag in {namespace + "br", namespace + "cr"}:
                    pieces.append("\n")
                else:
                    raise CellRenderingUnsupported("Source DOCX run rendering is unsupported")
            return "".join(pieces)
        if element.tag == namespace + "hyperlink":
            return "".join(paragraph_part(child) for child in element)
        if element.tag in {namespace + name for name in ("pPr", "bookmarkStart", "bookmarkEnd", "proofErr")}:
            return ""
        raise CellRenderingUnsupported("Source DOCX paragraph rendering is unsupported")

    paragraphs = []
    for element in cell:
        if element.tag == namespace + "tcPr":
            continue
        if element.tag != namespace + "p":
            raise CellRenderingUnsupported("Source DOCX cell rendering is unsupported")
        paragraphs.append("".join(paragraph_part(child) for child in element))
    return "\n".join(paragraphs)


def _project_cell(cell) -> dict[str, str]:
    """Only recognized per-cell rendering limits become explicit markers."""
    try:
        return {"status": "supported", "text": _cell_text(cell)}
    except CellRenderingUnsupported:
        return {"status": "unsupported", "reason": "unsupported_cell_rendering"}


def extract_docx_tables(raw: bytes) -> dict[str, Any]:
    """Reproduce the v2 projection from asset bytes, never from a filename."""
    if len(raw) > MAX_BYTES:
        raise SourceSelectionError("Source asset exceeds the bounded size")
    with ZipFile(BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise SourceSelectionError("Source DOCX has duplicate archive members")
        info = archive.getinfo("word/document.xml")
        if info.file_size > MAX_BYTES:
            raise SourceSelectionError("Source DOCX XML exceeds the bounded size")
        document = _xml(archive.read(info))
        styles = None
        if "word/styles.xml" in names:
            style_info = archive.getinfo("word/styles.xml")
            if style_info.file_size > MAX_BYTES:
                raise SourceSelectionError("Source DOCX styles exceed the bounded size")
            styles = _xml(archive.read(style_info))
    hidden = ".//w:vanish | .//w:webHidden | .//w:specVanish"
    revisions = ".//w:ins | .//w:del | .//w:moveFrom | .//w:moveTo | .//w:delText"
    # Fail closed even for unused hidden styles; this is not a Word renderer.
    if (document.xpath(hidden + " | " + revisions + " | .//w:numPr", namespaces=NS)
            or (styles is not None and styles.xpath(hidden, namespaces=NS))):
        raise SourceSelectionError("Source DOCX hidden, revised or numbered rendering is unsupported")
    body = document.find("w:body", NS)
    if body is None:
        raise SourceSelectionError("Source DOCX has no document body")
    direct_tables = body.findall("w:tbl", NS)
    if len(direct_tables) != len(document.findall(".//w:tbl", NS)):
        raise SourceSelectionError("Source DOCX nested or non-body tables are unsupported")
    if document.xpath(".//w:gridSpan | .//w:vMerge | .//w:hMerge", namespaces=NS):
        raise SourceSelectionError("Source DOCX merged cells are unsupported")
    namespace = "{" + NS["w"] + "}"
    for table in direct_tables:
        if any(node.tag not in {namespace + name for name in ("tblPr", "tblGrid", "tr")} for node in table):
            raise SourceSelectionError("Source DOCX row alignment is unsupported")
        for row in table.findall("w:tr", NS):
            if any(node.tag not in {namespace + "trPr", namespace + "tc"} for node in row):
                raise SourceSelectionError("Source DOCX cell alignment is unsupported")
    tables = [
        [[_project_cell(cell)
          for cell in row.findall("w:tc", NS)] for row in table.findall("w:tr", NS)]
        for table in direct_tables
    ]
    return {"format": FORMAT, "asset_sha256": sha256(raw).hexdigest(), "tables": tables}


def _no_symlinks(path: Path) -> None:
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise SourceSelectionError("Source paths must not contain symlinks")


def _capture(path: Path, captured: dict[Path, bytes]) -> bytes:
    _no_symlinks(path)
    if path not in captured:
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise SourceSelectionError("Source path is missing, not a file, or too large")
        raw = path.read_bytes()
        if len(raw) > MAX_BYTES:
            raise SourceSelectionError("Source file exceeds the bounded size")
        captured[path] = raw
    return captured[path]


def _contained(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in name
            or relative.as_posix() != name or name in {"", "."}):
        raise SourceSelectionError("Source paths must be normalized contained relative paths")
    path = root / name
    _no_symlinks(path)
    if not path.resolve().is_relative_to(root):
        raise SourceSelectionError("Source path escapes its catalog directory")
    return path


@dataclass
class SelectedSource:
    """One captured cell plus its complete source identity and snapshot."""

    text: str
    identity: dict[str, Any]
    captured: dict[Path, bytes]
    reference_title: str | None = None

    def verify_unchanged(self) -> None:
        """Cooperative drift guard before a validation result is returned."""
        for path, raw in self.captured.items():
            _no_symlinks(path)
            if path.read_bytes() != raw:
                raise SourceSelectionError("Selected source changed during validation")


def select_source(
    reference: str,
    locator_value: Any,
    catalog_path: Path | None,
    normalize_reference: Callable[[str], str],
) -> SelectedSource:
    """Read, identify and replay exactly one source; no implicit source cache.

    Every invocation captures its own bytes, including repeated calls for the
    same PMID. Thus a prior article or another asset's memory cache cannot
    satisfy this route. The result identity includes the entire selection.
    """
    try:
        locator = SourceLocator.model_validate(locator_value)
        if catalog_path is None:
            raise SourceSelectionError("Explicit source locator requires a source catalog")
        path = Path(catalog_path).absolute()
        captured: dict[Path, bytes] = {}
        catalog_raw = _capture(path, captured)
        catalog = SourceCatalog.model_validate(_json(catalog_raw))
        parent = normalize_reference(reference)
        if not (parent.startswith("PMID:") or parent.startswith("DOI:")):
            raise SourceSelectionError("Supplement parents must be PMID or DOI references")
        entries: dict[tuple[str, str, str], SourceEntry] = {}
        for entry in catalog.sources:
            key = (normalize_reference(entry.reference), entry.asset_id, entry.version)
            if key in entries:
                raise SourceSelectionError("Duplicate source catalog identity")
            entries[key] = entry
        wanted = (parent, locator.asset_id, locator.version)
        if wanted not in entries:
            raise SourceSelectionError("Requested source parent/asset/version is not catalogued")
        selected = entries[wanted]
        asset_path = _contained(path.parent, selected.asset_path)
        extraction_path = _contained(path.parent, selected.extraction_path)
        asset = _capture(asset_path, captured)
        extraction = _capture(extraction_path, captured)
        if sha256(asset).hexdigest() != selected.asset_sha256:
            raise SourceSelectionError("Source asset hash mismatch")
        if sha256(extraction).hexdigest() != selected.extraction_sha256:
            raise SourceSelectionError("Source extraction hash mismatch")
        projection = TableProjection.model_validate(_json(extraction))
        if projection.model_dump() != extract_docx_tables(asset):
            raise SourceSelectionError("Source extraction does not replay from the bound asset")
        try:
            cell = projection.tables[locator.table - 1][locator.row - 1][locator.cell - 1]
        except IndexError as exc:
            raise SourceSelectionError("Source table/row/cell does not exist") from exc
        if not isinstance(cell, SupportedCell):
            raise SourceSelectionError("Selected source cell rendering is unsupported")
        text = cell.text
        if not text.strip():
            raise SourceSelectionError("Selected source cell is blank")
        identity = {
            "reference": parent, "asset_id": locator.asset_id, "version": locator.version,
            "asset_sha256": selected.asset_sha256, "extraction_sha256": selected.extraction_sha256,
            "catalog_sha256": sha256(catalog_raw).hexdigest(), "extractor": FORMAT,
            "locator": locator.model_dump(), "selected_sha256": sha256(text.encode()).hexdigest(),
        }
        result = SelectedSource(text, identity, captured, selected.reference_title)
        result.verify_unchanged()
        return result
    except (OSError, UnicodeError, ValueError, KeyError, BadZipFile, etree.XMLSyntaxError) as exc:
        if isinstance(exc, SourceSelectionError):
            raise
        # Decode, schema, archive and filesystem errors are input failures,
        # never a reason to try the main article or a different asset.
        raise SourceSelectionError(f"Invalid selected source: {exc}") from exc
