"""Operatore modale: orbita "turntable" attorno a Z, clic sul gizmo Z-up, H/F.

Finche' e' attivo intercetta solo il gesto di orbita scelto
(tasto centrale, oppure Alt + tasto sinistro) quando il mouse e' sopra il
viewport, e lascia passare tutto il resto (pan con tasto destro, zoom con la
rotella, selezione, gizmo...). Esc lo disattiva.

Se LichtFeld naviga gia' con Z in alto (verticale nativa "data_z", dopo la
0.5.4) il gesto di orbita passa all'orbita nativa: il modale resta solo per
i clic sul gizmo Z-up e per il tasto H.

Note dalla sorgente di LichtFeld:
* Il modale Python riceve gli eventi prima del controller camera nativo
  (input_controller.cpp), quindi RUNNING_MODAL blocca l'orbita nativa.
* event.over_gui non viene popolato per gli operatori registrati
  (py_ui.cpp, convert_modal_event): usiamo il rettangolo del viewport
  ricavato dall'overlay.
"""

from __future__ import annotations

import lichtfeld as lf
from lfs_plugins.types import Operator

from . import zup_bridge as zb
from .zup_i18n import t

PASS = {"PASS_THROUGH"}
MODAL = {"RUNNING_MODAL"}
CANCELLED = {"CANCELLED"}

_ORBIT_BUTTONS = ("MIDDLEMOUSE", "LEFTMOUSE")


class ZupOrbitOperator(Operator):
    label = "Navigazione Z-up"
    description = "Orbita attorno all'asse Z (Esc per uscire)"
    options = set()

    def __init__(self):
        super().__init__()
        self._dragging = False
        self._last = None

    @classmethod
    def poll(cls, context) -> bool:
        return True

    # ------------------------------------------------------------------ #
    def invoke(self, context, event) -> set:
        self._dragging = False
        self._last = None
        zb.S.modal_active = True
        if not zb.S.always_orbit:
            zb.level_view()
            zb._set_msg(t("msg_orbit_on"))
        zb.request_redraw()
        return MODAL

    @staticmethod
    def _button() -> str:
        return _ORBIT_BUTTONS[1 if zb.S.orbit_button_idx == 1 else 0]

    def _is_orbit_press(self, event) -> bool:
        if event.type != self._button():
            return False
        if zb.S.orbit_button_idx == 1:
            return bool(getattr(event, "alt", False))
        return True

    @staticmethod
    def _inside_viewport(event) -> bool:
        o, s = zb.S.viewport_origin, zb.S.viewport_size
        if not o or not s:
            return True  # rettangolo ignoto: non blocchiamo
        x, y = float(event.mouse_x), float(event.mouse_y)
        return o[0] <= x <= o[0] + s[0] and o[1] <= y <= o[1] + s[1]

    def modal(self, context, event) -> set:
        result = self._modal(event)
        zb.S._orbit_dragging = self._dragging
        return result

    def _modal(self, event) -> set:
        if not zb.S.modal_active:  # spento dal pannello
            self._dragging = False
            return CANCELLED

        et = getattr(event, "type", "")
        ev = getattr(event, "value", "")

        if et == "ESC" and ev == "PRESS":
            if zb.S.always_orbit:
                return PASS  # sempre attiva: Esc resta agli altri strumenti
            return self._finish(CANCELLED)

        if ev == "PRESS" and zb.S.override_home_focus and not self._dragging \
                and not (getattr(event, "ctrl", False) or getattr(event, "shift", False) or getattr(event, "alt", False)):
            if et == "KEY_H":
                zb.home_zup()
                return MODAL
            if et == "KEY_F" and not zb.native_zup_active():
                zb.focus_selection_zup()
                return MODAL

        if self._dragging:
            if et == self._button() and ev == "RELEASE":
                self._dragging = False
                self._last = None
                return MODAL
            if et == "MOUSEMOVE":
                dx = float(getattr(event, "delta_x", 0.0) or 0.0)
                dy = float(getattr(event, "delta_y", 0.0) or 0.0)
                pos = (float(event.mouse_x), float(event.mouse_y))
                if dx == 0.0 and dy == 0.0 and self._last is not None:
                    dx, dy = pos[0] - self._last[0], pos[1] - self._last[1]
                self._last = pos
                if dx or dy:
                    zb.drag_orbit(dx, dy)
                return MODAL
            if ev == "PRESS" and et.endswith("MOUSE") and not et.startswith("WHEEL"):
                # Il rilascio precedente e' andato perso (es. fuori finestra).
                if self._is_orbit_press(event) and self._inside_viewport(event):
                    # stesso gesto: ricomincia il drag, non lo cediamo all'orbita nativa
                    self._last = (float(event.mouse_x), float(event.mouse_y))
                    return MODAL
                # un altro tasto: chiudiamo il drag e lasciamo passare
                self._dragging = False
                self._last = None
            return PASS

        if et == "LEFTMOUSE" and ev == "PRESS" and not getattr(event, "alt", False):
            from . import zup_overlay

            view = zup_overlay.gizmo_hit(float(event.mouse_x), float(event.mouse_y))
            if view is not None:
                zb.go_standard_view(view)
                return MODAL

        if ev == "PRESS" and self._is_orbit_press(event) and self._inside_viewport(event) \
                and not zb.native_zup_active():
            self._dragging = True
            self._last = (float(event.mouse_x), float(event.mouse_y))
            return MODAL

        return PASS

    def _finish(self, result):
        self._dragging = False
        zb.S.modal_active = False
        zb._set_msg(t("msg_orbit_off"))
        zb.request_redraw()
        return result

    def cancel(self, context):
        # Chiamata anche da unregister_class con il lock del registro preso:
        # qui niente chiamate a lf.ui.ops.*.
        self._dragging = False
        zb.S._orbit_dragging = False
        zb.S.modal_active = False


# ---------------------------------------------------------------------- #
# Avvio/arresto dal pannello
# ---------------------------------------------------------------------- #
def operator_id() -> str:
    return ZupOrbitOperator._class_id()


def start_modal(quiet: bool = False) -> bool:
    if zb.modal_busy():
        # LichtFeld non annullerebbe il modale esistente: rischio di due modali attivi
        if not quiet:
            zb._set_err(t("err_modal_busy"))
        return False
    try:
        res = lf.ui.ops.invoke(operator_id())
    except Exception as e:
        zb.S.modal_active = False
        if not quiet:
            zb._set_err(t("err_modal_start"), e)
        return False
    running = bool(getattr(res, "running_modal", False)) or getattr(res, "status", "") == "RUNNING_MODAL"
    zb.S.modal_active = running
    if not running and not quiet:
        zb._set_err(t("err_modal_state", status=getattr(res, "status", res)))
    return running


def stop_modal() -> None:
    """Spegne solo il nostro modale: al prossimo evento modal() ritorna
    CANCELLED. Non usa lf.ui.ops.cancel_modal(), che cancellerebbe qualunque
    modale attivo (anche nativo o di altri plugin)."""
    zb.S.modal_active = False
    zb.request_redraw()
