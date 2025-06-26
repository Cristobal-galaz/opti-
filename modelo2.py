import random
import math
import re
import time

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
# FUNCIONES GA
# ----------------------
def calcular_distancia(ciudad1, ciudad2):
    x1, y1 = ciudad1
    x2, y2 = ciudad2
    return math.hypot(x2 - x1, y2 - y1)

def distancia_total(rutas, coordenadas):
    total = 0
    for ruta in rutas:
        if len(ruta) == 0:
            continue
        total += calcular_distancia(coordenadas[1], coordenadas[ruta[0]])  # inicio en depot
        for i in range(len(ruta) - 1):
            total += calcular_distancia(coordenadas[ruta[i]], coordenadas[ruta[i + 1]])
        total += calcular_distancia(coordenadas[ruta[-1]], coordenadas[1])  # regreso a depot
    return total

def crear_individuo(nodos, salesmen):
    random.shuffle(nodos)
    k, m = divmod(len(nodos), salesmen)
    return [nodos[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(salesmen)]

def mutacion(individuo):
    rutas = [ruta[:] for ruta in individuo]
    idx1, idx2 = random.sample(range(len(rutas)), 2)
    if rutas[idx1] and rutas[idx2]:
        i, j = random.randint(0, len(rutas[idx1]) - 1), random.randint(0, len(rutas[idx2]) - 1)
        rutas[idx1][i], rutas[idx2][j] = rutas[idx2][j], rutas[idx1][i]
    return rutas

def crossover(p1, p2):
    todos = list({nodo for ruta in p1 for nodo in ruta})
    random.shuffle(todos)
    return crear_individuo(todos, len(p1))

def seleccionar(poblacion, coordenadas, k):
    evaluado = sorted(poblacion, key=lambda ind: distancia_total(ind, coordenadas))
    return evaluado[:k]

# ----------------------
# RESOLVER CBTSP CON GA
# ----------------------
def resolver_ga_cbptsp(ruta_archivo, generaciones=1000, tam_poblacion=100, tiempo_max=600):
    inicio = time.time()
    datos = leer_instancia_cbtsp(ruta_archivo)
    coordenadas = datos["coordenadas"]
    salesmen = datos["salesmen"]
    nodos = [n for n in coordenadas if n != 1]

    poblacion = [crear_individuo(nodos[:], salesmen) for _ in range(tam_poblacion)]
    mejor = None
    mejor_dist = float('inf')

    for gen in range(generaciones):
        if time.time() - inicio > tiempo_max:
            print("⏱️ Tiempo límite alcanzado.")
            break

        seleccionados = seleccionar(poblacion, coordenadas, tam_poblacion // 2)
        nueva_pob = []
        for _ in range(tam_poblacion):
            p1, p2 = random.sample(seleccionados, 2)
            hijo = crossover(p1, p2)
            if random.random() < 0.2:
                hijo = mutacion(hijo)
            nueva_pob.append(hijo)

        poblacion = nueva_pob
        candidato = min(poblacion, key=lambda ind: distancia_total(ind, coordenadas))
        dist = distancia_total(candidato, coordenadas)
        if dist < mejor_dist:
            mejor_dist = dist
            mejor = candidato

    duracion = time.time() - inicio
    print(f"\n✅ Finalizado en {duracion:.2f} segundos")
    print(f"🎯 Mejor solución: {mejor_dist:.2f}")

    suma_costos = 0
    max_cost = 0
    for idx, ruta in enumerate(mejor, 1):
        costo = 0
        if ruta:
            costo += calcular_distancia(coordenadas[1], coordenadas[ruta[0]])
            for i in range(len(ruta)-1):
                costo += calcular_distancia(coordenadas[ruta[i]], coordenadas[ruta[i+1]])
            costo += calcular_distancia(coordenadas[ruta[-1]], coordenadas[1])
        suma_costos += costo
        max_cost = max(max_cost, costo)
        print(f"🚗 Viajero {idx}: {costo:.2f} | Ruta: 1 → {' → '.join(map(str, ruta))} → 1")

    print(f"\n➕ Suma de costos individuales: {suma_costos:.2f}")
    print(f"🔥 Máximo costo individual: {max_cost:.2f}")

# ----------------------
# EJECUCIÓN
# ----------------------
resolver_ga_cbptsp("gr229_10.cbtsp", generaciones=1000, tam_poblacion=100, tiempo_max=60)
