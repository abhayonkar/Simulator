# simulator/management/commands/import_gaslib.py
from django.core.management.base import BaseCommand
import os
from simulator.services.xml_parser import validate_xml_against_xsd, parse_compressor_stations, write_config_json, write_boundary_examples

class Command(BaseCommand):
    help = 'Import GasLib compressorStations XML, validate, and write config/boundary files'

    def add_arguments(self, parser):
        parser.add_argument('xmlpath', type=str, help='Path to compressors XML')
        parser.add_argument('--outdir', type=str, default='media/runs/run_001', help='Output directory')
        parser.add_argument('--xsd', type=str, default='http://gaslib.zib.de/schema/CompressorStations.xsd', help='XSD path or URL to use for validation')
        parser.add_argument('--local-schema-dir', type=str, default=None, help='Local directory containing GasLib XSDs (resolve imports locally)')
        parser.add_argument('--no-validate', action='store_true', help='Skip XSD validation entirely')

    def handle(self, *args, **options):
        xmlpath = options['xmlpath']
        outdir = options['outdir']
        xsd = options.get('xsd')
        local_schema_dir = options.get('local_schema_dir')
        no_validate = options.get('no_validate', False)

        os.makedirs(outdir, exist_ok=True)

        if not no_validate:
            print('Validating XML (best-effort)...')
            ok, msg = validate_xml_against_xsd(xmlpath, xsd_path_or_url=xsd, local_schema_dir=local_schema_dir)
            print(msg)
        else:
            print('Skipping XML validation (user requested --no-validate).')

        parsed = parse_compressor_stations(xmlpath)
        write_config_json(parsed, outdir)
        write_boundary_examples(outdir)
        print('Wrote config.json and example boundary files to', outdir)
