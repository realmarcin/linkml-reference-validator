"""Read retained DOCX content-control shapes for #1996/#2930, 2026-11-15.

Input: exact local DOCX. Output: structural tag/attribute patterns and counts;
no source text, source edits, acquisition or rendering.
"""

import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from lxml import etree


def shape(node):
    """Omit text and property values; preserve structural element identities."""
    return {"tag": etree.QName(node).localname,
            "attributes": sorted(etree.QName(name).localname for name in node.attrib),
            "children": [shape(child) for child in node]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", type=Path)
    args = parser.parse_args()
    raw = args.asset.read_bytes()
    with ZipFile(BytesIO(raw)) as archive:
        xml = archive.read("word/document.xml")
    document = etree.fromstring(xml, etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False))
    controls = document.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sdt")
    patterns = Counter(json.dumps(shape(node), sort_keys=True) for node in controls)
    if args.asset.read_bytes() != raw:
        raise ValueError("Source changed during inspection")
    print(json.dumps({"asset_sha256": sha256(raw).hexdigest(), "controls": len(controls),
                      "patterns": [{"count": count, "shape": json.loads(pattern)}
                                   for pattern, count in patterns.items()]}, indent=2))


if __name__ == "__main__":
    main()
