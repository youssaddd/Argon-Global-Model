import argparse
import os
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog

# --- UNITS ---
SPECIAL_UNITS = {
    'velocity': 'm/s',
    'temp': 'K',
    'pressure': 'Pa',
    'density': 'kg/m³'
}
DEFAULT_UNIT = 'cm⁻³'


def get_unit(species_name):
    """Return display unit for a species/variable name."""
    lower_name = species_name.lower()
    for key, unit in SPECIAL_UNITS.items():
        if key in lower_name:
            return unit
    return DEFAULT_UNIT


# --- FILE SELECTION ---
def select_files_gui():
    """Open a GUI to select multiple files."""
    root = Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(
        title='Select Tecplot / GlobalKin files',
        filetypes=[('All files', '*.*')]  # Show everything by default
    )
    root.destroy()
    return files if files else None


# --- SAVE SPECIES TO TEXT ---
def save_species_to_txt(data_frame, species, output_dir):
    """Save single species data to text file."""
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize filename: remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    sanitized_name = species
    for char in invalid_chars:
        sanitized_name = sanitized_name.replace(char, '_')

    filename = f"{sanitized_name}.txt"
    filepath = os.path.join(output_dir, filename)

    try:
        data_frame[[data_frame.columns[0], species]].to_csv(filepath, sep='\t', index=False)
        print(f"Saved {species} data to {filepath}")
    except Exception as e:
        print(f"Error saving {species}: {e}")


# --- PROCESS TEC FILES ---
def process_tec_file(file_path):
    """Parse Tecplot .tec ASCII data files."""
    with open(file_path, "r") as f:
        lines = f.readlines()

    headers, inside_vars, data_start_line = [], False, 0
    for idx, line in enumerate(lines):
        line_upper = line.upper()
        if "VARIABLES" in line_upper:
            inside_vars = True
        if inside_vars:
            found = re.findall(r'"([^"]+)"', line)
            headers.extend([h.strip() for h in found])
        if inside_vars and "ZONE" in line_upper:
            data_start_line = idx + 1
            break

    if not headers:
        raise ValueError(f"No VARIABLES block found in {file_path}")

    raw_data = []
    for line in lines[data_start_line:]:
        if "ZONE" in line.upper():
            break
        line = line.strip()
        if not line or any(line.upper().startswith(k) for k in ("TITLE", "VARIABLES")):
            continue
        try:
            raw_data.extend([float(x) for x in line.split()])
        except ValueError:
            continue

    num_vars = len(headers)
    total_values = len(raw_data)
    if total_values % num_vars != 0:
        raise ValueError(f"Data inconsistency in file {file_path}")

    num_points = total_values // num_vars
    data = {}
    for i, name in enumerate(headers):
        start = i * num_points
        end = (i + 1) * num_points
        data[name] = raw_data[start:end]

    return pd.DataFrame(data), os.path.basename(file_path)


# --- PLOTTING ---
def plot_species(data_frame, species, file_name=None):
    """Plot a single species with proper units."""
    x_axis = data_frame.columns[0]
    unit = get_unit(species)

    plt.figure(figsize=(10, 6))
    plt.plot(data_frame[x_axis], data_frame[species], label=f"{species} [{unit}]")

    plt.xlabel(x_axis)
    plt.ylabel(f"Concentration / {unit}")
    title = f"{species} vs {x_axis}"
    if file_name:
        title += f" ({file_name})"
    plt.title(title)

    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


# --- MAIN FUNCTION ---
def main():
    parser = argparse.ArgumentParser(description="Global Kinetics Data Visualizer")
    parser.add_argument('-f', '--files', nargs='+', help="File paths (.tec, .dat, .nam, .out)")
    parser.add_argument('-g', '--gui', action='store_true', help="Use GUI file selector")
    parser.add_argument('-s', '--save', action='store_true', help="Save species data to text files")
    args = parser.parse_args()

    # Choose files
    if args.gui:
        file_paths = select_files_gui()
        if not file_paths:
            print("No files selected.")
            return
    elif args.files:
        file_paths = args.files
    else:
        print("No files specified. Use -g to select files via GUI or -f to specify paths.")
        return

    all_dfs = []
    for file_path in file_paths:
        ext = Path(file_path).suffix.lower()
        try:
            if ext == '.tec':
                data_frame, file_name = process_tec_file(file_path)
                all_dfs.append((data_frame, file_name))
                print(f"\nLoaded {file_name} with variables:")
                print("\n".join(f"{i}: {col}" for i, col in enumerate(data_frame.columns[1:], 1)))
            else:
                # Just open other files (.dat, .nam, .out) for manual inspection
                print(f"\n--- {os.path.basename(file_path)} ---")
                with open(file_path, 'r', errors='ignore') as f:
                    preview = f.read(500)  # show a preview
                print(preview)
                print("\n[Full file opened in background for reference]")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    # Interactive mode for .tec files only
    if not all_dfs:
        print("\nNo .tec files loaded for plotting.")
        return

    while True:
        print("\nAvailable commands:")
        print("  plot [species]     - Plot a species")
        print("  save [species]     - Save species data to text")
        print("  list               - Show available species")
        print("  exit               - Quit program")

        user_input = input("Enter command: ").strip()
        if user_input.lower() in ('exit', 'quit', 'q'):
            break

        if user_input.lower().startswith('list'):
            for data_frame, file_name in all_dfs:
                print(f"\nSpecies in {file_name}:")
                print("\n".join(data_frame.columns[1:]))
            continue

        if user_input.lower().startswith(('plot ', 'save ')):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("Please specify a species.")
                continue

            command = parts[0].lower()
            species_input = parts[1]  # Keep original case for exact matching

            matches = []
            for data_frame, file_name in all_dfs:
                for col in data_frame.columns[1:]:
                    # Exact case-insensitive matching
                    if col.lower() == species_input.lower():
                        matches.append((col, data_frame, file_name))

            if not matches:
                print(f"No exact match found for '{species_input}'. Available species:")
                for data_frame, file_name in all_dfs:
                    print(f"\nIn {file_name}:")
                    for col in data_frame.columns[1:]:
                        if species_input.lower() in col.lower():
                            print(f"  - {col}")
                continue

            if command == 'plot':
                for col, data_frame, file_name in matches:
                    plot_species(data_frame, col, file_name)
            elif command == 'save':
                if args.save:
                    for col, data_frame, file_name in matches:
                        save_species_to_txt(data_frame, col, "species_data")
                else:
                    print("Run with -s to enable save functionality.")
        else:
            print("Unknown command.")


if __name__ == "__main__":
    main()
