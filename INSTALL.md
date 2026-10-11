# Installation guide / Guida all'installazione

Requires **LichtFeld Studio 0.5.4 or newer**. No extra Python packages are needed.

*Italiano più sotto.*

## Option A: Plugin Marketplace (recommended)

1. In LichtFeld, open **Tools → Plugin Marketplace**.
2. In the **GitHub URL or shorthand** field, type `Tonysa87/lichtfeld-zup-view`.
3. Click **Install Plugin**.
4. The **Z-up View** tab appears in the right panel. The plugin starts automatically from then on.

## Option B: Python console

1. Open **Tools → Python Console**.
2. Run:

   ```python
   import lichtfeld as lf
   lf.plugins.install("Tonysa87/lichtfeld-zup-view")
   ```

## Option C: manual copy (offline)

1. Download the repository as a ZIP from GitHub (**Code → Download ZIP**) and extract it.
2. Rename the extracted folder to `zup_view`. The folder name must match the plugin name.
3. Move it into the plugins folder:
   - Windows: `C:\Users\<user>\.lichtfeld\plugins\zup_view`
   - Linux: `~/.lichtfeld/plugins/zup_view`
4. Restart LichtFeld. `pyproject.toml` must sit directly inside `zup_view`, not in a nested subfolder.

## Check it works

1. Right after installing, the Z-up gizmo replaces LichtFeld's in the top-right corner. Seen from the side, its blue Z points up.
2. Load a scene, then open **Z-up View → Status and diagnostics → Run diagnostics**. Every line should read `OK` or `--`.
3. Click **Frame scene**, then **Plan**: X should point right and North up.
4. Drag with the middle mouse: the view orbits around Z and the horizon stays level.

## Update and uninstall

- **Update:** use **Update** in Tools → Plugin Marketplace, or run `lf.plugins.update("zup_view")`, then restart LichtFeld. Your preferences are kept, because they live in the plugin data folder.
- **Uninstall:** use **Uninstall** in the Marketplace, or run `lf.plugins.uninstall("zup_view")`.

## Troubleshooting

| Symptom | What to do |
|---|---|
| "Plugin directory already exists" | A previous copy is in `~/.lichtfeld/plugins/zup_view`. Delete that folder and install again. |
| The tab does not appear | Run `lf.plugins.get_error("zup_view")` and `lf.plugins.get_traceback("zup_view")` in the Python Console. |
| "requires LichtFeld …" | Your LichtFeld is older than 0.5.4. Update it. |
| "git not found in PATH" | Options A and B use git. Install git, or use option C. |
| Plugin loaded but not active | In the Marketplace, select `zup_view` and click **Load**, or run `lf.plugins.load("zup_view")`. |

To report a bug, open an [issue](https://github.com/Tonysa87/lichtfeld-zup-view/issues). Include the diagnostics output, your LichtFeld version and, if you can, a screenshot.

---

## Italiano

Serve **LichtFeld Studio 0.5.4 o successivo**. Non servono pacchetti Python aggiuntivi.

**A. Dal Marketplace (consigliato).** Apri **Strumenti → Marketplace plugin**. Nel campo dell'indirizzo GitHub scrivi `Tonysa87/lichtfeld-zup-view` e clicca **Installa plugin**. Nel pannello di destra compare la scheda **Z-up View**.

**B. Dalla console.** Apri **Strumenti → Console Python** ed esegui:

```python
import lichtfeld as lf
lf.plugins.install("Tonysa87/lichtfeld-zup-view")
```

**C. Copia manuale.**
1. Scarica lo ZIP da GitHub (**Code → Download ZIP**) ed estrailo.
2. Rinomina la cartella in `zup_view`.
3. Spostala in `C:\Users\<utente>\.lichtfeld\plugins\` su Windows, oppure in `~/.lichtfeld/plugins/` su Linux.
4. Riavvia LichtFeld. Il file `pyproject.toml` deve stare direttamente dentro `zup_view`.

**Verifica.**
1. In alto a destra compare il gizmo Z-up al posto di quello di LichtFeld.
2. Carica una scena e usa **Stato e diagnostica → Esegui diagnostica**: tutte le righe devono essere `OK` o `--`.
3. Clicca **Inquadra scena**, poi **Pianta**: X deve andare a destra e il Nord in alto.
4. Trascina col tasto centrale: la vista gira attorno a Z con l'orizzonte in piano.

**Problemi.**
- Se compare "Plugin directory already exists", cancella la vecchia cartella `zup_view` e reinstalla.
- Se la scheda non compare, esegui `lf.plugins.get_traceback("zup_view")` nella console.
- Le opzioni A e B usano git. Se git non è installato, usa la C.
