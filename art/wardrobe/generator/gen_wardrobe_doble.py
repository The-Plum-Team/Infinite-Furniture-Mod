"""Genera el armario de dos puertas (2x2, .bbmodel, Bedrock): el cuerpo del alto
a 32 de ancho, con la tapa larga del de dos de ancho y dos puertas que abren
desde el centro. Dentro, un tabique: a la izquierda de quien mira, baldas con
ropa doblada; a la derecha, una barra con ropa colgada y unas botas.

Usa wardrobe_lib.py, que tiene que estar en la misma carpeta.
Uso:
    python gen_wardrobe_doble.py <carpeta_salida>
"""
import sys

from wardrobe_lib import (CLOTH, Lienzo, Modelo, animaciones_puertas, bajos_rows,
                          balda_por_debajo, con_bisagras, pared, pared_lateral, pila,
                          pintar_lateral_alto, pintar_patas, pintar_puerta, pintar_ropa,
                          pintar_tapa_larga, pintar_tiras, pintar_tiras_anchas,
                          por_columnas, shelf_rows, suelo_rows, tapa_larga)

OUT_DIR = sys.argv[1]
cv = Lienzo(128, 128)
draw, flat = cv.draw, cv.flat


# ---------------------------------------------------------------- textura
# Mismas reglas que los demás: cada píxel pertenece a una pieza, luz desde
# arriba a la izquierda, pasos de un tono entre vecinos (dos solo en rebajes y
# sombras) y los cambios de tono escalonados.

# Lo que comparte con los otros armarios: lateral alto con zócalo, puertas (la
# de la derecha de quien mira lleva el tirador a la izquierda y la otra al
# revés, para que los dos queden en el centro), tapa larga, tiras, patas y ropa.
pintar_lateral_alto(cv, side=(0, 0), stile_edge=(45, 0))
pintar_puerta(cv, door=(106, 0), door_edge=(104, 0), door_in=(14, 27), door_r=(0, 27))
pintar_tapa_larga(cv, top=(0, 52), edge_long=(0, 68), edge=(32, 68))
pintar_tiras_anchas(cv, rail_top=(95, 61), rail_low=(95, 62), base_front=(95, 63))
pintar_tiras(cv, None, None, None, front_top=(106, 25), front_bottom=(106, 26))
pintar_patas(cv, 95, 52)
pintar_ropa(cv, {"white": (91, 68), "red": (96, 68), "denim": (101, 68),
                 "green": (106, 68), "gray": (111, 68)})
# Montante entre las puertas (1x25): hundido en la sombra de las dos hojas.
draw("mullion", 105, 0, list("3" + "4" * 22 + "33"))
# Bajos: las tablas largas de la tapa vistas desde abajo, un tono más oscuras.
draw("underside", 64, 52, bajos_rows(tapa_larga(), 31))

# Trasera 29x27: las tablas del de dos de ancho (A cols 0-2, B 4-7, C 9-11,
# D 13-15, E 17-20, F 22-24, G 26-27; juntas 3, 8, 12, 16, 21 y 25; canto
# derecho en sombra) alargadas como las del alto: goteos de largos distintos
# colgando de la sombra de la tapa, el centro en calma y vetas largas subiendo
# desde el suelo, más en el lado en sombra.
JUNTAS = (3, 8, 12, 16, 21, 25)
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
    [(4, 2), (5, 19), (4, 4)],        # 11 goteo y veta
    [(3, 3), (4, 18), (3, 4)],        # 12 junta
    [(5, 20), (4, 5)],                # 13 D, veta
    [(4, 3), (5, 22)],                # 14 goteo
    [(5, 25)],                        # 15
    [(3, 2), (4, 20), (3, 3)],        # 16 junta
    [(4, 2), (5, 23)],                # 17 E, goteo corto
    [(5, 16), (4, 9)],                # 18 veta larga
    [(4, 6), (5, 19)],                # 19 goteo largo
    [(5, 23), (4, 2)],                # 20 veta corta
    [(3, 3), (4, 17), (3, 5)],        # 21 junta
    [(5, 25)],                        # 22 F
    [(4, 4), (5, 14), (4, 7)],        # 23 goteo y veta
    [(5, 21), (4, 4)],                # 24 veta
    [(3, 2), (4, 19), (3, 4)],        # 25 junta
    [(4, 3), (5, 18), (4, 4)],        # 26 G, goteo y veta
    [(5, 15), (4, 10)],               # 27 veta larga (lado en sombra)
    [(3, 2), (4, 22), (3, 1)],        # 28 canto en sombra
]
draw("back", 46, 0,
     ["".join("2" if c in JUNTAS or c == 28 else "3" for c in range(29))]
     + por_columnas(BACK_COLUMNS)
     + ["".join("2" if c == 28 else "3" if c in JUNTAS or runs[-1][0] == 4 else "4"
                for c, runs in enumerate(BACK_COLUMNS))])

# Dentro, un tabique parte el armario en dos: a la izquierda de quien mira (+X)
# las baldas, con las mismas paredes que el alto; a la derecha el ropero, un
# solo hueco alto con la sombra de la tapa arriba y la oclusión del suelo abajo.
ROPERO = [(0, 25)]
# Trasera por dentro (29x27, columna 0 = +X): las tablas vistas desde dentro (en
# espejo, juntas 3, 7, 12, 16, 20 y 25; rincones 0 y 28; la 14 queda tras el
# tabique), un tono por debajo de las de fuera, con la sombra bajo cada balda
# en el lado de las baldas y bajo la tapa en el del ropero.
BASE_IN = [3 if c in (0, 3, 7, 12, 14, 16, 20, 25, 28) else 4 for c in range(29)]
back_baldas = pared(BASE_IN[:15], 2, [
    ("222233322222222", "000000000000000"),
    ("111122211111111", "000000000000000"),
    ("111122211111111", "000000000000000"),
])
back_ropero = pared(BASE_IN[15:], 2, [("22333222222222", "00000000000000")], ROPERO)
draw("back_in", 75, 0, [a + b for a, b in zip(back_baldas, back_ropero)])

# Paredes del ropero (15x27, columna 0 = el canto de la puerta): las mismas
# tablas que se apagan hacia el fondo, con un solo hueco. Las dos paredes de
# fuera llevan junto a la puerta las placas de las bisagras.
ROPERO_PARED = pared([5, 5, 5, 5, 5, 3, 4, 4, 4, 4, 3, 4, 4, 3, 2], None,
                     [("111112222333344", "000000000000011")], ROPERO)
draw("side_in", 15, 0, con_bisagras(pared_lateral()))
draw("side_in_h", 30, 0, con_bisagras(ROPERO_PARED))
# Caras del tabique (13x25): el mismo dibujo que la pared de enfrente, sin la
# columna del canto (el tabique empieza tras el montante) ni las filas de la
# tapa y el suelo.
draw("divider_in", 28, 27, [fila[1:14] for fila in pared_lateral()[1:26]])
draw("divider_in_h", 41, 27, [fila[1:14] for fila in ROPERO_PARED[1:26]])

# Techo por dentro (32x16, fila 0 = el fondo): las tablas de la tapa vistas
# desde abajo y en sombra, tres tonos por debajo y la tabla del fondo uno más.
draw("ceiling", 32, 52, ["".join(str(max(2, int(ch) - (4 if r < 5 else 3)))
                                  for ch in tapa_larga()[15 - r]) for r in range(16)])

# Baldas del lado de las baldas (14 de ancho): la luz entra por delante y cada
# columna se hunde en la sombra a su altura. El suelo de todo el armario (29),
# tres tablas a lo ancho con la sombra también a los dos lados del tabique.
COLUMNAS_14 = [2, 3, 3, 4, 3, 2, 3, 4, 3, 3, 2, 3, 2, 3]
draw("shelf_top", 48, 68, shelf_rows(6, 0, COLUMNAS_14))
draw("floor_top", 62, 68, suelo_rows(29, (13, 15)))
draw("shelf_front", 95, 60, ["56666666666665"])
draw("shelf_under", 48, 84, balda_por_debajo(shelf_rows(6, 0, COLUMNAS_14)))

# Ropa colgada (7 de fondo, 2 de grueso): cada fila de la prenda es de un tipo.
# Por el lado se ve la prenda entera: hombros que caen desde el cuello, un
# pliegue con luz a la izquierda y otro en sombra, la tapeta con botones y las
# mangas a los lados hasta el puño; por delante, el canto, que es lo que más se
# ve con la puerta abierta: hombro claro, manga, puño y bajo en sombra.
FILAS = {
    "H": ("1123211", "32"),        # hombros
    "S": ("1322211", "21"),        # manga
    "s": ("1322211", "31"),        # manga, pliegue con luz en el canto
    "b": ("132{}211", "21"),       # manga y botón
    "P": ("3322213", "33"),        # puño
    "C": ("2322211", "21"),        # cuerpo
    "c": ("232{}211", "21"),       # cuerpo y botón
    "W": ("1111111", "11"),        # cintura
    "F": ("2332211", "22"),        # falda, pliegue con luz
    "B": ("0111110", "10"),        # bajo
}
# (tela, plan de filas de arriba abajo, botón: un tono de la tela o latón)
COLGADAS = {
    "camisa_blanca": ("white", "HSbSsbPcCCcB", "3"),
    "abrigo": ("gray", "HSSbSsSbSPcCCcCCcB", "c"),
    "camisa_roja": ("red", "HSbSsbPcCCcB", "3"),
    "vestido": ("green", "HCCCWFFFFCCCFFFB", "3"),
    "chaqueta": ("denim", "HSbSsbSPcCcCB", "c"),
}
x = 120
for i, (nombre, (tela, plan, boton)) in enumerate(COLGADAS.items()):
    lado = [FILAS[k][0].format(boton) for k in plan]
    canto = [FILAS[k][1] for k in plan]
    draw(f"{nombre}_side", 54 + 7 * i, 27, lado, CLOTH[tela])
    draw(f"{nombre}_edge", (120, 122, 124, 126, 120)[i], (0, 0, 0, 0, 19)[i], canto, CLOTH[tela])
# Hombros por arriba y bajos por debajo (2x7), uno por tela.
for i, tela in enumerate(("white", "gray", "red", "green", "denim")):
    draw(f"{tela}_hombros", 89 + 2 * i, 27, ["22", "33", "33", "32", "33", "33", "22"], CLOTH[tela])
    draw(f"{tela}_bajo", 89 + 2 * i, 34, ["10", "11", "11", "11", "11", "11", "10"], CLOTH[tela])

# Barra de latón (14 de largo): clara por arriba con un brillo hacia la luz, el
# frente a medio tono y oscura por debajo; los ganchos, de latón medio.
draw("barra_top", 99, 27, ["cccdccccccccbb"])
draw("barra_front", 99, 28, ["bbbcbbbbbbbbab"])
draw("barra_bottom", 99, 29, ["aaaaaaaaaaaaaa"])
draw("gancho", 113, 27, ["b"])
# Botas de cuero, con los oscuros de la paleta: caña con el borde de arriba
# claro y la suela en sombra; la boca, honda.
draw("bota", 99, 31, ["43", "32", "21", "10"])
draw("bota_boca", 101, 31, ["10", "00"])
draw("pie", 103, 31, ["32", "21"])
draw("bota_suela", 105, 31, ["00", "00"])

# Superficies secundarias.
flat("interior", 111, 52, 4, 4, 2, 2)
flat("dark", 115, 52, 4, 4, 3, 3)
flat("edge", 119, 52, 4, 4, 6, 6)


# ---------------------------------------------------------------- geometría
m = Modelo("wardrobe_doble", cv)
cube, group = m.cube, m.group

# Mueble (frente al norte, -Z): 32x32, el cuerpo 1 px hundido por delante y las
# puertas sobresaliendo ese píxel; entre ellas, el montante.
cabinet = group("cabinet", [0, 0, 0], [
    cube("foot_fl", [-15.5, 0, -7], [-13.5, 1, -5], "plinth"),
    cube("foot_fr", [13.5, 0, -7], [15.5, 1, -5], "plinth"),
    cube("foot_bl", [-15.5, 0, 6], [-13.5, 1, 8], "plinth"),
    cube("foot_br", [13.5, 0, 6], [15.5, 1, 8], "plinth"),
    cube("bottom", [-15.5, 1, -7], [15.5, 2, 8], "base_front",
         up="interior", down="underside"),
    cube("side_left", [-15.5, 2, -7], [-14.5, 29, 8], "edge",
         west="side", east="side_in_h~",
         north="stile_edge", south="stile_edge"),
    cube("side_right", [14.5, 2, -7], [15.5, 29, 8], "edge",
         east="side", west="side_in",
         north="stile_edge", south="stile_edge"),
    cube("back", [-14.5, 2, 7], [14.5, 29, 8], "edge",
         south="back", north="back_in"),
    cube("rail_low", [-14.5, 2, -7], [14.5, 3, -6], "interior",
         north="rail_low"),
    cube("rail_top", [-14.5, 28, -7], [14.5, 29, -6], "interior",
         north="rail_top"),
    cube("mullion", [-0.5, 3, -7], [0.5, 28, -6], "interior",
         north="mullion"),
    cube("top", [-16, 29, -8], [16, 32, 8], "top_edge",
         up="top", down="ceiling",
         north="top_edge_long", south="top_edge_long~"),
    # Dentro: suelo enrasado con el travesaño de abajo, el tabique y dos baldas
    # en el lado de las baldas.
    cube("floor", [-14.5, 2, -6], [14.5, 3, 7], "dark", up="floor_top"),
    cube("divider", [-0.5, 3, -6], [0.5, 28, 7], "dark",
         east="divider_in~", west="divider_in_h"),
    cube("shelf_low", [0.5, 11, -6], [14.5, 12, 7], "dark",
         up="shelf_top", north="shelf_front", down="shelf_under"),
    cube("shelf_high", [0.5, 19, -6], [14.5, 20, 7], "dark",
         up="shelf_top", north="shelf_front", down="shelf_under"),
])

# Lado de las baldas: tres pilas por hueco, como en el alto, ordenadas de otra
# manera y algunas un píxel más al fondo.
X3 = (9.75, 5.5, 1.25)
PILAS = {
    3: ([("denim", 3), ("denim", 3)], [("green", 2), ("white", 1), ("red", 2)],
        [("gray", 1), ("white", 1), ("gray", 1)]),
    12: ([("white", 1), ("red", 2), ("gray", 1)], [("green", 2), ("green", 2), ("white", 1)],
         [("denim", 3)]),
    20: ([("red", 2), ("red", 2), ("white", 1)], [("gray", 1), ("white", 1), ("gray", 1)],
         [("denim", 3), ("white", 1)]),
}
FONDO = {3: (0, 1, 0), 12: (1, 0, 1), 20: (0, 0, 1)}
clothes = group("clothes", [7.5, 3, 0],
                [c for y0, pilas in PILAS.items() for i, prendas in enumerate(pilas)
                 for c in pila(m, f"stack_{y0}_{i}", X3[i], y0, prendas, FONDO[y0][i])])

# Lado del ropero: la barra a lo ancho bajo la tapa y, colgadas de ella con su
# gancho, cinco prendas de largos distintos (de la izquierda de quien mira a la
# derecha: camisa, abrigo largo, camisa, vestido y chaqueta). Debajo de las
# cortas, un par de botas, delante de las prendas.
X_COLGADAS = (-3, -5.75, -8.5, -11.25, -14)
colgado = [cube("barra", [-14.5, 25, 0.5], [-0.5, 26, 1.5], "barra_front",
                up="barra_top", down="barra_bottom", east="gancho", west="gancho")]
for x0, (nombre, (tela, plan, _)) in zip(X_COLGADAS, COLGADAS.items()):
    largo = len(plan)
    colgado += [
        cube(f"{nombre}_gancho", [x0 + 0.5, 24, 0.5], [x0 + 1.5, 25, 1.5], "gancho"),
        cube(nombre, [x0, 24 - largo, -2], [x0 + 2, 24, 5], f"{nombre}_side",
             north=f"{nombre}_edge", south=f"{nombre}_edge",
             up=f"{tela}_hombros", down=f"{tela}_bajo"),
    ]
for lado, x0 in (("l", -8), ("r", -5.5)):
    colgado += [
        cube(f"bota_{lado}", [x0, 3, -4], [x0 + 2, 7, -2], "bota",
             up="bota_boca", down="bota_suela"),
        cube(f"pie_{lado}", [x0, 3, -6], [x0 + 2, 4, -4], "pie", down="bota_suela"),
    ]
hanging = group("hanging", [-7.5, 3, 0], colgado)

# Puertas: cada una gira sobre su canto de fuera y abren desde el centro.
door_left = group("door_left", [-14.5, 15.5, -7], [
    cube("door_left", [-14.5, 3, -8], [-0.5, 28, -7], "door_edge",
         north="door", south="door_in", up="front_top", down="front_bottom"),
])
door_right = group("door_right", [14.5, 15.5, -7], [
    cube("door_right", [0.5, 3, -8], [14.5, 28, -7], "door_edge",
         north="door_r", south="door_in~", up="front_top", down="front_bottom"),
])

root = group("wardrobe", [0, 0, 0], [cabinet, clothes, hanging, door_left, door_right])


# ---------------------------------------------------------------- animaciones
animations = animaciones_puertas(m, [(door_left, 1), (door_right, -1)])

m.escribir(OUT_DIR, root, animations, visible_box=[3, 3.5, 1.5], mover=("door",))
