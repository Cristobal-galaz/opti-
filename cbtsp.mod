# ------------------------
# PARÁMETROS Y CONJUNTOS
# ------------------------

param dimension integer;
param salesmen integer;
param max_color_diff := 30;

set NODES := 1..dimension;
set COLORS := 1..salesmen;

set cluster{COLORS} within NODES;  # Cada color tiene un conjunto de nodos

param depot_node integer;

param coord_lat{NODES};
param coord_lon{NODES};

param x{i in NODES} := coord_lat[i];
param y{i in NODES} := coord_lon[i];

# ------------------------
# DISTANCIA EUCLIDIANA
# ------------------------

param dist{i in NODES, j in NODES} :=
    if i = j then 0 else sqrt((x[i] - x[j])^2 + (y[i] - y[j])^2);

# ------------------------
# VARIABLES DE DECISIÓN
# ------------------------

var route{i in NODES, j in NODES} binary;

# Variables auxiliares para MTZ
var u{i in NODES} >= 0, <= card(NODES) - 1;

# Variables de diferencia entre colores
var color_balance_diff{c1 in COLORS, c2 in COLORS: c1 < c2} >= 0;

var route_cost{s in COLORS} >= 0;

subject to route_cost_def{s in COLORS}:
    route_cost[s] = sum{i in cluster[s], j in NODES: i != j} dist[i,j] * route[i,j];

var max_route_cost >= 0;

subject to max_route_cost_def{s in COLORS}:
    max_route_cost >= route_cost[s];

# ------------------------
# OBJETIVO
# ------------------------

minimize total_distance:
    sum{i in NODES, j in NODES: i != j} dist[i,j] * route[i,j];

# ------------------------
# RESTRICCIONES BÁSICAS
# ------------------------

subject to one_in{j in NODES diff {depot_node}}:
    sum{i in NODES: i != j} route[i,j] = 1;

subject to one_out{i in NODES diff {depot_node}}:
    sum{j in NODES: j != i} route[i,j] = 1;

subject to depot_out:
    sum{j in NODES: j != depot_node} route[depot_node, j] = salesmen;

subject to depot_in:
    sum{i in NODES: i != depot_node} route[i, depot_node] = salesmen;

# ------------------------
# RESTRICCIÓN MTZ (Eliminación de subciclos)
# ------------------------

subject to mtz{i in NODES, j in NODES:
               i != j && i != depot_node && j != depot_node}:
    u[i] - u[j] + card(NODES) * route[i,j] <= card(NODES) - 1;

# ------------------------
# BALANCE ENTRE COLORES (clusters)
# ------------------------


subject to balance_color_pos{c1 in COLORS, c2 in COLORS: c1 < c2}:
    sum{i in cluster[c1]} sum{j in NODES: j != i} route[i,j]
    - sum{i in cluster[c2]} sum{j in NODES: j != i} route[i,j]
    <= color_balance_diff[c1,c2];

subject to balance_color_neg{c1 in COLORS, c2 in COLORS: c1 < c2}:
    sum{i in cluster[c1]} sum{j in NODES: j != i} route[i,j]
    - sum{i in cluster[c2]} sum{j in NODES: j != i} route[i,j]
    >= -color_balance_diff[c1,c2];

subject to limit_color_diff{c1 in COLORS, c2 in COLORS: c1 < c2}:
    color_balance_diff[c1,c2] <= max_color_diff;
