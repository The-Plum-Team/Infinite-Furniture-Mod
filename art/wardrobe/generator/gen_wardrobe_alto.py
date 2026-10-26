"""Genera el armario de dos de alto (.bbmodel, Bedrock): el mismo mueble que el
de 1x1 (patas, tapa, laterales con plafón, trasera de tablas) pero con una
puerta de bisagra de dos plafones y, dentro, dos baldas con ropa doblada.

Usa wardrobe_lib.py, que tiene que estar en la misma carpeta.
Uso:
    python gen_wardrobe_alto.py <carpeta_salida>
"""
import sys

from wardrobe_lib import (Lienzo, Modelo, animaciones_puertas, balda_por_debajo,
                          con_bisagras, con_iman, pared, pared_lateral, pila, pintar_bajo,
                          pintar_lateral_alto, pintar_patas, pintar_puerta, pintar_ropa,
                          pintar_tapa, pintar_tiras, por_columnas, shelf_rows, suelo_rows)

OUT_DIR = sys.argv[1]
cv = Lienzo(128, 64)
draw, flat = cv.draw, cv.flat


# ---------------------------------------------------------------- textura
# Mismas reglas que el 1x1: cada píxel pertenece a una pieza, luz desde arriba
# a la izquierda, pasos de un tono entre vecinos (dos solo en rebajes y
# sombras) y los cambios de tono escalonados.

# Puerta de dos plafones con su tirador de latón y lateral de moldura ancha con
# zócalo (en el lib, compartidos con el de dos puertas).
pintar_puerta(cv, door=(32, 0), door_edge=(31, 0), door_in=(46, 0))
pintar_lateral_alto(cv, side=(0, 0), stile_edge=(30, 0))

# Trasera 13x27: las mismas tablas que en el 1x1 (A cols 0-2, B 4-7, C 9-11;
# juntas 3 y 8; canto derecho en sombra), por tramos de la fila 1 a la 25:
# goteos de largos distintos colgando de la sombra de la tapa, el centro en
# calma, vetas largas subiendo desde el suelo (más en el lado en sombra) y las
# juntas marcadas cerca de los extremos y suaves en el centro.
BACK_COLUMNS = [
    [(4, 2), (5, 23)],                # 0  A (goteo de la esquina)
    [(4, 3), (5, 15), (4, 7)],        # 1  goteo y veta larga
    [(5, 25)],                        # 2
    [(3, 3), (4, 17), (3, 5)],        # 3  junta
    [(5, 22), (4, 3)],                # 4  B, veta corta
    [(4, 5), (5, 20)],                # 5  goteo largo
    [(5, 17), (4, 8)],                # 6  veta larga
    [(5, 25)],                        # 7
    [(3, 2), (4, 19), (3, 4)],        # 8  junta
    [(4, 1), (5, 24)],                # 9  C
    [(4, 4), (5, 13), (4, 8)],        # 10 goteo y veta larga
    [(4, 2), (5, 19), (4, 4)],        # 11 goteo de la esquina y veta
    [(3, 2), (4, 22), (3, 1)],        # 12 canto en sombra
]
draw("back", 16, 0, ["3332333323332"] + por_columnas(BACK_COLUMNS)
     + ["4343343434332"])
# Trasera por dentro (13x27): las mismas tablas vistas desde dentro (en espejo,
# juntas en las columnas 4 y 9), un tono por debajo de las de fuera; juntas y
# rincones, otro más. La sombra bajo cada balda, en 2.
draw("back_in", 16, 28, pared(
    [3, 4, 4, 4, 3, 4, 4, 4, 4, 3, 4, 4, 3], 2, [
        ("2222233332222", "0000000000000"),
        ("1111122221111", "0000000000000"),
        ("1111122221111", "0000000000000"),
    ]))

# Paredes de dentro de los laterales: tablas que se apagan hacia el fondo, con la
# sombra de cada balda (en el lib, compartidas con el de dos puertas). Junto al
# canto de la puerta, los herrajes: en el lado de la bisagra, las placas de las
# tres bisagras; en el otro, el imán del cierre.
draw("side_in", 64, 0, con_iman(pared_lateral()))
draw("side_in_bisagras", 80, 16, con_bisagras(pared_lateral()))

# Techo por dentro (16x16, fila 0 = el fondo): las tres tablas de la tapa vistas
# desde abajo (juntas 5 y 10), oscuras al fondo y con luz hacia la puerta; cada
# tabla cambia de tono a su altura y las juntas van un tono por debajo.
TECHO_TABLAS = [(range(0, 5), 6, 11), (range(6, 10), 7, 12), (range(11, 16), 5, 10)]


def techo_rows():
    tono = {}
    for cols, a, b in TECHO_TABLAS:
        for c in cols:
            tono[c] = [2 if r < a else 3 if r < b else 4 for r in range(16)]
    for c in (5, 10):
        tono[c] = [max(2, min(tono[c - 1][r], tono[c + 1][r]) - 1) for r in range(16)]
    return ["".join(str(tono[c][r]) for c in range(16)) for r in range(16)]


draw("ceiling", 80, 0, techo_rows())

pintar_tapa(cv, top=(0, 28), edge=(16, 56), edge_side=(16, 59))
pintar_tiras(cv, rail_top=(32, 59), rail_low=(32, 60), base_front=(32, 61),
             front_top=(32, 62), front_bottom=(32, 63))
pintar_patas(cv, 48, 56)
pintar_bajo(cv, underside=(96, 0))
pintar_ropa(cv, {"white": (32, 25), "red": (37, 25), "denim": (42, 25),
                 "green": (47, 25), "gray": (52, 25)})

# Superficies secundarias.
flat("edge", 60, 0, 4, 4, 6, 6)
flat("interior", 60, 4, 4, 4, 2, 2)
flat("dark", 60, 8, 4, 4, 3, 3)

draw("shelf_top", 0, 44, shelf_rows(6, 0))
draw("floor_top", 32, 45, suelo_rows(13))
draw("shelf_front", 32, 44, ["5666666666665"])
draw("shelf_under", 111, 0, balda_por_debajo(shelf_rows(6, 0)))


# ---------------------------------------------------------------- geometría
m = Modelo("wardrobe_alto", cv)
cube, group = m.cube, m.group

# Mueble (frente al norte, -Z): 16x32, el cuerpo 1 px hundido por delante y la
# puerta sobresaliendo ese píxel, como el cajón del 1x1.
cabinet = group("cabinet", [0, 0, 0], [
    cube("foot_fl", [-7.5, 0, -7], [-5.5, 1, -5], "plinth"),
    cube("foot_fr", [5.5, 0, -7], [7.5, 1, -5], "plinth"),
    cube("foot_bl", [-7.5, 0, 6], [-5.5, 1, 8], "plinth"),
    cube("foot_br", [5.5, 0, 6], [7.5, 1, 8], "plinth"),
    cube("bottom", [-7.5, 1, -7], [7.5, 2, 8], "base_front",
         up="interior", down="underside"),
    cube("side_left", [-7.5, 2, -7], [-6.5, 29, 8], "edge",
         west="side", east="side_in_bisagras~",
         north="stile_edge", south="stile_edge"),
    cube("side_right", [6.5, 2, -7], [7.5, 29, 8], "edge",
         east="side", west="side_in",
         north="stile_edge", south="stile_edge"),
    cube("back", [-6.5, 2, 7], [6.5, 29, 8], "edge",
         south="back", north="back_in"),
    cube("rail_low", [-6.5, 2, -7], [6.5, 3, -6], "interior",
         north="rail_low"),
    cube("rail_top", [-6.5, 28, -7], [6.5, 29, -6], "interior",
         north="rail_top"),
    cube("top", [-8, 29, -8], [8, 32, 8], "top_edge",
         up="top", down="ceiling",
         east="top_edge_side", west="top_edge_side"),
    # Dentro: suelo enrasado con el travesaño de abajo y dos baldas.
    cube("floor", [-6.5, 2, -6], [6.5, 3, 7], "dark", up="floor_top"),
    cube("shelf_low", [-6.5, 11, -6], [6.5, 12, 7], "dark",
         up="shelf_top", north="shelf_front", down="shelf_under"),
    cube("shelf_high", [-6.5, 19, -6], [6.5, 20, 7], "dark",
         up="shelf_top", north="shelf_front", down="shelf_under"),
])


# Tres pilas por hueco (+X queda a la izquierda de quien mira), con alturas
# distintas y llenando el hueco hasta 2-3 px de la balda de arriba. Nunca dos
# prendas iguales de 1 px seguidas: con el mismo canto se leen como una sola.
X3 = (2.25, -2, -6.25)
PILAS = {
    3: ([("denim", 3), ("denim", 3)], [("white", 1), ("red", 2), ("gray", 1)],
        [("green", 2), ("green", 2), ("white", 1)]),
    12: ([("red", 2), ("gray", 1), ("white", 1)], [("denim", 3)],
         [("green", 2), ("white", 1), ("red", 2)]),
    20: ([("gray", 1), ("white", 1), ("gray", 1)], [("red", 2), ("red", 2), ("white", 1)],
         [("denim", 3), ("white", 1)]),
}
# Unas pilas un píxel más al fondo que otras, como colocadas a mano.
FONDO = {3: (0, 1, 0), 12: (1, 0, 0), 20: (0, 1, 1)}
clothes = group("clothes", [0, 3, 0],
                [c for y0, pilas in PILAS.items() for i, prendas in enumerate(pilas)
                 for c in pila(m, f"stack_{y0}_{i}", X3[i], y0, prendas, FONDO[y0][i])])

# Puerta: gira sobre el canto derecho de quien mira (x = -7).
door = group("door", [-7, 15.5, -7], [
    cube("door", [-7, 3, -8], [7, 28, -7], "door_edge",
         north="door", south="door_in", up="front_top", down="front_bottom"),
])

root = group("wardrobe", [0, 0, 0], [cabinet, clothes, door])


# ---------------------------------------------------------------- animaciones
animations = animaciones_puertas(m, [(door, 1)])

m.escribir(OUT_DIR, root, animations, visible_box=[2, 3.5, 1.5], mover=("door",))
