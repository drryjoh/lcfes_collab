# H2 Detonation #
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "SDToolbox", "Python3"))

import cantera as ct
import matplotlib.pyplot as plt

from sdtoolbox.postshock import CJspeed, PostShock_eq, PostShock_fr
from sdtoolbox.znd import zndsolve


# ------------------
# Initial Conditions
# ------------------

T1 = 300.0          # K
P1 = ct.one_atm     # Pa
phi = 0.5

mech = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffcm2_h2.yaml") # H2 submechanism from FFCM2

# Lean H2-air at phi = 0.5
q = 'H2:1 O2:1 N2:3.76'

# ---------------------
# Check initial mixture
# ---------------------

gas1 = ct.Solution(mech); #sets gas1 to the solution mechanism
gas1.TPX = T1,P1,q  #sets the temp, pressure, and composition

# ------------------------------------------
# Calculate Chapman-Jouguet detonation speed
# ------------------------------------------

cj_speed = CJspeed(P1, T1, q, mech)

# --------------------------------------
# Calculate equilibrium CJ product state
# --------------------------------------

gas_cj = PostShock_eq(cj_speed, P1, T1, q, mech)

# -------------
# Print results
# -------------

print("\nCJ detonation")
print("-------------")
print(f"CJ speed = {cj_speed:.2f} m/s")
#print(f"CJ pressure = {gas_cj.P/1e5:.3f} bar") #converts Pa to bar for display
#print(f"CJ temperature = {gas_cj.T:.1f} K")
#print(f"CJ density = {gas_cj.density:.4f} kg/m^3")

# ---------------------------------------------
# Frozen state immediately behind leading shock
# ---------------------------------------------

gas_shock = PostShock_fr(cj_speed, P1, T1, q, mech)

# -----------------------
# Integrate ZND equations
# -----------------------

znd = zndsolve(gas_shock, gas1, cj_speed, t_end=5.0e-5, advanced_output=True)

# ---------------
# Extract results
# ---------------

x = znd["distance"]
T = znd["T"]
P = znd["P"]
h2_index = gas1.species_index("H2")
Y_H2 = znd["species"][h2_index, :]

# -----------------------
# Print useful quantities
# -----------------------

print("\nZND structure")
print("-------------")

if "ind_len_ZND" in znd:
    print(f"Induction length = " f"{znd['ind_len_ZND']:.6e} m")

if "ind_time_ZND" in znd:
    print(f"Induction time = " f"{znd['ind_time_ZND']:.6e} s")

if "exo_len_ZND" in znd:
    print(f"Exothermic length = " f"{znd['exo_len_ZND']:.6e} m")

# ----------------
# Plot temperature
# ----------------

plt.figure()

plt.plot(x * 1000.0, T)

plt.xlabel("Distance behind shock [mm]")
plt.ylabel("Temperature [K]")

plt.tight_layout()
#plt.savefig("znd_temperature.png", dpi=300)

# ------------------------
# Plot H2 mass fraction
# ------------------------

plt.figure()
plt.plot(x * 1000.0, Y_H2)

plt.xlabel("Distance behind shock [mm]")
plt.ylabel("H2 mass fraction [-]")

plt.tight_layout()
#plt.savefig("znd_H2.png", dpi=300)

plt.show()