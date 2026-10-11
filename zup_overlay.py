"""Overlay nel viewport: griglia XY, assi, triade, HUD.

Disegnato con un draw handler POST_VIEW. Note sul contesto di LichtFeld
(src/python/lfs/py_viewport.cpp, src/visualizer/gui/native_panels.cpp):

* draw_line_3d / world_to_screen usano il mondo del viewport ("vis") e una
  matrice SEMPRE prospettica: in vista ortografica proiettiamo noi i punti
  (stessa formula di projectWorldPoint) e disegniamo con draw_line_2d.
* Un estremo dietro la camera fa scartare l'intero segmento: i segmenti
  vengono tagliati al piano near prima di essere passati.
* Le coordinate 2D sono pixel della finestra, non del viewport: l'origine del
  viewport si ricava proiettando il pivot, che cade sempre al centro.
"""

from __future__ import annotations

import lichtfeld as lf

from . import zup_bridge as zb
from . import zup_core as zc
from .zup_i18n import t

HANDLER_ID = "zup_view.overlay"

COL_X = (0.93, 0.30, 0.30, 1.0)
COL_Y = (0.45, 0.85, 0.35, 1.0)
COL_Z = (0.35, 0.55, 1.00, 1.0)
COL_MINOR = (0.55, 0.55, 0.55, 0.22)
COL_MAJOR = (0.70, 0.70, 0.70, 0.45)
COL_TEXT = (0.95, 0.95, 0.95, 0.90)
COL_WARN = (1.00, 0.75, 0.30, 0.95)

NEAR = 0.15  # leggermente oltre DEFAULT_NEAR_PLANE (0.1) di LichtFeld

_last_error = ""
_grid_cache = {"key": None, "lines": None, "truncated": False}


class _Projector:
    """Disegna segmenti in coordinate data, prospettica o ortografica."""

    def __init__(self, ctx, eye, target, up):
        self.ctx = ctx
        self.eye = eye
        self.f, self.r, self.u = zc.camera_basis(eye, target, up)
        self.size = tuple(ctx.viewport_size)
        self.origin = _viewport_origin(ctx, target, self.size)
        self.ortho = zb.is_ortho()
        self.scale = zb.ortho_scale() if self.ortho else None
        # ortografica senza scala nota: meglio non disegnare che disegnare storto
        self.enabled = not (self.ortho and self.scale is None)

    def line(self, a, b, color, thickness=1.0):
        if not self.enabled:
            return
        seg = zc.clip_segment_front(a, b, self.eye, self.f, NEAR)
        if seg is None:
            return
        a, b = seg
        if self.scale is not None:
            pa = zc.project_ortho(a, self.eye, self.r, self.u, self.scale, self.origin, self.size)
            pb = zc.project_ortho(b, self.eye, self.r, self.u, self.scale, self.origin, self.size)
            self.ctx.draw_line_2d(pa, pb, color, thickness)
        else:
            self.ctx.draw_line_3d(zc.data_to_vis(a), zc.data_to_vis(b), color, thickness)


def _viewport_origin(ctx, target, size):
    try:
        p = ctx.world_to_screen(zc.data_to_vis(target))
        if p is not None:
            return (float(p[0]) - size[0] * 0.5, float(p[1]) - size[1] * 0.5)
    except Exception:
        pass
    return (0.0, 0.0)


def _grid(center):
    S = zb.S
    step = S.grid_step
    key = (
        int(round(center[0] / step)) if step > 0 else 0,
        int(round(center[1] / step)) if step > 0 else 0,
        step, S.grid_half_size, S.grid_z, S.grid_major_every,
    )
    if _grid_cache["key"] != key:
        lines, truncated = zc.grid_lines(center, S.grid_half_size, step, S.grid_z, S.grid_major_every)
        _grid_cache.update(key=key, lines=lines, truncated=truncated)
    S.grid_truncated = _grid_cache["truncated"]
    return _grid_cache["lines"]


def _draw_grid(proj, center):
    for (p0, p1), major, axis in _grid(center):
        if axis == "x":
            proj.line(p0, p1, COL_X, 2.0)
        elif axis == "y":
            proj.line(p0, p1, COL_Y, 2.0)
        else:
            proj.line(p0, p1, COL_MAJOR if major else COL_MINOR, 1.5 if major else 1.0)


def _draw_origin_axes(proj, length):
    o = (0.0, 0.0, zb.S.grid_z)
    proj.line(o, (length, 0.0, o[2]), COL_X, 3.0)
    proj.line(o, (0.0, length, o[2]), COL_Y, 3.0)
    proj.line(o, (0.0, 0.0, o[2] + length), COL_Z, 3.0)


def _draw_triad(ctx, origin, size, f, r, u):
    """Triade in basso a sinistra, orientata come la camera reale."""
    base = (origin[0] + 70.0, origin[1] + size[1] - 70.0)
    L = 45.0
    axes = (("X", (1.0, 0.0, 0.0), COL_X), ("Y", (0.0, 1.0, 0.0), COL_Y), ("Z", (0.0, 0.0, 1.0), COL_Z))
    # prima gli assi che puntano lontano dalla camera
    for name, a, col in sorted(axes, key=lambda a: zc.dot(a[1], f), reverse=True):
        end = (base[0] + zc.dot(a, r) * L, base[1] - zc.dot(a, u) * L)
        ctx.draw_line_2d(base, end, col, 3.0)
        ctx.draw_text_2d((end[0] + 4.0, end[1] - 8.0), name, col, 0.0)


def _draw_hud(ctx, origin, size, eye, target, up):
    S = zb.S
    el = zc.elevation_deg(eye, target)
    heading = zc.view_heading_deg(eye, target, up)
    mode = t("hud_orbit") if S.modal_active else t("hud_native")
    proj = t("hud_ortho") if zb.is_ortho() else t("hud_persp")
    txt = t("hud_line", h=heading, e=el, x=target[0], y=target[1], z=target[2], proj=proj, mode=mode)
    ctx.draw_text_2d((origin[0] + 14.0, origin[1] + size[1] - 18.0), txt, COL_TEXT, 0.0)
    warn = []
    if S.large_coords:
        warn.append(t("hud_large"))
    if S.grid_truncated and S.show_grid:
        warn.append(t("hud_trunc"))
    if warn:
        ctx.draw_text_2d((origin[0] + 14.0, origin[1] + size[1] - 38.0), " | ".join(warn), COL_WARN, 0.0)


def draw(ctx):
    """Callback del draw handler. Non solleva mai e non modifica la camera."""
    global _last_error
    S = zb.S
    try:
        zb.reconcile_modal_state()
        cam = zb.get_camera_data()
        if cam is None:
            return
        eye, target, up, _fov = cam
        proj = _Projector(ctx, eye, target, up)
        S.viewport_origin, S.viewport_size = proj.origin, proj.size
        if S.show_grid:
            center = target if (S.grid_follow_target or S.scene_center is None) else S.scene_center
            _draw_grid(proj, center)
        if S.show_origin_axes:
            _draw_origin_axes(proj, max(S.grid_step * 5.0, 1.0))
        if S.show_triad:
            _draw_triad(ctx, proj.origin, proj.size, proj.f, proj.r, proj.u)
        if S.show_hud:
            _draw_hud(ctx, proj.origin, proj.size, eye, target, up)
        zb.maybe_save_settings()
        _last_error = ""
    except Exception as e:  # evita di inondare il log a ogni frame
        msg = f"overlay: {e}"
        if msg != _last_error:
            _last_error = msg
            zb._set_err(t("err_overlay"), e)


def register() -> None:
    try:
        if lf.has_draw_handler(HANDLER_ID):
            lf.remove_draw_handler(HANDLER_ID)
    except Exception:
        pass
    lf.add_draw_handler(HANDLER_ID, draw, "POST_VIEW")


def unregister() -> None:
    try:
        lf.remove_draw_handler(HANDLER_ID)
    except Exception:
        pass
