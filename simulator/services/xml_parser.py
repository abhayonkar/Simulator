import os
import json
from lxml import etree

NS = {'g':'http://gaslib.zib.de/CompressorStations'}

def validate_xml_against_xsd(xml_path, xsd_url=None):
    # Try to download XSD if URL provided, else skip.
    try:
        if xsd_url:
            import requests
            r = requests.get(xsd_url, timeout=6)
            if r.status_code == 200:
                xsd_doc = etree.XML(r.content)
                xml_doc = etree.parse(xml_path)
                schema = etree.XMLSchema(xsd_doc)
                schema.assertValid(xml_doc)
                return True, 'XML validated against remote XSD.'
            else:
                return False, 'Could not download XSD (status %s). Skipping strict validation.' % r.status_code
        else:
            return False, 'No XSD URL provided, skipped.'
    except Exception as e:
        return False, 'Validation skipped / failed: %s' % str(e)

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
