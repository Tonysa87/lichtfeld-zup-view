"""Operatore modale: orbita "turntable" attorno a Z.

Finche' e' attivo intercetta solo il gesto di orbita scelto
(tasto centrale, oppure Alt + tasto sinistro) quando il mouse e' sopra il
viewport, e lascia passare tutto il resto (pan con tasto destro, zoom con la
rotella, selezione, gizmo...). Esc lo disattiva.

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
        if not zb.S.modal_active:  # spento dal pannello
            self._dragging = False
            return CANCELLED

        et = getattr(event, "type", "")
        ev = getattr(event, "value", "")

        if et == "ESC" and ev == "PRESS":
            return self._finish(CANCELLED)

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

        if ev == "PRESS" and self._is_orbit_press(event) and self._inside_viewport(event):
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
        zb.S.modal_active = False


# ---------------------------------------------------------------------- #
# Avvio/arresto dal pannello
# ---------------------------------------------------------------------- #
def operator_id() -> str:
    return ZupOrbitOperator._class_id()


def start_modal() -> bool:
    if zb.modal_busy():
        # LichtFeld non annullerebbe il modale esistente: rischio di due modali attivi
        zb._set_err(t("err_modal_busy"))
        return False
    try:
        res = lf.ui.ops.invoke(operator_id())
    except Exception as e:
        zb.S.modal_active = False
        zb._set_err(t("err_modal_start"), e)
        return False
    running = bool(getattr(res, "running_modal", False)) or getattr(res, "status", "") == "RUNNING_MODAL"
    zb.S.modal_active = running
    if not running:
        zb._set_err(t("err_modal_state", status=getattr(res, "status", res)))
    return running


def stop_modal() -> None:
    """Spegne solo il nostro modale: al prossimo evento modal() ritorna
    CANCELLED. Non usa lf.ui.ops.cancel_modal(), che cancellerebbe qualunque
    modale attivo (anche nativo o di altri plugin)."""
    zb.S.modal_active = False
    zb.request_redraw()
