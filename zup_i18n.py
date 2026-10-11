"""Testi dell'interfaccia: inglese (predefinito) e italiano.

La lingua segue quella di LichtFeld (lf.ui.get_current_language()) a meno che
l'utente non la forzi dal pannello. Le chiavi mancanti ricadono sull'inglese.
"""

from __future__ import annotations

import lichtfeld as lf

LANGS = ("auto", "en", "it")

_EN = {
    # panel
    "title": "Survey view: XY plan, +Z up",
    "subtitle": "Viewport only. Scene data is never modified.",
    "large_coords": "Very large coordinates: the viewport works in float32. Re-import with centralize_dataset enabled.",
    "sec_views": "Views",
    "frame": "Frame scene",
    "level": "Level view",
    "ortho_axis": "Orthographic for plan and elevations",
    "to_persp": "Switch to perspective",
    "to_ortho": "Switch to orthographic",
    "sec_nav": "Navigation",
    "orbit_on_label": "Z-up orbit active (Esc to exit)",
    "orbit_off_label": "Z-up orbit off: native navigation (Y-up)",
    "orbit_on_btn": "Start Z-up orbit",
    "orbit_off_btn": "Stop Z-up orbit",
    "orbit_note": "While active, native tools that need their own modal (e.g. Align point picking) wait until you exit with Esc.",
    "gesture": "Orbit gesture",
    "gesture_mmb": "Middle mouse",
    "gesture_alt": "Alt + left mouse",
    "gesture_alt_note": "With the selection tool, Alt + left is also 'intersect': prefer the middle mouse.",
    "gesture_mmb_note": "Drag with the middle mouse to orbit around Z. Right mouse pans, wheel zooms.",
    "sensitivity": "Sensitivity (deg/px)",
    "inv_yaw": "Invert horizontal",
    "inv_pitch": "Invert vertical",
    "steps_note": "Step rotation (always works):",
    "step": "Step (deg)",
    "rot_left": "Rotate left",
    "rot_right": "Rotate right",
    "rot_up": "Up",
    "rot_down": "Down",
    "sec_grid": "Grid and axes",
    "grid": "XY grid",
    "triad": "Axis triad",
    "hud": "HUD",
    "origin_axes": "Axes at origin",
    "grid_follow": "Grid centred on pivot",
    "grid_auto": "Automatic spacing",
    "grid_half": "Half extent (m)",
    "grid_step_lbl": "Grid spacing: {step:g} m",
    "grid_step": "Grid spacing (m)",
    "grid_major": "Major line every",
    "grid_z": "Grid plane height Z (m)",
    "grid_trunc": "Grid truncated: increase spacing or reduce extent.",
    "native_grid": "LichtFeld native grid:",
    "native_xy": "Native on XY (Z = 0)",
    "native_hide": "Hide",
    "native_reset": "Restore",
    "sec_state": "Status and diagnostics",
    "pivot": "Pivot (data): {x:.3f}, {y:.3f}, {z:.3f}",
    "camera": "Camera (data): {x:.3f}, {y:.3f}, {z:.3f}",
    "heading": "Looking toward {h:.1f}° (0 = North)   Elevation {e:.1f}°   FOV {f:.1f}°",
    "scene_center": "Scene centre: {x:.2f}, {y:.2f}, {z:.2f}",
    "run_diag": "Run diagnostics",
    "language": "Language",
    "lang_auto": "Same as LichtFeld",
    # views
    "view_top": "Plan",
    "view_bottom": "From below",
    "view_front": "Front (from South)",
    "view_back": "Back (from North)",
    "view_right": "Right (from East)",
    "view_left": "Left (from West)",
    "view_iso": "Isometric",
    # messages
    "msg_view": "View: {name}",
    "msg_leveled": "View levelled (Z up)",
    "msg_bounds": "Bounds (1-99 percentile): X {x0:.2f}..{x1:.2f}  Y {y0:.2f}..{y1:.2f}  Z {z0:.2f}..{z1:.2f}",
    "msg_orbit_on": "Z-up orbit active (Esc to exit)",
    "msg_orbit_off": "Z-up orbit stopped",
    "msg_orbit_dropped": "Z-up orbit interrupted by another tool",
    "msg_native_shown": "Native grid shown",
    "msg_native_hidden": "Native grid hidden",
    "msg_native_xy": "Native grid on the data XY plane (Z = 0)",
    "msg_native_default": "Native grid on its default plane",
    "err_no_scene": "no scene loaded",
    "err_no_points": "no splats or point cloud in the scene",
    "err_bounds": "bounds computation failed",
    "err_degenerate": "degenerate camera pose (eye = pivot)",
    "err_modal_busy": "another tool is running a modal action: finish it (or press Esc), then retry",
    "err_modal_start": "could not start the modal operator (use step rotation)",
    "err_modal_state": "the operator did not enter modal state ({status})",
    "err_overlay": "overlay error",
    "err_set_camera": "set_camera failed",
    "err_ortho": "set_orthographic failed",
    "err_render_settings": "render settings unavailable",
    "err_native_grid": "could not change the native grid (use Alt+G)",
    "err_settings": "settings could not be saved",
    # HUD (ASCII only: the overlay font may lack the degree sign)
    "hud_line": "Z-up | looking toward {h:5.1f} (0 = North)  elev {e:5.1f} | pivot {x:.2f}, {y:.2f}, {z:.2f} | {proj} | {mode}",
    "hud_ortho": "ortho",
    "hud_persp": "persp",
    "hud_orbit": "Z-up orbit on",
    "hud_native": "native navigation",
    "hud_large": "very large coordinates: enable centralize_dataset on import",
    "hud_trunc": "grid truncated: increase spacing",
}

_IT = {
    "title": "Vista da rilievo: XY in piano, +Z in alto",
    "subtitle": "Agisce solo sul viewport. I dati della scena non vengono modificati.",
    "large_coords": "Coordinate molto grandi: il viewport lavora in float32. Reimporta con centralize_dataset attivo.",
    "sec_views": "Viste",
    "frame": "Inquadra scena",
    "level": "Raddrizza vista",
    "ortho_axis": "Ortografica per pianta e prospetti",
    "to_persp": "Passa a prospettica",
    "to_ortho": "Passa a ortografica",
    "sec_nav": "Navigazione",
    "orbit_on_label": "Orbita Z-up attiva (Esc per uscire)",
    "orbit_off_label": "Orbita Z-up spenta: navigazione nativa (Y in alto)",
    "orbit_on_btn": "Attiva orbita Z-up",
    "orbit_off_btn": "Disattiva orbita Z-up",
    "orbit_note": "Mentre è attiva, gli strumenti nativi che usano un proprio modale (es. selezione punti di Align) aspettano che tu esca con Esc.",
    "gesture": "Gesto orbita",
    "gesture_mmb": "Tasto centrale",
    "gesture_alt": "Alt + tasto sinistro",
    "gesture_alt_note": "Con lo strumento selezione, Alt + sinistro è anche 'intersezione': preferisci il tasto centrale.",
    "gesture_mmb_note": "Trascina col tasto centrale per orbitare attorno a Z. Tasto destro: pan, rotella: zoom.",
    "sensitivity": "Sensibilità (gradi/px)",
    "inv_yaw": "Inverti orizzontale",
    "inv_pitch": "Inverti verticale",
    "steps_note": "Rotazione a passi (funziona sempre):",
    "step": "Passo (gradi)",
    "rot_left": "Ruota a sinistra",
    "rot_right": "Ruota a destra",
    "rot_up": "Su",
    "rot_down": "Giù",
    "sec_grid": "Griglia e assi",
    "grid": "Griglia XY",
    "triad": "Triade assi",
    "hud": "HUD",
    "origin_axes": "Assi all'origine",
    "grid_follow": "Griglia centrata sul pivot",
    "grid_auto": "Passo automatico",
    "grid_half": "Semi-estensione (m)",
    "grid_step_lbl": "Passo griglia: {step:g} m",
    "grid_step": "Passo griglia (m)",
    "grid_major": "Linea principale ogni",
    "grid_z": "Quota piano griglia Z (m)",
    "grid_trunc": "Griglia troncata: aumenta il passo o riduci l'estensione.",
    "native_grid": "Griglia nativa di LichtFeld:",
    "native_xy": "Nativa su XY (Z = 0)",
    "native_hide": "Nascondi",
    "native_reset": "Ripristina",
    "sec_state": "Stato e diagnostica",
    "pivot": "Pivot (dati): {x:.3f}, {y:.3f}, {z:.3f}",
    "camera": "Camera (dati): {x:.3f}, {y:.3f}, {z:.3f}",
    "heading": "Guarda verso {h:.1f}° (0 = Nord)   Elevazione {e:.1f}°   FOV {f:.1f}°",
    "scene_center": "Centro scena: {x:.2f}, {y:.2f}, {z:.2f}",
    "run_diag": "Esegui diagnostica",
    "language": "Lingua",
    "lang_auto": "Come LichtFeld",
    "view_top": "Pianta",
    "view_bottom": "Da sotto",
    "view_front": "Fronte (da Sud)",
    "view_back": "Retro (da Nord)",
    "view_right": "Destra (da Est)",
    "view_left": "Sinistra (da Ovest)",
    "view_iso": "Isometrica",
    "msg_view": "Vista: {name}",
    "msg_leveled": "Vista raddrizzata (Z in alto)",
    "msg_bounds": "Estensione (percentili 1-99): X {x0:.2f}..{x1:.2f}  Y {y0:.2f}..{y1:.2f}  Z {z0:.2f}..{z1:.2f}",
    "msg_orbit_on": "Orbita Z-up attiva (Esc per uscire)",
    "msg_orbit_off": "Orbita Z-up disattivata",
    "msg_orbit_dropped": "Orbita Z-up interrotta da un altro strumento",
    "msg_native_shown": "Griglia nativa visibile",
    "msg_native_hidden": "Griglia nativa nascosta",
    "msg_native_xy": "Griglia nativa sul piano XY dei dati (Z = 0)",
    "msg_native_default": "Griglia nativa sul piano predefinito",
    "err_no_scene": "nessuna scena caricata",
    "err_no_points": "nessuno splat o nuvola di punti nella scena",
    "err_bounds": "calcolo dell'estensione fallito",
    "err_degenerate": "posa camera degenere (camera = pivot)",
    "err_modal_busy": "un altro strumento ha un'azione modale in corso: concludila (o premi Esc) e riprova",
    "err_modal_start": "impossibile avviare l'operatore modale (usa la rotazione a passi)",
    "err_modal_state": "l'operatore non è entrato in modale ({status})",
    "err_overlay": "errore overlay",
    "err_set_camera": "set_camera fallita",
    "err_ortho": "set_orthographic fallita",
    "err_render_settings": "impostazioni di render non disponibili",
    "err_native_grid": "impossibile cambiare la griglia nativa (usa Alt+G)",
    "err_settings": "impostazioni non salvate",
    "hud_line": "Z-up | guarda verso {h:5.1f} (0 = Nord)  elev {e:5.1f} | pivot {x:.2f}, {y:.2f}, {z:.2f} | {proj} | {mode}",
    "hud_ortho": "orto",
    "hud_persp": "prosp",
    "hud_orbit": "orbita Z-up attiva",
    "hud_native": "navigazione nativa",
    "hud_large": "coordinate molto grandi: attiva centralize_dataset all'import",
    "hud_trunc": "griglia troncata: aumenta il passo",
}

_TABLES = {"en": _EN, "it": _IT}
_override = "auto"


def set_language(code: str) -> None:
    global _override
    _override = code if code in LANGS else "auto"


def current() -> str:
    if _override != "auto":
        return _override
    try:
        code = str(lf.ui.get_current_language() or "en").lower()
    except Exception:
        code = "en"
    return "it" if code.startswith("it") else "en"


def t(key: str, **kw) -> str:
    table = _TABLES.get(current(), _EN)
    s = table.get(key) or _EN.get(key) or key
    try:
        return s.format(**kw) if kw else s
    except Exception:
        return s


def view_label(name: str) -> str:
    return t("view_" + name)


def missing_keys() -> dict:
    """Per i test: chiavi presenti in una lingua e assenti nell'altra."""
    return {
        "it_missing": sorted(set(_EN) - set(_IT)),
        "en_missing": sorted(set(_IT) - set(_EN)),
    }
