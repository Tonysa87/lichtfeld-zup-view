"""Matematica pura del plugin Z-up (nessuna dipendenza da LichtFeld).

Convenzioni
-----------
* "data"  = coordinate del dataset, come arrivano da Metashape: XY in piano, +Z in alto.
* "vis"   = coordinate interne del viewport di LichtFeld.

LichtFeld passa dai dati al viewport con una rotazione fissa di 180 gradi
attorno a X (src/rendering/include/rendering/coordinate_conventions.hpp,
DATA_TO_VISUALIZER_WORLD_AXES = diag(1, -1, -1)):

    vis = (x, -y, -z)      e, essendo un'involuzione,      data = (x, -y, -z)

Le API di camera del viewport (get_camera / set_camera) e il draw handler
lavorano in "vis". Questo modulo ragiona sempre in "data" e converte solo al
confine. I dati della scena NON vengono mai modificati.
"""

from __future__ import annotations

import math

Vec3 = tuple[float, float, float]

ZUP_DATA: Vec3 = (0.0, 0.0, 1.0)


# --------------------------------------------------------------------------- #
# Conversione data <-> vis (stessa formula nei due versi)
# --------------------------------------------------------------------------- #
def data_to_vis(p) -> Vec3:
    return (float(p[0]), -float(p[1]), -float(p[2]))


def vis_to_data(p) -> Vec3:
    return (float(p[0]), -float(p[1]), -float(p[2]))


ZUP_VIS: Vec3 = data_to_vis(ZUP_DATA)  # (0, 0, -1)


# --------------------------------------------------------------------------- #
# Vettori
# --------------------------------------------------------------------------- #
def add(a, b) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def lerp(a, b, t: float) -> Vec3:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(a) -> float:
    return math.sqrt(dot(a, a))


def normalize(a) -> Vec3:
    n = length(a)
    if n < 1e-12:
        return (0.0, 0.0, 0.0)
    return (a[0] / n, a[1] / n, a[2] / n)


# --------------------------------------------------------------------------- #
# Camera in coordinate data
# --------------------------------------------------------------------------- #
MAX_ELEVATION_DEG = 89.5
_VERTICAL_COS = 0.999  # |forward.z| oltre cui la vista e' considerata verticale


def camera_basis(eye, target, up=ZUP_DATA):
    """Ritorna (forward, right, up_ortho) come makeVisualizerLookAtRotation:
    right = forward x up, up_ortho = right x forward."""
    f = normalize(sub(target, eye))
    r = normalize(cross(f, up))
    if length(r) < 1e-9:  # up parallelo alla direzione di vista
        r = normalize(cross(f, (0.0, 1.0, 0.0)))
        if length(r) < 1e-9:
            r = normalize(cross(f, (1.0, 0.0, 0.0)))
    u = normalize(cross(r, f))
    return f, r, u


def horizontal_heading(up) -> Vec3 | None:
    """Proiezione orizzontale (XY) normalizzata di un vettore, None se degenere."""
    h = (float(up[0]), float(up[1]), 0.0)
    if length(h) < 1e-6:
        return None
    return normalize(h)


def level_up(eye, target, current_up) -> Vec3:
    """Up "a bolla" per la camera corrente.

    Vista non verticale -> Z. Vista verticale (pianta / da sotto) -> mantiene
    l'orientamento attuale dello schermo (direzione orizzontale dell'up
    corrente), cosi' raddrizzare non fa ruotare la pianta.
    """
    f = normalize(sub(target, eye))
    if abs(f[2]) < _VERTICAL_COS:
        return ZUP_DATA
    return horizontal_heading(current_up) or (0.0, 1.0, 0.0)


def orbit_turntable(eye, target, d_yaw_deg: float, d_pitch_deg: float, up=None) -> Vec3:
    """Orbita "a piatto girevole" attorno all'asse Z passante per target.

    d_yaw   > 0  -> la camera ruota in senso antiorario visto dall'alto.
    d_pitch > 0  -> la camera sale (guarda piu' dall'alto).
    up: up corrente della camera; serve solo quando la camera e' esattamente
        sulla verticale del pivot, per non perdere l'orientamento della pianta.
    Ritorna il nuovo eye; target invariato.
    """
    v = sub(eye, target)
    r = length(v)
    if r < 1e-9:
        return tuple(eye)
    horiz = math.hypot(v[0], v[1])
    if horiz < 1e-6 * r:
        # Camera sul polo: atan2(0, 0) non dice nulla. L'alto dello schermo
        # indica dove "guarda" la pianta; la camera, uscendo dal polo, deve
        # stare dalla parte opposta (alto schermo = verso il pivot).
        h = horizontal_heading(up) if up is not None else None
        if h is None:
            h = (0.0, 1.0, 0.0)
        if v[2] < 0:  # vista da sotto: l'alto schermo resta lo stesso lato
            az = math.atan2(h[1], h[0])
        else:
            az = math.atan2(-h[1], -h[0])
    else:
        az = math.atan2(v[1], v[0])
    el = math.asin(max(-1.0, min(1.0, v[2] / r)))
    az += math.radians(d_yaw_deg)
    lim = math.radians(MAX_ELEVATION_DEG)
    el = max(-lim, min(lim, el + math.radians(d_pitch_deg)))
    ce = math.cos(el)
    return add(target, (r * ce * math.cos(az), r * ce * math.sin(az), r * math.sin(el)))


def elevation_deg(eye, target) -> float:
    v = sub(eye, target)
    r = length(v)
    if r < 1e-9:
        return 0.0
    return math.degrees(math.asin(max(-1.0, min(1.0, v[2] / r))))


def view_heading_deg(eye, target, up=None) -> float:
    """Direzione in cui si guarda, in gradi da Nord in senso orario
    (0 = verso Nord/+Y, 90 = verso Est/+X). In vista verticale usa l'alto
    dello schermo."""
    f = sub(target, eye)
    h = (f[0], f[1])
    if math.hypot(*h) < 1e-6 * max(length(f), 1e-12):
        hu = horizontal_heading(up) if up is not None else None
        if hu is None:
            return 0.0
        h = (hu[0], hu[1])
    return (math.degrees(math.atan2(h[0], h[1])) + 360.0) % 360.0


# --------------------------------------------------------------------------- #
# Viste standard (in coordinate data, Z in alto, Y = Nord)
# --------------------------------------------------------------------------- #
# nome -> (direzione dal target verso la camera, up della camera)
_S3 = 1.0 / math.sqrt(3.0)
STANDARD_VIEWS: dict[str, tuple[Vec3, Vec3]] = {
    "top": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),       # pianta: X a destra, Y (Nord) in alto
    "bottom": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    "front": ((0.0, -1.0, 0.0), ZUP_DATA),           # da Sud, guarda verso +Y
    "back": ((0.0, 1.0, 0.0), ZUP_DATA),             # da Nord
    "right": ((1.0, 0.0, 0.0), ZUP_DATA),            # da Est
    "left": ((-1.0, 0.0, 0.0), ZUP_DATA),            # da Ovest
    "iso": ((_S3, -_S3, _S3), ZUP_DATA),             # isometrica da Sud-Est
}

def standard_view(name: str, center, distance: float):
    """Ritorna (eye, target, up) in coordinate data."""
    direction, up = STANDARD_VIEWS[name]
    eye = add(center, mul(normalize(direction), distance))
    return eye, tuple(center), up


def fit_distance(extent: float, fov_deg: float, margin: float = 1.15) -> float:
    """Distanza alla quale una sfera di diametro `extent` riempie la vista."""
    fov = math.radians(max(5.0, min(170.0, fov_deg or 60.0)))
    return max(1e-3, (extent * 0.5 * margin) / math.tan(fov * 0.5))


# --------------------------------------------------------------------------- #
# Griglia sul piano XY
# --------------------------------------------------------------------------- #
MAX_GRID_LINES_PER_SIDE = 200


def nice_step(raw: float) -> float:
    """Arrotonda un passo alla serie 1-2-5 x 10^k."""
    if not (raw > 0 and math.isfinite(raw)):
        return 1.0
    k = math.floor(math.log10(raw))
    base = 10.0 ** k
    for m in (1.0, 2.0, 5.0, 10.0):
        if raw <= m * base * 1.0000001:
            return m * base
    return 10.0 * base


def auto_grid_step(half_size: float, lines_per_side: int = 50) -> float:
    return nice_step(max(half_size, 1e-6) / max(1, lines_per_side))


def grid_lines(center, half_size: float, step: float, z: float, major_every: int = 10):
    """Genera segmenti ((p0, p1), is_major, axis) in coordinate data.

    La griglia e' agganciata ai multipli di `step` (coordinate "tonde"),
    centrata vicino a `center`. axis = 'x' per la linea y=0 (asse X),
    'y' per la linea x=0 (asse Y), None per le altre.
    Ritorna (lines, truncated).
    """
    if step <= 0 or half_size <= 0 or not math.isfinite(step) or not math.isfinite(half_size):
        return [], False
    major_every = max(1, int(major_every))
    n = max(1, int(math.ceil(half_size / step)))
    truncated = n > MAX_GRID_LINES_PER_SIDE
    n = min(n, MAX_GRID_LINES_PER_SIDE)
    ix0 = int(round(center[0] / step))
    iy0 = int(round(center[1] / step))
    x0, x1 = (ix0 - n) * step, (ix0 + n) * step
    y0, y1 = (iy0 - n) * step, (iy0 + n) * step
    out = []
    for i in range(-n, n + 1):
        ix = ix0 + i
        iy = iy0 + i
        x = ix * step
        y = iy * step
        # linea parallela a Y (x costante)
        out.append((((x, y0, z), (x, y1, z)), ix % major_every == 0, "y" if ix == 0 else None))
        # linea parallela a X (y costante)
        out.append((((x0, y, z), (x1, y, z)), iy % major_every == 0, "x" if iy == 0 else None))
    return out, truncated


# --------------------------------------------------------------------------- #
# Proiezione e clipping (in coordinate data, coerenti con la camera nativa)
# --------------------------------------------------------------------------- #
def clip_segment_front(a, b, eye, forward, near: float):
    """Taglia il segmento a-b alla parte davanti al piano (depth >= near).
    Ritorna (a', b') oppure None se interamente dietro."""
    da = dot(sub(a, eye), forward)
    db = dot(sub(b, eye), forward)
    if da < near and db < near:
        return None
    if da >= near and db >= near:
        return a, b
    t = (near - da) / (db - da)
    p = lerp(a, b, t)
    return (p, b) if da < near else (a, p)


def project_ortho(p, eye, right, up, ortho_scale: float, origin, size):
    """Stessa formula di projectWorldPoint(orthographic=True):
    x = cx + view.x * scale, y = cy - view.y * scale (pixel finestra)."""
    v = sub(p, eye)
    return (
        origin[0] + size[0] * 0.5 + dot(v, right) * ortho_scale,
        origin[1] + size[1] * 0.5 - dot(v, up) * ortho_scale,
    )


# --------------------------------------------------------------------------- #
# Bounding robusto
# --------------------------------------------------------------------------- #
def robust_bounds(points, lo_pct: float = 1.0, hi_pct: float = 99.0, max_samples: int = 1_000_000):
    """points: array numpy (N,3). Ritorna (min, max, center) ignorando i floaters."""
    import numpy as np

    pts = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    if pts.shape[0] > max_samples:
        pts = pts[:: int(math.ceil(pts.shape[0] / max_samples))]
    pts = pts[np.isfinite(pts).all(axis=1)]
    if pts.shape[0] == 0:
        raise ValueError("nessun punto valido")
    lo = np.percentile(pts, lo_pct, axis=0)
    hi = np.percentile(pts, hi_pct, axis=0)
    c = (lo + hi) * 0.5
    return tuple(map(float, lo)), tuple(map(float, hi)), tuple(map(float, c))


def apply_transform_rowmajor(points, m16):
    """Applica una 4x4 row-major (tupla di 16 o 4x4) a punti (N,3) numpy."""
    import numpy as np

    M = np.asarray(m16, dtype=np.float64).reshape(4, 4)
    if np.allclose(M, np.eye(4)):
        return points
    P = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    return P @ M[:3, :3].T + M[:3, 3]
