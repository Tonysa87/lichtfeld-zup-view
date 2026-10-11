"""Ponte tra la matematica (zup_core) e l'API Python di LichtFeld Studio.

Tutte le chiamate a `lichtfeld` passano da qui, protette da try/except,
cosi' un'eventuale differenza di API nella tua build produce un messaggio
leggibile nel pannello invece di bloccare il plugin.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
import time
import traceback
from pathlib import Path

import lichtfeld as lf

from . import zup_core as zc
from . import zup_i18n as i18n
from .zup_i18n import t

PLUGIN_NAME = "zup_view"
LARGE_COORD_WARN_M = 1.0e5  # oltre ~100 km dall'origine il float32 del viewport perde il centimetro


# --------------------------------------------------------------------------- #
# Stato condiviso del plugin (singleton semplice)
# --------------------------------------------------------------------------- #
class ZupSettings:
    # Campi persistiti tra le sessioni (lf.plugins.settings)
    PERSISTED = (
        "show_grid", "show_triad", "show_origin_axes", "show_hud",
        "grid_step", "grid_auto_step", "grid_half_size", "grid_major_every", "grid_follow_target",
        "orbit_sensitivity", "invert_yaw", "invert_pitch", "orbit_button_idx",
        "step_deg", "ortho_for_axis_views", "language", "native_grid_xy_on_load",
    )

    def __init__(self):
        # overlay
        self.show_grid = True
        self.show_triad = True
        self.show_origin_axes = False
        self.show_hud = True
        self.grid_step = 1.0           # metri
        self.grid_auto_step = True     # passo scelto in base all'estensione
        self.grid_half_size = 25.0     # metri
        self.grid_major_every = 10
        self.grid_z = 0.0              # quota del piano griglia (data), non persistita
        self.grid_follow_target = True
        # navigazione
        self.orbit_sensitivity = 0.3   # gradi per pixel
        self.invert_yaw = False
        self.invert_pitch = False
        self.orbit_button_idx = 0      # 0 = tasto centrale, 1 = Alt + sinistro
        self.step_deg = 15.0
        self.ortho_for_axis_views = True
        self.language = "auto"         # "auto" | "en" | "it"
        self.native_grid_xy_on_load = True  # griglia nativa sul piano XY dei dati all'avvio
        self._native_grid_pending = False
        self._native_grid_prev_plane = None

        # stato runtime
        self.scene_center = None
        self.scene_min = None
        self.scene_max = None
        self.modal_active = False
        self.viewport_origin = None    # (x, y) pixel finestra, aggiornato dall'overlay
        self.viewport_size = None
        self.grid_truncated = False
        self.large_coords = False
        self.last_message = ""
        self.last_error = ""
        self.diagnostics = []
        self._saved_snapshot = None
        self._last_save_t = 0.0

    def snapshot(self) -> dict:
        return {k: getattr(self, k) for k in self.PERSISTED}


S = ZupSettings()


def _set_msg(msg: str) -> None:
    S.last_message = msg
    S.last_error = ""
    try:
        lf.log.info(f"[zup_view] {msg}")
    except Exception:
        pass


def _set_err(msg: str, exc: BaseException | None = None) -> None:
    S.last_error = msg + (f": {exc}" if exc else "")
    try:
        lf.log.error(f"[zup_view] {S.last_error}")
        if exc is not None:
            lf.log.debug(traceback.format_exc())
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Persistenza impostazioni
# --------------------------------------------------------------------------- #
# File JSON in lf.plugins.data_dir("zup_view"), cartella dati durevole del
# plugin: sopravvive agli aggiornamenti dal marketplace (lf.plugins.settings
# scrive invece dentro la cartella del plugin, che l'update sostituisce).
SETTINGS_FILE = "settings.json"
SAVE_INTERVAL_S = 1.0


def _settings_path() -> Path | None:
    try:
        return Path(lf.plugins.data_dir(PLUGIN_NAME)) / SETTINGS_FILE
    except Exception:
        return None


def _coerce(default, v):
    if isinstance(default, bool):
        return bool(v)
    if isinstance(default, int):
        return int(v)
    if isinstance(default, float):
        return float(v)
    if isinstance(default, str):
        return str(v)
    return v


def load_settings() -> None:
    path = _settings_path()
    data = {}
    if path is not None and path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            _set_err(t("err_settings"), e)
            data = {}
    for k in S.PERSISTED:
        if k in data:
            try:
                setattr(S, k, _coerce(getattr(S, k), data[k]))
            except Exception:
                pass
    i18n.set_language(S.language)
    S._saved_snapshot = S.snapshot()


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def maybe_save_settings(force: bool = False) -> None:
    """Salva se qualcosa e' cambiato, al massimo una volta al secondo.
    Chiamata a ogni frame dall'overlay, quindi l'ultima modifica viene
    scritta al massimo un secondo dopo, anche se il pannello non ridisegna."""
    snap = S.snapshot()
    if snap == S._saved_snapshot:
        return
    now = time.monotonic()
    if not force and now - S._last_save_t < SAVE_INTERVAL_S:
        return
    S._last_save_t = now
    i18n.set_language(S.language)
    path = _settings_path()
    if path is None:
        return
    try:
        _write_json_atomic(path, snap)
        S._saved_snapshot = snap
    except Exception as e:
        _set_err(t("err_settings"), e)


# --------------------------------------------------------------------------- #
# Camera del viewport
# --------------------------------------------------------------------------- #
def get_camera_data():
    """Ritorna (eye, target, up, fov) in coordinate data, oppure None.
    up e' l'asse "alto" ortonormale della camera (non l'up richiesto)."""
    try:
        cam = lf.get_camera()
    except Exception as e:  # pragma: no cover - dipende dalla build
        _set_err("get_camera", e)
        return None
    if cam is None:
        return None
    eye = zc.vis_to_data(cam.eye)
    target = zc.vis_to_data(cam.target)
    up = zc.vis_to_data(cam.up)
    fov = float(getattr(cam, "fov", 60.0) or 60.0)
    return eye, target, up, fov


def set_camera_data(eye, target, up=zc.ZUP_DATA) -> bool:
    """Imposta la camera del viewport partendo da coordinate data.
    Rifiuta pose degeneri (LichtFeld le ignorerebbe con un solo warning)."""
    f = zc.sub(target, eye)
    if zc.length(f) < 1e-9:
        _set_err(t("err_degenerate"))
        return False
    if zc.length(zc.cross(zc.normalize(f), up)) < 1e-6:
        up = zc.horizontal_heading(up) or (0.0, 1.0, 0.0)
    try:
        lf.set_camera(zc.data_to_vis(eye), zc.data_to_vis(target), zc.data_to_vis(up))
        return True
    except Exception as e:
        _set_err(t("err_set_camera"), e)
        return False


def set_ortho(enabled: bool, extent: float | None = None) -> None:
    try:
        if enabled and extent and math.isfinite(extent) and extent > 0:
            lf.set_orthographic(True, float(extent))
        else:
            lf.set_orthographic(bool(enabled))
    except Exception as e:
        _set_err(t("err_ortho"), e)


def is_ortho() -> bool:
    try:
        return bool(lf.is_orthographic())
    except Exception:
        return False


def ortho_scale() -> float | None:
    """Pixel per unita' di mondo della vista ortografica corrente."""
    try:
        view = lf.get_current_view()
        if view is None or not view.orthographic:
            return None
        s = float(view.ortho_scale)
        return s if (math.isfinite(s) and s > 0) else None
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Stato dell'operatore modale
# --------------------------------------------------------------------------- #
def request_redraw() -> None:
    try:
        lf.ui.request_redraw()
    except Exception:
        pass


def modal_busy() -> bool:
    """True se un qualunque modale (nativo o di un altro plugin) e' attivo."""
    try:
        return bool(lf.ui.ops.has_modal())
    except Exception:
        return False


def reconcile_modal_state() -> None:
    """LichtFeld puo' sostituire il modale Python (es. con una selezione) senza
    chiamare cancel(): se nessun modale e' attivo, il flag torna falso."""
    if not S.modal_active:
        return
    try:
        if not lf.ui.ops.has_modal():
            S.modal_active = False
            S.last_message = t("msg_orbit_dropped")
            request_redraw()
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Bounding della scena (dalle posizioni delle gaussiane, in coordinate data)
# --------------------------------------------------------------------------- #
_SAMPLES_PER_NODE = 400_000


def _tensor_sample_numpy(t, n_total: int):
    """Sottocampiona un Tensor prima di copiarlo su CPU, se possibile."""
    step = max(1, int(math.ceil(max(n_total, 1) / _SAMPLES_PER_NODE)))
    if step > 1:
        try:
            return t[::step].cpu().numpy()
        except Exception:
            pass
    return t.cpu().numpy()


def _node_points(node):
    """Punti di un nodo nel sistema dati della scena (world transform applicata)."""
    pts = None
    try:
        sd = node.splat_data()
    except Exception:
        sd = None
    if sd is not None:
        try:
            n = int(getattr(sd, "num_points", 0) or 0)
            if n > 0:
                pts = _tensor_sample_numpy(sd.get_means(), n)
        except Exception:
            pts = None
    if pts is None:
        try:
            pc = node.point_cloud()
        except Exception:
            pc = None
        if pc is not None:
            try:
                n = int(getattr(pc, "size", 0) or 0)
                if n > 0:
                    pts = _tensor_sample_numpy(pc.means, n)
            except Exception:
                pts = None
    if pts is None:
        return None
    try:
        return zc.apply_transform_rowmajor(pts, node.world_transform)
    except Exception:
        return pts


def _scene_points(scene):
    import numpy as np

    chunks = []
    try:
        for node in scene.get_nodes():
            p = _node_points(node)
            if p is not None and len(p):
                chunks.append(np.asarray(p).reshape(-1, 3))
    except Exception:
        chunks = []
    if chunks:
        return np.vstack(chunks)
    # ripiego: modello combinato (coordinate locali dei nodi, senza transform)
    model = scene.combined_model()
    if model is not None and model.num_points > 0:
        return _tensor_sample_numpy(model.get_means(), model.num_points)
    return None


def compute_scene_bounds() -> bool:
    try:
        scene = lf.get_scene()
        if scene is None:
            _set_err(t("err_no_scene"))
            return False
        pts = _scene_points(scene)
        if pts is None:
            _set_err(t("err_no_points"))
            return False
        lo, hi, c = zc.robust_bounds(pts)
        S.scene_min, S.scene_max, S.scene_center = lo, hi, c
        S.grid_z = lo[2]
        size = max(hi[0] - lo[0], hi[1] - lo[1], 1e-3)
        S.grid_half_size = float(max(5.0, math.ceil(size * 0.75)))
        if S.grid_auto_step:
            S.grid_step = zc.auto_grid_step(S.grid_half_size)
        S.large_coords = max(abs(v) for v in c) > LARGE_COORD_WARN_M
        _set_msg(t("msg_bounds", x0=lo[0], x1=hi[0], y0=lo[1], y1=hi[1], z0=lo[2], z1=hi[2]))
        return True
    except Exception as e:
        _set_err(t("err_bounds"), e)
        return False


def scene_extent() -> float:
    if S.scene_min is None or S.scene_max is None:
        return 10.0
    d = zc.sub(S.scene_max, S.scene_min)
    return max(zc.length(d), 1e-3)


# --------------------------------------------------------------------------- #
# Azioni di navigazione
# --------------------------------------------------------------------------- #
def level_view() -> bool:
    """Mantiene eye e target, raddrizza la camera con Z in alto.
    In vista verticale conserva l'orientamento della pianta."""
    cam = get_camera_data()
    if cam is None:
        return False
    eye, target, up, _fov = cam
    ok = set_camera_data(eye, target, zc.level_up(eye, target, up))
    if ok:
        _set_msg(t("msg_leveled"))
    return ok


def go_standard_view(name: str) -> bool:
    cam = get_camera_data()
    fov = cam[3] if cam else 60.0
    if S.scene_center is not None:
        center = S.scene_center
        extent = scene_extent()
        dist = zc.fit_distance(extent, fov)
    elif cam is not None:
        center = cam[1]
        dist = max(zc.length(zc.sub(cam[0], cam[1])), 1.0)
        extent = 2.0 * dist * math.tan(math.radians(fov) * 0.5)
    else:
        return False
    eye, target, up = zc.standard_view(name, center, dist)
    ok = set_camera_data(eye, target, up)
    if name == "iso":
        set_ortho(False)
    elif S.ortho_for_axis_views:
        set_ortho(True, extent * 1.1)
    if ok:
        _set_msg(t("msg_view", name=i18n.view_label(name)))
    return ok


def frame_scene() -> bool:
    if not compute_scene_bounds():
        return False
    return go_standard_view("iso")


def step_orbit(d_yaw: float, d_pitch: float) -> bool:
    cam = get_camera_data()
    if cam is None:
        return False
    eye, target, up, _fov = cam
    new_eye = zc.orbit_turntable(eye, target, d_yaw, d_pitch, up)
    return set_camera_data(new_eye, target, zc.ZUP_DATA)


def drag_orbit(dx_px: float, dy_px: float) -> bool:
    k = S.orbit_sensitivity
    d_yaw = -dx_px * k * (-1.0 if S.invert_yaw else 1.0)
    d_pitch = dy_px * k * (-1.0 if S.invert_pitch else 1.0)
    return step_orbit(d_yaw, d_pitch)


# --------------------------------------------------------------------------- #
# Griglia nativa
# --------------------------------------------------------------------------- #
# grid_plane: "0" YZ, "1" XZ (default), "2" XY  (py_rendering.cpp, add_int_enum)
# Il piano XY del viewport (z_vis = 0) coincide con il piano XY dei dati a Z = 0.
NATIVE_GRID_PLANE_XY = "2"
NATIVE_GRID_PLANE_DEFAULT = "1"


def _render_settings():
    try:
        return lf.get_render_settings()
    except Exception as e:
        _set_err(t("err_render_settings"), e)
        return None


def native_grid_state() -> dict:
    rs = _render_settings()
    if rs is None:
        return {}
    out = {}
    for key in ("show_grid", "grid_plane", "grid_opacity"):
        try:
            out[key] = rs.get(key)
        except Exception:
            pass
    return out


def set_native_grid(visible: bool) -> bool:
    rs = _render_settings()
    if rs is None:
        return False
    try:
        rs.set("show_grid", bool(visible))
        _set_msg(t("msg_native_shown") if visible else t("msg_native_hidden"))
        return True
    except Exception as e:
        _set_err(t("err_native_grid"), e)
        return False


def set_native_grid_plane(plane_id: str) -> bool:
    rs = _render_settings()
    if rs is None:
        return False
    try:
        rs.set("grid_plane", plane_id)
        if plane_id == NATIVE_GRID_PLANE_XY:
            rs.set("show_grid", True)
        _set_msg(t("msg_native_xy") if plane_id == NATIVE_GRID_PLANE_XY else t("msg_native_default"))
        return True
    except Exception as e:
        _set_err(t("err_native_grid"), e)
        return False


# --------------------------------------------------------------------------- #
# Griglia nativa su XY all'avvio del plugin (e ripristino allo scarico)
# --------------------------------------------------------------------------- #
def _plane_id(value) -> str:
    return str(value).strip() if value is not None else ""


def apply_native_grid_on_load() -> bool:
    """Porta la griglia nativa sul piano XY dei dati se l'opzione e' attiva.
    Se le impostazioni di render non sono ancora disponibili (avvio dell'app),
    riprova dal draw handler al primo frame utile."""
    if not S.native_grid_xy_on_load:
        S._native_grid_pending = False
        return False
    try:
        rs = lf.get_render_settings()
        if rs is None:
            raise RuntimeError("render settings not ready")
        current = _plane_id(rs.get("grid_plane"))
        if current != NATIVE_GRID_PLANE_XY:
            if S._native_grid_prev_plane is None:
                S._native_grid_prev_plane = current or NATIVE_GRID_PLANE_DEFAULT
            rs.set("grid_plane", NATIVE_GRID_PLANE_XY)
        S._native_grid_pending = False
        return True
    except Exception:
        S._native_grid_pending = True
        return False


def restore_native_grid_on_unload() -> None:
    """Rimette il piano che c'era prima, solo se l'abbiamo cambiato noi e
    l'utente non l'ha modificato nel frattempo."""
    prev = S._native_grid_prev_plane
    S._native_grid_prev_plane = None
    S._native_grid_pending = False
    if prev is None:
        return
    try:
        rs = lf.get_render_settings()
        if rs is not None and _plane_id(rs.get("grid_plane")) == NATIVE_GRID_PLANE_XY:
            rs.set("grid_plane", prev)
    except Exception:
        pass
