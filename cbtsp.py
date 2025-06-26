import os
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def parse_cbtsp_file(path):
    with open(path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    dimension = 0
    salesmen = 0
    depot = None
    coords = {}
    Vk = {}
    section = None

    for line in lines:
        if "DIMENSION" in line:
            dimension = int(line.split(":")[1])
        elif "SALESMEN" in line:
            salesmen = int(line.split(":")[1])
        elif line == "NODE_COORD_SECTION":
            section = "COORD"
            continue
        elif line == "CTSP_SET_SECTION":
            section = "CTSP"
            continue
        elif line == "DEPOT_SECTION":
            section = "DEPOT"
            continue
        elif line == "EOF":
            break

        if section == "COORD":
            parts = line.split()
            i = int(parts[0])
            coords[i] = (float(parts[1]), float(parts[2]))
        elif section == "CTSP":
            parts = list(map(int, line.split()))
            k = parts[0]
            Vk[k] = parts[1:-1]
        elif section == "DEPOT":
            depot = int(line)

    exclusivas = set(i for lst in Vk.values() for i in lst)
    U = sorted(set(coords.keys()) - exclusivas)

    return dimension, salesmen, coords, Vk, U, depot

def write_ampl_dat(filename, V, K, coords, Vk, U, depot, dist_matrix):
    with open(filename, "w") as f:
        f.write("set V := " + " ".join(map(str, sorted(V))) + ";\n")
        f.write("set K := " + " ".join(map(str, K)) + ";\n\n")
        f.write("param depot :=\n")
        for k in K:
            f.write(f"{k} {depot}\n")
        f.write(";\n\n")

        f.write("set U := " + " ".join(map(str, U)) + ";\n\n")
        for k in K:
            f.write(f"set Vk[{k}] := " + " ".join(map(str, Vk.get(k, []))) + ";\n")
        f.write("\n")

        f.write("param w : " + " ".join(map(str, sorted(V))) + " :=\n")
        for i in sorted(V):
            f.write(f"{i} " + " ".join(f"{round(dist_matrix[i][j],2)}" for j in sorted(V)) + "\n")
        f.write(";\n")

def process_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for file in os.listdir(input_folder):
        if file.endswith(".cbtsp"):
            path = os.path.join(input_folder, file)
            print(f"Procesando {file}...")
            dim, m, coords, Vk, U, depot = parse_cbtsp_file(path)
            V = list(coords.keys())
            K = list(range(1, m+1))

            dist = {i: {} for i in V}
            for i in V:
                for j in V:
                    lat1, lon1 = coords[i]
                    lat2, lon2 = coords[j]
                    dist[i][j] = haversine(lat1, lon1, lat2, lon2) if i != j else 0

            output_name = os.path.splitext(file)[0] + ".dat"
            output_path = os.path.join(output_folder, output_name)
            write_ampl_dat(output_path, V, K, coords, Vk, U, depot, dist)

    print("✅ ¡Conversión completada!")

# Dirección personalizada en tu PC
if __name__ == "__main__":
    input_folder = r"D:\OneDrive\Desktop\ampl\CBTSP\INSTANCES\Gr"
    output_folder = r"D:\OneDrive\Desktop\ampl\CBTSP\DATOS\Gr"
    process_folder(input_folder, output_folder)
