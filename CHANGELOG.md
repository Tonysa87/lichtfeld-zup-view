# Changelog

## 0.2.4 (2026-10-11)

- Everything is set up as soon as the plugin is active. The Z-up orbit is always on and the panel no longer offers a way to switch it off; it still pauses by itself during other tools' modal actions and the Align tool.
- The Z-up gizmo, native grid on XY and Z-up Home/Focus are on at every start. Their checkboxes only apply to the current session and are no longer saved.

## 0.2.3 (2026-10-11)

- Z-up orbit always on (default): the middle mouse always orbits around Z, so native navigation no longer pulls the view back to Y-up after a view button. It pauses by itself while another tool runs a modal action (for example a selection rectangle) and while the Align tool is active, then comes back. Esc no longer turns it off; use the Stop button or the checkbox.
- Home and Focus under the gizmo now work in Z-up. Home frames the whole scene in a Z-up isometric view. Focus keeps LichtFeld's framing of the selection, then levels the horizon with Z up. The H and F keys do the same while the Z-up orbit is active. Optional.
- Z-up gizmo: an opaque backdrop now fully covers LichtFeld's gizmo. The renderer still draws it after its panel is disabled; disabling the panel only removes its clicks and dragging.

## 0.2.2 (2026-10-11)

- Panel layout fix: widgets no longer go missing or out of order after opening or closing a section or switching the orbit on and off. LichtFeld's immediate-mode layout matches widgets by position, so each section now lives in a stable child container and every variable part has its own container.
- The status line under Navigation now also shows when the Z-up orbit is off.
- When the plugin starts, LichtFeld's native grid moves to the data XY plane (Z = 0); the previous plane is restored when the plugin is unloaded. This can be turned off in Grid and axes.
- Z-up orientation gizmo: when the plugin starts, LichtFeld's gizmo (top right) is hidden and replaced, at the same place and size, by one that shows the data axes. LichtFeld's gizmo shows the viewport's internal axes, where Y and Z appear reversed for Z-up data. While the Z-up orbit is active, clicking a sphere snaps to that view (+Z = plan, −Y = front from South, and so on). It comes back when the plugin unloads, and can be turned off in Grid and axes.

## 0.2.1 (2026-10-11)

- Supports LichtFeld Studio 0.5.4, the latest release: every host API the plugin uses is identical in 0.5.4 and 0.5.5. The minimum is now `>=0.5.4`.

## 0.2.0 (2026-10-11)

Audit against the LichtFeld Studio 0.5.5 source.

- Orthographic views: the overlay is projected with the host's orthographic formula (the draw context matrix is always perspective), so grid and axes line up with the splats.
- Grid segments are clipped at the near plane, so lines no longer vanish or streak when the camera is low.
- Orbiting from the exact plan or bottom view no longer rotates the picture by 90 degrees.
- The plugin's state stays in step when LichtFeld replaces its modal (selection, Align); it refuses to start while another modal is active, and never cancels other tools' modals.
- HUD and triad take the viewport offset into account; the triad uses the real camera orientation.
- Orbit presses outside the viewport (panels) are ignored; a lost button release no longer hands the drag to the native Y-up orbit.
- Scene bounds apply node world transforms and sample large models before copying to the CPU.
- Automatic grid spacing (1-2-5 series), truncation warning, cached grid.
- Button to put the native grid on the data XY plane (`grid_plane = 2`).
- Warning for survey coordinates far from the origin (float32 precision).
- Settings persisted in the plugin data directory (survive updates).
- English and Italian UI, following LichtFeld's language.
- Diagnostics rewritten (English output, correct horizon test).
- Removed the experimental auto-level option (it fought the native Y-up orbit every frame).
- Requires LichtFeld Studio >= 0.5.5 and features operators.v1, panels.v1.

## 0.1.0

First version, tested only offline.
