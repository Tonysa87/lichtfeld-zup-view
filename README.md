# Z-up View for LichtFeld Studio

A survey-style viewport for scenes whose data is **Z-up** (XY horizontal, +Z up), as exported by Agisoft Metashape, RealityCapture, laser-scanning and GIS workflows.

It changes **only how the scene is viewed**: camera presets, a turntable orbit around Z, an XY grid, an axis triad and a HUD. Scene data, node transforms and exports are never modified.

*Italiano più sotto.*

## Why

LichtFeld assumes COLMAP data with Y pointing down, and shows it upright by applying a fixed 180° rotation about X (`DATA_TO_VISUALIZER_WORLD_AXES = diag(1, -1, -1)`). Native navigation then orbits around the viewport's +Y axis. With Z-up data, that axis is a horizontal direction (data −Y): the floor appears vertical and orbiting tumbles the scene. There is no world-up setting in LichtFeld (checked up to 0.5.5), so this plugin provides Z-up views and navigation on top of the native camera.

## Install

In LichtFeld, open **Tools → Plugin Marketplace**, enter `Tonysa87/lichtfeld-zup-view` in the GitHub field and click **Install Plugin**. The **Z-up View** tab appears in the right panel.

Requires LichtFeld Studio ≥ 0.5.4. For other methods (Python console, manual copy), updating, uninstalling and troubleshooting, see **[INSTALL.md](INSTALL.md)**.

## Features

- **Views:** Frame scene, Plan, From below, Front (from South), Back (from North), Right (from East), Left (from West), Isometric. Plan and elevations can switch to orthographic. In plan, X points right and Y (North) points up.
- **Level view:** keeps the camera position and pivot, makes Z vertical. In plan view it keeps the current map orientation.
- **Z-up orbit (modal):** while active, the middle mouse button (or Alt + left mouse) orbits around the vertical axis through the pivot. Pan (right mouse), zoom (wheel), selection and gizmos stay native. Press Esc to exit.
- **Always on (default):** the Z-up orbit stays active, so the middle mouse never falls back to LichtFeld's Y-up orbit. It pauses during other tools' modal actions and the Align tool.
- **Home and Focus in Z-up:** the buttons under the gizmo and the H and F keys frame the scene or the selection, keeping Z up.
- **Step rotation:** ±N° buttons, horizontally and vertically. These work even without the modal.
- **XY grid** at a chosen height (default: estimated floor), automatic 1-2-5 spacing, major lines, X axis in red and Y axis in green. It is aligned in both perspective and orthographic views.
- **Native grid on XY:** when the plugin starts, LichtFeld's own grid moves to the data XY plane at Z = 0, and the previous plane is restored when the plugin unloads. This is optional, and buttons let you switch it by hand.
- **Z-up gizmo** in place of LichtFeld's (top right). LichtFeld's gizmo shows the viewport's internal axes, with Y and Z reversed for Z-up data; the plugin's gizmo shows the data axes. With the Z-up orbit active, clicking a sphere snaps to that view. This is optional.
- **Axis triad** and **HUD**: view heading (0 = North), elevation and pivot in data coordinates.
- **Large-coordinate warning:** survey coordinates far from the origin (for example UTM) exceed float32 precision. Re-import with `centralize_dataset` enabled.
- **Diagnostics:** one button checks the host behaviours the plugin relies on and prints a report in English that you can paste into an issue.
- **Settings** are saved in the plugin data folder and survive updates. The UI is in English and Italian and follows LichtFeld's language; you can also choose it in the panel.

## Known limits

- Clicking the Z-up gizmo snaps views only while the Z-up orbit is active (always, by default).
- With "always on" enabled, the plugin keeps a modal operator running. Native tools that refuse to start while a modal is active may need the orbit switched off; Align is already handled.
- Native navigation (middle-mouse orbit when the plugin's orbit is off, the view cube, Align to Ground) remains Y-up. Use the plugin's orbit or the view buttons.
- While the Z-up orbit is active, native tools that need their own modal (for example Align point picking) wait until you press Esc. The plugin will not start its orbit while another modal is running.
- Coordinates are shown as LichtFeld reads them: if `centralize_dataset` was used at import, they are translated.
- In independent split view, the overlay follows the main viewport.

## Quick test

1. Import a Metashape COLMAP export, or open a PLY.
2. Open **Status and diagnostics → Run diagnostics**. All lines should read `OK` or `--`.
3. Click **Frame scene**, then **Plan**. X should point right and North up, and the grid should sit on the floor.
4. Click **Front (from South)**. Z should be vertical.
5. Click **Start Z-up orbit** and drag with the middle mouse. The horizon should stay level, and pan and zoom should work as usual.

## Files

| File | Contents |
|---|---|
| `zup_core.py` | Pure math: axis mapping, views, turntable, grid, clipping, ortho projection |
| `zup_bridge.py` | Guarded calls to `lichtfeld`, state, settings |
| `zup_overlay.py` | Draw handler: grid, axes, triad, HUD |
| `zup_ops.py` | Modal orbit operator |
| `zup_panel.py` | UI panel |
| `zup_diag.py` | Host diagnostics |
| `zup_i18n.py` | English and Italian strings |

## License

Copyright © 2026 Antonio Sartini. Released under GPL-3.0-or-later, the same license as LichtFeld Studio.

---

## Italiano

Plugin che fa vedere la scena come in Metashape, CloudCompare o un CAD: **XY in piano, +Z in alto**. Agisce solo sul viewport, quindi dati, trasformazioni ed export restano identici.

Per installarlo: **Strumenti → Marketplace plugin**, scrivi `Tonysa87/lichtfeld-zup-view` e clicca **Installa plugin**. Gli altri metodi sono in [INSTALL.md](INSTALL.md). Compare la scheda **Z-up View**, in italiano se LichtFeld è in italiano.

Per la prima prova usa **Stato e diagnostica → Esegui diagnostica**, poi Pianta, Fronte e l'orbita Z-up (tasto centrale, Esc per uscire). Con coordinate UTM o comunque grandi, reimporta con `centralize_dataset` attivo: il viewport lavora in float32.
