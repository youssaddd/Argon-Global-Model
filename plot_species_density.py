import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# --- Configuration ---
file_path = r"C:\Users\Youssef\Desktop\AEPT\globalKin\global_kin.tec"

# --- Check if file exists ---
if not os.path.exists(file_path):
    print(f"Error: File not found at: {file_path}")
    exit()

# --- Read file lines ---
with open(file_path, "r") as f:
    lines = f.readlines()

# --- Parse headers from VARIABLES block ---
headers = []
start_row = None
in_variables = False

for idx, line in enumerate(lines):
    if "VARIABLES" in line.upper():
        in_variables = True
        headers += re.findall(r'"([^"]+)"', line)
    elif in_variables:
        if "ZONE" in line.upper():
            start_row = idx + 1
            break
        headers += re.findall(r'"([^"]+)"', line)

if not headers or start_row is None:
    print("Error: Could not find VARIABLES block or ZONE line.")
    exit()

# Clean up header names
headers = [h.strip() for h in headers]

# --- Load data ---
try:
    df = pd.read_csv(
        file_path,
        sep=r'\s+|\t+',
        engine='python',
        skiprows=start_row,
        names=headers
    )
except Exception as e:
    print(f"Error while reading the file: {e}")
    exit()

x_axis = headers[0]

# --- Interactive plotting loop ---
print("\nAvailable variables:")
for i, name in enumerate(headers[1:], start=1):
    print(f"{i}: {name}")

while True:
    species = input("\nEnter species name to plot (or 'q' to quit): ").strip()
    if species.lower() in ['q', 'quit', 'exit']:
        print("Exiting...")
        break

    if species not in df.columns:
        print(f"Error: '{species}' not found.")
        continue

    plt.figure(figsize=(8, 5))
    plt.plot(df[x_axis], df[species], label=species)
    plt.xlabel(x_axis)
    plt.ylabel(f"{species} [#/cm³]")
    plt.title(f"{species} vs {x_axis}")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
