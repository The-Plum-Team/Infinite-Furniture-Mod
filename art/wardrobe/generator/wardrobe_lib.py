"""Piezas comunes de los armarios: paleta, PNG, lienzo de textura, texturas
compartidas (tapa, patas, base, bajos, laterales, cajón, puerta, paredes de
dentro, baldas, ropa), montaje del .bbmodel, el cajón, las pilas de ropa y las
animaciones de cajones y puertas.

Las texturas están dibujadas a mano: cada cara es una cuadrícula de dígitos
0-9 que indexan la paleta RAMP. No hay nada aleatorio.
"""
import base64
import json
import os
import struct
import uuid
import zlib


# ---------------------------------------------------------------- PNG
def png_bytes(pixels, w, h):
    raw = b"".join(
        b"\x00" + bytes(c for px in pixels[y * w:(y + 1) * w] for c in px)
        for y in range(h)
    )

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- paleta
# 2-8: los 7 tonos de oak_planks vanilla; 0-1: oscuros fríos para sombras;
# 9: brillo cálido.
RAMP = [c + (255,) for c in [
    (60, 42, 34), (84, 62, 40),
    (103, 80, 44), (126, 98, 55), (150, 116, 65), (159, 132, 77),
    (175, 143, 85), (184, 148, 95), (194, 157, 98),
    (214, 181, 120),
]]

# Latón de los tiradores (acento): a oscuro, b medio, c claro, d brillo.
BRASS = {"a": (121, 83, 33, 255), "b": (186, 136, 52, 255),
         "c": (226, 182, 84, 255), "d": (249, 224, 150, 255)}

# Telas (otro material, como el latón): 0 sombra honda, 1 sombra, 2 base, 3 luz.
# Paleta de análogos cálidos, elegida con el artifact de colores: vecinos de la
# madera en el círculo cromático (óxido y mostaza), crema, gris topo y un
# vaquero oscuro como único frío. Las claves conservan el nombre de la tela que
# había antes en cada sitio: "red" es el óxido y "green" la mostaza.
CLOTH = {
    "white": [(208, 171, 130), (222, 199, 167), (236, 225, 204), (250, 247, 241)],   # crema
    "red": [(104, 26, 27), (144, 44, 37), (185, 65, 47), (206, 105, 77)],   # óxido
    "green": [(124, 83, 25), (167, 120, 33), (209, 162, 42), (217, 191, 85)],   # mostaza
    "gray": [(80, 85, 100), (102, 109, 129), (154, 140, 128), (176, 167, 157)],   # topo
    "denim": [(19, 25, 48), (33, 48, 85), (47, 74, 122), (64, 105, 156)],   # vaquero oscuro
}


# ---------------------------------------------------------------- lienzo
class Lienzo:
    """Textura en construcción: píxeles y regiones con nombre (x, y, ancho, alto)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.tex = [(0, 0, 0, 0)] * (w * h)
        self.regions = {}

    def put(self, x, y, c):
        self.tex[y * self.w + x] = c

    def region(self, name, x, y, w, h):
        self.regions[name] = (x, y, w, h)

    def draw(self, name, x0, y0, rows, pal=None):
        """Dibujo a mano: cada dígito es un índice de RAMP (o de `pal`); a-d, latón."""
        self.region(name, x0, y0, len(rows[0]), len(rows))
        for j, row in enumerate(rows):
            assert len(row) == len(rows[0]), (name, j, row)
            for i, ch in enumerate(row):
                if ch in BRASS:
                    c = BRASS[ch]
                elif pal:
                    c = pal[int(ch)] + (255,)
                else:
                    c = RAMP[int(ch)]
                self.put(x0 + i, y0 + j, c)

    def flat(self, name, x0, y0, w, h, top, body):
        self.draw(name, x0, y0, [str(top) * w] + [str(body) * w] * (h - 1))

    def garment(self, name, x0, y0, cloth, edge, top=None):
        """Prenda doblada en una columna de 5x8: arriba la cara superior (4x5) y
        debajo los cantos (5x3, fila 0 arriba). `top` se dibuja tal como se ve
        desde delante del mueble (fila 0 = lo más lejano, columna 0 = izquierda) y
        se gira 180°, porque en la textura la fila 0 es el lado del frente y la
        columna 0 queda a la derecha de quien mira."""
        pal = CLOTH[cloth]
        if top:
            self.draw(name + "_top", x0, y0, [row[::-1] for row in top[::-1]], pal)
        self.draw(name + "_edge", x0, y0 + 5, edge, pal)

    def png(self):
        return png_bytes(self.tex, self.w, self.h)


# ---------------------------------------------------------------- texturas comunes
# Tapa: tres tablas de delante (fila 0) a atrás (fila 15): A cols 0-4, B 6-9,
# C 11-15, juntas en las cols 5 y 10. Lo que manda es el degradado a lo largo
# de las tablas: muy clara delante, una banda más oscura hacia atrás y la testa
# trasera algo más clara. Los cantos de cada tabla van un tono por encima del
# campo y las juntas uno o dos por debajo, siguiendo el mismo degradado; cada
# columna cambia de tono a su propia altura (tramos tono, largo).
TOP_COLUMNS = [
    [(9, 3), (8, 3), (7, 5), (6, 3), (7, 2)],          # 0  canto A
    [(8, 1), (7, 4), (6, 6), (5, 3), (6, 2)],          # 1  campo A
    [(8, 3), (7, 2), (6, 3), (5, 2), (6, 2), (5, 3), (6, 1)],  # 2  (veta 8-9)
    [(8, 2), (7, 4), (6, 5), (5, 4), (6, 1)],          # 3
    [(9, 2), (8, 4), (7, 5), (6, 3), (7, 2)],          # 4  canto A
    [(7, 2), (6, 3), (5, 7), (4, 3), (5, 1)],          # 5  junta
    [(9, 3), (8, 2), (7, 6), (6, 3), (7, 2)],          # 6  canto B
    [(8, 2), (7, 3), (6, 7), (5, 2), (6, 2)],          # 7  campo B
    [(8, 3), (7, 3), (6, 3), (5, 2), (6, 1), (5, 3), (6, 1)],  # 8  (veta 9-10)
    [(9, 2), (8, 3), (7, 6), (6, 4), (7, 1)],          # 9  canto B
    [(7, 2), (6, 4), (5, 6), (4, 3), (5, 1)],          # 10 junta
    [(9, 3), (8, 3), (7, 4), (6, 4), (7, 2)],          # 11 canto C
    [(8, 2), (7, 4), (6, 5), (5, 2), (6, 3)],          # 12 campo C
    [(8, 3), (7, 1), (6, 7), (5, 4), (6, 1)],          # 13
    [(8, 2), (7, 3), (6, 6), (5, 3), (6, 2)],          # 14
    [(8, 3), (7, 4), (6, 5), (5, 2), (6, 2)],          # 15 canto C (borde)
]


def por_columnas(columnas):
    """Filas a partir de columnas: cada columna es una lista de tramos (tono,
    largo) de arriba abajo, y todas tienen que sumar el mismo alto."""
    cols = [[str(t) for t, n in runs for _ in range(n)] for runs in columnas]
    alto = len(cols[0])
    assert all(len(c) == alto for c in cols), [len(c) for c in cols]
    return ["".join(c[r] for c in cols) for r in range(alto)]


def plank_top():
    cols = []
    for runs in TOP_COLUMNS:
        col = [str(t) for t, n in runs for _ in range(n)]
        assert len(col) == 16, runs
        cols.append(col)
    return ["".join(cols[c][r] for c in range(16)) for r in range(16)]


# Testas de las tres tablas (16x3; C cols 0-4, B 6-9, A 11-15, juntas 5 y 10):
# cada una con un bloque de luz centrado arriba, tono medio y sombra abajo.
TOP_EDGE_ROWS = [
    "7888767887678887",
    "6777656776567776",
    "5555545555455555",
]


def pintar_tapa(cv, top, edge, edge_side):
    """La tapa de 16x16 y sus cantos de 16x3; cada argumento es la posición (x, y)."""
    cv.draw("top", *top, plank_top())
    # Canto delantero: las testas, en espejo respecto a la tapa.
    cv.draw("top_edge", *edge, TOP_EDGE_ROWS)
    # Cantos laterales: el costado largo de una tabla, con la veta en horizontal
    # a distinta altura en cada fila.
    cv.draw("top_edge_side", *edge_side, [
        "7888888777888887",
        "6777766677777776",
        "5666666655566665",
    ])


def tramos(runs):
    """Fila a partir de tramos (tono, largo) de izquierda a derecha."""
    return "".join(str(t) * n for t, n in runs)


# Tapa 32x16: tres tablas largas de lado a lado, como en una cómoda de verdad
# (F filas 0-4, M 6-9, B 11-15; juntas en las filas 5 y 10). Dibujada como se
# ve desde delante (columna 0 = la izquierda de quien mira) y girada al pintar,
# porque en la cara de arriba la columna 0 cae a la derecha. Lo que manda es el
# degradado a lo largo de cada tabla: muy clara en la punta izquierda, más
# oscura hacia la derecha y la testa derecha algo más clara. Los cantos de
# cada tabla un tono por encima del campo, las juntas dos por debajo (sin bajar
# de 4), cada fila cambia de tono a su propia altura y cada tabla lleva una
# veta corta.
TAPA_LARGA = [
    [(9, 3), (8, 8), (7, 9), (6, 7), (7, 5)],                    # 0  canto F (delante)
    [(8, 2), (7, 10), (6, 9), (5, 7), (6, 4)],                   # 1
    [(8, 3), (7, 10), (6, 9), (5, 6), (6, 4)],                   # 2
    [(8, 2), (7, 11), (6, 2), (7, 4), (6, 4), (5, 6), (6, 3)],   # 3  veta
    [(9, 3), (8, 9), (7, 10), (6, 6), (7, 4)],                   # 4  canto F
    [(6, 2), (5, 10), (4, 15), (5, 5)],                          # 5  junta
    [(9, 5), (8, 4), (7, 9), (6, 8), (7, 6)],                    # 6  canto M
    [(8, 4), (7, 5), (6, 10), (5, 7), (6, 6)],                   # 7
    [(8, 4), (7, 6), (6, 3), (5, 3), (6, 3), (5, 8), (6, 5)],    # 8  veta
    [(9, 5), (8, 5), (7, 10), (6, 7), (7, 5)],                   # 9  canto M
    [(6, 4), (5, 6), (4, 16), (5, 6)],                           # 10 junta
    [(9, 2), (8, 12), (7, 8), (6, 7), (7, 3)],                   # 11 canto B
    [(8, 3), (7, 11), (6, 9), (5, 6), (6, 3)],                   # 12
    [(8, 3), (7, 12), (6, 2), (7, 4), (6, 3), (5, 6), (6, 2)],   # 13 veta
    [(8, 2), (7, 13), (6, 8), (5, 6), (6, 3)],                   # 14
    [(8, 4), (7, 9), (6, 10), (5, 7), (6, 2)],                   # 15 borde de atrás
]


def tapa_larga():
    """Filas de la tapa larga tal como van en la textura (girada: en la cara de
    arriba la columna 0 cae a la derecha de quien mira)."""
    return [tramos(r)[::-1] for r in TAPA_LARGA]


def pintar_tapa_larga(cv, top, edge_long, edge):
    """Tapa de 32x16 de los muebles de dos de ancho, su canto largo de 32x3 y los
    costados de 16x3; cada argumento es la posición (x, y)."""
    cv.draw("top", *top, tapa_larga())
    # Canto delantero (32x3): el costado largo de la tabla de delante, con el mismo
    # degradado que su canto en la tapa y cada fila un tono más abajo, cambiando de
    # tono a su propia altura; las puntas, un tono más oscuras. Detrás va en espejo,
    # para que la punta clara siga cayendo donde la de la tapa.
    cv.draw("top_edge_long", *edge_long, [
        tramos([(7, 1), (8, 11), (7, 9), (6, 6), (7, 4), (6, 1)]),
        tramos([(6, 1), (7, 12), (6, 9), (5, 6), (6, 3), (5, 1)]),
        tramos([(5, 1), (6, 10), (5, 11), (4, 6), (5, 3), (4, 1)]),
    ])
    # Costados de la tapa (16x3): las testas de las tres tablas, como el canto
    # delantero del 1x1 (las juntas caen en las mismas filas que en la tapa).
    cv.draw("top_edge", *edge, TOP_EDGE_ROWS)


def pintar_tiras_anchas(cv, rail_top, rail_low, base_front):
    """Tiras de 1 px de los muebles de dos de ancho: la sombra bajo la tapa (más
    honda en las puntas y donde baja el montante del centro), la de encima de la
    base y el frente de la base, claro en el centro y oscuro en las esquinas como
    en el 1x1. Cada argumento es la posición (x, y)."""
    cv.draw("rail_top", *rail_top, ["3" + "4" * 13 + "3" + "4" * 13 + "3"])
    cv.draw("rail_low", *rail_low, ["3" * 29])
    cv.draw("base_front", *base_front, ["3444" + "5" * 22 + "44433"])


def pintar_patas(cv, x, y):
    """Patas: caras de 2x1 con el lado izquierdo iluminado; arriba/abajo de 2x2."""
    cv.draw("plinth", x, y, ["54" + "4" * 14, "43" + "4" * 14] + ["4" * 16] * 6)


def pintar_tiras(cv, rail_top, rail_low, base_front, front_top, front_bottom):
    """Tiras de 1 px: sombra bajo la tapa y sobre la base, el frente de la base y
    los cantos de arriba y abajo de la pieza delantera (cajón o puerta). Las de
    posición None no se dibujan (un mueble más ancho lleva las suyas)."""
    for nombre, pos, fila in (("rail_top", rail_top, "3444444444443"),
                              ("rail_low", rail_low, "3333333333333"),
                              ("base_front", base_front, "344455555544433"),
                              ("front_top", front_top, "78888888888887"),
                              ("front_bottom", front_bottom, "34444444444443")):
        if pos:
            cv.draw(nombre, *pos, [fila])


def pintar_lateral_bajo(cv, side, stile_edge):
    """Lateral de un bloque de alto (15x11) y el canto de su montante (1x11);
    cada argumento es la posición (x, y)."""
    # Laterales 15x11, de moldura ancha: el montante delantero con el filo exterior
    # claro, su cuerpo y una sola línea de sombra por dentro (col 2); el trasero con
    # la moldura cogiendo luz por dentro (col 12) y el canto exterior en sombra. Cada
    # columna degrada de claro arriba a oscuro abajo a su propia altura. Los
    # travesaños, una fila de luz y debajo la sombra que echan sobre el plafón; el
    # plafón degrada de 6 a 4 con el corte en escalones anchos, sin dientes.
    cv.draw("side", *side, [
        "344444444444443",
        "765777777777765",
        "763444444444665",
        "764666666666765",
        "764666666655665",
        "664556665555654",
        "653555555544654",
        "653445554444654",
        "553444444444654",
        "545777777777743",
        "543444444444643",
    ])
    cv.draw("stile_edge", *stile_edge, list("35666554445"))


def pintar_cajon(cv, pos):
    """Frente del cajón con su tirador y la caja de dentro; `pos` da la posición
    (x, y) de cada región."""
    # Frente del cajón 14x9 (el foco del mueble, el tono más claro tras la tapa):
    # canto superior degradado hacia el centro, bisel claro en los laterales,
    # cuerpo del marco, rebaje un tono más oscuro (dos abajo, en la sombra del
    # panel), panel plano y tirador de latón con dos patas y su sombra. Simétrico.
    cv.draw("front", *pos["front"], [
        "56788888888765",
        "76666666666667",
        "76555555555567",
        "7657c7777c7567",
        "7657bcdccb7567",
        "76576555567567",
        "65444444444456",
        "65555555555556",
        "34444444444443",
    ])
    cv.draw("front_side", *pos["front_side"], list("677777665"))
    cv.flat("drawer_wood", *pos["drawer_wood"], 16, 16, 5, 4)
    # Caja del cajón: tablas puestas en horizontal, así que la veta corre a lo
    # largo de cada fila (tramos de distinto largo que cortan en columnas
    # distintas), con la luz arriba, la sombra abajo y las testas más oscuras.
    # Laterales por fuera (12x7, columna 0 = el frente).
    cv.draw("drawer_side_out", *pos["drawer_side_out"], [
        "566666666665",
        "455566665554",
        "455555555444",
        "444555544444",
        "444444444444",
        "344444444443",
        "333333333333",
    ])
    # Por dentro todo va un tono más abajo: el interior del cajón está en sombra.
    # Solo asoman las 3 filas de arriba; la de abajo, junto al fondo, es la más
    # oscura. Las demás quedan tapadas por el fondo.
    cv.draw("drawer_side_in", *pos["drawer_side_in"], [
        "455555555554",
        "444555555444",
        "334444444433",
        "333333333333",
        "333333333333",
        "333333333333",
        "333333333333",
    ])
    # Trasera por dentro (11x7): es la pared que se ve de frente al abrir.
    cv.draw("drawer_back_in", *pos["drawer_back_in"], [
        "45555555554",
        "44555555444",
        "33444444433",
        "33333333333",
        "33333333333",
        "33333333333",
        "33333333333",
    ])
    # Dorso del frente (14x9): solo asoma desde atrás.
    cv.draw("drawer_front_in", *pos["drawer_front_in"], [
        "45666666666654",
        "45555555555554",
        "34444444444443",
        "34444444444443",
        "34444444444443",
        "33444444444433",
        "33333333333333",
        "33333333333333",
        "33333333333333",
    ])
    # Fondo (11x11, fila 0 = el frente): solo se ve en las rendijas entre prendas
    # y junto a las paredes, que son hondas y oscuras.
    cv.draw("drawer_floor", *pos["drawer_floor"], ["22222222222"] * 11)
    # Cantos de arriba de las paredes, vistos desde arriba: claros, con las
    # puntas un tono más oscuras.
    cv.draw("rim_side", *pos["rim_side"], [c for c in "566666666665"])
    cv.draw("rim_back", *pos["rim_back"], ["56666666665"])
    # Por debajo, lo que se ve del cajón abierto desde abajo: el fondo (11x11,
    # fila 0 = atrás) son las tablas del centro de la tapa, un tono más oscuras,
    # como los bajos del mueble. Los cantos de abajo de las paredes, en sombra,
    # con las puntas un tono más oscuras.
    tapa = plank_top()
    cv.draw("drawer_under", *pos["drawer_under"],
            ["".join(str(max(2, int(ch) - 1)) for ch in tapa[11 - r][3:14]) for r in range(11)])
    cv.draw("drawer_rim_low", *pos["drawer_rim_low"], list("344444444443"))
    cv.draw("drawer_back_low", *pos["drawer_back_low"], ["34444444443"])


# Bajos del mueble: las mismas tablas que la tapa vistas desde abajo, un tono
# más oscuras (el juego ya pinta las caras de abajo a media luz, así que quedan
# como la tapa en sombra). La cara de abajo tiene la fila 0 atrás: la fila r de
# los bajos cae bajo la fila 15 - r de la tapa, y la fila 0 de la tapa es el
# vuelo delantero, que no tiene nada debajo.
def bajos_rows(top, ancho):
    """Filas de los bajos (ancho x 15) a partir de las filas de la tapa (fila 0
    = delante, columna 0 = x mínima)."""
    return ["".join(str(max(2, int(ch) - 1)) for ch in top[15 - r][:ancho]) for r in range(15)]


def pintar_bajo(cv, underside):
    """Bajos de 15x15 de los muebles de un bloque de ancho; `underside` es la
    posición (x, y)."""
    cv.draw("underside", *underside, bajos_rows(plank_top(), 15))


# Puerta 14x25, el lenguaje del frente del cajón estirado a una puerta de
# bastidor: canto de arriba degradado, montantes con bisel claro que se apagan
# hacia abajo (el derecho antes que el izquierdo), dos plafones (el de arriba el
# doble de alto) con su rebaje (dos tonos más oscuro abajo, en la sombra del
# plafón), travesaño intermedio y tirador vertical de latón en el montante
# izquierdo, a media altura, con su sombra a la derecha. La bisagra va a la
# derecha de quien mira.
DOOR_ROWS = [
    "56788888888765",
    "76666666666667",
    "76555555555567",
    "76577777777567",
    "76576666667567",
    "76576666667567",
    "76576666667567",
    "76576666667567",
    "76576666667567",
    "76576666667567",
    "76576666667567",
    "7c576666667567",
    "7d476666667567",
    "6c344444444456",
    "7c566666666667",
    "7b455555555567",
    "76477777777567",
    "76576666667567",
    "65576666667556",
    "65576666667556",
    "65575555557556",
    "65444444444456",
    "65555555555556",
    "55555555555555",
    "34444444444443",
]


# Dorso de la puerta (14x25): el envés del mismo bastidor con sus dos plafones,
# un tono más oscuro que por delante y sin el tirador (en su columna va lo que
# hay al otro lado de la puerta, en espejo). Al abrir se ve entero.
def dorso(rows):
    out = []
    for row in rows:
        row = list(row)
        row[1], row[2] = row[12], row[11]
        out.append("".join(str(max(2, int(ch) - 1)) for ch in row))
    return out




# Herrajes de latón, como los tiradores. Tres bisagras por puerta (arriba, en
# medio y abajo), cada una de 2x3 con la luz arriba a la izquierda: en la pared,
# la placa; en el dorso de la puerta, la cazoleta, junto al canto de la
# bisagra. En el otro lado, el imán del cierre a la altura del tirador.
BISAGRAS = (2, 11, 20)                     # primera fila de cada bisagra en la puerta
PLACA = ["db", "cb", "ba"]
CAZOLETA = ["cb", "bb", "ba"]
IMAN = ["cb", "ba"]


def con_herraje(rows, dibujo, filas, col=0):
    """Copia de `rows` con `dibujo` estampado a partir de cada fila de `filas`,
    en las columnas col y col + 1."""
    out = [list(f) for f in rows]
    for f0 in filas:
        for j, trozo in enumerate(dibujo):
            out[f0 + j][col:col + 2] = list(trozo)
    return ["".join(f) for f in out]


def con_bisagras(rows):
    """Pared de dentro del lado de la bisagra (columna 0 = el canto de la
    puerta): la pared empieza una fila por encima de la puerta."""
    return con_herraje(rows, PLACA, [f + 1 for f in BISAGRAS])


def con_iman(rows):
    """Pared de dentro del lado donde cierra la puerta, con el imán."""
    return con_herraje(rows, IMAN, [13])


def tirador_a_la_derecha(rows):
    """La misma puerta con el tirador en el montante derecho, para la hoja
    izquierda de un armario de dos puertas: el montante izquierdo se queda como
    el derecho y el tirador pasa a la columna 12, con su sombra a la derecha
    (la luz sigue viniendo de la izquierda)."""
    out = []
    for row in rows:
        r = list(row)
        if row[1] in BRASS:
            r[1], r[2] = row[12], row[11]
            r[12], r[13] = row[1], row[2]
        out.append("".join(r))
    return out


def pintar_puerta(cv, door, door_edge, door_in, door_r=None):
    """Puerta de 14x25 (bisagra a la derecha de quien mira), sus cantos de 1x25 y
    su dorso; con `door_r`, también la hoja con el tirador a la derecha. Cada
    argumento es la posición (x, y)."""
    cv.draw("door", *door, DOOR_ROWS)
    # Cantos de la puerta: claros arriba, apagándose hacia abajo.
    cv.draw("door_edge", *door_edge, list("6777777777777676666665655"))
    # Dorso con las cazoletas de las bisagras en el canto de la columna 0 (la
    # puerta que tenga la bisagra al otro lado lo lleva en espejo).
    cv.draw("door_in", *door_in, con_herraje(dorso(DOOR_ROWS), CAZOLETA, BISAGRAS))
    if door_r:
        cv.draw("door_r", *door_r, tirador_a_la_derecha(DOOR_ROWS))


# Laterales 15x27, la misma moldura ancha que el 1x1 con dos plafones (el
# travesaño de en medio a la altura del de la puerta) y abajo un zócalo macizo:
# el labio con luz y la cara del travesaño degradando hasta la sombra del suelo.
def pintar_lateral_alto(cv, side, stile_edge):
    """Lateral de dos bloques de alto (15x27) y el canto de su montante (1x27);
    cada argumento es la posición (x, y)."""
    cv.draw("side", *side, [
        "344444444444443",
        "765777777777765",
        "763444444444665",
        "764666666666765",
        "764666666666765",
        "764666666655765",
        "764556665555765",
        "764555555555765",
        "764555555555765",
        "764555555555765",
        "764555555544655",
        "664445554444654",
        "654444444444654",
        "654444444444654",
        "655777777777754",
        "653444444444654",
        "653666666666654",
        "653666666655654",
        "653556665555654",
        "553555555555654",
        "543555555544644",
        "543445554444644",
        "543444444444643",
        "545777777777743",
        "545666666666543",
        "544555666555443",
        "543444444444343",
    ])
    cv.draw("stile_edge", *stile_edge, list("356666666655555554444444445"))


# Dentro, las paredes son tablas como la trasera, con la luz entrando por la
# puerta. Cada hueco va de la fila en sombra bajo su balda (o bajo la tapa) a la
# de oclusión sobre la balda de abajo; las filas 9, 17 y 26 quedan detrás de
# baldas y suelo. De cada columna cuelga un goteo de sombra y sube una veta desde
# el pie, de largos distintos en cada hueco: en las tablas, uno o dos por tabla
# y nunca dos iguales al lado.
HUECOS = [(0, 8), (10, 16), (18, 25)]


def pared(base, sombra, marcas, huecos=HUECOS):
    """Filas de una pared de 27 de alto. `base`: tono de cada columna; `sombra`:
    tono de la fila bajo la balda (None = base - 1); `marcas`: por hueco, el
    largo del goteo y de la veta de cada columna, en dos cadenas de dígitos;
    `huecos`: (fila en sombra, última fila) de cada hueco."""
    rows = []
    for r in range(27):
        row = ""
        for c, t in enumerate(base):
            for (a, b), (goteo, veta) in zip(huecos, marcas):
                if a <= r <= b:
                    if r == a and sombra is not None:
                        t = sombra
                    elif r - a <= int(goteo[c]) or b - r <= int(veta[c]):
                        t -= 1
                    break
            else:
                t -= 1
            row += str(max(2, t))
        rows.append(row)
    return rows




def pared_lateral():
    """Paredes de dentro de los laterales del armario alto (15x27, columna 0 =
    el canto de la puerta): tres tablas que se apagan hacia el fondo (5, 4 y 4
    con la última columna en la oclusión del rincón), juntas un tono por debajo
    de la tabla más oscura."""
    return pared([5, 5, 5, 5, 5, 3, 4, 4, 4, 4, 3, 4, 4, 3, 2], None, [
        ("111112222333344", "000000000000011"),
        ("000001111222233", "000000000000011"),
        ("000001111222233", "000000000000011"),
    ])


# Baldas de dentro (13x13, fila 0 = el frente): una tabla que recibe luz por
# delante y se hunde en la sombra hacia el fondo, cambiando de tono a distinta
# altura en cada columna.
SHELF_COLUMNS = [2, 3, 3, 4, 3, 2, 3, 4, 3, 3, 2, 3, 2]   # filas en 6 antes de bajar


def shelf_rows(light, depth_shift, columnas=SHELF_COLUMNS):
    """Filas de una balda de 13 de fondo; `columnas` da, por columna, cuántas
    filas van en el tono de luz antes de bajar."""
    rows = []
    for r in range(13):
        row = ""
        for c, n in enumerate(columnas):
            if r < n:
                t = light
            elif r < n + 4 + depth_shift:
                t = light - 1
            elif r < n + 8 + depth_shift:
                t = light - 2
            else:
                t = light - 3
            row += str(t)
        rows.append(row)
    return rows



def suelo_rows(ancho, pegadas=()):
    """Suelo de dentro (13 de fondo, fila 0 = la puerta): tres tablas a lo ancho,
    la de delante clara con su canto, la del medio un tono menos y la del fondo
    otro más; las juntas en sombra y un tono menos pegado a las paredes y a las
    columnas `pegadas` (junto a lo que se apoye en el suelo, como un tabique)."""
    tono = [6, 5, 5, 5, 3, 4, 4, 4, 2, 3, 3, 3, 3]
    sombra = {0, ancho - 1} | set(pegadas)
    return ["".join(str(max(2, tono[r] - (c in sombra))) for c in range(ancho)) for r in range(13)]


def balda_por_debajo(rows):
    """Cara de abajo de una balda: las mismas tablas vistas desde abajo (en la
    cara de abajo la fila 0 es el fondo) y dos tonos más oscuras, en la sombra
    del hueco."""
    return ["".join(str(max(2, int(ch) - 2)) for ch in fila) for fila in reversed(rows)]


def pintar_ropa(cv, pos):
    """Ropa doblada, leída por bandas como se ve una prenda de verdad: cuello al
    fondo, una franja de luz encima del pliegue y el borde de delante cayendo en
    sombra; cada banda se apaga un poco hacia la derecha. Las prendas que van
    debajo de otra solo enseñan los cantos y van más oscuras.
    `pos` da la columna (x, y) de 5x8 de cada prenda."""
    cv.garment("white", *pos["white"], "white", ["33221", "22110", "11000"],
               ["3113", "2222", "3332", "2221", "1110"])
    cv.garment("red", *pos["red"], "red", ["33322", "11110", "11000"],
               ["3003", "2112", "3332", "2221", "1110"])
    # Vaqueros: cinturilla con el botón de latón y la bragueta debajo.
    cv.garment("denim", *pos["denim"], "denim", ["33332", "11111", "22210"],
               ["1c11", "2122", "3332", "2221", "1110"])
    cv.garment("green", *pos["green"], "green", ["22211", "11000", "00000"])
    cv.garment("gray", *pos["gray"], "gray", ["33221", "22110", "11000"],
               ["3113", "2222", "3332", "2221", "1110"])


# ---------------------------------------------------------------- geometría
def uid():
    return str(uuid.uuid4())


def face_size(size, face):
    sx, sy, sz = size
    return {"north": (sx, sy), "south": (sx, sy), "east": (sz, sy),
            "west": (sz, sy), "up": (sx, sz), "down": (sx, sz)}[face]


class Modelo:
    """Cubos, grupos y animaciones de un .bbmodel (formato Bedrock entity)."""

    def __init__(self, nombre, lienzo):
        self.nombre, self.cv, self.elements = nombre, lienzo, []

    def cube(self, name, frm, to, default, **faces):
        size = [t - f for f, t in zip(frm, to)]
        out = {}
        for face in ("north", "east", "south", "west", "up", "down"):
            spec = faces.get(face, default)       # "~" al final: UV en espejo
            rx, ry, rw, rh = self.cv.regions[spec.rstrip("~")]
            fw, fh = face_size(size, face)
            fw, fh = min(fw, rw), min(fh, rh)
            u0, u1 = (rx + fw, rx) if spec.endswith("~") else (rx, rx + fw)
            out[face] = {"uv": [u0, ry, u1, ry + fh], "texture": 0}
        el = {
            "name": name, "box_uv": False, "rescale": False, "locked": False,
            "light_emission": 0, "render_order": "default",
            "allow_mirror_modeling": True,
            "from": frm, "to": to, "autouv": 0, "color": len(self.elements) % 8,
            "origin": [0, 0, 0], "faces": out, "type": "cube", "uuid": uid(),
        }
        self.elements.append(el)
        return el["uuid"]

    @staticmethod
    def group(name, origin, children):
        return {"name": name, "origin": origin, "color": 0, "uuid": uid(),
                "export": True, "mirror_uv": False, "isOpen": True,
                "locked": False, "visibility": True, "autouv": 0,
                "children": children}

    def anim(self, name, loop, length, bone, channel, keys, *mas):
        """`keys`: lista de (tiempo, (x, y, z)); los valores de texto van tal cual.
        `mas`: otros huesos de la misma animación, como (hueso, canal, keys)."""
        def kf(channel, t, xyz):
            x, y, z = (v if isinstance(v, str) else str(v) for v in xyz)
            return {"channel": channel,
                    "data_points": [{"x": x, "y": y, "z": z}],
                    "uuid": uid(), "time": t, "color": -1, "interpolation": "linear"}

        return {"uuid": uid(), "name": f"animation.{self.nombre}.{name}", "loop": loop,
                "override": False, "length": length, "snapping": 24,
                "selected": False, "anim_time_update": "", "blend_weight": "",
                "start_delay": "", "loop_delay": "",
                "animators": {b["uuid"]: {
                    "name": b["name"], "type": "bone",
                    "keyframes": [kf(ch, t, xyz) for t, xyz in ks]}
                    for b, ch, ks in ((bone, channel, keys),) + mas}}

    def escribir(self, out_dir, root, animations, visible_box, mover=()):
        """Guarda <nombre>.png y <nombre>.bbmodel (textura solo incrustada) en
        out_dir. Con WARDROBE_PREVIEW, deja los datos para preview.py (los cubos
        cuyo nombre empieza por algo de `mover` son la parte que se abre)."""
        png = self.cv.png()
        model = {
            "meta": {"format_version": "5.0", "model_format": "bedrock",
                     "box_uv": False},
            "name": self.nombre,
            "model_identifier": self.nombre,
            "visible_box": visible_box,
            "variable_placeholders": "",
            "variable_placeholder_buttons": [],
            "timeline_setups": [],
            "unhandled_root_fields": {},
            "resolution": {"width": self.cv.w, "height": self.cv.h},
            "elements": self.elements,
            "outliner": [root],
            "textures": [{
                "path": "",                 # solo incrustada: Blockbench no la recarga del disco
                "name": f"{self.nombre}.png", "folder": "", "namespace": "", "id": "0",
                "group": "", "width": self.cv.w, "height": self.cv.h,
                "uv_width": self.cv.w, "uv_height": self.cv.h,
                "particle": False, "use_as_default": False, "layers_enabled": False,
                "sync_to_project": "", "render_mode": "default",
                "render_sides": "auto", "pbr_channel": "color", "frame_time": 1,
                "frame_order_type": "loop", "frame_order": "",
                "frame_interpolate": False, "visible": True, "internal": True,
                "saved": True, "uuid": uid(),
                "source": "data:image/png;base64," + base64.b64encode(png).decode(),
            }],
            "animations": animations,
        }
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"{self.nombre}.png"), "wb") as f:
            f.write(png)
        with open(os.path.join(out_dir, f"{self.nombre}.bbmodel"), "w", encoding="utf-8") as f:
            json.dump(model, f, indent=1)
        if os.environ.get("WARDROBE_PREVIEW"):
            with open(os.environ["WARDROBE_PREVIEW"], "w") as f:
                json.dump({"elements": self.elements,
                           "drawer": [e["uuid"] for e in self.elements
                                      if e["name"].startswith(tuple(mover))]}, f)
        print("ok", len(self.elements), "cubos")


def pila(m, name, x0, y0, prendas, dz=0):
    """Pila de ropa de 4x5 apoyada en y0, un poco por detrás del canto de la
    balda (dz píxeles más al fondo): `prendas` va de abajo arriba como (tela,
    alto). Solo la de arriba enseña su cara superior."""
    cubos = []
    y = y0
    for i, (tela, alto) in enumerate(prendas):
        arriba = i == len(prendas) - 1 and tela != "green"
        cubos.append(m.cube(f"{name}_{i}", [x0, y, -5 + dz], [x0 + 4, y + alto, dz],
                            f"{tela}_edge", up=f"{tela}_top" if arriba else f"{tela}_edge"))
        y += alto
    return cubos


def animaciones_puertas(m, puertas):
    """open, close y open_idle de una o varias puertas de bisagra: `puertas` es
    una lista de (hueso, signo); +1 abre hacia la derecha de quien mira."""
    def swing(signo, keys):
        """Giro de la puerta: solo en y."""
        return [(t, ("0", a if signo > 0 else 0.0 - a, "0")) for t, a in keys]

    abierta = 110
    # Abrir: curva propia de frenado (cúbica), abierta del todo a los 0.5 s.
    t_abrir = 0.5
    open_keys = [(t, round(abierta * (1 - (1 - t / t_abrir) ** 3), 1) + 0.0)
                 for t in (0, 0.1, 0.2, 0.3, 0.4, t_abrir)]
    # Cerrar: arranca suave y acelera hasta encajar, a los 0.45 s.
    t_cerrar = 0.45
    close_keys = [(t, round(abierta * (1 - (t / t_cerrar) ** 2), 1) + 0.0)
                  for t in (0, 0.15, 0.3, 0.4, t_cerrar)]

    def anim(nombre, loop, largo, keys):
        (b, s), *resto = puertas
        return m.anim(nombre, loop, largo, b, "rotation", swing(s, keys),
                      *[(b2, "rotation", swing(s2, keys)) for b2, s2 in resto])

    return [anim("open", "hold", t_abrir, open_keys),
            anim("close", "hold", t_cerrar, close_keys),
            anim("open_idle", "loop", 0, [(0, abierta)])]


def cajon(m, nombre, x, ropa):
    """Cajón centrado en x: frente de 14x9 (como el de un mueble real, más ancho
    que alto) y caja de 13x12, casi tan ancha como el frente, con paredes de
    1 px y el fondo encajado entre ellas, 3 px de hondo para que la ropa llegue
    al borde y se vea desde la altura de los ojos. `ropa` es el grupo de
    prendas, que se mueve con él."""
    cube, group = m.cube, m.group
    return group(nombre, [x, 3, -8], [
        cube(f"{nombre}_front", [x - 7, 3, -8], [x + 7, 12, -7], "front_side",
             north="front", south="drawer_front_in",
             up="front_top", down="front_bottom"),
        cube(f"{nombre}_bottom", [x - 5.5, 3, -7], [x + 5.5, 7, 4], "drawer_wood",
             up="drawer_floor", down="drawer_under"),
        cube(f"{nombre}_left", [x - 6.5, 3, -7], [x - 5.5, 10, 5], "drawer_side_in",
             west="drawer_side_out", up="rim_side", down="drawer_rim_low"),
        cube(f"{nombre}_right", [x + 5.5, 3, -7], [x + 6.5, 10, 5], "drawer_side_in",
             east="drawer_side_out~", up="rim_side", down="drawer_rim_low"),
        cube(f"{nombre}_back", [x - 5.5, 3, 4], [x + 5.5, 10, 5], "drawer_back_in",
             up="rim_back", down="drawer_back_low"),
        ropa,
    ])


def animaciones_cajon(m, bone):
    """open, close y open_idle de lo que sale como un cajón (9 px en z)."""
    def slide(keys):
        return [(t, ("0", "0", z)) for t, z in keys]

    abierto = -9
    # Abrir: curva propia de frenado (cúbica), abierto del todo a los 0.45 s.
    t_abrir = 0.45
    open_keys = [(t, round(abierto * (1 - (1 - t / t_abrir) ** 3), 2) + 0.0)
                 for t in (0, 0.075, 0.15, 0.225, 0.3, t_abrir)]
    return [
        m.anim("open", "hold", t_abrir, bone, "position", slide(open_keys)),
        m.anim("close", "hold", 0.4167, bone, "position",
               slide([(0, abierto), (0.125, -6.3), (0.25, -2.7), (0.3333, -0.5), (0.4167, 0)])),
        m.anim("open_idle", "loop", 0, bone, "position", slide([(0, abierto)])),
    ]
