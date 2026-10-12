# Z-up View for LichtFeld Studio

A survey-style viewport for scenes whose data is **Z-up** (XY horizontal, +Z up), as produced by Agisoft Metashape, RealityCapture, laser scanning and GIS workflows.

It changes **only how the scene is viewed**: camera views, a turntable orbit around Z, a Z-up orientation gizmo, an XY grid and a HUD. Scene data, node transforms and exports are never modified.

**Version 0.3.0** works with LichtFeld Studio 0.5.4 and with the native Z-up navigation added after it (PR #3203, master of 2026-10-11). Changes are listed in [CHANGELOG.md](CHANGELOG.md).

*Italiano più sotto.*

## Why

LichtFeld assumes COLMAP data with Y pointing down. To show it upright it applies a fixed 180° rotation about X (`DATA_TO_VISUALIZER_WORLD_AXES = diag(1, -1, -1)`), and its navigation orbits around the viewport's +Y axis. With Z-up data that axis is a horizontal direction (data −Y), so:

- the floor appears vertical;
- orbiting with the middle mouse tumbles the scene;
- the orientation gizmo labels the viewport's internal axes, so Y and Z appear reversed;
- Home and Focus restore a Y-up camera.

LichtFeld 0.5.4 has no world-up setting; the plugin then provides its own Z-up orbit. Newer builds have a per-project **Up axis** (Rendering → Viewport): the plugin switches it to data +Z and leaves the orbit to LichtFeld. The gizmo labels, Home, the camera reset after loading data and survey views are still Y-up or missing natively, and the plugin covers them.

## Install

In LichtFeld, open **Tools → Plugin Marketplace**, enter `Tonysa87/lichtfeld-zup-view` in the GitHub field and click **Install Plugin**. The **Z-up View** tab appears in the right panel.

Requires LichtFeld Studio ≥ 0.5.4 and needs no extra Python packages (not even numpy: scene bounds use LichtFeld's tensors). For the Python console, a manual copy, updating, uninstalling and troubleshooting, see **[INSTALL.md](INSTALL.md)**.

## What happens when the plugin is active

Nothing needs to be configured. As soon as the plugin loads:

- **The middle mouse orbits around Z.** With a LichtFeld that has the native Up axis, the plugin sets it to data +Z for the current project (again when a project is opened or created, and when data is loaded) and the orbit, fly and drone modes are LichtFeld's own. On 0.5.4 the plugin's Z-up orbit is used instead: it pauses by itself only while another tool runs an action (for example a selection rectangle) or while the Align tool is active, then resumes.
- **After loading data the view is upright.** LichtFeld resets the camera to its Y-up Home; the plugin frames the scene in a Z-up isometric view instead.
- **A Z-up gizmo replaces LichtFeld's** in the top-right corner. It shows the data axes: X red, Y green, Z blue. Clicking a sphere snaps to that view: +Z gives the plan, −Y the front from South, +X the view from East, and so on.
- **LichtFeld's grid moves to the data XY plane** (Z = 0).
- **Home and Focus work in Z-up.** This applies to the buttons under the gizmo and to the H and F keys. Home frames the whole scene in a Z-up isometric view. Focus keeps LichtFeld's framing of the selection, then levels the horizon (with the native Up axis, LichtFeld's Focus is already level and is used as is).

When the plugin is unloaded, LichtFeld's gizmo, grid plane, Home/Focus buttons and the project's Up axis (if the plugin changed it) return to normal.

## Using it

**Mouse and keys**

| Input | Action |
|---|---|
| Middle mouse drag | Orbit around the vertical axis through the pivot (LichtFeld's own orbit when its Up axis is Z) |
| Right mouse drag / wheel | Pan / zoom (native) |
| Click on a Z-up gizmo sphere | Snap to that axis view |
| H / Home button | Frame the scene, Z-up isometric |
| F / Focus button | Frame the selection, horizon levelled |

**Panel (Z-up View tab)**

- **Views:**
  - Frame scene, Level view.
  - Plan, From below, Isometric.
  - Front (from South), Back (from North), Left (from West), Right (from East).
  - Plan and elevations switch to orthographic (optional). In plan, X points right and North up.
- **Navigation:**
  - Orbit status: LichtFeld's native Z-up, plugin orbit active, or paused.
  - Use LichtFeld's native Z-up navigation (on by default, only on builds that have it).
  - Frame the scene in Z-up after loading data (on by default).
  - Orbit gesture: middle mouse, or Alt + left mouse.
  - Sensitivity and direction inversion.
  - Step rotation buttons.
- **Grid and axes:**
  - Plugin XY grid at a chosen height, by default the estimated floor. Automatic 1-2-5 spacing, major lines, X axis in red and Y axis in green. It is aligned in perspective and orthographic views.
  - Axis triad, HUD and axes at the origin.
  - Native grid controls.
- **Status and diagnostics:**
  - Pivot, camera, view heading and elevation in data coordinates.
  - Language: same as LichtFeld, English or Italian.
  - **Run diagnostics:** checks the host behaviours the plugin relies on and prints a report in English that you can paste into an issue.

**Settings.** Your preferences are saved in the plugin's data folder and survive updates: grid, sensitivity, inversions, gesture, language and similar. The core behaviours (Z-up gizmo, native grid on XY, Z-up Home/Focus) are switched on at every start. Their checkboxes only turn them off for the current session. The Z-up orbit cannot be switched off.

**Large coordinates.** LichtFeld's viewport works in float32. With survey coordinates far from the origin, for example UTM, precision drops to tens of centimetres and the scene can jitter. The plugin shows a warning in the HUD and in the panel. Re-import the dataset with `centralize_dataset` enabled; it only applies a translation, so Z stays up.

## Known limits

- The plugin keeps a modal operator running for the Z-up orbit, the gizmo clicks and the H key, also with the native Up axis. The Align tool is handled automatically. If another native tool refuses to start, please open an issue.
- With the native Up axis the plugin sets it again when a project is opened or created and when data is loaded. If you choose Y-up in Rendering → Viewport it is respected until the next project or dataset; to keep Y-up, turn off the option in Navigation.
- LichtFeld's Align to Ground still works in Y-up and does not know about the plugin. Use the plugin's views instead.
- Coordinates are shown as LichtFeld reads them: if `centralize_dataset` was used at import, they are translated.
- In independent split view, the overlay follows the main viewport.

## Reporting a bug

Open an [issue](https://github.com/Tonysa87/lichtfeld-zup-view/issues) with:
- your LichtFeld version and operating system;
- what you did, what you expected and what happened;
- a screenshot;
- the output of **Run diagnostics**.

If the plugin does not load, also include the output of `lf.plugins.get_traceback("zup_view")` from the Python Console.

## Development

| File | Contents |
|---|---|
| `zup_core.py` | Pure math: axis mapping, views, turntable, grid, near-plane clipping, orthographic projection |
| `zup_bridge.py` | Guarded calls to `lichtfeld`, state, settings, native grid, gizmo and toolbar hooks |
| `zup_overlay.py` | Draw handler: grid, axes, Z-up gizmo, triad, HUD |
| `zup_ops.py` | Modal operator: Z-up orbit, gizmo clicks, H and F keys |
| `zup_panel.py` | UI panel |
| `zup_diag.py` | Host diagnostics |
| `zup_i18n.py` | English and Italian strings |
| `tests/` | Offline tests against a mock of the LichtFeld Python API |

Run the tests with `python tests/test_zup.py` (needs numpy). GitHub Actions runs them on every push.

Notes for contributors:

- **Coordinates.** All camera APIs and draw handlers work in viewport coordinates. The plugin converts with `(x, y, z) → (x, −y, −z)` at the boundary and does all its math in data coordinates.
- **Orthographic overlay.** The draw context always projects with a perspective matrix, so in orthographic views the overlay is projected by the plugin with the host's formula.
- **Native gizmo.** Disabling the `native.viewport_gizmo` panel removes only its input handling; the renderer still draws it, so the Z-up gizmo covers it with an opaque backdrop.
- **Panel layout.** LichtFeld's immediate-mode UI matches widgets by position. Each panel section therefore lives in its own `begin_child` container, and every variable part has its own container. A test checks that the widget sequence never changes between panel states.

## License

Copyright © 2026 Antonio Sartini. Released under GPL-3.0-or-later, the same license as LichtFeld Studio.

---

## Italiano

Plugin che fa vedere la scena come in Metashape, CloudCompare o un CAD: **XY in piano, +Z in alto**. Agisce solo sul viewport, quindi dati, trasformazioni ed export restano identici.

**Versione 0.3.0**: funziona con LichtFeld Studio 0.5.4 e con la navigazione Z-up nativa arrivata dopo (PR #3203, master dell'11/10/2026).

**Installazione.** Apri **Strumenti → Marketplace plugin**, scrivi `Tonysa87/lichtfeld-zup-view` e clicca **Installa plugin**. Gli altri metodi sono in [INSTALL.md](INSTALL.md). Compare la scheda **Z-up View**, in italiano se LichtFeld è in italiano.

**All'attivazione è già tutto impostato:**
- il tasto centrale gira attorno a Z: se LichtFeld ha l'**Up axis** nativo, il plugin lo imposta su +Z dei dati (anche a ogni progetto aperto o creato e a ogni caricamento di dati) e l'orbita è quella di LichtFeld; con la 0.5.4 resta l'orbita del plugin, che va in pausa solo mentre lavora un altro strumento o con Align;
- dopo il caricamento dei dati la vista è dritta: LichtFeld riporta la camera alla sua Home Y-up, il plugin inquadra la scena in isometrica Z-up;
- in alto a destra c'è il gizmo Z-up con gli assi dei dati, e un clic su una sferetta porta alla vista corrispondente;
- la griglia di LichtFeld passa sul piano XY;
- Home, Focus e i tasti H e F lavorano in Z-up.

**Pannello.**
- Viste: Pianta, Prospetti, Isometrica, Inquadra scena, Raddrizza vista.
- Navigazione: sensibilità, inversioni, rotazione a passi.
- Griglia e assi.
- Stato e diagnostica, con il pulsante **Esegui diagnostica**.

Le preferenze (griglia, sensibilità, lingua) restano salvate anche dopo un aggiornamento. Gizmo Z-up, griglia su XY e Home/Focus Z-up si riattivano a ogni avvio.

**Coordinate grandi.** Il viewport lavora in float32. Con coordinate UTM la scena può tremare e il plugin lo segnala: reimporta il dataset con `centralize_dataset` attivo.

**Limiti.** L'Align to Ground di LichtFeld resta Y-up. Se uno strumento nativo non parte perché è attiva l'orbita, apri una issue.
