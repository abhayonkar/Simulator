Django GasSim - packaged minimal scaffold

This ZIP contains a minimal Django scaffold and simulator service scripts.
Run the following (recommended inside a virtualenv):

1) Install requirements:
   pip install -r requirements.txt

2) Import sample XML:
   python manage.py import_gaslib inputs/compressors.xml --outdir media/runs/run_001

3) Run the python-based transient sim:
   python -c "from simulator.services.simple_sim import run_sim_cli; run_sim_cli('media/runs/run_001', duration=600, dt=1)"

Outputs will be written to media/runs/run_001/ as CSV and MAT files.
