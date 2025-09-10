from django.core.management.base import BaseCommand
import os
from simulator.services.xml_parser import validate_xml_against_xsd, parse_compressor_stations, write_config_json, write_boundary_examples

class Command(BaseCommand):
    help = 'Import GasLib compressorStations XML, validate, and write config/boundary files'

    def add_arguments(self, parser):
        parser.add_argument('xmlpath', type=str, help='Path to compressors XML')
        parser.add_argument('--outdir', type=str, default='media/runs/run_001', help='Output directory')

    def handle(self, *args, **options):
        xmlpath = options['xmlpath']
        outdir = options['outdir']
        os.makedirs(outdir, exist_ok=True)
        print('Validating XML (best-effort)...')
        xsd_url = 'http://gaslib.zib.de/schema/CompressorStations.xsd'
        ok, msg = validate_xml_against_xsd(xmlpath, xsd_url)
        print(msg)
        parsed = parse_compressor_stations(xmlpath)
        write_config_json(parsed, outdir)
        write_boundary_examples(outdir)
        print('Wrote config.json and example boundary files to', outdir)
