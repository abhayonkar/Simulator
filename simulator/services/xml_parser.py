import os
import json
from lxml import etree

NS = {'g':'http://gaslib.zib.de/CompressorStations'}

def validate_xml_against_xsd(xml_path, xsd_path_or_url=None, local_schema_dir=None, timeout=8):
    """
    Robust validation using xmlschema with local-schema fallback.

    Parameters
    ----------
    xml_path : str
        Path to XML file to validate.
    xsd_path_or_url : str or None
        Path or URL to the main XSD (e.g. 'schema_local/CompressorStations.xsd'
        or 'http://gaslib.zib.de/schema/CompressorStations.xsd').
    local_schema_dir : str or None
        If provided and exists, used as base_url for resolving includes/imports.
        e.g. '/home/user/gasim/schema_local'
    timeout : int
        Timeout (seconds) for remote downloads; only used when fetching remote XSDs.

    Returns
    -------
    (bool, str)
        (True, message) if validated, otherwise (False, message).
    """
    try:
        import xmlschema
    except Exception as e:
        return False, f"xmlschema library not installed: {e}"

    try:
        # prefer local schema directory (so xmlschema resolves relative schemaLocations)
        if local_schema_dir and os.path.isdir(local_schema_dir):
            # xsd_path_or_url may be relative: build absolute path
            if xsd_path_or_url:
                xsd_abs = os.path.abspath(xsd_path_or_url)
            else:
                # try default filename in local dir
                xsd_abs = os.path.join(local_schema_dir, 'CompressorStations.xsd')
            base = 'file:///' + os.path.abspath(local_schema_dir).rstrip('/') + '/'
            schema = xmlschema.XMLSchema(xsd_abs, base_url=base)
            schema.validate(xml_path)
            return True, "XML validated against local XSDs (xmlschema)."

        # else, if an xsd_path_or_url is provided, try using it (may be http(s))
        if xsd_path_or_url:
            # provide a downloader with timeout for remote fetches
            # xmlschema will use urllib under the hood; set a global socket timeout as a pragmatic fallback
            import socket
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout)
            try:
                schema = xmlschema.XMLSchema(xsd_path_or_url)
            finally:
                socket.setdefaulttimeout(old_timeout)
            schema.validate(xml_path)
            return True, "XML validated against remote XSD (xmlschema)."

        return False, "No XSD path/url or local_schema_dir provided; skipped validation."
    except xmlschema.XMLSchemaException as e:
        return False, f"Validation failed: {str(e)}"
    except Exception as e:
        # catch network timeouts, file not found, etc.
        return False, f"Validation error: {str(e)}"


def parse_compressor_stations(xml_path):
    tree = etree.parse(xml_path)
    root = tree.getroot()
    stations = []
    for cs in root.findall('g:compressorStation', NS):
        cs_id = cs.get('id')
        compressors = []
        for comp in cs.findall('.//g:turboCompressor', NS):
            comp_dict = {'id': comp.get('id'), 'drive': comp.get('drive')}
            speedMin = comp.find('g:speedMin', NS)
            if speedMin is not None:
                comp_dict['speedMin'] = float(speedMin.get('value'))
            speedMax = comp.find('g:speedMax', NS)
            if speedMax is not None:
                comp_dict['speedMax'] = float(speedMax.get('value'))
            # gather coefficients starting with n_isoline_coeff_...
            coeffs = {}
            for child in comp:
                tag = etree.QName(child.tag).localname
                if tag.endswith('_coeff_1') or 'coeff' in tag:
                    coeffs[tag] = float(child.get('value'))
            comp_dict['coeffs'] = coeffs
            compressors.append(comp_dict)
        # drives
        drives = []
        for d in cs.findall('.//g:gasTurbine', NS):
            d_id = d.get('id')
            coeffs = {}
            for child in d:
                tag = etree.QName(child.tag).localname
                coeffs[tag] = float(child.get('value'))
            drives.append({'id': d_id, 'coeffs': coeffs})
        stations.append({'id': cs_id, 'compressors': compressors, 'drives': drives})
    return {'compressorStations': stations}

def write_config_json(parsed, outdir):
    path = os.path.join(outdir, 'config.json')
    with open(path, 'w') as f:
        json.dump(parsed, f, indent=2)
    return path

def write_boundary_examples(outdir, duration=600, dt=1):
    # produce per-second example boundary conditions suitable for Simulink or Python sim
    import numpy as np
    import pandas as pd
    t = np.arange(0, duration+dt, dt)
    # example inlet pressure (bar), outlet pressure (bar), flows (m3/s), compressor speed (% of nominal)
    p_in = 50 + 2*np.sin(2*3.1415*(t/300))  # bar-ish signal
    p_out = 48 + 1.5*np.cos(2*3.1415*(t/400))
    q = 100*np.ones_like(t) * 0.01  # m3/s small constant
    # compressor speed schedule: linear ramp 0.8 -> 1.0
    speed_frac = 0.8 + 0.2*(t.max()>0 and (t/t.max()))
    df = pd.DataFrame({'time_s': t, 'p_in_bar': p_in, 'p_out_bar': p_out, 'q_m3s': q, 'comp_speed_frac': speed_frac})
    csvp = os.path.join(outdir, 'boundary_conditions.csv')
    df.to_csv(csvp, index=False)
    # save MAT
    try:
        from scipy.io import savemat
        savemat(os.path.join(outdir, 'boundary_conditions.mat'), {'time_s': t, 'p_in_bar': p_in, 'p_out_bar': p_out, 'q_m3s': q, 'comp_speed_frac': speed_frac})
    except Exception:
        pass
    return csvp
