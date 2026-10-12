"""Diagnostics: checks on the running build the assumptions the plugin relies on.

Output is in English on purpose (easy to paste into an issue for the
LichtFeld maintainers). Results go to the panel and to the log ("[zup_view]").
"""

from __future__ import annotations

import lichtfeld as lf

from . import zup_bridge as zb
from . import zup_core as zc


def _fmt(v):
    try:
        return "(" + ", ".join(f"{float(x):.3f}" for x in v) + ")"
    except Exception:
        return str(v)


def run() -> list[str]:
    out: list[str] = []

    def ok(msg):
        out.append("OK   " + msg)

    def ko(msg):
        out.append("KO   " + msg)

    def info(msg):
        out.append("--   " + msg)

    # 1. versioni
    try:
        info(f"host plugin API {lf.PLUGIN_API_VERSION}")
    except Exception:
        info("host plugin API: unknown")
    try:
        from lfs_plugins import compat

        info(f"LichtFeld {compat.LICHTFELD_VERSION}, features {', '.join(compat.SUPPORTED_PLUGIN_FEATURES)}")
    except Exception:
        pass

    # 1b. native Z-up navigation (LichtFeld after 0.5.4)
    if zb.native_up_supported():
        axis = zb.native_up_axis()
        (ok if axis == zb.NATIVE_UP_DATA_Z else info)(
            f"native navigation up axis: {axis} (plugin sets data_z: {zb.S.native_zup_per_project})")
    else:
        info("native navigation up axis: not available in this build (plugin orbit used)")

    # 2. set_camera with up = data Z: the camera right vector must be horizontal
    try:
        cam = lf.get_camera()
        if cam is None:
            ko("get_camera() = None (no active viewport?)")
        else:
            info(f"camera vis: eye {_fmt(cam.eye)} target {_fmt(cam.target)} up {_fmt(cam.up)} fov {cam.fov}")
            orig = (tuple(cam.eye), tuple(cam.target), tuple(cam.up))
            target = tuple(cam.target)
            dist = max(zc.length(zc.sub(cam.eye, cam.target)), 1.0)
            # oblique test pose: from South-West, about 30 deg above the horizon
            eye = zc.add(target, zc.data_to_vis(zc.mul(zc.normalize((-1.0, -1.0, 0.8)), dist)))
            lf.set_camera(eye, target, zc.ZUP_VIS)
            cam2 = lf.get_camera()
            f = zc.normalize(zc.sub(cam2.target, cam2.eye))
            right = zc.normalize(zc.cross(f, cam2.up))
            tilt = abs(zc.dot(right, zc.ZUP_VIS))
            up_ok = zc.dot(cam2.up, zc.ZUP_VIS) > 0
            if tilt < 1e-3 and up_ok:
                ok(f"set_camera with up = Z keeps a level horizon (|right.z| = {tilt:.1e})")
            else:
                ko(f"set_camera: tilted horizon |right.z| = {tilt:.3f}, up {_fmt(cam2.up)}")
            lf.set_camera(*orig)
    except Exception as e:
        ko(f"get/set_camera: {e}")

    # 3. current view / orthographic
    try:
        view = lf.get_current_view()
        if view is None:
            ko("get_current_view() = None")
        else:
            info(f"viewport {view.width}x{view.height}, orthographic {view.orthographic}, "
                 f"ortho_scale {float(view.ortho_scale):.3f} px/m")
    except Exception as e:
        ko(f"get_current_view: {e} (grid hidden in orthographic)")

    # 4. draw handler and viewport rectangle
    try:
        from . import zup_overlay

        (ok if lf.has_draw_handler(zup_overlay.HANDLER_ID) else ko)("overlay draw handler registered")
        if zb.S.viewport_origin:
            info(f"viewport origin {_fmt(zb.S.viewport_origin)} size {_fmt(zb.S.viewport_size)}")
        else:
            ko("viewport rectangle not yet known (overlay not drawn yet)")
    except Exception as e:
        ko(f"draw handler: {e}")

    # 5. operator
    try:
        from . import zup_ops

        op_id = zup_ops.operator_id()
        found = False
        for entry in lf.ops.get_all():
            s = entry if isinstance(entry, str) else str(getattr(entry, "id", entry))
            if s == op_id:
                found = True
                break
        (ok if found else ko)(f"operator registered: {op_id}")
        info(f"modal active in registry: {lf.ui.ops.has_modal()}")
    except Exception as e:
        ko(f"operator registry: {e}")

    # 6. native grid
    st = zb.native_grid_state()
    if "grid_plane" in st and "show_grid" in st:
        ok(f"native grid: show_grid={st.get('show_grid')} grid_plane={st.get('grid_plane')}")
    else:
        ko(f"native grid properties not found: {st}")

    # 7. persistence
    p = zb._settings_path()
    (ok if p is not None else ko)(f"settings file: {p}")

    # 8. scene
    try:
        scene = lf.get_scene()
        if scene is None:
            info("no scene loaded")
        else:
            info(f"total gaussians: {scene.total_gaussian_count:,}")
            if zb.S.scene_center is not None:
                c = zb.S.scene_center
                info(f"scene centre (data): {_fmt(c)}")
                if zb.S.large_coords:
                    ko("coordinates beyond 100 km from origin: float32 precision too low, "
                       "re-import with centralize_dataset")
    except Exception as e:
        ko(f"scene: {e}")

    zb.S.diagnostics = out
    for line in out:
        try:
            lf.log.info(f"[zup_view] {line}")
        except Exception:
            pass
    return out
