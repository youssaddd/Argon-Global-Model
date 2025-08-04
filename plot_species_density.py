import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# --- CONFIGURATION ---
file_path = r"C:\Users\Youssef\Desktop\AEPT\globalKin\global_kin.tec"

# --- CHECK FILE EXISTENCE ---
if not os.path.exists(file_path):
    print(f"[ERROR] File not found: {file_path}")
    exit()

# --- READ FILE LINES ---
with open(file_path, "r") as f:
    lines = f.readlines()

# --- EXTRACT HEADERS FROM MULTI-LINE VARIABLES BLOCK ---
headers = []
inside_vars = False
data_start_line = 0

for idx, line in enumerate(lines):
    upper = line.upper()
    if "VARIABLES" in upper:
        inside_vars = True
    if inside_vars:
        found = re.findall(r'"([^"]+)"', line)
        headers.extend([h.strip() for h in found])
    if inside_vars and "ZONE" in upper:
        data_start_line = idx + 1
        break

if not headers:
    print("[ERROR] No VARIABLES block found.")
    exit()

print(f"[DEBUG] Found {len(headers)} variables: {headers}")

# --- EXTRACT FLAT NUMERIC DATA LIST ---
raw_data = []
for line in lines[data_start_line:]:
    if "ZONE" in line.upper():
        break
    line = line.strip()
    if not line or any(line.upper().startswith(k) for k in ("TITLE", "VARIABLES")):
        continue
    try:
        tokens = line.split()
        raw_data.extend([float(x) for x in tokens])
    except ValueError:
        print(f"[WARNING] Skipping non-numeric or malformed line: {line}")
        continue

# --- REBUILD DATAFRAME FROM BLOCKS ---
num_vars = len(headers)
total_values = len(raw_data)
if total_values % num_vars != 0:
    print(f"[ERROR] Total values ({total_values}) not divisible by number of variables ({num_vars})")
    exit()

num_points = total_values // num_vars
print(f"[DEBUG] Found {num_points} data points per species.")

data = {}
for i, name in enumerate(headers):
    start = i * num_points
    end = (i + 1) * num_points
    data[name] = raw_data[start:end]

df = pd.DataFrame(data)
x_axis = headers[0]

# --- DEBUG: SHOW STRUCTURE ---
print(f"\nData loaded successfully with shape {df.shape}")
print(df.head())

print("\nAvailable species to plot:")
for i, name in enumerate(headers[1:], start=1):
    print(f"{i}: {name}")

# --- INTERACTIVE PLOTTING LOOP ---
while True:
    species_input = input("\nEnter species name to plot (or 'q' to quit): ").strip()
    if species_input.lower() in ['q', 'quit', 'exit']:
        print("Exiting.")
        break

    # Case-insensitive match
    matches = [col for col in df.columns if col.strip().lower() == species_input.lower()]
    if not matches:
        print(f"[ERROR] Species '{species_input}' not found.")
        continue

    species = matches[0]

    plt.figure(figsize=(8, 5))
    plt.plot(df[x_axis], df[species], label=species)
    plt.xlabel(x_axis)
    plt.ylabel(f"{species} [#/cm³]")
    plt.title(f"{species} vs {x_axis}")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

