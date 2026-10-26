"""Genera el armario de dos de ancho (.bbmodel, Bedrock): el mismo mueble que el
de 1x1 (patas, tapa que vuela, laterales de moldura ancha, trasera de tablas)
alargado a 32 px, con dos cajones iguales separados por un montante, que salen
a la vez, y ropa doblada dentro de cada uno.

Usa wardrobe_lib.py, que tiene que estar en la misma carpeta.
Uso:
    python gen_wardrobe_ancho.py <carpeta_salida>
"""
import sys

from wardrobe_lib import (Lienzo, Modelo, animaciones_cajon, bajos_rows, cajon,
                          pintar_cajon, pintar_lateral_bajo, pintar_patas, pintar_ropa,
                          pintar_tapa_larga, pintar_tiras, pintar_tiras_anchas,
                          por_columnas, tapa_larga)

OUT_DIR = sys.argv[1]
cv = Lienzo(128, 64)
draw, flat = cv.draw, cv.flat


# ---------------------------------------------------------------- textura
# Mismas reglas que el 1x1: cada píxel pertenece a una pieza, luz desde arriba
# a la izquierda, pasos de un tono entre vecinos (dos solo en rebajes y
# sombras) y los cambios de tono escalonados.

# Tapa de tres tablas largas, con su canto largo y las testas en los costados
# (en el lib, compartida con el de dos puertas).
pintar_tapa_larga(cv, top=(0, 0), edge_long=(0, 16), edge=(32, 16))

# Trasera 29x11: las tablas del 1x1 (en 5, con goteos que cuelgan de la sombra
# de la tapa y vetas que suben del suelo, uno de cada por tabla y de largos
# distintos) repetidas a lo ancho: A cols 0-2, B 4-7, C 9-11, D 13-15, E 17-20,
# F 22-24, G 26-27; juntas 3, 8, 12, 16, 21 y 25 (fuertes cerca de los extremos,
# suaves en el centro); canto derecho en sombra.
JUNTAS = (3, 8, 12, 16, 21, 25)
BACK_COLUMNS = [
    [(4, 2), (5, 7)],                 # 0  A (goteo de la esquina)
    [(5, 6), (4, 3)],                 # 1  veta
    [(5, 9)],                         # 2
    [(3, 2), (4, 4), (3, 3)],         # 3  junta
    [(5, 9)],                         # 4  B
    [(4, 3), (5, 6)],                 # 5  goteo
    [(5, 7), (4, 2)],                 # 6  veta
    [(5, 9)],                         # 7
    [(3, 1), (4, 5), (3, 3)],         # 8  junta
    [(5, 9)],                         # 9  C
    [(5, 5), (4, 4)],                 # 10 veta larga
    [(4, 2), (5, 7)],                 # 11 goteo
    [(3, 2), (4, 5), (3, 2)],         # 12 junta
    [(4, 1), (5, 8)],                 # 13 D, goteo corto
    [(5, 9)],                         # 14
    [(5, 6), (4, 3)],                 # 15 veta
    [(3, 3), (4, 3), (3, 3)],         # 16 junta
    [(5, 9)],                         # 17 E
    [(4, 4), (5, 5)],                 # 18 goteo largo
    [(5, 8), (4, 1)],                 # 19 veta corta
    [(5, 9)],                         # 20
    [(3, 2), (4, 4), (3, 3)],         # 21 junta
    [(4, 2), (5, 4), (4, 3)],         # 22 F, goteo y veta
    [(5, 9)],                         # 23
    [(5, 7), (4, 2)],                 # 24 veta
    [(3, 1), (4, 6), (3, 2)],         # 25 junta
    [(4, 3), (5, 6)],                 # 26 G, goteo
    [(5, 5), (4, 4)],                 # 27 veta larga
    [(3, 1), (4, 7), (3, 1)],         # 28 canto en sombra
]
# Fila 0, la sombra de la tapa (más honda en las juntas); fila 10, la del
# suelo, más honda en las juntas y al pie de las vetas.
draw("back", 32, 0,
     ["".join("2" if c in JUNTAS or c == 28 else "3" for c in range(29))]
     + por_columnas(BACK_COLUMNS)
     + ["".join("2" if c == 28 else "3" if c in JUNTAS or runs[-1][0] == 4 else "4"
                for c, runs in enumerate(BACK_COLUMNS))])

# Tiras de 1 px a lo ancho (en el lib) y el montante entre los cajones, hundido
# en la sombra de los dos frentes.
pintar_tiras_anchas(cv, rail_top=(32, 11), rail_low=(32, 12), base_front=(32, 13))
draw("mullion", 95, 0, list("344444433"))
pintar_tiras(cv, None, None, None, front_top=(80, 9), front_bottom=(80, 10))

# Lateral, cajones, patas y ropa: los mismos del 1x1.
pintar_lateral_bajo(cv, side=(64, 0), stile_edge=(79, 0))
pintar_cajon(cv, {"front": (80, 0), "front_side": (94, 0), "drawer_wood": (98, 16),
                  "drawer_side_out": (0, 19), "drawer_side_in": (12, 19),
                  "drawer_back_in": (110, 0), "drawer_front_in": (96, 0),
                  "drawer_floor": (114, 16), "rim_side": (24, 19), "rim_back": (110, 7),
                  "drawer_under": (32, 32), "drawer_rim_low": (43, 32),
                  "drawer_back_low": (32, 44)})
pintar_patas(cv, 50, 16)
pintar_ropa(cv, {"white": (25, 19), "red": (30, 19), "denim": (35, 19),
                 "green": (40, 19), "gray": (45, 19)})

# Bajos (31x15): las tablas largas de la tapa vistas desde abajo, un tono más
# oscuras, como en el 1x1.
draw("underside", 0, 32, bajos_rows(tapa_larga(), 31))

# Superficies secundarias.
flat("interior", 66, 16, 16, 16, 2, 2)
flat("edge", 82, 16, 16, 16, 6, 6)


# ---------------------------------------------------------------- geometría
m = Modelo("wardrobe_ancho", cv)
cube, group = m.cube, m.group

# Mueble (frente al norte, -Z): el del 1x1 a 32 de ancho. Los dos frentes de
# cajón sobresalen 1 px y entre ellos queda el montante, hundido como las tiras
# de arriba y abajo.
cabinet = group("cabinet", [0, 0, 0], [
    cube("foot_fl", [-15.5, 0, -7], [-13.5, 1, -5], "plinth"),
    cube("foot_fr", [13.5, 0, -7], [15.5, 1, -5], "plinth"),
    cube("foot_bl", [-15.5, 0, 6], [-13.5, 1, 8], "plinth"),
    cube("foot_br", [13.5, 0, 6], [15.5, 1, 8], "plinth"),
    cube("bottom", [-15.5, 1, -7], [15.5, 2, 8], "base_front",
         up="interior", down="underside"),
    cube("side_left", [-15.5, 2, -7], [-14.5, 13, 8], "edge",
         west="side", east="interior",
         north="stile_edge", south="stile_edge"),
    cube("side_right", [14.5, 2, -7], [15.5, 13, 8], "edge",
         east="side", west="interior",
         north="stile_edge", south="stile_edge"),
    cube("back", [-14.5, 2, 7], [14.5, 13, 8], "edge",
         south="back", north="interior"),
    cube("rail_low", [-14.5, 2, -7], [14.5, 3, -6], "interior",
         north="rail_low"),
    cube("rail_top", [-14.5, 12, -7], [14.5, 13, -6], "interior",
         north="rail_top"),
    cube("mullion", [-0.5, 3, -7], [0.5, 12, -6], "interior",
         north="mullion"),
    cube("top", [-16, 13, -8], [16, 16, 8], "top_edge",
         up="top", down="interior",
         north="top_edge_long", south="top_edge_long~"),
])


def prenda(nombre, tela, x, y, z, alto, arriba=True):
    """Prenda de 4x5 con la esquina en (x, y, z); solo la de arriba de cada pila
    enseña su cara superior (el jersey verde no tiene: siempre va debajo)."""
    return cube(nombre, [x, y, z], [x + 4, y + alto, z + 5], f"{tela}_edge",
                up=f"{tela}_top" if arriba else f"{tela}_edge")


# Ropa: como en el 1x1, dos columnas y dos filas por cajón con rendijas de 1 px
# y tres alturas (delante lo más bajo; detrás, 1 px por encima), pero cada
# cajón ordenado a su manera: desde la altura de los ojos solo asoma la fila de
# atrás, y ahí se ve gris y vaqueros en uno, rojo y blanco en el otro. +X queda
# a la izquierda de quien mira.
clothes_l = group("clothes_l", [7.5, 7, 0], [
    prenda("tee_white_l", "white", 8, 7, -7, 1),
    prenda("sweater_red_l", "red", 3, 7, -7, 2),
    prenda("sweater_green_l", "green", 8, 7, -1, 2, arriba=False),
    prenda("tee_gray_l", "gray", 8, 9, -1, 1),
    prenda("jeans_l", "denim", 3, 7, -1, 3),
])
clothes_r = group("clothes_r", [-7.5, 7, 0], [
    prenda("tee_gray_r", "gray", -7, 7, -7, 1),
    prenda("sweater_red_r", "red", -12, 7, -7, 2),
    prenda("tee_white_r", "white", -7, 7, -1, 1, arriba=False),
    prenda("sweater_red_r2", "red", -7, 8, -1, 2),
    prenda("sweater_green_r", "green", -12, 7, -1, 2, arriba=False),
    prenda("tee_white_r2", "white", -12, 9, -1, 1),
])

# Los dos cajones van en un grupo y salen juntos.
drawers = group("drawers", [0, 3, -8], [
    cajon(m, "drawer_l", 7.5, clothes_l),
    cajon(m, "drawer_r", -7.5, clothes_r),
])

root = group("wardrobe", [0, 0, 0], [cabinet, drawers])


# ---------------------------------------------------------------- animaciones
animations = animaciones_cajon(m, drawers)

m.escribir(OUT_DIR, root, animations, visible_box=[3, 2.5, 0.75],
           mover=("drawer", "tee", "sweater", "jeans"))
