# ======================================================================
# ARGON PLASMA KINETICS SIMULATION
# 
# Purpose: Simulates time evolution of species densities in argon plasma
#          using a 0D collisional-radiative model with 10 key reactions
#
# Model Features:
# - Tracks 5 species: e⁻, Ar, Ar(4s), Ar(4p), Ar⁺
# - Constant electron temperature (Te = 5.4 eV)
# - Explicit Euler integration (Δt = 1 ps, tₘₐₓ = 50 ns)
# - Includes excitation, de-excitation, and ionization processes
#
# Author: [Your Name]
# Date: [YYYY-MM-DD]
# Requires: Julia 1.6+, Plots.jl, GR backend
# ======================================================================

using Plots
gr()  # Using GR backend for faster plotting

# =============================
# PHYSICAL CONSTANTS AND INITIAL CONDITIONS
# =============================

# Initial number densities [m⁻³]
n₀ = Float64[
    9.24e18,    # Electrons (e⁻)
    1.4e23,     # Argon ground state (Ar)
    1.43e18,    # Argon 4s excited state (Ar4s)
    8.7e17,     # Argon 4p excited state (Ar4p)
    9.24e18     # Argon ions (Ar⁺)
]

const Te = 5.4  # Electron temperature [eV] (constant in this model)

# =============================
# REACTION RATE CALCULATIONS
# =============================

"""
    calculate_rate(A, B, C, D, T)
Calculate Arrhenius-type reaction rate coefficient.

Parameters:
- A: Pre-exponential factor [m³/s]
- B: Scaling exponent (base 10)
- C: Temperature exponent
- D: Activation energy [eV]
- T: Electron temperature [eV]

Returns rate coefficient in [m³/s]
"""
function calculate_rate(A, B, C, D, T)
    return A * (10.0^-B) * (T^C) * exp(-D/T)
end

# =============================
# ODE SYSTEM: DENSITY EVOLUTION
# =============================

"""
    density_derivatives(n, Te)
Calculate time derivatives of all species densities.

Parameters:
- n: Current densities [e⁻, Ar, Ar4s, Ar4p, Ar⁺] in [m⁻³]
- Te: Electron temperature [eV]

Returns array of time derivatives [dn/dt for each species]
"""
function density_derivatives(n, Te)
    e⁻, Ar, Ar4s, Ar4p, Ar⁺ = n  # Unpack variables for clarity
    
    # -------------------------------------------------
    # REACTION RATE COEFFICIENTS (m³/s)
    # -------------------------------------------------
    # Format: kₙ = process description
    k₁ = 2.34e-14 * Te^0.59 * exp(-15.76 / Te)  # e⁻ + Ar → e⁻ + Ar(4s)
    k₂ = calculate_rate(5.0, 15.0, 0.74, 11.56, Te)  # e⁻ + Ar → 2e⁻ + Ar⁺ (direct ionization)
    k₃ = calculate_rate(4.3, 16.0, 0.74, 0.0, Te)    # e⁻ + Ar(4s) → e⁻ + Ar (de-excitation)
    k₄ = calculate_rate(1.4, 14.0, 0.71, 13.2, Te)   # e⁻ + Ar → e⁻ + Ar(4p)
    k₅ = calculate_rate(3.9, 16.0, 0.71, 0.0, Te)    # e⁻ + Ar(4p) → e⁻ + Ar (de-excitation)
    k₆ = calculate_rate(8.9, 13.0, 0.51, 1.59, Te)   # e⁻ + Ar(4s) → e⁻ + Ar(4p) (excitation)
    k₇ = calculate_rate(3.0, 13.0, 0.51, 0.0, Te)    # e⁻ + Ar(4p) → e⁻ + Ar(4s) (de-excitation)
    k₈ = calculate_rate(2.9, 14.0, 0.68, 15.759, Te) # e⁻ + Ar → 2e⁻ + Ar⁺ (ionization from ground state)
    k₉ = calculate_rate(6.8, 15.0, 0.67, 4.2, Te)    # e⁻ + Ar(4s) → 2e⁻ + Ar⁺ (stepwise ionization)
    k₁₀ = calculate_rate(1.8, 13.0, 0.61, 2.61, Te)  # e⁻ + Ar(4p) → 2e⁻ + Ar⁺ (stepwise ionization)
    
    # -------------------------------------------------
    # REACTION RATES (m⁻³s⁻¹)
    # -------------------------------------------------
    R₁ = k₁ * e⁻ * Ar
    R₂ = k₂ * e⁻ * Ar
    R₃ = k₃ * e⁻ * Ar4s
    R₄ = k₄ * e⁻ * Ar
    R₅ = k₅ * e⁻ * Ar4p
    R₆ = k₆ * e⁻ * Ar4s
    R₇ = k₇ * e⁻ * Ar4p
    R₈ = k₈ * e⁻ * Ar
    R₉ = k₉ * e⁻ * Ar4s
    R₁₀ = k₁₀ * e⁻ * Ar4p
    
    # -------------------------------------------------
    # SPECIES BALANCE EQUATIONS
    # -------------------------------------------------
    # Electrons: Production from all ionization processes
    de⁻_dt = R₈ + R₉ + R₁₀
    
    # Argon ground state: Loss to excitation/ionization, gain from de-excitation
    dAr_dt = -R₂ + R₃ - R₄ + R₅ - R₈
    
    # Ar(4s): Balance of excitation/de-excitation processes
    dAr4s_dt = R₂ - R₃ - R₆ + R₇ - R₉
    
    # Ar(4p): Similar to 4s but with different pathways
    dAr4p_dt = R₄ - R₅ + R₆ - R₇ - R₁₀
    
    # Argon ions: Sum of all ionization processes
    dAr⁺_dt = R₈ + R₉ + R₁₀
    
    return [de⁻_dt, dAr_dt, dAr4s_dt, dAr4p_dt, dAr⁺_dt]
end

# =============================
# SIMULATION PARAMETERS
# =============================
t_span = (0.0, 5e-8)  # Simulation time range [s] (0 to 50 ns)
Δt = 1e-12             # Time step [s] (1 ps)
n_steps = Int((t_span[2] - t_span[1]) / Δt) + 1

# Initialize results array
density_results = zeros(Float64, 5, n_steps)
density_results[:, 1] .= n₀  # Set initial conditions

# =============================
# TIME INTEGRATION (EULER METHOD)
# =============================
for i in 1:n_steps-1
    # Calculate derivatives at current time step
    derivatives = density_derivatives(density_results[:, i], Te)
    
    # Update densities
    density_results[:, i+1] .= density_results[:, i] .+ Δt .* derivatives
end

# =============================
# VISUALIZATION
# =============================
time_axis = range(t_span[1], t_span[2], length=n_steps)

# Create plot with linear y-scale
plot(time_axis, density_results',
    title="Argon Plasma Species Densities",
    xlabel="Time (s)",
    ylabel="Density (m⁻³)",
    label=["e⁻" "Ar" "Ar(4s)" "Ar(4p)" "Ar⁺"],
    linewidth=2,
    yscale=:identity,
    ylims=(0, 1.5e23),
    size=(900, 600),
    legend=:right
)

# Save plot to file
savefig("argon_plasma_densities.png")

# =============================
# RESULTS VERIFICATION
# =============================
println("\n=== SIMULATION SUMMARY ===")
println("Time steps: $n_steps")
println("Final time: $(t_span[2]) s")
println("\nInitial densities [m⁻³]:")
println("e⁻: $(n₀[1])")
println("Ar: $(n₀[2])")
println("Ar(4s): $(n₀[3])")
println("Ar(4p): $(n₀[4])")
println("Ar⁺: $(n₀[5])")

println("\nFinal densities [m⁻³]:")
println("e⁻: $(density_results[1, end])")
println("Ar: $(density_results[2, end])")
println("Ar(4s): $(density_results[3, end])")
println("Ar(4p): $(density_results[4, end])")
println("Ar⁺: $(density_results[5, end])")