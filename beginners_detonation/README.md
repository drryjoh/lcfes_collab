# Beginner's Detonation Example

A self-contained example computing the Chapman-Jouguet (CJ) detonation speed and
ZND detonation structure for a lean (φ = 0.5) H2-air mixture, using Caltech's
Shock and Detonation Toolbox (SDToolbox) with Cantera.

## Contents

- `h2_air_phi05_RFJ.py` — the main script (CJ speed, ZND integration, temperature and
  H2 mass fraction plots)
- `ffcm2_h2.yaml` — a 9-species H2-air chemical mechanism (extracted from FFCM2), used
  in place of the much larger `gri30.yaml` for speed (see "Troubleshooting" below)
- `SDToolbox/` — **not included in this repo** (see "Getting SDToolbox" below); this is
  where the toolbox needs to live for the script to import it
- `troubleshooting_notes_sierra.md` — notes on the bugs we hit while getting this
  script working and why each fix mattered

## Requirements

- Python 3
- [Cantera](https://cantera.org/) 3.0+ (`pip install cantera` or via conda)
- `matplotlib`

## Getting SDToolbox

SDToolbox isn't distributed through this repo (it's listed in `.gitignore` — it's a
large third-party toolbox, not our code). Download it yourself from Caltech's
Explosion Dynamics Laboratory:

- Toolbox + docs: http://shepherd.caltech.edu/EDL/PublicResources/sdt/
- Background reading: https://shepherd.caltech.edu/EDL/PublicResources/sdt/doc/ShockDetonation/ShockDetonation.pdf

Download it, unzip it, and place the resulting `SDToolbox` folder directly inside
this `beginners_detonation/` folder, so you end up with:

```
beginners_detonation/
├── SDToolbox/
│   └── Python3/
│       └── sdtoolbox/
├── ffcm2_h2.yaml
├── h2_air_phi05_RFJ.py
├── README.md
└── troubleshooting_notes_sierra.md
```

The script adds `SDToolbox/Python3` to `sys.path` at runtime (relative to its own
location), so as long as `SDToolbox` sits next to the script as shown above, no
manual `PYTHONPATH` setup or install step is needed.

## Running

From this folder (or anywhere — the script resolves paths relative to itself):

```
python3 h2_air_phi05_RFJ.py
```

This will print the CJ speed and ZND induction/exothermic length and time, then show
two plots: temperature and H2 mass fraction, both vs. distance behind the shock.

## Troubleshooting

This script went through a few rounds of debugging to get right — a missing-module
import path, an incorrect post-shock state feeding the ZND integration, a solver
singularity at large `t_end`, and a mechanism swap for performance. Full details and
the reasoning behind each fix are in
[`troubleshooting_notes_sierra.md`](troubleshooting_notes_sierra.md).
