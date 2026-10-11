"""Pannello "Z-up View" nella colonna di destra di LichtFeld.

Nota sul layout immediato di LichtFeld (rml_im_mode_layout.cpp): i widget
vengono riconosciuti per posizione nella sequenza di ogni contenitore. Se la
sequenza cambia (un widget condizionale, una sezione chiusa) gli elementi
sostituiti vengono riaccodati in fondo e le righe possono perdere i figli,
con widget spariti o fuori posto. Per questo:
* ogni sezione ha il suo contenitore stabile (begin_child) sempre presente;
* dentro un contenitore la sequenza dei widget non cambia mai;
* ogni parte variabile sta in un contenitore suo.
"""

from __future__ import annotations

import lichtfeld as lf

from . import zup_bridge as zb
from . import zup_core as zc
from . import zup_diag
from . import zup_i18n as i18n
from .zup_i18n import t

COL_OK = (0.55, 0.85, 0.55, 1.0)
COL_INFO = (0.62, 0.62, 0.62, 1.0)
COL_WARN = (1.00, 0.75, 0.30, 1.0)
COL_ERR = (0.95, 0.45, 0.40, 1.0)


class _Box:
    """Contenitore persistente con id stabile (begin_child / end_child)."""

    def __init__(self, ui, key: str):
        self.ui = ui
        self.key = "zup_" + key

    def __enter__(self):
        self.ui.begin_child(self.key, (0.0, 0.0), False)
        return self

    def __exit__(self, *exc):
        self.ui.end_child()
        return False


class ZupPanel(lf.ui.Panel):
    id = "zup_view.main_panel"
    label = "Z-up View"
    space = lf.ui.PanelSpace.MAIN_PANEL_TAB
    order = 150

    def draw(self, ui):
        S = zb.S
        zb.reconcile_modal_state()

        ui.heading(t("title"))
        ui.text_disabled(t("subtitle"))
        with _Box(ui, "warn"):
            if S.large_coords:
                ui.text_colored(t("large_coords"), COL_WARN)
        ui.separator()

        open_views = ui.collapsing_header(t("sec_views"), True)
        with _Box(ui, "views"):
            if open_views:
                self._views(ui)

        open_nav = ui.collapsing_header(t("sec_nav"), True)
        with _Box(ui, "nav"):
            if open_nav:
                self._navigation(ui)

        open_grid = ui.collapsing_header(t("sec_grid"), True)
        with _Box(ui, "grid"):
            if open_grid:
                self._grid(ui)

        open_state = ui.collapsing_header(t("sec_state"), False)
        with _Box(ui, "state"):
            if open_state:
                self._state(ui)

        ui.separator()
        with _Box(ui, "msg"):
            if S.last_error:
                ui.text_colored(S.last_error, COL_ERR)
            elif S.last_message:
                ui.text_colored(S.last_message, COL_INFO)

        zb.maybe_save_settings()

    # ------------------------------------------------------------------ #
    def _views(self, ui):
        S = zb.S
        if ui.button(t("frame")):
            zb.frame_scene()
        ui.same_line()
        if ui.button(t("level")):
            zb.level_view()

        for row in (("top", "bottom", "iso"), ("front", "back"), ("left", "right")):
            for i, name in enumerate(row):
                if i:
                    ui.same_line()
                if ui.button(i18n.view_label(name)):
                    zb.go_standard_view(name)

        _, S.ortho_for_axis_views = ui.checkbox(t("ortho_axis"), S.ortho_for_axis_views)
        ortho = zb.is_ortho()
        if ui.button(t("to_persp") if ortho else t("to_ortho")):
            # senza estensione: LichtFeld conserva l'inquadratura attuale
            zb.set_ortho(not ortho)

    def _navigation(self, ui):
        S = zb.S
        # stato: sempre lo stesso widget (attiva / in pausa)
        if S.modal_active:
            ui.text_colored(t("orbit_on_label"), COL_OK)
        else:
            ui.text_colored(t("orbit_paused_label"), COL_INFO)
        _, S.override_home_focus = ui.checkbox(t("override_home"), S.override_home_focus)
        ui.text_disabled(t("orbit_note"))

        _, S.orbit_button_idx = ui.combo(t("gesture"), S.orbit_button_idx, [t("gesture_mmb"), t("gesture_alt")])
        ui.text_disabled(t("gesture_alt_note") if S.orbit_button_idx == 1 else t("gesture_mmb_note"))
        _, S.orbit_sensitivity = ui.slider_float(t("sensitivity"), S.orbit_sensitivity, 0.05, 1.0)
        _, S.invert_yaw = ui.checkbox(t("inv_yaw"), S.invert_yaw)
        ui.same_line()
        _, S.invert_pitch = ui.checkbox(t("inv_pitch"), S.invert_pitch)

        ui.text_disabled(t("steps_note"))
        _, S.step_deg = ui.slider_float(t("step"), S.step_deg, 1.0, 90.0)
        if ui.button(t("rot_left")):
            zb.step_orbit(S.step_deg, 0.0)
        ui.same_line()
        if ui.button(t("rot_right")):
            zb.step_orbit(-S.step_deg, 0.0)
        ui.same_line()
        if ui.button(t("rot_up")):
            zb.step_orbit(0.0, S.step_deg)
        ui.same_line()
        if ui.button(t("rot_down")):
            zb.step_orbit(0.0, -S.step_deg)

    def _grid(self, ui):
        S = zb.S
        _, S.show_grid = ui.checkbox(t("grid"), S.show_grid)
        ui.same_line()
        _, S.show_triad = ui.checkbox(t("triad"), S.show_triad)
        ui.same_line()
        _, S.show_hud = ui.checkbox(t("hud"), S.show_hud)
        changed, S.replace_native_gizmo = ui.checkbox(t("replace_gizmo"), S.replace_native_gizmo)
        if changed:
            zb.apply_gizmo_setting()
        _, S.show_origin_axes = ui.checkbox(t("origin_axes"), S.show_origin_axes)
        _, S.grid_follow_target = ui.checkbox(t("grid_follow"), S.grid_follow_target)
        _, S.grid_auto_step = ui.checkbox(t("grid_auto"), S.grid_auto_step)
        _, S.grid_half_size = ui.input_float(t("grid_half"), S.grid_half_size, 1.0, 10.0)
        S.grid_half_size = max(0.1, S.grid_half_size)
        with _Box(ui, "grid_step"):
            if S.grid_auto_step:
                S.grid_step = zc.auto_grid_step(S.grid_half_size)
                ui.label(t("grid_step_lbl", step=S.grid_step))
            else:
                _, S.grid_step = ui.input_float(t("grid_step"), S.grid_step, 0.1, 1.0)
                S.grid_step = max(0.001, S.grid_step)
        _, S.grid_major_every = ui.input_int(t("grid_major"), S.grid_major_every, 1, 5)
        S.grid_major_every = max(1, S.grid_major_every)
        _, S.grid_z = ui.input_float(t("grid_z"), S.grid_z, 0.1, 1.0)
        with _Box(ui, "grid_warn"):
            if S.grid_truncated:
                ui.text_colored(t("grid_trunc"), COL_WARN)

        ui.text_disabled(t("native_grid"))
        changed, S.native_grid_xy_on_load = ui.checkbox(t("native_xy_on_load"), S.native_grid_xy_on_load)
        if changed and S.native_grid_xy_on_load:
            zb.apply_native_grid_on_load()
        if ui.button(t("native_xy")):
            zb.set_native_grid_plane(zb.NATIVE_GRID_PLANE_XY)
        ui.same_line()
        if ui.button(t("native_hide")):
            zb.set_native_grid(False)
        ui.same_line()
        if ui.button(t("native_reset")):
            zb.set_native_grid_plane(zb.NATIVE_GRID_PLANE_DEFAULT)

    def _state(self, ui):
        S = zb.S
        with _Box(ui, "state_info"):
            cam = zb.get_camera_data()
            if cam:
                eye, target, up, fov = cam
                ui.label(t("pivot", x=target[0], y=target[1], z=target[2]))
                ui.label(t("camera", x=eye[0], y=eye[1], z=eye[2]))
                ui.label(t("heading", h=zc.view_heading_deg(eye, target, up), e=zc.elevation_deg(eye, target), f=fov))
            if S.scene_center:
                c = S.scene_center
                ui.label(t("scene_center", x=c[0], y=c[1], z=c[2]))
        idx = i18n.LANGS.index(S.language) if S.language in i18n.LANGS else 0
        changed, idx = ui.combo(t("language"), idx, [t("lang_auto"), "English", "Italiano"])
        if changed:
            S.language = i18n.LANGS[idx]
            i18n.set_language(S.language)
        if ui.button(t("run_diag")):
            zup_diag.run()
        with _Box(ui, "diag"):
            for line in S.diagnostics:
                ui.text_wrapped(line)
