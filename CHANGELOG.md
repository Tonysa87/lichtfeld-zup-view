# Changelog

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
