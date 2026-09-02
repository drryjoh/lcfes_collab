# Troubleshooting notes: `h2_air_phi05_RFJ.py`

Notes for Sierra on what changed in the H2-air detonation script, and why each change mattered.

## 1. `ModuleNotFoundError: No module named 'sdtoolbox'`

The script imports from `sdtoolbox`, but that package isn't installed — it lives locally in
`SDToolbox/Python3/sdtoolbox/`. Python doesn't know to look there unless we tell it.

**Fix:** add the folder to `sys.path` before the `sdtoolbox` imports:

```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "SDToolbox", "Python3"))
```

Using `os.path.dirname(os.path.abspath(__file__))` (the script's own folder) instead of a hardcoded
path means this works no matter what directory you run the script from.

## 2. Added a second plot: H2 mass fraction vs. distance

`zndsolve(..., advanced_output=True)` returns a `species` array (mass fraction of every species
at every integration step). We pull out the H2 row and plot it alongside temperature:

```python
h2_index = gas1.species_index("H2")
Y_H2 = znd["species"][h2_index, :]
```

## 3. "H2 is unusually small" — actually two separate things, not a bug (at first)

- `znd["species"]` stores **mass fraction**, not mole fraction. H2 is very light (2 g/mol) next to
  N2/O2 (~28-32 g/mol), so even in the *unburned* mixture, `Y_H2` is only ~1.4%, even though its
  mole fraction is ~17%.
- The mixture is lean (φ = 0.5), so H2 is the limiting reactant and gets consumed as you move
  through the reaction zone — `Y_H2` dropping toward 0 downstream is expected.

This explained why the *shape* of the curve looked right, but not why the *starting value* was
wrong (see next section).

## 4. Real bug: ZND integration started from the wrong post-shock state

This was the important one. The script computed:

```python
gas_shock = PostShock_eq(cj_speed, P1, T1, q, mech)
znd = zndsolve(gas_shock, gas1, cj_speed, ...)
```

`PostShock_eq` gives the **equilibrium** (fully-burned) state behind the shock — i.e., H2 already
almost entirely consumed. Feeding that into `zndsolve` as the *starting point* of the reaction-zone
integration meant the ZND profile started with H2 already reacted away, showing `Y_H2 ≈ 1e-5` at
`x = 0` instead of the expected `≈ 0.0144`.

The correct input is the **frozen** post-shock state — compressed and heated by the shock, but not
yet chemically reacted — which is what the reaction-zone integration is supposed to react *from*.
Confirmed this against the official SDToolbox demos (`demo_ZNDCJ.py`, `demo_ZND_CJ_CV.py`), which
use `PostShock_fr` for exactly this purpose and reserve `PostShock_eq` only for reporting the final
CJ product state.

**Fix:**

```python
gas_shock = PostShock_fr(cj_speed, P1, T1, q, mech)   # was PostShock_eq
```

After this fix, `Y_H2` at `x = 0` correctly matched the hand-calculated initial mass fraction
(≈ 0.0144).

## 5. `t_end` and the ZND "sonic singularity"

Increasing `t_end` to give the reaction more room caused `lsoda` to get stuck (repeated
"internal t and h" warnings, step size collapsing to ~1e-20) and take forever, or in one case
crash outright when interrupted with Ctrl+C mid-solve.

This isn't a tolerance bug to "fix" — the steady ZND model has a genuine mathematical singularity
at the CJ (sonic) point: as the flow approaches sonic velocity relative to the detonation wave,
`1 - M²  → 0` in the denominator of the governing ODEs, so derivatives blow up and the solver's
step size has to shrink to keep up. `zndsolve` doesn't stop automatically at that point, so pushing
`t_end` past where the reaction has effectively completed just makes the solver spin.

Ctrl+C during that spin is its own separate problem: interrupting `lsoda` mid-callback corrupts
scipy's f2py thread-local state, producing a `Fatal Python error` — unrelated to the tolerance
issue, just don't interrupt a solver mid-call.

**Fix:** picked `t_end = 5.0e-5` s, which comfortably covers the induction + exothermic zones
without running into the singularity.

## 6. Mechanism swap: `gri30.yaml` → `ffcm2_h2.yaml`

The script was using `gri30.yaml`, a general-purpose 53-species mechanism built for methane/natural
gas combustion. For a pure H2-air problem, this is way more chemistry than needed — most of those
species and reactions are irrelevant to H2 combustion, and Cantera still has to evaluate all of them
at every integration step. That's the "performance issue" we were seeing: CJ speed + ZND integration
was noticeably slower than it needed to be, and it likely contributed to how easily we could nudge
the solver into the slow/stuck sonic-singularity behavior above.

Switched to `ffcm2_h2.yaml` — a 9-species H2 submechanism (H, H2, O, O2, OH, H2O, HO2, H2O2, N2)
extracted from FFCM2, pulled from
[drryjoh/chemgen](https://github.com/drryjoh/chemgen/blob/main/chemical_mechanisms/ffcm2_h2.yaml)
and saved locally as `ffcm2_h2.yaml`. Same physics for this problem, far fewer species/reactions to
evaluate per step — runs noticeably faster with no loss of accuracy for H2-air combustion.

```python
mech = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffcm2_h2.yaml")
```

Verified end-to-end after the swap: CJ speed = 1618.37 m/s, induction length = 4.81 mm, induction
time = 14.9 μs, exothermic length = 0.143 mm, and `Y_H2` at `x = 0` still correctly starts at
≈ 0.01447.

## Summary

| Issue | Root cause | Fix |
|---|---|---|
| `ModuleNotFoundError` | `sdtoolbox` not on `sys.path` | Add `SDToolbox/Python3` to `sys.path` relative to the script |
| H2 mass fraction looked tiny | Mass fraction (not mole fraction) of a light species, in a lean mixture | Expected behavior, not a bug — just needed to know which unit we were looking at |
| H2 started at ~1e-5 instead of ~0.0144 | ZND integration started from the **equilibrium** post-shock state instead of the **frozen** one | `PostShock_eq` → `PostShock_fr` for the ZND input |
| Solver hangs / crashes at large `t_end` | ZND equations are singular at the CJ (sonic) point; `zndsolve` doesn't stop there automatically | Chose `t_end` that covers the reaction zone without overshooting into the singularity |
| Slow overall runtime | `gri30.yaml` carries ~53 species irrelevant to H2 combustion | Swapped to the 9-species `ffcm2_h2.yaml` H2 submechanism |
