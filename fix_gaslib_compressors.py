#!/usr/bin/env python3
"""
fix_gaslib_compressors.py

Fill missing required coefficient elements for GasLib CompressorStations XML
so that xmlschema validation passes. Writes a new file with suffix _fixed.xml.

WARNING: This inserts placeholder numeric values ("0"). These are NOT physical
values — replace them with the correct coefficients for real simulations.
"""

import sys
import os
from lxml import etree

CS_NS = "http://gaslib.zib.de/CompressorStations"
NSMAP = {None: CS_NS}  # default namespace when writing

# Elements in the order expected by the XSD inside turboCompressor
TURBO_EXPECTED = []
# n_isoline_coeff_1..9
TURBO_EXPECTED += [f"n_isoline_coeff_{i}" for i in range(1,10)]
# eta_ad_isoline_coeff_1..9
TURBO_EXPECTED += [f"eta_ad_isoline_coeff_{i}" for i in range(1,10)]
# surgeline_coeff_1..3
TURBO_EXPECTED += [f"surgeline_coeff_{i}" for i in range(1,4)]
# chokeline_coeff_1..3
TURBO_EXPECTED += [f"chokeline_coeff_{i}" for i in range(1,4)]

# gasTurbine expected sequence (as in schema): energy_rate_fun_coeff_1..3 then power_fun_coeff_1..9
GASTURBINE_EXPECTED = [f"energy_rate_fun_coeff_{i}" for i in range(1,4)]
GASTURBINE_EXPECTED += [f"power_fun_coeff_{i}" for i in range(1,10)]

def qname(tag):
    return f"{{{CS_NS}}}{tag}"

def find_child_by_local(parent, localname):
    for c in parent:
        if etree.QName(c).localname == localname:
            return c
    return None

def ensure_children_in_order(parent, expected_list, keep_prefix_order_after=None):
    """
    Rebuild parent's children so that:
    - if speedMin/speedMax exist, keep them first (in that order),
    - then all expected_list elements in the sequence defined,
    - then any remaining other children appended after.
    For each expected child missing, create with attribute value="0".
    Returns list of added element names.
    """
    added = []
    # collect existing children into dict by localname
    existing = {etree.QName(c).localname: c for c in parent}
    # build new children list
    new_children = []

    # Keep speedMin and speedMax if present (schema has them before coeffs)
    for nm in ("speedMin", "speedMax"):
        if nm in existing:
            new_children.append(existing[nm])
            existing.pop(nm)

    # Add expected sequence (use existing if present else create)
    for tag in expected_list:
        if tag in existing:
            new_children.append(existing[tag])
            existing.pop(tag)
        else:
            el = etree.Element(qname(tag), nsmap=NSMAP)
            el.set("value", "0")
            # some coeffs might not require a 'unit' attribute; we keep minimal
            new_children.append(el)
            added.append(tag)

    # Append any remaining existing children (preserve them)
    for c_local, c_elem in existing.items():
        new_children.append(c_elem)

    # remove all original children and append new_children in order
    for c in list(parent):
        parent.remove(c)
    for c in new_children:
        parent.append(c)

    return added

def process_file(inpath, outpath):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(inpath, parser)
    root = tree.getroot()

    total_added = []
    # find all turboCompressor elements
    for turbo in root.findall(".//{%s}turboCompressor" % CS_NS):
        added = ensure_children_in_order(turbo, TURBO_EXPECTED)
        if added:
            total_added.append(("turboCompressor", turbo.get("id"), added))

    # find all gasTurbine elements
    for gt in root.findall(".//{%s}gasTurbine" % CS_NS):
        added = ensure_children_in_order(gt, GASTURBINE_EXPECTED)
        if added:
            total_added.append(("gasTurbine", gt.get("id"), added))

    # write out fixed XML
    tree.write(outpath, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return total_added

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_gaslib_compressors.py INPUT_XML [OUTPUT_XML]")
        sys.exit(1)
    inp = sys.argv[1]
    if len(sys.argv) >= 3:
        outp = sys.argv[2]
    else:
        base, ext = os.path.splitext(inp)
        outp = base + "_fixed" + ext

    added = process_file(inp, outp)
    print("Wrote fixed XML to:", outp)
    if not added:
        print("No additions were necessary.")
    else:
        print("Added the following missing elements (placeholders value='0'):")
        for kind, idv, elems in added:
            print(f" - {kind} id={idv}: {len(elems)} elements added -> {elems}")

if __name__ == "__main__":
    main()
