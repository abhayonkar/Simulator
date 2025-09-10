import os, json, numpy as np
import pandas as pd
from scipy.io import savemat

# Physical constants
R_specific = 519.6  # J/(kg K) ~ methane
T_ref = 288.15  # K

def default_pipe_props():
    return {'length_m': 10000.0, 'diameter_m': 0.5, 'roughness': 0.0001, 'area_m2': np.pi*(0.5/2)**2}

def compute_flow_from_dp(dp_pa, rho, pipe):
    # Use Darcy-Weisbach pressure drop approximation to compute velocity v from dp:
    # dp = f*(L/D)*(rho * v^2 / 2)  => v = sqrt( 2*dp / (rho * f * L/D) )
    # If dp negative, take absolute and keep sign.
    f = 0.01  # assume friction factor (could be function of Re; keep fixed for simplicity)
    L = pipe['length_m']
    D = pipe['diameter_m']
    A = pipe['area_m2']
    K = f * (L / D)
    # prevent division by zero and negative/zero density
    rho = max(rho, 1e-6)
    dp = dp_pa
    sign = 1.0 if dp >= 0 else -1.0
    v = np.sqrt(2.0 * abs(dp) / (rho * K) + 0.0)
    Q = A * v * sign  # volumetric flow m3/s
    return Q

def run_simulation(config_json_path, boundary_csv_path, outdir, duration=600, dt=1.0):
    os.makedirs(outdir, exist_ok=True)
    with open(config_json_path,'r') as f:
        cfg = json.load(f)
    # Build a simple linear network connecting compressor stations
    stations = cfg.get('compressorStations', [])
    n_nodes = max(2, len(stations) + 1)
    # Node volumes (m3) - assume each node represents a pipe segment
    node_volume = 1000.0
    # initial pressures (Pa) - start from 50 bar
    p0_bar = 50.0
    p = np.ones(n_nodes) * p0_bar * 1e5  # convert bar->Pa
    # read boundary conditions
    bc = pd.read_csv(boundary_csv_path)
    tvec = bc['time_s'].values
    # prepare pipe props between nodes i->i+1
    pipes = [default_pipe_props() for _ in range(n_nodes-1)]
    # records
    records = []
    # simulation loop
    for idx, t in enumerate(tvec):
        # determine compressor speed fraction (apply to compressors by index)
        speed_frac = bc['comp_speed_frac'].iloc[idx] if 'comp_speed_frac' in bc.columns else 1.0
        # compute flows on edges based on dp between nodes
        Qs = np.zeros(n_nodes-1)
        for i in range(n_nodes-1):
            dp = p[i] - p[i+1]
            # take average density
            rho_avg = 0.5 * (p[i]/(R_specific*T_ref) + p[i+1]/(R_specific*T_ref))
            Qs[i] = compute_flow_from_dp(dp, rho_avg, pipes[i])
        # incorporate compressor boosts: for each compressor station, apply simple pressure boost proportional to speed_frac
        # We assume station i is at node i+1 (1-based). We'll boost downstream node pressure slightly.
        for i, st in enumerate(stations):
            node_idx = min(n_nodes-1, i+1)
            # nominal speed not used directly — apply a small boost (e.g., +2% * speed_frac)
            boost_ratio = 1.0 + 0.02 * (speed_frac - 0.9)  # small effect
            p[node_idx] = p[node_idx] * boost_ratio
        # compute mass flows and update node masses
        rho = p / (R_specific * T_ref)
        m = rho * node_volume
        dm_dt = np.zeros_like(m)
        # mass flow from left to right edges: mass flow = rho_edge * Q_vol
        for i in range(n_nodes-1):
            rho_edge = max(1e-6, 0.5*(rho[i] + rho[i+1]))
            mass_flow = rho_edge * Qs[i]
            # left node loses mass (outflow), right node gains
            dm_dt[i] -= mass_flow / 1.0
            dm_dt[i+1] += mass_flow / 1.0
        # apply boundary inlet/outlet mass flows from boundary CSV (convert p_bar to Pa)
        # Let's take p_in_bar and p_out_bar and create small source/sink proportional to pressure difference
        p_in_bar = bc['p_in_bar'].iloc[idx] if 'p_in_bar' in bc.columns else 50.0
        p_out_bar = bc['p_out_bar'].iloc[idx] if 'p_out_bar' in bc.columns else 48.0
        p_in_pa = p_in_bar * 1e5
        p_out_pa = p_out_bar * 1e5
        # simple boundary flows: inlet injects if p_in > node0, outlet draws if nodeN > p_out
        K_boundary = 1e6
        Q_in = compute_flow_from_dp(p_in_pa - p[0], rho[0], {'length_m':1000,'diameter_m':0.3,'area_m2':np.pi*(0.3/2)**2})
        Q_out = compute_flow_from_dp(p[n_nodes-1] - p_out_pa, rho[-1], {'length_m':1000,'diameter_m':0.3,'area_m2':np.pi*(0.3/2)**2})
        dm_dt[0] += rho[0] * Q_in
        dm_dt[-1] -= rho[-1] * Q_out
        # integrate masses
        m_new = m + dm_dt * dt
        # prevent negative
        m_new = np.maximum(m_new, 1e-6)
        rho_new = m_new / node_volume
        p = rho_new * R_specific * T_ref
        # record per-node pressure (bar), temp (K), flow on edges (m3/s)
        rec = {'time_s': float(t)}
        for ni in range(n_nodes):
            rec[f'node_{ni}_p_bar'] = float(p[ni]/1e5)
            rec[f'node_{ni}_T_K'] = float(T_ref)
        for ei in range(n_nodes-1):
            rec[f'edge_{ei}_q_m3s'] = float(Qs[ei])
        records.append(rec)
    df = pd.DataFrame.from_records(records)
    csv_out = os.path.join(outdir, 'outputs.csv')
    df.to_csv(csv_out, index=False)
    try:
        savemat(os.path.join(outdir,'outputs.mat'), {'records': df.to_dict(orient='list')})
    except Exception:
        pass
    # also write a small summary
    with open(os.path.join(outdir,'sim_meta.json'),'w') as f:
        json.dump({'n_nodes': n_nodes, 'n_steps': len(tvec), 'dt': float(dt)}, f, indent=2)
    return csv_out

def run_sim_cli(outdir, duration=600, dt=1.0):
    # helper expecting config.json and boundary_conditions.csv in outdir
    cfg = os.path.join(outdir, 'config.json')
    bc = os.path.join(outdir, 'boundary_conditions.csv')
    if not os.path.exists(cfg) or not os.path.exists(bc):
        raise FileNotFoundError('Need config.json and boundary_conditions.csv in ' + outdir)
    return run_simulation(cfg, bc, outdir, duration=duration, dt=dt)
