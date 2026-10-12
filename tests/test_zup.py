"""Offline tests for zup_view against a mock of the LichtFeld Python API.

The mock (tests/mock) reproduces the host behaviours the plugin relies on, as
read from the LichtFeld Studio 0.5.5 source: camera look-at and up
orthogonalisation, orthographic scale, draw-context projection rules, modal
registry. Run from the repository root:  python tests/test_zup.py
"""
import importlib.util
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "mock"))

import numpy as np
import lichtfeld as lf

# load the repository root as the package "zup_view"
_spec = importlib.util.spec_from_file_location(
    "zup_view", os.path.join(ROOT, "__init__.py"), submodule_search_locations=[ROOT])
zup_view = importlib.util.module_from_spec(_spec)
sys.modules["zup_view"] = zup_view
_spec.loader.exec_module(zup_view)
from zup_view import zup_core as zc, zup_bridge as zb, zup_overlay, zup_ops, zup_panel, zup_diag

VP_POS = (300.0, 40.0)
VP_SIZE = (1600.0, 900.0)


def nrm(v): v = np.asarray(v, float); return v / np.linalg.norm(v)


def cam_basis_vis():
    c = lf.get_camera(); eye = np.array(c.eye); tgt = np.array(c.target); up = np.array(c.up)
    f = nrm(tgt - eye); r = nrm(np.cross(f, up)); u = nrm(np.cross(r, f))
    return eye, f, r, u


def screen_dirs():
    """Emula makeVisualizerLookAtRotation e ritorna come appaiono a schermo
    gli assi DATI X, Y, Z: vettori (destra, su) a schermo."""
    _, f, r, u = cam_basis_vis()
    out = {}
    for n, a in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
        v = np.array(zc.data_to_vis(a))
        out[n] = np.round([v @ r, v @ u], 3)
    return out


def native_ortho_px(p_vis):
    """projectWorldPoint(orthographic=True) + offset del viewport."""
    eye, f, r, u = cam_basis_vis()
    d = np.asarray(p_vis) - eye
    s = lf.get_current_view().ortho_scale
    return (VP_POS[0] + VP_SIZE[0] / 2 + d @ r * s, VP_POS[1] + VP_SIZE[1] / 2 - d @ u * s)


def native_persp_px(p_vis, fov=60.0):
    eye, f, r, u = cam_basis_vis()
    d = np.asarray(p_vis) - eye
    depth = d @ f
    if depth <= 0:
        return None
    fy = VP_SIZE[1] / 2 / math.tan(math.radians(fov) / 2)
    return (VP_POS[0] + VP_SIZE[0] / 2 + d @ r * fy / depth, VP_POS[1] + VP_SIZE[1] / 2 - d @ u * fy / depth)


class Ctx:
    """Contesto draw con le stesse regole di py_viewport.cpp."""
    viewport_size = VP_SIZE

    def __init__(s): s.l3 = []; s.l2 = []; s.t = []; s.circ = []

    def world_to_screen(s, p): return native_persp_px(p)

    def draw_line_3d(s, a, b, c, t=1):
        assert len(a) == 3 and len(c) == 4
        s.l3.append((a, b, c))

    def draw_line_2d(s, a, b, c, t=1): s.l2.append((a, b, c))

    def draw_filled_circle_2d(s, p, r, c): s.circ.append((p, r, c))

    def draw_circle_2d(s, p, r, c, t=1): s.circ.append((p, r, c))

    def draw_text_2d(s, p, txt, c, f=0): s.t.append((p, txt))


fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails += 1


# ---------------------------------------------------------------- caricamento
import json, os
with open(os.path.join(lf.plugins.data_dir("zup_view"), "settings.json"), "w") as fh:
    json.dump({"grid_major_every": 5, "invert_yaw": True}, fh)
zup_view.on_load()
check(zup_overlay.HANDLER_ID in lf._handlers, "overlay registrato")
check(lf._rs.p["grid_plane"] == "2", "all'avvio la griglia nativa va sul piano XY dei dati")
check(lf._panels["native.viewport_gizmo"] is False, "all'avvio il gizmo nativo viene nascosto")

# ---- orbita sempre attiva, Home/Focus Z-up
from lfs_plugins import toolbar as tb
check(zb.S.always_orbit and zb.S._toolbar_patch is not None, "default: orbita sempre attiva, barra Home/Focus agganciata")
zb.S._last_orbit_attempt = 0; zup_overlay.draw(Ctx())
check(zb.S.modal_active and len(lf.ui.ops.invoked) == 1, "orbita Z-up avviata da sola al primo frame")
opA = zup_ops.ZupOrbitOperator(); opA.invoke(None, None)
EA = lambda **k: types.SimpleNamespace(**{"type": "", "value": "PRESS", "mouse_x": 800., "mouse_y": 400., "delta_x": 0., "delta_y": 0., "alt": False, "ctrl": False, "shift": False, "over_gui": False, **k})
check(opA.modal(None, EA(type="ESC")) == {"PASS_THROUGH"} and zb.S.modal_active, "sempre attiva: Esc passa agli altri strumenti")
# un modale nativo (selezione) la sostituisce: stato riallineato, poi riaccesa quando finisce
lf.ui.ops.modal[0] = False; zb.S._last_orbit_attempt = 1e18; zup_overlay.draw(Ctx())
check(not zb.S.modal_active, "modale nativo: orbita sospesa")
lf._tool[0] = "builtin.align"; zb.S._last_orbit_attempt = 0; zup_overlay.draw(Ctx())
check(not zb.S.modal_active, "con lo strumento Align non si riaccende")
lf._tool[0] = ""; zb.S._last_orbit_attempt = 0; zup_overlay.draw(Ctx())
check(zb.S.modal_active, "finito lo strumento: orbita riaccesa")
# pulsanti Home/Focus sotto il gizmo
lf.set_camera(zc.data_to_vis((0, -10, 3)), zc.data_to_vis((0, 0, 0)), (0, 1, 0))
tb._UtilityToolbarController().dispatch("home", "")
d = screen_dirs(); check(d["Z"][1] > 0 and abs(d["Z"][0]) < 1e-3 and "home" not in tb.calls, "Home: vista Z-up invece del reset nativo")
zb.go_standard_view("front"); lf.ui.ops.modal[0] = True
tb._UtilityToolbarController().dispatch("focus_selection", "")
d = screen_dirs(); check(lf._focus_calls[0] == 1 and d["Z"][1] > 0.99, "Focus: inquadratura nativa poi Z in alto")
tb._UtilityToolbarController().dispatch("set_camera_navigation_mode", "orbit")
check(tb.calls == ["set_camera_navigation_mode"], "altre azioni della barra invariate")
# tasti H e F con l'orbita attiva
zb.go_standard_view("front")
check(opA.modal(None, EA(type="KEY_F")) == {"RUNNING_MODAL"} and lf._focus_calls[0] == 2 and screen_dirs()["Z"][1] > 0.99, "tasto F: focus Z-up")
check(opA.modal(None, EA(type="KEY_H")) == {"RUNNING_MODAL"}, "tasto H: home Z-up")
check(opA.modal(None, EA(type="KEY_F", ctrl=True)) == {"PASS_THROUGH"}, "Ctrl+F passa (scorciatoie native)")
# il pannello non offre piu' modi di spegnere l'orbita
class LabelUI:
    def __init__(s): s.labels = []
    def __getattr__(s, n):
        def f(*a, **k):
            if a and isinstance(a[0], str): s.labels.append(a[0])
            if n == "collapsing_header": return True
            if n in ("checkbox", "slider_float", "input_float", "input_int", "combo"): return (False, a[1])
            return False
        return f
lu = LabelUI(); zup_panel.ZupPanel().draw(lu)
check(not any("Disattiva" in l or "Attiva orbita" in l or "sempre attiva (tasto" in l for l in lu.labels), "nessun pulsante o casella per spegnere l'orbita")
check("always_orbit" not in zb.S.PERSISTED and "replace_native_gizmo" not in zb.S.PERSISTED, "comportamenti di base non salvati: attivi a ogni avvio")
# da qui i test storici provano l'operatore in modalita' manuale (solo interna)
zb.S.always_orbit = False
lf.ui.ops.invoked.clear(); lf.ui.ops.modal[0] = False; zb.S.modal_active = False
check(zb.S.grid_major_every == 5 and zb.S.invert_yaw is True, "impostazioni caricate da data_dir")
from zup_view import zup_i18n
mk = zup_i18n.missing_keys()
check(not mk["it_missing"] and not mk["en_missing"], f"tabelle EN/IT complete {mk}")
check(zup_i18n.t("view_top") == "Pianta", "lingua seguita da LichtFeld (it)")
lf._lang[0] = "en"; check(zup_i18n.t("view_top") == "Plan", "lingua seguita da LichtFeld (en)")
lf._lang[0] = "it"
check(all(ord(ch) < 128 for ch in zup_i18n._EN["hud_line"] + zup_i18n._IT["hud_line"]), "HUD solo ASCII")
zb.S.invert_yaw = False

# ---------------------------------------------------------------- bounds
rng = np.random.default_rng(1)
pts = rng.uniform([100, 200, 50], [110, 206, 53], (50000, 3))
pts = np.vstack([pts, rng.uniform(-1e4, 1e4, (100, 3))])
M = np.eye(4); M[:3, 3] = (1000, 0, 0)
lf._scene[0] = lf.Scene(pts, M)
check(zb.compute_scene_bounds(), "bounds calcolati")
c = zb.S.scene_center
check(abs(c[0] - 1105) < 0.3 and abs(c[1] - 203) < 0.3 and abs(c[2] - 51.5) < 0.3, f"centro robusto con world_transform del nodo {np.round(c, 2)}")
check(not zb.S.large_coords, "coordinate normali: nessun avviso")
lf._scene[0] = lf.Scene(pts + np.array([2.3e6, 5.0e6, 0]))
zb.compute_scene_bounds()
check(zb.S.large_coords, "coordinate da rilievo (2.3e6): avviso float32")
lf._scene[0] = lf.Scene(pts); zb.compute_scene_bounds()
check(zb.S.grid_step in (0.1, 0.2, 0.5, 1.0, 2.0) and zb.S.grid_half_size / zb.S.grid_step <= 60, f"passo automatico {zb.S.grid_step} per semi-estensione {zb.S.grid_half_size}")

# ---------------------------------------------------------------- viste
zb.go_standard_view("top"); d = screen_dirs()
check(d["X"][0] > 0.99 and abs(d["X"][1]) < 1e-3, f"pianta: X a destra {d['X']}")
check(d["Y"][1] > 0.99 and abs(d["Y"][0]) < 1e-3, f"pianta: Y in alto (Nord) {d['Y']}")
check(lf.is_orthographic(), "pianta in ortografica")
zb.go_standard_view("front"); d = screen_dirs()
check(d["X"][0] > 0.99 and d["Z"][1] > 0.99, f"fronte: X a destra, Z in alto {d}")
zb.go_standard_view("right"); d = screen_dirs()
check(d["Y"][0] > 0.99 and d["Z"][1] > 0.99, f"destra (da Est): Y a destra, Z in alto")
zb.go_standard_view("left"); d = screen_dirs()
check(d["Y"][0] < -0.99 and d["Z"][1] > 0.99, f"sinistra (da Ovest)")
zb.go_standard_view("back"); d = screen_dirs()
check(d["X"][0] < -0.99 and d["Z"][1] > 0.99, f"retro (da Nord)")
zb.go_standard_view("bottom"); d = screen_dirs()
check(d["Y"][1] > 0.99, f"da sotto: Y in alto {d['Y']}")
zb.go_standard_view("iso"); d = screen_dirs()
check(abs(d["Z"][0]) < 1e-3 and d["Z"][1] > 0, f"iso: Z verticale a schermo {d['Z']}")
check(not lf.is_orthographic(), "iso in prospettica")

# ---------------------------------------------------------------- orbita
eye0, tgt0, _, _ = zb.get_camera_data(); r0 = zc.length(zc.sub(eye0, tgt0))
for i in range(37):
    zb.drag_orbit(13.0, -4.0 if i % 2 else 5.0)
d = screen_dirs(); eye, tgt, _, _ = zb.get_camera_data()
check(abs(d["Z"][0]) < 1e-3 and d["Z"][1] > 0, f"turntable: Z resta verticale")
check(abs(zc.length(zc.sub(eye, tgt)) - r0) < 1e-6 and np.allclose(tgt, tgt0), "turntable: distanza e pivot invariati")
zb.step_orbit(0, 500)
check(zc.elevation_deg(*zb.get_camera_data()[:2]) <= zc.MAX_ELEVATION_DEG + 1e-6, "elevazione limitata")

# H3: uscita dal polo senza salto di 90 gradi
for name in ("top", "bottom"):
    zb.go_standard_view(name)
    zb.step_orbit(0.0, -5.0 if name == "top" else 5.0); d = screen_dirs()
    check(d["Y"][1] > 0.9 and abs(d["X"][1]) < 0.1, f"{name}: dopo il primo passo il Nord resta in alto {d['Y']}")
# polo con pianta ruotata (Est in alto): deve restare Est in alto
zb.set_camera_data((0, 0, 20), (0, 0, 0), (1, 0, 0))
zb.step_orbit(0.0, -5.0); d = screen_dirs()
check(d["X"][1] > 0.9, f"pianta ruotata: Est resta in alto {d['X']}")

zb.go_standard_view("front"); e, t, _, _ = zb.get_camera_data(); az0 = math.degrees(math.atan2(e[1] - t[1], e[0] - t[0]))
zb.drag_orbit(10, 0); e, t, _, _ = zb.get_camera_data(); az1 = math.degrees(math.atan2(e[1] - t[1], e[0] - t[0]))
check(az1 < az0, f"drag a destra: la camera gira in senso orario visto dall'alto {az0:.1f}->{az1:.1f}")
zb.drag_orbit(0, 10); check(zc.elevation_deg(*zb.get_camera_data()[:2]) > 0, "drag in basso: la camera sale")

# ---------------------------------------------------------------- raddrizza
lf.set_camera(zc.data_to_vis((0, -10, 3)), zc.data_to_vis((0, 0, 0)), (0.3, 0.9, 0.2))
zb.level_view(); d = screen_dirs()
check(abs(d["Z"][0]) < 1e-3, f"raddrizza: Z verticale {d['Z']}")
zb.set_camera_data((0, 0, 20), (0, 0, 0), (1, 0, 0)); zb.level_view(); d = screen_dirs()
check(d["X"][1] > 0.99, f"raddrizza in pianta conserva l'orientamento {d['X']}")
check(not zb.set_camera_data((1, 1, 1), (1, 1, 1)), "posa degenere rifiutata")

# heading
check(abs(zc.view_heading_deg((0, -10, 5), (0, 0, 0)) - 0.0) < 1e-9, "heading: da Sud guarda verso Nord = 0")
check(abs(zc.view_heading_deg((-10, 0, 5), (0, 0, 0)) - 90.0) < 1e-9, "heading: da Ovest guarda verso Est = 90")

# ---------------------------------------------------------------- overlay prospettico
zb.go_standard_view("iso"); zb.S.show_origin_axes = True
ctx = Ctx(); zup_overlay.draw(ctx)
check(zb.S.last_error == "" and len(ctx.l3) > 20 and len(ctx.l2) == 6 and len(ctx.circ) == 11 and len(ctx.t) >= 7,
      f"overlay prospettico: {len(ctx.l3)} linee 3D, {len(ctx.l2)} linee 2D (triade+gizmo), {len(ctx.circ)} cerchi, {len(ctx.t)} testi, err='{zb.S.last_error}'")
check(np.allclose(zb.S.viewport_origin, VP_POS, atol=1e-3), f"origine viewport ricavata {zb.S.viewport_origin}")
check(all(p[0] >= VP_POS[0] and p[1] >= VP_POS[1] for p, _ in ctx.t), "HUD e triade dentro il viewport (offset applicato)")

# H2: camera bassa dentro la griglia -> nessun estremo dietro la camera
zb.set_camera_data((105, 199, 50.5), (105, 203, 50.2), zc.ZUP_DATA)
zb.S.grid_follow_target = True; zb.S.grid_z = 50.0
ctx = Ctx(); zup_overlay.draw(ctx)
eye, f, r, u = cam_basis_vis()
behind = [1 for a, b, _ in ctx.l3 for p in (a, b) if (np.asarray(p) - eye) @ f < 0.1]
check(len(ctx.l3) > 20 and not behind, f"clipping near: {len(ctx.l3)} segmenti, {len(behind)} estremi dietro la camera")

# H1: overlay ortografico allineato alla proiezione nativa
zb.go_standard_view("top")
check(lf.is_orthographic(), "pianta ortografica")
ctx = Ctx(); zup_overlay.draw(ctx)
check(len(ctx.l3) == 0 and len(ctx.l2) > 20, f"in ortografica si disegna in 2D ({len(ctx.l2)} segmenti)")
# gizmo Z-up in pianta: +X a destra del centro, +Y sopra, Z verso la camera; in alto a destra
gm = {v: (x, y) for x, y, rr, v in zb.S.gizmo_markers}
gcx = (gm["right"][0] + gm["left"][0]) / 2; gcy = (gm["back"][1] + gm["front"][1]) / 2
check(gm["right"][0] > gcx + 20 and gm["back"][1] < gcy - 20, f"gizmo in pianta: X a destra, Y (Nord) in alto")
check(gcx > VP_POS[0] + VP_SIZE[0] - 120 and gcy < VP_POS[1] + 120, f"gizmo in alto a destra del viewport ({gcx:.0f},{gcy:.0f})")
check(zb.S.gizmo_markers[0][3] == "top", "gizmo: in pianta la sferetta cliccabile al centro e' +Z (vista dall'alto)")
lines, _ = zc.grid_lines(zb.get_camera_data()[1], zb.S.grid_half_size, zb.S.grid_step, zb.S.grid_z, zb.S.grid_major_every)
(p0, p1), _, _ = lines[len(lines) // 3]
exp0 = native_ortho_px(zc.data_to_vis(p0))
got = [a for a, b, _ in ctx.l2]
err = min(math.hypot(g[0] - exp0[0], g[1] - exp0[1]) for g in got)
check(err < 1e-3, f"griglia ortografica coincide con projectWorldPoint (errore {err:.2e} px)")

# griglia
lines, tr = zc.grid_lines((5.3, 2.2, 0), 3, 1, -1.5)
check(all(p[2] == -1.5 for (a, b), _, _ in lines for p in (a, b)) and not tr, "griglia sul piano Z costante")
check(any(ax == "y" for *_, ax in zc.grid_lines((0, 0, 0), 3, 1, 0)[0]), "griglia: asse Y evidenziato all'origine")
check(zc.grid_lines((0, 0, 0), 5000, 1, 0)[1], "griglia enorme: segnalata come troncata")
check([zc.nice_step(x) for x in (0.13, 0.3, 0.7, 1.0, 4.0, 12)] == [0.2, 0.5, 1.0, 1.0, 5.0, 20.0], "nice_step 1-2-5")

# triade in pianta: X a destra, Y in alto
zb.go_standard_view("top")
zb.S.replace_native_gizmo = False
ctx = Ctx(); zup_overlay.draw(ctx)
zb.S.replace_native_gizmo = True
tri = {c: (b[0] - a[0], b[1] - a[1]) for a, b, c in ctx.l2[-3:]}
check(tri[zup_overlay.COL_X][0] > 40 and tri[zup_overlay.COL_Y][1] < -40, f"triade pianta {tri}")

# ---------------------------------------------------------------- pannello
class UI:
    def __init__(s, press=None): s.press = press or set(); s.calls = []

    def __getattr__(s, n):
        def f(*a, **k):
            s.calls.append(n)
            if n in ("button", "button_styled"): return a[0] in s.press
            if n == "collapsing_header": return True
            if n in ("checkbox", "slider_float", "input_float", "input_int", "combo"): return (False, a[1])
            return None
        return f


zb._set_msg("")
p = zup_panel.ZupPanel(); p.draw(UI()); check(zb.S.last_error == "", f"pannello disegnato (err='{zb.S.last_error}')")
zb.go_standard_view("iso")
p.draw(UI({"Pianta"})); check(lf.is_orthographic(), "pulsante Pianta")
p.draw(UI({"Nativa su XY (Z = 0)"})); check(lf._rs.p["grid_plane"] == "2" and lf._rs.p["show_grid"], "griglia nativa sul piano XY")
p.draw(UI({"Nascondi"})); check(lf._rs.p["show_grid"] is False, "griglia nativa nascosta")
p.draw(UI({"Ripristina"})); check(lf._rs.p["grid_plane"] == "1" and lf._rs.p["show_grid"] is False, "griglia nativa: piano predefinito, visibilita' rispettata")
p.draw(UI({"Esegui diagnostica"}))
print("   diag:", *zb.S.diagnostics, sep="\n     ")
check(not any(l.startswith("KO") for l in zb.S.diagnostics), "diagnostica senza KO sul mock fedele")
zb.S.step_deg = 22.0; zb.maybe_save_settings(force=True)
saved = json.load(open(os.path.join(lf.plugins.data_dir("zup_view"), "settings.json")))
check(saved["step_deg"] == 22.0, "impostazioni salvate in data_dir")
zb.S.step_deg = 23.0; zb.S._last_save_t = 0; zup_overlay.draw(Ctx())
saved = json.load(open(os.path.join(lf.plugins.data_dir("zup_view"), "settings.json")))
check(saved["step_deg"] == 23.0, "salvataggio anche dal draw handler (senza ridisegno pannello)")
# M1: altro modale attivo -> rifiuta
lf.ui.ops.modal[0] = True
check((not zup_ops.start_modal()) and not zb.S.modal_active and zb.S.last_error != "", f"start rifiutato con un altro modale attivo: '{zb.S.last_error}'")
lf.ui.ops.modal[0] = False

# layout stabile: in ogni contenitore non dinamico la sequenza di widget non cambia
DYNAMIC = {"zup_warn", "zup_msg", "zup_grid_step", "zup_grid_warn", "zup_state_info", "zup_diag"}
class SeqUI:
    def __init__(s, open_sections=True): s.stack = ["root"]; s.seq = {}; s.open = open_sections
    def begin_child(s, key, size, border=False): s.seq.setdefault(s.stack[-1], []).append("child:" + key); s.stack.append(key)
    def end_child(s): s.stack.pop()
    def __getattr__(s, n):
        def f(*a, **k):
            s.seq.setdefault(s.stack[-1], []).append(n)
            if n == "collapsing_header": return s.open
            if n in ("checkbox", "slider_float", "input_float", "input_int", "combo"): return (False, a[1])
            return False
        return f
def layout(**state):
    saved = {k: getattr(zb.S, k) for k in state}
    for k, v in state.items(): setattr(zb.S, k, v)
    u = SeqUI(state.pop("_open", True) if "_open" in state else True)
    zup_panel.ZupPanel().draw(u)
    for k, v in saved.items(): setattr(zb.S, k, v)
    return {c: q for c, q in u.seq.items() if c not in DYNAMIC}
base = layout()
variants = [layout(modal_active=True), layout(grid_auto_step=False), layout(orbit_button_idx=1),
            layout(large_coords=True), layout(grid_truncated=True), layout(diagnostics=["a", "b", "c"]),
            layout(last_error="x"), layout(scene_center=None)]
check(all(v == base for v in variants), "layout del pannello stabile in tutti gli stati (nessun widget condizionale fuori dai box)")
closed = SeqUI(False); zup_panel.ZupPanel().draw(closed)
check(closed.seq["root"] == base["root"], "sezioni chiuse: sequenza principale invariata")

# ---------------------------------------------------------------- operatore modale
r0 = lf._redraws[0]
check(zup_ops.start_modal() and zb.S.modal_active, f"start_modal: un solo invoke con l'id corretto {lf.ui.ops.invoked}")
check(len(lf.ui.ops.invoked) == 1, "nessun tentativo con id inesistenti")
op = zup_ops.ZupOrbitOperator(); op.invoke(None, None)
E = lambda **k: types.SimpleNamespace(**{"type": "", "value": "NOTHING", "mouse_x": 800., "mouse_y": 400., "delta_x": 0., "delta_y": 0., "alt": False, "over_gui": False, **k})
check(op.modal(None, E(type="RIGHTMOUSE", value="PRESS")) == {"PASS_THROUGH"}, "tasto destro passa al pan nativo")
check(op.modal(None, E(type="MOUSEMOVE", delta_x=5)) == {"PASS_THROUGH"}, "movimento senza drag passa")
check(op.modal(None, E(type="MIDDLEMOUSE", value="PRESS", mouse_x=100., mouse_y=100.)) == {"PASS_THROUGH"}, "MMB fuori dal viewport (pannello) passa")
check(op.modal(None, E(type="MIDDLEMOUSE", value="PRESS")) == {"RUNNING_MODAL"}, "MMB nel viewport catturato")
e0 = zb.get_camera_data()[0]
check(op.modal(None, E(type="MOUSEMOVE", mouse_x=820.)) == {"RUNNING_MODAL"} and zb.get_camera_data()[0] != e0, "drag senza delta: orbita da posizione")
check(op.modal(None, E(type="MIDDLEMOUSE", value="RELEASE")) == {"RUNNING_MODAL"}, "MMB release")
check(op.modal(None, E(type="WHEELUPMOUSE", value="PRESS")) == {"PASS_THROUGH"}, "zoom rotella passa")
op.modal(None, E(type="MIDDLEMOUSE", value="PRESS"))
check(op.modal(None, E(type="MIDDLEMOUSE", value="PRESS")) == {"RUNNING_MODAL"} and op._dragging, "rilascio perso: nuovo MMB riprende il drag (non va all'orbita nativa)")
check(op.modal(None, E(type="LEFTMOUSE", value="PRESS")) == {"PASS_THROUGH"} and not op._dragging, "rilascio perso: un altro clic chiude il drag")
# clic sul gizmo Z-up con orbita attiva: va alla vista dell'asse
zb.go_standard_view("iso"); zup_overlay.draw(Ctx())
fx, fy, _, _ = next(m for m in zb.S.gizmo_markers if m[3] == "front")
check(op.modal(None, E(type="LEFTMOUSE", value="PRESS", mouse_x=fx, mouse_y=fy)) == {"RUNNING_MODAL"}, "clic sul gizmo catturato")
d = screen_dirs(); check(d["X"][0] > 0.99 and d["Z"][1] > 0.99, "clic su -Y del gizmo: vista Fronte (da Sud)")
check(op.modal(None, E(type="LEFTMOUSE", value="PRESS", mouse_x=800., mouse_y=400.)) == {"PASS_THROUGH"}, "clic fuori dal gizmo passa (selezione)")
check(op.modal(None, E(type="ESC", value="PRESS")) == {"CANCELLED"} and not zb.S.modal_active, "Esc esce")
check(lf._redraws[0] > r0, "redraw richiesto al cambio di stato")
zb.S.orbit_button_idx = 1; op.invoke(None, None)
check(op.modal(None, E(type="LEFTMOUSE", value="PRESS")) == {"PASS_THROUGH"}, "LMB senza Alt passa (selezione)")
check(op.modal(None, E(type="LEFTMOUSE", value="PRESS", alt=True)) == {"RUNNING_MODAL"}, "Alt+LMB orbita")
zb.S.orbit_button_idx = 0
zup_ops.stop_modal()
check(op.modal(None, E(type="MOUSEMOVE")) == {"CANCELLED"}, "Disattiva dal pannello: il modale si chiude da solo")
# H4: modale sostituito da uno strumento nativo
zb.S.modal_active = True; lf.ui.ops.modal[0] = False
zup_overlay.draw(Ctx())
check(not zb.S.modal_active, "stato riallineato quando LichtFeld toglie il modale")

zup_view.on_unload(); check(not lf._handlers and not lf._registered, "unload pulito (senza cancel_modal globale)")
check(lf._panels["native.viewport_gizmo"] is True, "allo scarico il gizmo nativo torna visibile")
check(tb._UtilityToolbarController.dispatch.__name__ == "dispatch" and not hasattr(tb._UtilityToolbarController.dispatch, "_zup_original"), "allo scarico la barra torna originale")
# ciclo completo: piano originale -> XY all'avvio -> ripristino allo scarico
lf._rs.p["grid_plane"] = "1"
zup_view.on_load(); check(lf._rs.p["grid_plane"] == "2", "ricarico: griglia su XY")
zup_view.on_unload(); check(lf._rs.p["grid_plane"] == "1", "scarico: piano originale ripristinato")
# render settings non ancora pronte all'avvio: applicato al primo frame
_orig = lf.get_render_settings
lf.get_render_settings = lambda: None
zup_view.on_load(); check(zb.S._native_grid_pending, "avvio senza render settings: in attesa")
lf.get_render_settings = _orig
zup_overlay.draw(Ctx()); check(lf._rs.p["grid_plane"] == "2" and not zb.S._native_grid_pending, "applicato al primo frame utile")
zup_view.on_unload()
# opzione disattivata: nessuna modifica
zb.S.native_grid_xy_on_load = False; lf._rs.p["grid_plane"] = "1"
zup_view.on_load(); check(lf._rs.p["grid_plane"] == "1", "opzione spenta: griglia nativa non toccata")
zup_view.on_unload()

# ---------------------------------------------------------------- bounds senza numpy
# Il mock di Tensor.numpy() solleva come nel venv reale: i bounds passano solo dai Tensor.
bad = np.vstack([pts, np.full((10, 3), np.nan), np.full((10, 3), np.inf)])
lf._scene[0] = lf.Scene(bad, M)
check(zb.compute_scene_bounds(), f"bounds con i Tensor (senza numpy), righe NaN/inf scartate: err='{zb.S.last_error}'")
c = zb.S.scene_center
check(abs(c[0] - 1105) < 0.3 and abs(c[1] - 203) < 0.3 and abs(c[2] - 51.5) < 0.3, f"centro con i Tensor {np.round(c, 2)}")
R = np.eye(4); R[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]  # 90 gradi attorno a Z
lf._scene[0] = lf.Scene(pts, R); zb.compute_scene_bounds(); c = zb.S.scene_center
check(abs(c[0] + 203) < 0.3 and abs(c[1] - 105) < 0.3, f"bounds con rotazione del nodo {np.round(c, 2)}")
check(zc.percentile_index(1, 99) == 0 and zc.percentile_index(101, 1) == 1 and zc.percentile_index(101, 99) == 99, "indice di percentile")

# ---------------------------------------------------------------- navigazione Z-up nativa
NATIVE_HOME = ((-5.657, 3.0, -5.657), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))  # viewport.hpp: home Y-up
def tick():
    zb.S._last_watch_t = 0.0; zup_overlay.draw(Ctx())
lf._scene[0] = lf.Scene(pts)
lf.enable_native_up(True); lf._up[0] = "legacy_y"; lf._up_calls.clear(); lf._rs.p["grid_plane"] = "1"
zb.S.native_grid_xy_on_load = True; zb.S.always_orbit = True
lf.ui.ops.invoked.clear(); lf.ui.ops.modal[0] = False; zb.S.modal_active = False
zup_view.on_load()
check(lf._up[0] == "data_z" and lf._up_calls == [("data_z", True)], f"all'avvio: verticale nativa data_z con griglia allineata {lf._up_calls}")
check(zb.native_zup_active(), "navigazione Z-up nativa riconosciuta")
# avvio dell'app: controller camera non ancora pronto, la chiamata non ha effetto
_real_set = lf.set_navigation_up_axis
zb.S._native_up_applied = False; lf._up[0] = "legacy_y"
lf.set_navigation_up_axis = lambda axis, align_grid=False: None
check(not zb.apply_native_up_axis() and not zb.S._native_up_applied, "controller non pronto: non segnata come applicata")
lf.set_navigation_up_axis = _real_set; tick()
check(lf._up[0] == "data_z" and zb.S._native_up_applied, "riprovata al frame successivo")
zb.S._last_orbit_attempt = 0; tick()
check(zb.S.modal_active, "modale avviato anche con la navigazione nativa (gizmo Z-up e tasto H)")
opN = zup_ops.ZupOrbitOperator(); opN.invoke(None, None)
EN = lambda **k: types.SimpleNamespace(**{"type": "", "value": "PRESS", "mouse_x": 800., "mouse_y": 400., "delta_x": 0., "delta_y": 0., "alt": False, "ctrl": False, "shift": False, "over_gui": False, **k})
check(opN.modal(None, EN(type="MIDDLEMOUSE")) == {"PASS_THROUGH"} and not zb.S._orbit_dragging, "tasto centrale all'orbita nativa Z-up")
zb.S.orbit_button_idx = 1
check(opN.modal(None, EN(type="LEFTMOUSE", alt=True)) == {"PASS_THROUGH"}, "anche Alt+sinistro passa a LichtFeld")
zb.S.orbit_button_idx = 0
zb.go_standard_view("iso"); tick()
gx, gy, _, _ = next(m for m in zb.S.gizmo_markers if m[3] == "top")
check(opN.modal(None, EN(type="LEFTMOUSE", mouse_x=gx, mouse_y=gy)) == {"RUNNING_MODAL"}, "clic sul gizmo Z-up ancora gestito dal plugin")
d = screen_dirs(); check(d["Y"][1] > 0.99 and lf.is_orthographic(), "gizmo +Z: pianta con il Nord in alto")
f0 = lf._focus_calls[0]
check(opN.modal(None, EN(type="KEY_F")) == {"PASS_THROUGH"} and lf._focus_calls[0] == f0, "tasto F al Focus nativo (gia' Z-up)")
check(opN.modal(None, EN(type="KEY_H")) == {"RUNNING_MODAL"}, "tasto H: Home Z-up del plugin (quella nativa e' Y-up)")
tb.calls.clear(); tb._UtilityToolbarController().dispatch("focus_selection", "")
check(tb.calls == ["focus_selection"], "pulsante Focus: azione nativa")
tb._UtilityToolbarController().dispatch("home", "")
check(tb.calls == ["focus_selection"], "pulsante Home: versione Z-up")
ctx = Ctx(); zup_overlay.draw(ctx)
check(any("LichtFeld Z-up" in txt or "Z-up di LichtFeld" in txt for _, txt in ctx.t), "HUD: navigazione Z-up di LichtFeld")

# dati caricati: LichtFeld torna alla Home nativa (Y-up) -> il plugin inquadra in Z-up
lf.set_camera(*NATIVE_HOME)
check(zb.horizon_tilted(), "la Home nativa e' storta per dati Z-up")
lf._scene[0] = lf.Scene(pts, name="nuovo_dataset"); tick()
d = screen_dirs()
check(not zb.horizon_tilted() and abs(d["Z"][0]) < 1e-3 and d["Z"][1] > 0, f"dopo il caricamento: scena inquadrata in Z-up {d['Z']}")
lf.set_camera(*NATIVE_HOME); tick()
check(zb.horizon_tilted(), "una sola volta per caricamento: dopo non si combatte con l'utente")
# reset nativo in ritardo (DatasetLoadCompleted dopo la comparsa del nodo)
lf._scene[0] = lf.Scene(pts, name="altro"); zb.go_standard_view("iso"); tick()
lf.set_camera(*NATIVE_HOME); tick()
check(not zb.horizon_tilted(), "reset nativo arrivato dopo il nodo: raddrizzato entro la finestra")
zb.S.auto_home_on_load = False
lf._scene[0] = lf.Scene(pts, name="terzo"); lf.set_camera(*NATIVE_HOME); tick()
check(zb.horizon_tilted(), "opzione spenta: nessuna inquadratura automatica")
zb.S.auto_home_on_load = True
# l'addestramento cambia solo il numero di gaussiane: nessun salto
sig = zb.S._scene_sig; lf._scene[0].total_gaussian_count += 1000; tick()
check(zb.S._scene_sig == sig and zb.S._home_pending_until == 0.0, "addestramento: nessuna inquadratura")

# nuovo progetto: LichtFeld torna a legacy_y -> il plugin rimette data_z
lf._project[0] = "uuid-2"; lf._up[0] = "legacy_y"; tick()
check(lf._up[0] == "data_z", "nuovo progetto: verticale riportata su data_z")
# scelta esplicita dell'utente (Y-up dal pannello Rendering) nello stesso progetto: rispettata
lf._up[0] = "legacy_y"; tick()
check(lf._up[0] == "legacy_y" and not zb.native_zup_active(), "Y-up scelta dall'utente: rispettata")
check(opN.modal(None, EN(type="MIDDLEMOUSE")) == {"RUNNING_MODAL"} and zb.S._orbit_dragging, "con Y-up nativa torna l'orbita del plugin")
opN.modal(None, EN(type="MIDDLEMOUSE", value="RELEASE"))
check(not zb.S._orbit_dragging, "fine drag registrata")
# opzione spenta dal pannello: ripristino
lf._up[0] = "data_z"; zb.S._native_up_prev = "legacy_y"
p = zup_panel.ZupPanel()
class Toggle(UI):
    def __getattr__(s, n):
        f = UI.__getattr__(s, n)
        if n == "checkbox":
            return lambda label, v, *a: (True, False) if label == zup_i18n.t("native_up") else (False, v)
        return f
p.draw(Toggle())
check(not zb.S.native_zup_per_project and lf._up[0] == "legacy_y", "opzione spenta: verticale originale ripristinata")
zb.S.native_zup_per_project = True
lf._project[0] = "uuid-3"; tick()
check(lf._up[0] == "data_z", "opzione riaccesa: di nuovo data_z al cambio progetto")
# layout stabile anche con la navigazione nativa
DYNAMIC.add("zup_native_nav")
check(layout() == layout(native_zup_per_project=False), "layout stabile con la navigazione nativa")
with_native = layout(); lf.enable_native_up(False); without_native = layout(); lf.enable_native_up(True)
check(with_native == without_native, "layout identico tra host con e senza navigazione nativa")
# scarico: rimette legacy_y solo se l'abbiamo cambiata noi
zup_view.on_unload()
check(lf._up[0] == "legacy_y", "scarico: verticale del progetto ripristinata")
lf._up[0] = "data_z"; lf._up_calls.clear()
zup_view.on_load(); zup_view.on_unload()
check(lf._up[0] == "data_z" and lf._up_calls == [], "progetto gia' Z-up: il plugin non lo tocca ne' all'avvio ne' allo scarico")
lf.enable_native_up(False)
print("\nFALLITI:", fails)
sys.exit(1 if fails else 0)
