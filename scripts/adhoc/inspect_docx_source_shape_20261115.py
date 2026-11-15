"""Inspect retained DOCX structure without publishing source text, #1996/#2930.

Input: one local DOCX. Output: hash, structural tag counts and direct paragraph
children by one-based table/row/cell. No edits or extraction substitution.
Date: 2026-11-15.
"""

import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from lxml import etree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", type=Path)
    args = parser.parse_args()
    raw = args.asset.read_bytes()
    with ZipFile(BytesIO(raw)) as archive:
        xml = archive.read("word/document.xml")
    document = etree.fromstring(xml, etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    allowed = {"r", "pPr", "hyperlink", "bookmarkStart", "bookmarkEnd", "proofErr"}
    rows = []
    for table_index, table in enumerate(document.findall("w:body/w:tbl", ns), 1):
        for row_index, row in enumerate(table.findall("w:tr", ns), 1):
            for cell_index, cell in enumerate(row.findall("w:tc", ns), 1):
                children = Counter(etree.QName(child).localname
                                   for paragraph in cell.findall("w:p", ns) for child in paragraph)
                unknown = {name: count for name, count in children.items() if name not in allowed}
                if unknown:
                    rows.append({"table": table_index, "row": row_index, "cell": cell_index,
                                 "paragraph_children_outside_contract": unknown})
    if args.asset.read_bytes() != raw:
        raise ValueError("Source changed during structural inspection")
    print(json.dumps({"asset": str(args.asset), "sha256": sha256(raw).hexdigest(),
                      "all_element_counts": dict(Counter(etree.QName(node).localname for node in document.iter())),
                      "unsupported_paragraph_children": rows}, indent=2))


if __name__ == "__main__":
    main()
