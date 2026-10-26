"""Genera un modelo Blockbench (.bbmodel, Bedrock) de un armario 1x1 con cajón.

Lo común con los demás armarios (paleta, tapa, patas, ropa y montaje del
.bbmodel) está en wardrobe_lib.py, que tiene que estar en la misma carpeta.
Uso:
    python gen_wardrobe.py <carpeta_salida>
"""
import sys

from wardrobe_lib import (Lienzo, Modelo, animaciones_cajon, cajon, pintar_bajo,
                          pintar_cajon, pintar_lateral_bajo, pintar_patas, pintar_ropa,
                          pintar_tapa, pintar_tiras, por_columnas)

OUT_DIR = sys.argv[1]
cv = Lienzo(64, 64)
draw, flat = cv.draw, cv.flat


# ---------------------------------------------------------------- textura
# Reglas: cada píxel pertenece a una pieza (marco, rebaje, panel, tabla, pomo);
# luz desde arriba a la izquierda. Degradado: entre píxeles vecinos se pasa al
# tono siguiente de la rampa; los saltos de dos tonos solo en bordes
# estructurales (rebajes, sombras de oclusión). Las superficies que degradan
# viven en 5-8 (pasos finos); 2-4 es para rebajes y sombras. Los límites entre
# tonos van escalonados (cada columna cambia a una altura distinta): ninguna
# fila se repite y no hay rectángulos de bordes rectos dentro de una pieza.

# Tiras en sombra bajo el cajón y bajo la tapa, la base y los cantos del cajón.
pintar_tiras(cv, rail_top=(48, 0), rail_low=(48, 1), base_front=(48, 4),
             front_top=(48, 2), front_bottom=(48, 3))

# Trasera 13x11: tablas verticales (A cols 0-2, B 4-7, C 9-11; juntas 3 y 8;
# canto derecho en sombra). Cada columna va por tramos (tono, largo) de la fila 1
# a la 9: las tablas en 5 con goteos que cuelgan de la sombra de la tapa y vetas
# que suben desde el suelo, de largos distintos; las juntas se marcan fuerte
# cerca de los extremos y se suavizan en el centro. Fila 0, la sombra de la
# tapa; fila 10, la sombra del suelo, más honda en las juntas y al pie de las
# vetas.
BACK_COLUMNS = [
    [(4, 2), (5, 7)],                 # 0  A (goteo de la esquina)
    [(5, 6), (4, 3)],                 # 1  veta que sube
    [(5, 9)],                         # 2
    [(3, 2), (4, 4), (3, 3)],         # 3  junta
    [(5, 9)],                         # 4  B
    [(4, 3), (5, 6)],                 # 5  goteo
    [(5, 7), (4, 2)],                 # 6  veta
    [(5, 9)],                         # 7
    [(3, 1), (4, 5), (3, 3)],         # 8  junta
    [(5, 9)],                         # 9  C
    [(4, 1), (5, 4), (4, 4)],         # 10 veta alta
    [(4, 2), (5, 7)],                 # 11 goteo de la esquina
    [(3, 1), (4, 7), (3, 1)],         # 12 canto en sombra
]
draw("back", 16, 0, ["3332333323332"] + por_columnas(BACK_COLUMNS)
     + ["4343443434342"])

pintar_tapa(cv, top=(0, 16), edge=(16, 16), edge_side=(16, 36))

# Superficies secundarias.
flat("edge", 16, 20, 16, 16, 6, 6)
flat("interior", 32, 16, 16, 16, 2, 2)
pintar_patas(cv, 48, 16)

# Frente y caja del cajón (en el lib, compartidos con el de dos de ancho) y el
# lateral de moldura ancha.
pintar_cajon(cv, {"front": (32, 0), "front_side": (63, 0), "drawer_wood": (0, 32),
                  "drawer_side_out": (0, 48), "drawer_side_in": (0, 55),
                  "drawer_back_in": (16, 40), "drawer_front_in": (16, 48),
                  "drawer_floor": (32, 40), "rim_side": (43, 40), "rim_back": (32, 51),
                  "drawer_under": (30, 52), "drawer_rim_low": (59, 40),
                  "drawer_back_low": (44, 55)})
pintar_lateral_bajo(cv, side=(0, 0), stile_edge=(30, 0))
pintar_bajo(cv, underside=(44, 40))

pintar_ropa(cv, {"white": (32, 32), "red": (42, 32), "denim": (47, 32),
                 "green": (52, 32), "gray": (57, 32)})


# ---------------------------------------------------------------- geometría
m = Modelo("wardrobe_cajon", cv)
cube, group = m.cube, m.group

# Mueble (frente al norte, -Z). El cuerpo queda 1 px hundido por delante y
# el frente del cajón sobresale ese píxel: lo que asoma es el cajón.
cabinet = group("cabinet", [0, 0, 0], [
    cube("foot_fl", [-7.5, 0, -7], [-5.5, 1, -5], "plinth"),
    cube("foot_fr", [5.5, 0, -7], [7.5, 1, -5], "plinth"),
    cube("foot_bl", [-7.5, 0, 6], [-5.5, 1, 8], "plinth"),
    cube("foot_br", [5.5, 0, 6], [7.5, 1, 8], "plinth"),
    cube("bottom", [-7.5, 1, -7], [7.5, 2, 8], "base_front",
         up="interior", down="underside"),
    cube("side_left", [-7.5, 2, -7], [-6.5, 13, 8], "edge",
         west="side", east="interior",
         north="stile_edge", south="stile_edge"),
    cube("side_right", [6.5, 2, -7], [7.5, 13, 8], "edge",
         east="side", west="interior",
         north="stile_edge", south="stile_edge"),
    cube("back", [-6.5, 2, 7], [6.5, 13, 8], "edge",
         south="back", north="interior"),
    cube("rail_low", [-6.5, 2, -7], [6.5, 3, -6], "interior",
         north="rail_low"),
    cube("rail_top", [-6.5, 12, -7], [6.5, 13, -6], "interior",
         north="rail_top"),
    cube("top", [-8, 13, -8], [8, 16, 8], "top_edge",
         up="top", down="interior",
         east="top_edge_side", west="top_edge_side"),
])

# Ropa: dos columnas y dos filas de 4x5 (+X queda a la izquierda de quien
# mira desde delante), separadas por rendijas de 1 px para que cada prenda se
# lea suelta (y otra junto a cada pared de la caja): si las filas se tocan, la de atrás (más alta) parece el borde de
# la de delante y la ropa parece metida una dentro de otra. Tres alturas para
# dar profundidad: delante, una camiseta blanca sola (la más baja) y un jersey
# rojo; detrás, 1 px más alto para que se vea por encima, unos vaqueros y una
# camiseta gris sobre un jersey verde.
clothes = group("clothes", [0, 7, 0], [
    cube("tee_white", [0.5, 7, -7], [4.5, 8, -2], "white_edge", up="white_top"),
    cube("sweater_red", [-4.5, 7, -7], [-0.5, 9, -2], "red_edge", up="red_top"),
    cube("jeans", [0.5, 7, -1], [4.5, 10, 4], "denim_edge", up="denim_top"),
    cube("sweater_green", [-4.5, 7, -1], [-0.5, 9, 4], "green_edge"),
    cube("tee_gray", [-4.5, 9, -1], [-0.5, 10, 4], "gray_edge", up="gray_top"),
])

drawer = cajon(m, "drawer", 0, clothes)

root = group("wardrobe", [0, 0, 0], [cabinet, drawer])


# ---------------------------------------------------------------- animaciones
animations = animaciones_cajon(m, drawer)

m.escribir(OUT_DIR, root, animations, visible_box=[2, 2.5, 0.75],
           mover=("drawer", "shirt", "tee", "sweater", "jeans"))
