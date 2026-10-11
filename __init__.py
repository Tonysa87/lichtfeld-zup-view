"""zup_view - vista Z-up per LichtFeld Studio.

Il viewport di LichtFeld presume dati COLMAP con Y verso il basso e li mostra
ruotati di 180 gradi attorno a X. Con dati da rilievo (Metashape, Z in alto)
il pavimento appare verticale. Questo plugin cambia solo il modo di guardare
la scena: viste standard, orbita attorno a Z, griglia sul piano XY, triade
degli assi. Nessun dato della scena viene modificato.
"""

import lichtfeld as lf

from . import zup_bridge, zup_overlay
from .zup_ops import ZupOrbitOperator, stop_modal
from .zup_panel import ZupPanel

_classes = [ZupOrbitOperator, ZupPanel]


def on_load():
    zup_bridge.load_settings()
    for cls in _classes:
        lf.register_class(cls)
    zup_bridge.apply_native_grid_on_load()
    zup_bridge.apply_gizmo_setting()
    try:
        zup_overlay.register()
    except Exception as e:
        zup_bridge._set_err("overlay non registrato", e)
    lf.log.info("zup_view caricato")


def on_unload():
    # unregister_class annulla da solo il nostro modale se e' attivo
    # (operator_registry.cpp): niente cancel_modal() globale.
    stop_modal()
    zup_bridge.maybe_save_settings(force=True)
    zup_bridge.restore_native_grid_on_unload()
    zup_bridge.restore_native_gizmo()
    zup_overlay.unregister()
    for cls in reversed(_classes):
        try:
            lf.unregister_class(cls)
        except Exception:
            pass
    lf.log.info("zup_view scaricato")
