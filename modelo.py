import pulp
import math
import re
import time
import os
from datetime import datetime

# ----------------------
# LECTURA DE ARCHIVO .CBTSP
# ----------------------
def leer_instancia_cbtsp(ruta_archivo):
    with open(ruta_archivo, 'r') as f:
        lineas = f.readlines()

    nombre, tipo, dimension, salesmen, edge_weight_type = None, None, None, None, None
    nodo_coord = {}
    leyendo_coords = False

    for linea in lineas:
        linea = linea.strip()
        if linea.startswith("NAME"):
            nombre = linea.split(":")[1].strip()
        elif linea.startswith("TYPE"):
            tipo = linea.split(":")[1].strip()
        elif linea.startswith("DIMENSION"):
            dimension = int(linea.split(":")[1].strip())
        elif linea.startswith("SALESMEN"):
            salesmen = int(linea.split(":")[1].strip())
        elif linea.startswith("EDGE_WEIGHT_TYPE"):
            edge_weight_type = linea.split(":")[1].strip()
        elif linea.startswith("NODE_COORD_SECTION"):
            leyendo_coords = True
        elif leyendo_coords and linea != "EOF":
            partes = re.split(r'\s+', linea)
            if len(partes) >= 3:
                nodo_id = int(partes[0])
                lat = float(partes[1])
                lon = float(partes[2])
                nodo_coord[nodo_id] = (lat, lon)

    return {
        "nombre": nombre,
        "dimension": dimension,
        "salesmen": salesmen,
        "coordenadas": nodo_coord
    }

# ----------------------
# RECONSTRUIR TOURS MÚLTIPLES
# ----------------------
def reconstruir_tours_multiples(rutas, depot=1):
    sucesores = {i: j for i, j in rutas}
    tours = []
    max_iters = len(rutas) + 10  # protección contra ciclos infinitos

    while sucesores and max_iters > 0:
        actual = depot
        tour = [actual]
        while True:
            siguiente = sucesores.get(actual)
            if siguiente is None or siguiente == depot:
                break
            tour.append(siguiente)
            actual = siguiente
        tour.append(depot)
        for i in range(len(tour) - 1):
            sucesores.pop(tour[i], None)
        if len(tour) > 2:
            tours.append(tour)
        max_iters -= 1

    return tours

# ----------------------
# RESOLVER mTSP con límite de tiempo
# ----------------------
def resolver_mtsp_desde_cbtsp(ruta_archivo, limite_tiempo=600):
    tiempo_inicio = time.time()

    datos = leer_instancia_cbtsp(ruta_archivo)
    dimension = datos["dimension"]
    salesmen = datos["salesmen"]
    coordenadas = datos["coordenadas"]
    depot_node = 1

    MODES = list(coordenadas.keys())
    COLORS = list(range(1, salesmen + 1))

    cluster = {c: [] for c in COLORS}
    nodos_sin_depot = [n for n in MODES if n != depot_node]
    for idx, nodo in enumerate(nodos_sin_depot):
        cluster[COLORS[idx % salesmen]].append(nodo)

    dist = {
        (i, j): 0 if i == j else math.hypot(coordenadas[i][0] - coordenadas[j][0],
                                            coordenadas[i][1] - coordenadas[j][1])
        for i in MODES for j in MODES
    }

    model = pulp.LpProblem("mTSP_balanceado", pulp.LpMinimize)
    route = pulp.LpVariable.dicts("route", (MODES, MODES), cat="Binary")
    u = pulp.LpVariable.dicts("u", MODES, lowBound=0, upBound=len(MODES)-1, cat="Continuous")

    max_color_diff = 1
    color_balance_diff = pulp.LpVariable.dicts(
        "color_balance_diff",
        ((c1, c2) for c1 in COLORS for c2 in COLORS if c1 < c2),
        lowBound=0, cat="Continuous"
    )

    model += pulp.lpSum(dist[i, j] * route[i][j] for i in MODES for j in MODES if i != j)

    for j in MODES:
        if j != depot_node:
            model += pulp.lpSum(route[i][j] for i in MODES if i != j) == 1
    for i in MODES:
        if i != depot_node:
            model += pulp.lpSum(route[i][j] for j in MODES if j != i) == 1

    model += pulp.lpSum(route[depot_node][j] for j in MODES if j != depot_node) == salesmen
    model += pulp.lpSum(route[i][depot_node] for i in MODES if i != depot_node) == salesmen

    for i in MODES:
        for j in MODES:
            if i != j and i != depot_node and j != depot_node:
                model += u[i] - u[j] + len(MODES) * route[i][j] <= len(MODES) - 1

    for c1 in COLORS:
        for c2 in COLORS:
            if c1 < c2:
                flow_c1 = pulp.lpSum(route[i][j] for i in cluster[c1] for j in MODES if j != i)
                flow_c2 = pulp.lpSum(route[i][j] for i in cluster[c2] for j in MODES if j != i)
                model += (flow_c1 - flow_c2 <= color_balance_diff[c1, c2])
                model += (flow_c1 - flow_c2 >= -color_balance_diff[c1, c2])
                model += color_balance_diff[c1, c2] <= max_color_diff

    # Crear solver con límite de tiempo en segundos
    solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=limite_tiempo)
    model.solve(solver)

    tiempo_fin = time.time()
    duracion = tiempo_fin - tiempo_inicio

    print("Estado:", pulp.LpStatus[model.status])
    print("Distancia total (óptimo parcial):", pulp.value(model.objective))
    print("🕒 Tiempo total de ejecución: {:.2f} segundos".format(duracion))

    rutas_solucion = []
    for i in MODES:
        for j in MODES:
            val = pulp.value(route[i][j])
            if i != j and val is not None and val > 0.5:
                rutas_solucion.append((i, j))

    if not rutas_solucion:
        print("⚠️ No se encontraron rutas válidas en la solución.")
        return

    print("\n📋 Resultado Final (óptimo parcial o completo):")
    print(f"🧮 Costo total (objetivo): {pulp.value(model.objective):.2f}")

    try:
        tours_finales = reconstruir_tours_multiples(rutas_solucion, depot=depot_node)
        print(f"🧭 Se reconstruyeron {len(tours_finales)} tours")
        if len(tours_finales) < salesmen:
            print(f"⚠️ Se esperaban {salesmen} tours (vendedores), pero se reconstruyeron {len(tours_finales)}")

        costos_individuales = []
        for idx, tour in enumerate(tours_finales, start=1):
            costo = sum(dist[tour[i], tour[i+1]] for i in range(len(tour)-1))
            costos_individuales.append(costo)
            print(f"🚗 Viajero {idx}: {costo:.2f} | Ruta: {' → '.join(map(str, tour))}")

        suma_costos = sum(costos_individuales)
        costo_maximo = max(costos_individuales)

        print(f"\n➕ Suma de costos individuales: {suma_costos:.2f}")
        print(f"🔥 Máximo costo individual: {costo_maximo:.2f}")
    except Exception as e:
        print("❌ Error al reconstruir los tours:", e)


# ----------------------
# EJECUCIÓN con límite de tiempo 600 segundos
# ----------------------
resolver_mtsp_desde_cbtsp("eil51-2.cbtsp", limite_tiempo=600)
