import matplotlib.pyplot as plt
import numpy as np

# !insert initial densities
E = 9.24e18  # Electron density
Ar = 1.4e23 # Argon groundstate density
Ar4s = 1.43e18 # Argon excited state density
Ar4p =  8.7e17 # Argon excited state density
Ar_ion =  9.24e18 # Argon positive ion density

# Electron temperature
Te = 5.4

def rate (A, B, C, D, T):
    return A* 10**(-B) * T**C * np.exp(-D/T)


def k1(Te):
    return 2.34e-14 * Te**0.59 * np.exp(-15.76 / Te)


def k2(Te):
    return rate(5.0, 15.0, 0.74, 11.56, Te)



def k3(Te):
    return  rate(4.3, 16.0, 0.74, 0, Te)



def k4(Te):
    return rate(1.4,14,0.71,13.2, Te)



def k5(Te):
    return rate(3.9, 16, 0.71, 0, Te )



def k6(Te):
    return rate(8.9, 13, 0.51, 1.59, Te)



def k7(Te):
    return  rate(3, 13, 0.51, 0 , Te)



# def k7(Te):
#     ...

def k8(Te):
    return rate(2.9, 14, 0.68, 15.759, Te)



# def k8(Te):
#     return 0

def k9(Te):
    return  rate(6.8, 15, 0.67, 4.2, Te)



# def k9(Te):
#     return 0

def k10(Te):
    return  rate(1.8, 13, 0.61, 2.61, Te)


# k10(Te) = 0


#################### Solving ###################################################
# Solve the ODE system
tspan = (0.0, 5e-8)
dt = 1e-12
n = [E, Ar, Ar4s, Ar4p, Ar_ion]  # inital densites as vector


def odesystem(n):  # n: Density vector
    E, Ar, Ar4s, Ar4p, Ar_ion = n  # Defines a variable for the different densities

    rates = [k1(Te),k2(Te),k3(Te),k4(Te),k5(Te),k6(Te),k7(Te),k8(Te),k9(Te),k10(Te)]
    reactants = [
        [E, Ar],  # R1
        [E, Ar],  # R2
        [E, Ar4s],  # R3
        [E, Ar],  # R4
        [E, Ar4p],  # R5
        [E, Ar4s],  # R6
        [E,Ar4p],  # R7
        [E, Ar],  # R8
        [E, Ar4s],  # R9
        [E, Ar4p]  # R10
    ]

    reaction_rates = [r * np.prod(reactant) for r, reactant in zip(rates, reactants)]
    R1, R2, R3, R4, R5, R6, R7, R8, R9, R10 = reaction_rates

    # !complete temporal derivatives for every density
    dEdt = + R8 + R9 + R10
    dArdt = -R2 +R3 -R4 +R5 - R8
    dAr4sdt = +R2 -R3 -R6 + R7 - R9
    dAr4pdt = +R4 -R5 + R6 - R7 - R10
    dAr_iondt =  + R8 + R9 + R10

    dn = np.array([dEdt, dArdt, dAr4sdt, dAr4pdt, dAr_iondt])  # temporal derivatives as vector
    return dn  # returns vector dn when function EulerExplicit() is called


# solve System with Euler Explicit
result = []  # empty array to save densities of each steps
trange = np.arange(tspan[0], tspan[1], dt)  # defines timerange from tspan[0] to tspan[1] in steps dt
# simulate every timestep in the following for loop
for t in trange:
    dn = odesystem(n)  # defines dn with function ODESystem
    result.append(n)  # saves previous densities in result
    n = n + dt * dn  # !insert the equation for one step of Euler Explicit

# Convert list of arrays to 2D NumPy array (shape: [timesteps, species])
nplot = np.vstack(result)

# Create x-axis: either use time values or just index
x = np.arange(nplot.shape[0])

# Plot each column (species) against x
plt.figure(figsize=(10, 6))

for i in range(nplot.shape[1]):
    plt.plot(x, nplot[:, i], label=f"Species {i + 1}")

# Labels and legend
plt.xlabel("Time step")
plt.ylabel("Density / $m^3$")
plt.legend()
plt.tight_layout()
plt.show()
