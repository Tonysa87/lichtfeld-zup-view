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

    def __init__(s): s.l3 = []; s.l2 = []; s.t = []

    def world_to_screen(s, p): return native_persp_px(p)

    def draw_line_3d(s, a, b, c, t=1):
        assert len(a) == 3 and len(c) == 4
        s.l3.append((a, b, c))

    def draw_line_2d(s, a, b, c, t=1): s.l2.append((a, b, c))

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
check(zb.S.last_error == "" and len(ctx.l3) > 20 and len(ctx.l2) == 3 and len(ctx.t) >= 4,
      f"overlay prospettico: {len(ctx.l3)} linee 3D, {len(ctx.l2)} triade, {len(ctx.t)} testi, err='{zb.S.last_error}'")
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
ctx = Ctx(); zup_overlay.draw(ctx)
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
print("\nFALLITI:", fails)
sys.exit(1 if fails else 0)
