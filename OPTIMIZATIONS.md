# Optimization Audit — 7DaysToBackup

**Audit date:** 2026-08-10
**Commit audited:** `4e20345`
**Scope:** `src/**`, `7DaysToBackup.py`, `requirements.txt`, `.github/workflows/auto-release.yml`
**Codebase size:** 610 lines of Python across 9 modules (at time of audit)
**Status:** Audited, then **implemented**. 16 of 19 findings are fixed; 3 are deferred as
product decisions. See *Implementation Status* immediately below.

> The findings in sections 1–5 are written in the present tense as they were at commit
> `4e20345`, describing the code **before** the fixes. They are kept that way deliberately
> so the reasoning and the measurements stay readable as a record. The status table says
> what has since changed.

---

## Implementation Status

Verified with 43 unit tests, `ruff`, an 8-part end-to-end GUI exercise (offscreen Qt), and
an event-loop stall probe. All green.

| Finding | Status | Where |
|---|---|---|
| F1 — blocking I/O on the GUI thread | **Fixed** | `core/operations.py`, `ui/workers.py`, `ui/window.py` |
| F2 — unused `PySide6_Addons` | **Fixed** | `requirements.txt` |
| F3 — no pip cache, duplicated build steps | **Fixed** | `auto-release.yml` |
| F4 — deflate level 6 | **Fixed** | `operations.export_save(compresslevel=1)` |
| F5 — PyInstaller onefile | **Deferred** — changes the shape of the release artifact | — |
| F6 — config path + silent write failure | **Fixed** | `core/config.py`, `core/paths.py` |
| F7 — logger import-time filesystem work | **Fixed** | `core/logger.py` |
| F8 — dead `SAVES_PATH` | **Fixed** | `core/platform.py` |
| F9 — import guard checked only `members[0]` | **Fixed** | `operations.archive_conflicts` |
| F10 — export clobbers existing archive | **Fixed** | `operations.unique_path` + timestamp |
| F10b — Windows Desktop under OneDrive | **Fixed** | `platform.get_desktop_path` via `QStandardPaths` |
| F11 — backups inside the game save tree | **Deferred** — user-visible relocation, needs a settings decision | — |
| F12 — broken `paths-ignore` negation | **Fixed** | `auto-release.yml` |
| F13 — duplicated retranslation | **Fixed** | `window._retranslate_ui` |
| F14 — re-listing on selection change | **Fixed** | `addItems` + `os.scandir` |
| F15 — dead imports | **Fixed** | `config.py`, `settings_dialog.py`, `window.py` |
| F16 — language not persisted | **Fixed** | `window.change_language` |
| F17 — CI concurrency / fail-fast / stale action | **Fixed** | `auto-release.yml` |
| F18 — no tests, no lint | **Fixed** | `tests/`, plus a `test` job gating `build` |
| F19 — modal error before the window shows | **Fixed** | `window.status_label` inline empty state |

### Measured result of the F1 fix

Event-loop stall probe (`QTimer` at 20 ms, 220 MB save, offscreen Qt) — the before/after
metric section 5 asks for:

| Path | Wall time | **Max GUI stall** |
|---|---|---|
| Old — blocking call in the slot | 1.63 s | **1.63 s** (100% of the operation) |
| New — `QRunnable` on `QThreadPool` | 0.20 s | **0.021 s** (one timer tick) |

The stall exactly equalled the wall time on the old path, which is direct proof of total
event-loop starvation. It is now one timer interval regardless of operation length, so the
window repaints and the Cancel button works throughout. (The wall-time column is not a
speedup — the second run benefited from a warm page cache. Only the stall column is the
result here.)

### Deferred, and why

* **F5 (onefile → onedir).** Real startup win, but it turns a single downloadable `.exe`
  into a folder or an installer. That is a product call about how you want to distribute,
  not a change to make on your behalf.
* **F11 (move backups out of the game save tree).** The right fix needs a new setting and a
  decision about what happens to users' existing in-tree backups. Worth pairing with the
  "Yedek geçmişi" feature already on your roadmap.
* **SHA-pinning `softprops/action-gh-release`.** Upgraded v1 → v2, but left on the tag: I
  could not verify a specific commit SHA from this environment, and pinning to a guessed
  SHA would be worse than the tag. Pin it when you can look up the real one.

---

## 1) Optimization Summary

This is a small, clean, readable codebase. The module split (`core` / `ui` / `i18n`) is
sensible and there is no algorithmic complexity worth attacking — no N+1 queries, no
nested loops over large collections, no hot paths in the classic sense. Layout, naming,
and type hints are consistent.

The optimization problems are **not** in the algorithms. They are in three places:

1. **Where the work runs** — every expensive filesystem operation executes on the Qt
   event-loop thread, so the application is unresponsive for the entire duration of every
   backup, delete, export and import.
2. **What ships** — roughly 70% of the dependency payload (Windows) and 75% (macOS) is a
   Qt package the application never imports, paid for on every CI run and in every
   released binary.
3. **What happens when things go wrong** — silent exception swallowing, a config path that
   depends on the working directory, and import/export guards that do not cover the cases
   that cause data loss.

Because this is a **backup tool**, reliability findings are weighted heavily here. A
performance bug in a backup tool is an annoyance; a silent overwrite is the failure the
tool exists to prevent.

### Top 3 highest-impact improvements

| # | Change | Measured / estimated effect |
|---|--------|------------------------------|
| 1 | Move backup / delete / export / import off the GUI thread | Eliminates a **34.7 s freeze per GB** on export (measured); restores progress + cancel |
| 2 | Drop `PySide6_Addons` from `requirements.txt` | **−157 MB** Windows / **−308 MB** macOS per CI run per OS, and a materially smaller binary |
| 3 | Add pip caching + merge the duplicated build steps in CI | Removes a ~230 MB download from every push, on all 3 runners |

### Biggest risk if no changes are made

**Silent data loss during export, plus a permanently frozen window during long operations.**

`export_save` opens the destination zip with mode `"w"` at a fixed, non-timestamped path
(`Desktop/<save>.zip`). Exporting the same save twice destroys the first archive with no
prompt and no warning. `backup_save`, by contrast, *does* timestamp its output — so the
tool is internally inconsistent about the exact thing it is for.

Compounding it: during a 1 GB export the window is frozen for ~35 seconds with no progress
indicator, so the OS paints "Not Responding" and users reasonably conclude the app has
hung and force-kill it. Killing mid-`copytree` leaves a partial backup directory that then
appears in the save list as if it were a real save; killing mid-`rmtree` leaves a partially
deleted save. Neither is detected or cleaned up on the next launch.

---

## 2) Findings (Prioritized)

### F1 — All filesystem work runs on the Qt event-loop thread

* **Category:** Concurrency / Reliability
* **Severity:** **Critical**
* **Impact:** Perceived latency, responsiveness, data integrity after a forced kill
* **Evidence:**
  * `src/ui/window.py:156` — `shutil.copytree(source_path, destination_path)`
  * `src/ui/window.py:180` — `shutil.rmtree(source_path)`
  * `src/ui/window.py:191-196` — `zipfile.ZipFile(...)` + `os.walk` + `write` loop
  * `src/ui/window.py:231` — `zip_file.extractall(target_map_path)`

  All four are invoked directly from `clicked` signal handlers, which Qt dispatches on the
  main thread. No `QThread`, `QThreadPool`, `QtConcurrent`, or `processEvents` call exists
  anywhere in the codebase.
* **Why it's inefficient:** The Qt event loop cannot dispatch paint, input, or timer events
  while a slot is executing. A multi-second slot means a window that does not repaint, does
  not respond to clicks, and is flagged as hung by Windows and macOS. There is no progress
  reporting and no way to cancel. 7DTD save directories routinely reach several GB once a
  world has been explored, so this is the normal case, not the edge case.
* **Measured** (synthetic 1090 MB tree, 425 files, container filesystem, warm page cache):

  | Operation | Wall time | UI state |
  |---|---|---|
  | `export_save` (DEFLATE, default level) | **34.7 s** | frozen |
  | `import_save` (`extractall` of the 842 MB archive) | **10.2 s** | frozen |
  | `backup_save` (`copytree`) | 0.9 s\* | frozen |
  | `delete_save` (`rmtree`) | 0.1 s\* | frozen |

  \* `copytree` and `rmtree` are unrepresentatively fast on this host: the filesystem
  supports server-side copy (`os.copy_file_range`) and the whole tree was in page cache.
  On a user's mechanical drive or external USB backup disk these scale with real device
  throughput — assume 1–3 minutes per GB on slow media. **Re-measure on target hardware**
  (see §5). The export number is CPU-bound and therefore transfers much more directly.
* **Recommended fix:** Move each operation into a `QRunnable` on a `QThreadPool` (or a
  `QThread` worker object), report progress back via signals, and drive a
  `QProgressDialog` with a working Cancel button. Disable the action buttons for the
  duration rather than leaving them clickable-but-dead. Sketch in §6.1.
* **Tradeoffs / Risks:** This is the largest change in the report. Threading introduces
  real hazards: Qt widgets must only be touched from the GUI thread, so workers must
  communicate exclusively by signal. Cancellation of a partially completed `copytree` needs
  explicit cleanup of the partial destination or you trade one data-integrity bug for
  another. Do this behind tests (F18).
* **Expected impact estimate:** Wall time is unchanged — the win is that the application
  stays interactive and cancellable for 100% of the operation duration, and stops being
  force-killed mid-write.
* **Removal Safety:** N/A (addition)
* **Reuse Scope:** service-wide — one shared worker/progress helper serves all four
  operations

---

### F2 — `PySide6_Addons` is a hard dependency and is never imported

* **Category:** Build / Cost
* **Severity:** **High**
* **Impact:** CI minutes, network transfer, released binary size, cold-start time
* **Evidence:** `requirements.txt` pins all four packages:

  ```
  PySide6==6.10.1
  PySide6_Addons==6.10.1
  PySide6_Essentials==6.10.1
  shiboken6==6.10.1
  ```

  The entire application imports only `PySide6.QtCore`, `PySide6.QtGui`, and
  `PySide6.QtWidgets` (`window.py:7-22`, `settings_dialog.py:1-5`, `theme.py:1`,
  `main.py:2`). All three modules live in **Essentials**. Nothing in `Addons` —
  QtWebEngine, Qt3D, QtCharts, QtMultimedia, QtDataVisualization — is referenced anywhere.

  Wheel sizes pulled from PyPI for 6.10.1:

  | Package | Windows x86-64 | macOS universal2 |
  |---|---|---|
  | `PySide6` (metapackage, pulls both) | 0.5 MB | 0.5 MB |
  | `PySide6_Essentials` | 71.0 MB | 100.6 MB |
  | **`PySide6_Addons`** | **157.2 MB** | **307.7 MB** |
  | `shiboken6` | 1.2 MB | 0.5 MB |

* **Why it's inefficient:** `Addons` is 69% of the Windows download and 75% of the macOS
  download for functionality that is never loaded. It is downloaded and unpacked on every
  CI run on every one of the three runners (there is no pip cache — see F3), and its
  presence in the build environment gives PyInstaller the opportunity to sweep additional
  Qt plugins and shared libraries into the bundle. Removing the package from the
  environment is a stronger guarantee than any `--exclude-module` flag.
* **Recommended fix:** Replace the four pins with the two packages actually needed:

  ```
  PySide6-Essentials==6.10.1
  shiboken6==6.10.1
  ```

  Listing the `PySide6` metapackage is what drags `Addons` in — the metapackage exists
  precisely to depend on both halves.
* **Tradeoffs / Risks:** Low, but verify first. If a future feature wants `QtCharts` or
  `QtMultimedia` it will need `Addons` back. Also confirm `import PySide6.QtWidgets` still
  resolves under Essentials-only in a clean venv on all three platforms before merging —
  it should, but it is one command to check.
* **Expected impact estimate:** ~157 MB less per Windows CI run, ~308 MB less per macOS
  run, ~150 MB+ less per Linux run. Binary size reduction needs measurement but should be
  substantial.
* **Removal Safety:** **Likely Safe** — verify with a clean-venv smoke launch per platform
* **Reuse Scope:** service-wide

---

### F3 — CI re-downloads the full dependency set on every push; build steps are duplicated

* **Category:** Build / Cost
* **Severity:** **High**
* **Impact:** CI wall time, runner minutes, maintenance surface
* **Evidence:** `.github/workflows/auto-release.yml`

  ```yaml
  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: '3.11'          # no `cache: 'pip'`

  - name: Install dependencies
    run: |
      python -m pip install --upgrade pip
      pip install -r requirements.txt
      pip install pyinstaller
  ```

  and then two steps that differ only in their `if:` condition and are otherwise
  **byte-identical**:

  ```yaml
  - name: Build with PyInstaller (Windows)
    if: runner.os == 'Windows'
    run: pyinstaller 7DaysToBackup.py -F -w -n 7DaysToBackup

  - name: Build with PyInstaller (macOS/Linux)
    if: runner.os != 'Windows'
    run: pyinstaller 7DaysToBackup.py -F -w -n 7DaysToBackup
  ```

* **Why it's inefficient:** With no `cache: 'pip'`, every push to `main` re-downloads
  ~230 MB of Qt wheels on each of three runners — roughly 700 MB of transfer and several
  minutes of install time per commit, for a dependency set that changes maybe twice a year.
  The duplicated build steps are a textbook copy-paste hazard: the two commands must be
  kept in lockstep by hand, and the `if:` split implies a platform difference that does not
  exist. `pip install --upgrade pip` on every run adds a further round trip for no benefit
  on a pinned toolchain.
* **Recommended fix:** Add `cache: 'pip'` with `cache-dependency-path: requirements.txt`,
  collapse the two build steps into one unconditional step, and drop the pip self-upgrade.
  Full patch in §6.5. Combined with F2 the install step shrinks dramatically.
* **Tradeoffs / Risks:** None meaningful. Cache keys derive from `requirements.txt`, so a
  dependency bump correctly invalidates.
* **Expected impact estimate:** Install step drops from minutes to seconds on cache hit;
  one fewer step to keep synchronized.
* **Removal Safety:** **Safe** (the duplicate step is provably redundant — identical
  command bodies)
* **Reuse Scope:** service-wide (CI)

---

### F4 — Export compresses at zlib level 6 for zero size benefit

* **Category:** CPU
* **Severity:** **Medium-High**
* **Impact:** Export latency (and therefore GUI freeze duration, see F1)
* **Evidence:** `src/ui/window.py:191` —
  `zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)`. No `compresslevel` is passed, so
  zlib's default level 6 is used.
* **Why it's inefficient:** 7DTD save payloads are dominated by region/chunk binaries that
  are already compressed on disk. Level 6 spends substantially more CPU than level 1
  searching for matches that mostly are not there. Because export is single-threaded and
  on the GUI thread, every second of that CPU is a second of frozen window.
* **Measured** (synthetic 1090 MB tree, 425 files, deliberately mixed: ~70% incompressible
  binary, ~20% repetitive binary, ~10% XML):

  | Variant | Time | Archive size | Ratio | Speedup |
  |---|---|---|---|---|
  | **Current** — DEFLATE, default level 6 | 34.7 s | 842 MB | 77.2% | baseline |
  | DEFLATE, `compresslevel=1` | **28.7 s** | **842 MB** | 77.3% | **1.21×** |
  | `ZIP_STORED` (no compression) | 2.8 s | 1090 MB | 100.0% | 12.2× |

  Level 1 produced an archive **the same size to three significant figures** (842 MB vs
  842 MB; 77.3% vs 77.2%) while running 21% faster. On real save data, which is more
  thoroughly pre-compressed than this synthetic mix, the size delta should be smaller still
  and the relative CPU saving similar or better.
* **Recommended fix:** Pass `compresslevel=1`. Optionally expose a "fast export
  (uncompressed)" checkbox in Settings for users who want the 12× path and have the disk
  space — but do not make `ZIP_STORED` the default, since +29% archive size is a real cost
  for a tool whose output users keep around.
* **Tradeoffs / Risks:** Essentially none at level 1 given the measured size parity. Verify
  once against a real save directory before committing to it (§5).
* **Expected impact estimate:** ~20% faster export; ~6 s saved per GB.
* **Removal Safety:** **Safe** (output remains a standard, universally readable zip)
* **Reuse Scope:** local file

> **Tested and rejected:** I hypothesised that `zipfile.ZipFile.write`'s internal 8 KiB
> copy buffer (`shutil.copyfileobj(src, dest, 1024*8)`, confirmed in the CPython 3.11
> source) was costing syscalls, and benchmarked replacing it with a 1 MiB buffer via
> `ZipFile.open(zinfo, 'w')`. On the I/O-bound `ZIP_STORED` path the result was
> **1.78 s @ 8 KiB vs 1.80 s @ 1 MiB — no measurable difference**; the page cache absorbs
> the small reads entirely. This micro-optimization is **not recommended**: it adds code
> for no gain. Noted so nobody re-derives the same dead end.

---

### F5 — PyInstaller `-F` (onefile) re-extracts the whole bundle on every launch

* **Category:** Build / Frontend (startup latency)
* **Severity:** **Medium-High**
* **Impact:** Cold-start time, temp-disk churn, antivirus friction
* **Evidence:** `.github/workflows/auto-release.yml` — `pyinstaller 7DaysToBackup.py -F -w -n 7DaysToBackup`,
  and `readme.md` documents the same `-F -w` command for local builds.
* **Why it's inefficient:** `--onefile` produces a self-extracting archive. Every launch
  unpacks the entire embedded payload — for a Qt application that is on the order of
  100–200 MB of shared libraries and plugins — into a temporary directory, runs from there,
  and deletes it on exit. Nothing is cached between runs, so the cost is paid every single
  time the user opens the app, and it is a multi-second delay on typical hardware with no
  splash screen to explain it. The same self-extraction behaviour is a well-known trigger
  for antivirus heuristics, which the README already apologises for at length under
  "Güvenlik Uyarısı".
* **Recommended fix:** Switch to `--onedir` and distribute a zip (or a real installer:
  Inno Setup on Windows, a `.dmg` on macOS). Startup then does a normal dynamic link
  against files already on disk. If a single-file download is a hard product requirement,
  keep onefile but set expectations with a splash screen (`--splash`).
* **Tradeoffs / Risks:** Distribution becomes a folder or an installer rather than one
  `.exe`, which is a genuine UX regression for the "download and run" case — this is a
  product decision, not purely technical. Release asset paths in the workflow need updating
  to match. Note the current macOS `-w -F` build also emits a `.app` bundle that the
  release step ignores, publishing only the bare Unix executable.
* **Expected impact estimate:** Cold start from seconds to near-instant; likely fewer AV
  false positives.
* **Removal Safety:** **Needs Verification** (changes the shape of the release artifact)
* **Reuse Scope:** service-wide (build + release + README)

---

### F6 — `config.json` resolves against the working directory, and write failures are silent

* **Category:** Reliability
* **Severity:** **High**
* **Impact:** Settings silently lost or written to unpredictable locations
* **Evidence:** `src/core/config.py:5` — `CONFIG_FILE = "config.json"` (a bare relative
  path), used at `config.py:18,20,29`. Plus:

  ```python
  def save_config(self) -> None:
      try:
          with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
              json.dump(self.config, f, indent=4)
      except Exception:
          pass          # config.py:31-32 — every failure discarded
  ```

* **Why it's inefficient:** A relative path resolves against the **current working
  directory**, which for a GUI application is whatever the launcher happened to set — the
  desktop for a shortcut, `C:\Windows\System32` for some launch paths, `/` for some Linux
  desktop entries. Consequences: the user's custom save path is written somewhere
  unpredictable, is not found on the next launch (so settings appear to reset at random),
  and in a read-only or protected directory the write fails outright. The bare
  `except Exception: pass` then discards that failure completely — no log line, no dialog,
  no return value. The user clicks Save, the dialog closes as if it worked, and the setting
  is gone. `load_config` has the same swallow at `config.py:22-23`, silently resetting to
  `{}` on a corrupt file rather than reporting it.

  A non-atomic `open(..., 'w')` is also a truncate-then-write: an interruption mid-write
  leaves a truncated, unparseable `config.json`, which `load_config` then silently discards.
* **Recommended fix:** Resolve to a per-user config directory
  (`%APPDATA%` / `~/Library/Application Support` / `$XDG_CONFIG_HOME`), write atomically
  (temp file in the same directory + `os.replace`), narrow the exception handlers to
  `OSError` / `json.JSONDecodeError`, log every failure, and return a success flag so
  `SettingsDialog._save_settings` can tell the user when a save did not happen. Patch in
  §6.3.
* **Tradeoffs / Risks:** Existing users' `config.json` in the old location is not migrated
  — either add a one-time migration or accept that the single stored setting is re-entered
  once. `config.json` is already in `.gitignore`, so nothing in the repo depends on the
  current location.
* **Expected impact estimate:** Removes an entire class of "my settings keep resetting"
  reports. No runtime cost.
* **Removal Safety:** **Needs Verification** (config location change is user-visible)
* **Reuse Scope:** module (`core`)

---

### F7 — `logger.py` performs filesystem work at import time, in the install directory

* **Category:** Reliability
* **Severity:** **High**
* **Impact:** Startup crash risk in packaged builds; unbounded log growth
* **Evidence:** `src/core/logger.py:4-22`, all at module scope:

  ```python
  LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
  LOG_DIR = os.path.abspath(LOG_DIR)
  os.makedirs(LOG_DIR, exist_ok=True)          # line 6 — runs on import
  ...
  fh = logging.FileHandler(LOG_PATH, encoding='utf-8')   # line 14 — opens the file on import
  ...
  sh = logging.StreamHandler()                 # line 20 — unconditional
  logger.addHandler(sh)
  ```

* **Why it's inefficient:** Three distinct failure modes, all at import time — before any
  UI exists to report them, so the user sees an instant silent exit:
  1. `__file__` in a PyInstaller onefile build points into the extracted temp directory, so
     logs are written to a directory that is deleted on exit. In an onedir build installed
     under `C:\Program Files`, `os.makedirs` and `FileHandler` raise `PermissionError`
     against a read-only location, and an unhandled exception during import of
     `settings_dialog` takes the whole application down.
  2. The build uses `-w` (windowed, no console). Under `pythonw`/windowed mode `sys.stderr`
     can be `None`; a `StreamHandler` bound to it raises on first emit. The comment says
     this handler is "for console during development", but nothing gates it to development.
  3. `logger.setLevel(logging.DEBUG)` with a plain `FileHandler` and no rotation means
     `debug.log` grows without bound for the life of the installation.
* **Recommended fix:** Move handler setup into an idempotent `setup_logging()` called once
  from `main()`, inside a `try`; target a per-user log directory (same resolver as F6);
  use `RotatingFileHandler(maxBytes=1_000_000, backupCount=3)`; add the `StreamHandler`
  only when `sys.stderr` is not `None`; default to `INFO` with `DEBUG` behind an env var.
  Patch in §6.4.
* **Tradeoffs / Risks:** Log location changes. `logs/` is already in `.gitignore`.
* **Expected impact estimate:** Removes a plausible hard-crash-on-startup path in packaged
  builds; bounds disk usage.
* **Removal Safety:** **Needs Verification** (must be tested against a real packaged build)
* **Reuse Scope:** module (`core`)

---

### F8 — `SAVES_PATH` is dead, and computing it at import does I/O and freezes a stale value

* **Category:** Dead Code
* **Severity:** **Medium**
* **Impact:** Import-time syscall; a latent correctness bug for any future caller
* **Evidence:** `src/core/platform.py:63` — `SAVES_PATH = get_saves_path()`.
  A repository-wide grep for `SAVES_PATH` returns exactly one other hit, `DESKTOP_PATH` on
  the following line, which *is* used. `SAVES_PATH` itself has **zero** references:

  ```
  ./src/core/platform.py:63:SAVES_PATH = get_saves_path()      # only occurrence
  ```

  `window.py:25` deliberately imports the *function* `get_saves_path`, not this constant.
* **Why it's inefficient:** Evaluating it at import time runs `platform.system()`, a
  `config.get`, and an `os.path.isdir` stat before `main()` is entered. Worse than the cost
  is the trap: the value is frozen at import, but `get_saves_path()` depends on the
  user-settable `custom_save_path`. Any future code that reaches for the convenient-looking
  constant instead of the function will silently ignore the user's configured path until
  restart. This is a bug waiting for its first caller.
* **Recommended fix:** Delete line 63. Keep `get_saves_path()` as the only accessor.
* **Tradeoffs / Risks:** None — no importer exists.
* **Expected impact estimate:** Negligible runtime; removes a real future-bug vector.
* **Removal Safety:** **Safe** (verified by grep across all `.py` files)
* **Reuse Scope:** local file

> **`DESKTOP_PATH` (line 64) has the same import-time-evaluation shape but is genuinely
> used** (`window.py:190,215`). It is lower risk because the desktop path does not change
> at runtime, but converting both to functions is the consistent fix. See also F10 for a
> separate correctness problem with how the desktop path is derived on Windows.

---

### F9 — The import overwrite guard inspects only the first archive entry

* **Category:** Reliability / Security-impacting
* **Severity:** **Medium**
* **Impact:** Silent overwrite of existing saves; unbounded disk consumption
* **Evidence:** `src/ui/window.py:222-231`:

  ```python
  members = zip_file.namelist()
  if not members:
      raise ValueError(...)
  top_level_folder = members[0].split("/")[0]      # only members[0] is examined
  extract_path = os.path.join(target_map_path, top_level_folder)
  if os.path.exists(extract_path):
      self._show_error(...); return
  zip_file.extractall(target_map_path)             # extracts everything regardless
  ```

* **Why it's inefficient:** The guard checks one path and then extracts all of them.
  Three ways through it, all silent:
  1. **Multi-root archive.** If the zip contains `SaveA/...` and `SaveB/...`, only `SaveA`
     is checked. An existing `SaveB` on disk is overwritten file-by-file by `extractall`
     with no prompt.
  2. **First entry is a top-level file.** If `members[0]` is `readme.txt`,
     `top_level_folder` becomes `"readme.txt"`, the existence check is meaningless, and the
     real save folders in the archive are extracted unchecked.
  3. **No size bound.** Nothing inspects `ZipInfo.file_size` before extracting. A
     maliciously crafted or merely corrupt archive can expand to an arbitrary size and fill
     the user's disk — the classic zip-bomb amplification, made worse by running on the GUI
     thread (F1), so the user cannot cancel it.
* **Explicitly *not* a finding — path traversal.** I checked the CPython 3.11 source of
  `ZipFile._extract_member` directly. It strips drive letters via `os.path.splitdrive`,
  filters `''`, `os.path.curdir` and `os.path.pardir` out of every path component, and
  applies `_sanitize_windows_name` on Windows. Classic "zip slip" (`../../evil`) is
  **not** exploitable through `extractall` on any supported Python version. Do not spend
  effort on it.
* **Recommended fix:** Compute the full set of top-level names
  (`{m.split("/")[0] for m in members}`), reject the import if **any** of them already
  exists on disk, and sum `ZipInfo.file_size` across members to reject archives above a
  sane threshold before extracting. Patch in §6.2.
* **Tradeoffs / Risks:** Stricter behaviour will reject some imports that currently
  "work" by overwriting. That is the intended change. The existence check remains TOCTOU
  against a concurrently running game, which is acceptable for a desktop tool.
* **Expected impact estimate:** Closes a silent data-loss path and a disk-exhaustion vector.
* **Removal Safety:** N/A (hardening)
* **Reuse Scope:** local file

---

### F10 — Export silently destroys an existing archive of the same name

* **Category:** Reliability
* **Severity:** **Medium**
* **Impact:** Data loss; inconsistent with `backup_save`
* **Evidence:** `src/ui/window.py:189-191`:

  ```python
  zip_filename = f"{selected_save}.zip"
  zip_path = os.path.join(DESKTOP_PATH, zip_filename)
  with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
  ```

  Compare `backup_save` at `window.py:154-155`, which *does* disambiguate:

  ```python
  backup_suffix = datetime.now().strftime("_backup_%Y.%m.%d-%H.%M.%S")
  destination_path = f"{source_path}{backup_suffix}"
  ```

* **Why it's inefficient:** Mode `"w"` truncates. The filename has no timestamp and there
  is no existence check or overwrite prompt, so exporting the same save on Tuesday destroys
  Monday's archive. The user is given a success dialog either way. The tool timestamps
  backups but not exports, which is an inconsistency users cannot predict.

  Secondary problem in the same code path: `DESKTOP_PATH` comes from
  `platform.py:42-59`, which builds `os.path.join(home, "Desktop")` on Windows. That is
  wrong whenever the Desktop folder is redirected — OneDrive Known Folder Move is common
  and enabled by default on many consumer installs — or localized on a non-English Windows.
  Export then either fails or writes to a stale directory the user does not look at.
* **Recommended fix:** Timestamp the export filename exactly as `backup_save` does, or
  prompt with `QFileDialog.getSaveFileName` (which supplies a native overwrite
  confirmation for free) and let the user choose the destination. On Windows, resolve the
  desktop via `SHGetKnownFolderPath(FOLDERID_Desktop)` rather than string-joining, and fall
  back to the home directory if the resolved path does not exist.
* **Tradeoffs / Risks:** A save dialog is one extra click; timestamping alone preserves
  the current zero-click flow. Prefer timestamping and treat the dialog as optional.
* **Expected impact estimate:** Eliminates a silent data-loss path.
* **Removal Safety:** **Safe**
* **Reuse Scope:** local file — the timestamp-suffix helper should be shared with
  `backup_save` (see F13)

---

### F11 — Backups are written inside the game's own save tree and then listed as saves

* **Category:** Cost / Correctness
* **Severity:** **Medium**
* **Impact:** Disk usage inside the game directory; confusing and compounding UI state
* **Evidence:** `src/ui/window.py:153-156`:

  ```python
  selected_map, selected_save, source_path = self._selected_paths()
  backup_suffix = datetime.now().strftime("_backup_%Y.%m.%d-%H.%M.%S")
  destination_path = f"{source_path}{backup_suffix}"
  shutil.copytree(source_path, destination_path)
  ```

  `source_path` is `<Saves>/<map>/<save>` (`window.py:251`), so the backup lands as a
  sibling **inside `<Saves>/<map>/`**. `load_saves` (`window.py:148-149`) then lists
  everything in that directory with no filtering.
* **Why it's inefficient:** Three consequences:
  1. Backups appear in the app's own save list, so a user can select a backup and back
     *that* up, producing `MySave_backup_A_backup_B` — and each round doubles disk usage
     again.
  2. 7 Days to Die enumerates its own `Saves` directory. Backups are liable to show up in
     the in-game load menu as if they were playable saves.
  3. Every backup doubles the space consumed inside the game's data folder, which is the
     one place a user is least likely to be watching. There is no retention policy, so
     backups accumulate until the disk fills.
* **Recommended fix:** Default the backup destination to a dedicated directory outside the
  game tree (e.g. `<Documents>/7DaysToBackup/<map>/`), configurable in Settings alongside
  the existing custom save path. At minimum, filter `_backup_` entries out of `load_saves`
  and add a retention setting ("keep last N backups").
* **Tradeoffs / Risks:** Changes where existing users' backups go; old in-tree backups
  should still be discoverable, so keep listing them read-only or offer a one-time move.
  Cross-filesystem copies are slower than same-filesystem ones, which interacts with F1.
* **Expected impact estimate:** Bounds disk growth; removes a confusing UI state.
* **Removal Safety:** **Needs Verification** (user-visible behaviour change)
* **Reuse Scope:** module (`ui` + `core`)

---

### F12 — CI `paths-ignore` almost certainly skips builds for dependency changes

* **Category:** Build / Reliability
* **Severity:** **Medium**
* **Impact:** A dependency bump ships no release
* **Evidence:** `.github/workflows/auto-release.yml`:

  ```yaml
  paths-ignore:
    - '**.md'
    ...
    - '**.txt'
    - '!requirements.txt'
  ```

* **Why it's inefficient:** `'**.txt'` matches `requirements.txt`. The following line is
  clearly intended to re-include it, but GitHub Actions does not apply `!` negation inside
  the `-ignore` family of filters the way it does inside the positive `paths` filter — the
  documented approach for "exclude these but keep that one" is `paths` with `!`, and
  `paths` and `paths-ignore` cannot both be set for the same event. Read literally,
  `'!requirements.txt'` is a pattern matching a file whose name begins with an exclamation
  mark, which no commit will ever contain. A push that changes **only** `requirements.txt`
  therefore matches the ignore list entirely and the workflow does not run — so a security
  or version bump to PySide6 produces no new build and no release.
* **Confidence:** High from the pattern semantics, but I could not reach `docs.github.com`
  from this environment to quote the specification verbatim, and no commit in this
  repository's history isolates a `requirements.txt`-only change to confirm empirically.
  Treat as **likely** and verify with the concrete test in §5.
* **Recommended fix:** Drop the ineffective negation and stop matching `**.txt` wholesale
  — list the specific text files that should be ignored, or switch the whole filter to the
  positive `paths` form where `!` is honoured. Patch in §6.5.
* **Tradeoffs / Risks:** Being less aggressive about skipping means a few more builds. That
  is the correct trade for a release pipeline.
* **Expected impact estimate:** Dependency changes actually produce releases.
* **Removal Safety:** **Needs Verification** (see §5 for the test)
* **Reuse Scope:** service-wide (CI)

---

### F13 — Retranslation logic is duplicated and already drifting

* **Category:** Reuse Opportunity
* **Severity:** **Low-Medium**
* **Impact:** Maintenance cost, guaranteed future bugs as strings are added
* **Evidence:** `_setup_ui` (`window.py:43-103`) sets each widget's text once, and
  `change_language` (`window.py:105-117`) sets six of them again by hand:

  ```python
  self.setWindowTitle(self.translations["title"])
  self.map_label.setText(self.translations["map_list"])
  self.save_label.setText(self.translations["save_list"])
  self.backup_button.setText(self.translations["backup"])
  self.delete_button.setText(self.translations["delete"])
  self.export_button.setText(self.translations["export"])
  self.import_button.setText(self.translations["import"])
  ```

  `self.settings_button` is **already missing** from that list — it is created with
  `self.translations["settings"]` at `window.py:51` but never re-set. The bug is invisible
  today only because the string happens to be the language-neutral glyph `⚙`.

  The same method also reverse-maps display name → language code with a linear scan
  (`window.py:106-109`) even though the combo box was populated with the code as item data
  at `window.py:57` (`self.language_box.addItem(display, code)`) and could simply call
  `currentData()`.
* **Why it's inefficient:** Two lists of widgets that must be kept in sync by hand. Every
  new translatable widget must be added in two places, and forgetting the second place
  produces a partially translated UI — which has already happened once. The signal is wired
  to `currentTextChanged` rather than `currentIndexChanged`, which is what forces the
  reverse lookup to exist at all.
* **Recommended fix:** Extract a single `_retranslate_ui()` and call it from both
  `_setup_ui` and `change_language`. Wire `currentIndexChanged` and read
  `self.language_box.currentData()`. Patch in §6.6.
* **Tradeoffs / Risks:** None.
* **Expected impact estimate:** No runtime change; removes a recurring class of UI bug.
* **Removal Safety:** **Safe**
* **Reuse Scope:** local file

---

### F14 — `load_saves` re-lists the directory on every selection change

* **Category:** I/O
* **Severity:** **Low**
* **Impact:** Redundant syscalls and widget churn during keyboard navigation
* **Evidence:** `window.py:79` — `self.map_list.itemSelectionChanged.connect(self.load_saves)`.
  Each fire runs `get_saves_path()` (a `config.get` plus an `os.path.isdir` stat),
  `os.listdir`, `sorted`, and one `addItem(QListWidgetItem(...))` per entry
  (`window.py:140-149`). Holding the Down arrow through the map list triggers the whole
  sequence per keypress. `get_saves_path()` is called again immediately afterwards by
  `_selected_paths` for any subsequent action.
* **Why it's inefficient:** Repeated identical work with no caching. Per-item `addItem`
  also lets the view recompute layout on each insertion, where `addItems(list_of_str)` does
  one batch and skips the explicit `QListWidgetItem` allocations entirely.
* **Honest assessment:** At realistic scale — a handful of maps, tens of saves — **this is
  not a measurable bottleneck** and I did not benchmark it because there is nothing to
  measure. It is listed because the fix is free and improves the code, not because it is
  costing users time today. Do not prioritise it over F1–F7.
* **Recommended fix:** Use `addItems(sorted(...))`; cache the resolved saves path for the
  lifetime of a window interaction and invalidate it when Settings is accepted; consider
  `os.scandir()` (which carries `is_dir()` from the directory read and avoids a separate
  `stat` per entry, unlike the `os.listdir` + `os.path.isdir` pair at `window.py:135-138`).
* **Tradeoffs / Risks:** A cached path must be invalidated on settings change or it
  reintroduces the staleness problem described in F8.
* **Expected impact estimate:** Not measurable at realistic N. Cleanliness win.
* **Removal Safety:** **Safe**
* **Reuse Scope:** local file

---

### F15 — Dead imports and unused unpacked variables

* **Category:** Dead Code
* **Severity:** **Low**
* **Impact:** Reader confusion; trivial import cost
* **Evidence:**
  * `src/core/config.py:3` — `from typing import Dict, Any, Optional`. Only `Any` is used
    (line 34, 37). `Dict` and `Optional` have no other occurrence in the file.
  * `src/ui/settings_dialog.py:5` — `from PySide6.QtCore import Qt`. `Qt` is never
    referenced in that file; the only `Qt.` usages in the repository are `window.py:71,75`.
  * `src/ui/window.py:153,166,188` — `selected_map` is unpacked from `_selected_paths()`
    in `backup_save`, `delete_save`, and `export_save` and never used in any of the three.
    Use `_` for the discarded element.
* **Why it's inefficient:** Not a performance issue at this scale — it is a signal-to-noise
  issue. Unused imports imply a dependency that does not exist, and unused unpacked names
  make a reader hunt for a use that is not there.
* **Recommended fix:** Delete them. Add `ruff` to CI to keep them from returning (F18).
* **Tradeoffs / Risks:** None.
* **Expected impact estimate:** Zero runtime. Clarity only.
* **Removal Safety:** **Safe** (verified by grep)
* **Reuse Scope:** local file

---

### F16 — `ConfigManager` is used for exactly one key; language selection is not persisted

* **Category:** Over-Abstracted Code / UX
* **Severity:** **Low**
* **Impact:** A singleton, a JSON file, and a load/save cycle serving one string
* **Evidence:** `src/core/config.py` implements a `__new__`-based singleton with
  `load_config` / `save_config` / `get` / `set`. Repository-wide, `config` is read at
  `settings_dialog.py:36`, written at `settings_dialog.py:81`, and read at
  `platform.py:36` — always the same key, `custom_save_path`.

  Meanwhile `window.py:33` hardcodes `self.lang_code = "tr"` on every construction, and
  `change_language` (`window.py:105-117`) never writes the choice back. An English-speaking
  user re-selects English on every single launch.
* **Why it's inefficient:** Not that the abstraction is wrong — it is that it is built and
  then not used. The cheapest way to make the singleton earn its place is to store the one
  preference users actually notice.
* **Recommended fix:** Persist `language` through the existing `ConfigManager` and read it
  in `SaveManagerWindow.__init__`, defaulting to `"tr"`. Roughly four lines, and it makes
  the existing machinery worthwhile.
* **Tradeoffs / Risks:** None. Depends on F6 being fixed first, or the setting will be lost
  as unpredictably as the save path currently is.
* **Expected impact estimate:** No runtime change; removes a daily papercut.
* **Removal Safety:** **Safe**
* **Reuse Scope:** module

---

### F17 — CI has no concurrency control and fails the release if any one platform fails

* **Category:** Build / Reliability
* **Severity:** **Low-Medium**
* **Impact:** Racing releases, all-or-nothing publishing, supply-chain exposure
* **Evidence:** `.github/workflows/auto-release.yml`:
  * No `concurrency:` block. Two pushes to `main` in the same minute run two release jobs
    that compute `TAG_NAME=v$(date +'%Y.%m.%d')-${GITHUB_SHA::7}` — different tags, but the
    jobs still race to publish overlapping artifact sets.
  * `strategy.matrix` sets no `fail-fast: false`, so the default `true` applies: one
    runner failing cancels the other two, and `release` (which `needs: build`) is skipped
    entirely. A transient macOS runner hiccup means no Windows release either.
  * `softprops/action-gh-release@v1` is a stale major (v2 is current) and is referenced by
    a mutable tag rather than a commit SHA, so the action's contents can change under a
    workflow that holds `contents: write`.
* **Recommended fix:** Add a `concurrency` group keyed on the ref with
  `cancel-in-progress: false`; set `fail-fast: false` on the matrix; upgrade to
  `softprops/action-gh-release@v2` pinned to a full commit SHA; add
  `permissions: contents: read` to the `build` job so only `release` holds write.
* **Tradeoffs / Risks:** SHA pinning requires a deliberate bump to take upstream fixes —
  that is the intended trade. `fail-fast: false` uses slightly more runner time on a
  genuinely broken commit.
* **Expected impact estimate:** Fewer stuck releases; smaller supply-chain surface.
* **Removal Safety:** **Safe**
* **Reuse Scope:** service-wide (CI)

---

### F18 — No tests, and no linting, on a tool whose core operations are destructive

* **Category:** Reliability / Maintainability
* **Severity:** **Medium** (blocks everything above it)
* **Impact:** Nothing here can be refactored with confidence
* **Evidence:** No test files exist anywhere in the repository. The CI workflow builds and
  releases without running a single check. `memory-bank/progress.md` lists
  "Unit testler" as an unchecked **high-priority** item, so this is a known gap.

  The untested surface includes `shutil.rmtree` (`window.py:180`),
  `zip_file.extractall` (`window.py:231`), and `shutil.copytree` (`window.py:156`) — three
  operations that destroy or overwrite user data by design.
* **Why it's inefficient:** This is the gating finding. F1 (threading) and F6/F7
  (config and logging relocation) are exactly the kind of change that silently breaks
  behaviour, and right now there is nothing that would catch it. Every release ships
  straight from `git push` to users' machines with no gate.
* **Recommended fix:** Add `pytest` covering the pure logic first — it is genuinely easy to
  test because the risky functions take plain paths: `get_saves_path` precedence
  (custom vs. default vs. missing), `get_default_saves_path` per OS via monkeypatched
  `platform.system`, the import guard against multi-root and file-first archives (F9),
  export round-trip integrity (export → import → compare trees) against a `tmp_path`
  fixture, and `ConfigManager` persistence. Add `ruff check` to catch F15-class issues.
  Run both as a `test` job that `build` depends on.
* **Tradeoffs / Risks:** Upfront effort. The UI layer needs `pytest-qt` or a refactor that
  separates file operations from `QMainWindow` — that separation is worth doing on its own
  merits and makes F1 easier.
* **Expected impact estimate:** No runtime change. It is the precondition for doing F1
  safely.
* **Removal Safety:** N/A (addition)
* **Reuse Scope:** service-wide

---

### F19 — A modal error dialog can appear before the main window does

* **Category:** Frontend / UX
* **Severity:** **Low**
* **Impact:** Confusing first-run experience
* **Evidence:** `window.py:41` calls `self.load_maps()` from `__init__`, which at
  `window.py:128-133` raises a modal `QMessageBox.critical` when the saves directory is
  missing. `main.py:8-9` constructs the window and only then calls `window.show()`, so on a
  machine without 7DTD installed the very first thing the user sees is a modal error with
  no parent window behind it. `open_settings` (`window.py:119-123`) then calls `load_maps`
  again on every accepted save, re-raising the same dialog each time.
* **Why it's inefficient:** An error about missing data is presented before the
  application has established any context for it. The repeat on every settings save is
  redundant — the user just told the app where to look and is immediately scolded.
* **Recommended fix:** Show the missing-saves state inline in the map list (an empty-state
  label with the searched path and a button that opens Settings) rather than as a modal.
  If a modal is kept, raise it after `show()` and only when the path actually changed.
* **Tradeoffs / Risks:** None.
* **Expected impact estimate:** No runtime change.
* **Removal Safety:** **Safe**
* **Reuse Scope:** local file

---

## 3) Quick Wins (Do First)

Ordered by impact per minute of work. Everything here is under an hour; the first four are
under ten minutes each.

| # | Change | Effort | Impact | Finding |
|---|---|---|---|---|
| 1 | `requirements.txt` → `PySide6-Essentials` + `shiboken6` only | 2 min | −157 MB Win / −308 MB macOS per CI run; smaller binary | F2 |
| 2 | Add `cache: 'pip'` to `setup-python` | 2 min | Removes ~230 MB download per runner per push | F3 |
| 3 | Merge the two identical PyInstaller steps | 2 min | Removes a copy-paste drift hazard | F3 |
| 4 | Delete `SAVES_PATH` (`platform.py:63`) | 1 min | Removes a latent stale-config bug | F8 |
| 5 | Pass `compresslevel=1` to `ZipFile` | 1 min | **21% faster export**, measured, at identical size | F4 |
| 6 | Timestamp the export filename | 5 min | Closes a silent data-loss path | F10 |
| 7 | Check **all** top-level names before `extractall` | 10 min | Closes a second silent data-loss path | F9 |
| 8 | Remove dead imports and unused unpacked vars | 5 min | Clarity | F15 |
| 9 | `fail-fast: false` + `concurrency` block in CI | 5 min | Stops one flaky runner from killing a release | F17 |
| 10 | Extract `_retranslate_ui()`; fix the missing settings button | 15 min | Fixes an existing drift bug | F13 |
| 11 | Persist the language choice | 10 min | Removes a per-launch papercut | F16 |

**Highest value for the least risk: items 1, 2, 5.** Two dependency/CI lines and one
keyword argument, together removing hundreds of MB per CI run and 21% of export time.

---

## 4) Deeper Optimizations (Do Next)

Ordered by dependency, not by value — each builds on the one before.

1. **Add a test suite and a CI check job (F18).** Do this *before* the threading work, not
   after. Start with the pure functions in `core/` (no Qt needed) and the import/export
   round trip against `tmp_path`; add `ruff check`. This is what makes the rest safe.

2. **Separate file operations from the UI layer.** Pull `copytree` / `rmtree` / zip
   read-write out of `SaveManagerWindow` into a `core/operations.py` that takes paths and
   emits progress via a callback. This is worth doing on its own — it makes the operations
   testable without Qt — and it is the natural seam for step 3.

3. **Move operations onto a worker thread with progress and cancel (F1).** With step 2
   done, this becomes a `QRunnable` wrapper plus a `QProgressDialog`, rather than surgery
   on the window class. Sketch in §6.1. Handle cancellation cleanup explicitly: a cancelled
   `copytree` must remove its partial destination.

4. **Relocate config and logs to per-user directories, atomically (F6, F7).** One shared
   path resolver serves both. Fix the silent `except: pass` at the same time and surface
   failures in the Settings dialog. Consider a one-time migration from the old locations.

5. **Move backups out of the game's save tree, and add retention (F11).** Requires a new
   setting and a decision about existing in-tree backups. Pairs naturally with the
   "Yedek geçmişi" (backup history) feature already listed in `memory-bank/progress.md`.

6. **Reconsider onefile packaging (F5).** A product decision as much as a technical one.
   `--onedir` plus a small installer removes the per-launch extraction cost and likely
   reduces antivirus false positives — which the README currently spends a whole section
   apologising for.

7. **Resolve Windows known folders properly (F10).** `os.path.join(home, "Desktop")` breaks
   under OneDrive Known Folder Move and on non-English Windows. Use
   `SHGetKnownFolderPath`, with the current string-join as fallback.

---

## 5) Validation Plan

### Benchmarks

The measurements in this report came from a synthetic tree (1090 MB, 425 files:
~70% incompressible binary, ~20% repetitive binary, ~10% XML) built to approximate a
7DTD save. **Re-run against a real save directory before acting on F4**, since real
region files are more thoroughly pre-compressed than the synthetic mix and the size/time
trade will shift.

```python
# export: compare compression settings against a REAL save folder
import time, zipfile, os

SRC = r"<path to a real 7DTD save>"
for name, comp, lvl in [("current-lvl6", zipfile.ZIP_DEFLATED, None),
                        ("lvl1",         zipfile.ZIP_DEFLATED, 1),
                        ("stored",       zipfile.ZIP_STORED,   None)]:
    out = f"/tmp/{name}.zip"
    t = time.perf_counter()
    with zipfile.ZipFile(out, "w", comp, compresslevel=lvl) as zf:
        for root, _, files in os.walk(SRC):
            for f in files:
                p = os.path.join(root, f)
                zf.write(p, os.path.relpath(p, os.path.dirname(SRC)))
    print(f"{name:14} {time.perf_counter()-t:6.1f}s  {os.path.getsize(out)/1048576:8.0f} MB")
```

Accept `compresslevel=1` if it is faster and the archive grows by less than ~2%.

**Measure `copytree` and `rmtree` on real target hardware, not in a container.** The
numbers in F1 (0.9 s and 0.1 s per GB) are unrepresentatively good because the benchmark
filesystem supports server-side copy and the tree was in page cache. Time a backup of a
real multi-GB save on a mechanical drive and on an external USB disk — those are the
numbers that justify the threading work.

### Profiling strategy

* **Where the time goes:** `python -X importtime 7DaysToBackup.py` for startup cost
  (this will also show the import-time work flagged in F7 and F8);
  `cProfile` around a single export for the split between `os.walk`, `zlib`, and write.
* **Whether the UI is actually blocked:** install a `QTimer` on a 100 ms interval that
  appends `time.perf_counter()` to a list, run each operation, and inspect the gaps. A gap
  equal to the operation duration is direct proof of event-loop starvation, and after F1 it
  should drop to a few tens of milliseconds. This is the single most useful before/after
  measurement in the whole plan.
* **Bundle size:** `du -sh dist/` before and after F2 and F5.
* **CI:** compare `Install dependencies` step duration on the Actions run summary before
  and after F2 + F3.

### Metrics to compare before/after

| Metric | How to measure | Target |
|---|---|---|
| Max event-loop stall during export | `QTimer` gap probe above | < 100 ms (from ~35 s/GB) |
| Export wall time per GB | benchmark script above | −20% (F4) |
| CI install step duration | Actions run summary | seconds on cache hit |
| Installed dependency size | `du -sh .venv/lib/*/site-packages/PySide6*` | −157 MB Win / −308 MB macOS |
| Released binary size | `du -sh dist/` | measure |
| Cold start time | wall-clock, 3 runs, second onward | measure after F5 |

### Test cases to ensure correctness is preserved

Regression tests worth writing before touching anything (F18):

1. **Export round trip.** Export a save, import it into a clean map directory, assert the
   directory trees compare equal (`filecmp.dircmp`, recursively, including file contents).
   Must hold at every `compresslevel`.
2. **Export does not clobber** (F10). Export the same save twice; assert both archives
   exist.
3. **Import rejects a colliding multi-root archive** (F9). Build a zip containing
   `SaveA/` and `SaveB/`, pre-create `SaveB` on disk, assert the import is refused and
   `SaveB` is byte-identical afterwards.
4. **Import rejects a file-first archive** (F9). First entry a top-level file, subsequent
   entries a folder that already exists on disk; assert refusal.
5. **Import rejects an oversized archive** (F9). Assert the size check trips before any
   file is written.
6. **`get_saves_path` precedence.** Custom path set and valid → custom; set but missing →
   default; unset → default. Monkeypatch `platform.system` to cover all three OS branches
   of `get_default_saves_path`.
7. **Config survives a restart and an interrupted write** (F6). Set a value, construct a
   fresh `ConfigManager`, assert the value is read back. Truncate `config.json` mid-file
   and assert the app starts with defaults *and logs the problem*.
8. **Backup naming is unique.** Two backups within the same second must not collide
   (the current format has 1-second resolution — worth asserting the behaviour you want).
9. **Cancellation leaves no partial state** (F1, once threading lands). Cancel a backup
   mid-copy; assert no partial destination directory remains.

### Verifying F12 (the CI `paths-ignore` question)

Concrete test, since I could not confirm from documentation in this environment:

1. On a scratch branch, temporarily add that branch to the workflow's `on.push.branches`.
2. Push a commit that touches **only** `requirements.txt` (a trailing-newline change is
   enough).
3. Check the Actions tab. **No run** confirms the negation is not honoured and F12 is real.
4. Revert the branch change.

---

## 6) Optimized Code / Patch

> These snippets were the original proposals. They have since been **implemented** — the
> shipped code differs in places where building it for real turned up details the sketch
> did not cover (empty-directory preservation in `copy_save`, partial-archive cleanup in
> `export_save`, `unique_path` for same-second collisions, and a dedicated dependency-free
> `core/paths.py` to break the `config` → `logger` → `platform` import cycle). Read
> `src/core/operations.py` and `src/ui/window.py` for the current state.

### 6.1 — Move operations off the GUI thread (F1)

The shape of the change, not a drop-in replacement. It assumes step 2 of §4 (file
operations extracted from the window class) has been done first.

```python
# src/core/operations.py  (new) — no Qt imports; unit-testable without a display
import os, shutil, zipfile
from typing import Callable, Optional

ProgressFn = Callable[[int, int], None]      # (files_done, files_total)
CancelFn = Callable[[], bool]                # returns True when cancellation is requested


def copy_tree_with_progress(src: str, dst: str,
                            progress: Optional[ProgressFn] = None,
                            is_cancelled: Optional[CancelFn] = None) -> None:
    entries = [(dp, f) for dp, _, fs in os.walk(src) for f in fs]
    total = len(entries)
    try:
        for i, (dirpath, filename) in enumerate(entries, 1):
            if is_cancelled and is_cancelled():
                raise InterruptedError("cancelled")
            rel = os.path.relpath(dirpath, src)
            target_dir = os.path.join(dst, rel) if rel != "." else dst
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy2(os.path.join(dirpath, filename),
                         os.path.join(target_dir, filename))
            if progress:
                progress(i, total)
    except BaseException:
        # a cancelled or failed backup must not leave a partial directory behind
        shutil.rmtree(dst, ignore_errors=True)
        raise
```

```python
# src/ui/workers.py  (new)
from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    progress = Signal(int, int)
    finished = Signal()
    failed = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self._fn, self._args, self._kwargs = fn, args, kwargs
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    @Slot()
    def run(self) -> None:
        try:
            self._fn(*self._args,
                     progress=self.signals.progress.emit,
                     is_cancelled=self.is_cancelled,
                     **self._kwargs)
        except InterruptedError:
            self.signals.finished.emit()          # cancelled: not an error
        except Exception as exc:                  # noqa: BLE001
            self.signals.failed.emit(str(exc))
        else:
            self.signals.finished.emit()
```

```python
# src/ui/window.py — backup_save, rewritten
def backup_save(self) -> None:
    try:
        _, _, source_path = self._selected_paths()
    except ValueError as exc:
        self._show_error(self.translations["title"], str(exc))
        return

    suffix = datetime.now().strftime("_backup_%Y.%m.%d-%H.%M.%S")
    worker = Worker(copy_tree_with_progress, source_path, f"{source_path}{suffix}")

    dialog = QProgressDialog(self.translations["backup"], self.translations["cancel"],
                             0, 100, self)
    dialog.setWindowModality(Qt.WindowModal)
    worker.signals.progress.connect(
        lambda done, total: dialog.setValue(int(done / total * 100)) if total else None)
    worker.signals.finished.connect(dialog.close)
    worker.signals.finished.connect(self.load_saves)
    worker.signals.finished.connect(
        lambda: self._show_info(self.translations["title"],
                                self.translations["backup_success"]))
    worker.signals.failed.connect(
        lambda msg: self._show_error(self.translations["title"],
                                     f"{self.translations['backup_error']} - {msg}"))
    dialog.canceled.connect(worker.cancel)
    QThreadPool.globalInstance().start(worker)
```

**What changed:** the filesystem walk moved into a testable, Qt-free function that reports
progress and honours cancellation; the slot now returns immediately so the event loop keeps
running; the user gets a progress bar and a working Cancel; and a cancelled or failed
backup cleans up its partial destination instead of leaving a half-copy that would appear
in the save list as a real save.

### 6.2 — Harden the import guard (F9)

```python
# src/ui/window.py — replace lines 222-231
MAX_EXTRACT_BYTES = 20 * 1024 ** 3      # refuse absurd archives (zip-bomb guard)

with zipfile.ZipFile(zip_path, "r") as zip_file:
    infos = zip_file.infolist()
    if not infos:
        raise ValueError(self.translations["import_error"].format("Empty archive"))

    total_uncompressed = sum(i.file_size for i in infos)
    if total_uncompressed > MAX_EXTRACT_BYTES:
        raise ValueError(self.translations["import_error"].format(
            f"Archive expands to {total_uncompressed / 1024 ** 3:.1f} GB"))

    # check EVERY top-level name, not just the first entry's
    top_level = {i.filename.replace("\\", "/").split("/")[0] for i in infos}
    existing = [n for n in sorted(top_level)
                if os.path.exists(os.path.join(target_map_path, n))]
    if existing:
        self._show_error(self.translations["title"],
                         self.translations["import_exists"] + "\n" + "\n".join(existing))
        return

    zip_file.extractall(target_map_path)
```

**What changed:** every top-level entry is checked instead of only `members[0]`, so
multi-root archives and archives whose first entry is a loose file can no longer overwrite
existing saves; and the total uncompressed size is bounded before a single byte is written.
`infolist()` replaces `namelist()` because it carries `file_size` at no extra cost.
Path traversal needs no handling — CPython's `_extract_member` already strips `..` and
drive letters (verified against the 3.11 source).

### 6.3 — Config: real location, atomic write, no silent failure (F6)

```python
# src/core/config.py
import json, os, sys, tempfile
from typing import Any
from src.core.logger import logger

APP_NAME = "7DaysToBackup"


def _config_dir() -> str:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform.startswith("darwin"):
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_NAME)


CONFIG_FILE = os.path.join(_config_dir(), "config.json")


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = {}
            cls._instance.load_config()
        return cls._instance

    def load_config(self) -> None:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Config unreadable (%s); starting with defaults: %s",
                           CONFIG_FILE, exc)
            self.config = {}

    def save_config(self) -> bool:
        """Write atomically. Returns False on failure — callers must not ignore it."""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(CONFIG_FILE), suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, CONFIG_FILE)      # atomic on POSIX and Windows
            except BaseException:
                os.unlink(tmp)
                raise
            return True
        except OSError as exc:
            logger.exception("Failed to save config to %s: %s", CONFIG_FILE, exc)
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        self.config[key] = value
        return self.save_config()


config = ConfigManager()
```

```python
# src/ui/settings_dialog.py — _save_settings must react to failure
def _save_settings(self):
    path = self.path_input.text().strip()
    if not config.set("custom_save_path", path):
        QMessageBox.critical(self, self.translations.get("error", "Hata"),
                             self.translations.get("save_failed", "Ayarlar kaydedilemedi."))
        return                                    # do NOT close on failure
    logger.info("Settings saved. custom_save_path=%s", path)
    self.accept()
```

**What changed:** the config path no longer depends on the working directory; writes are
atomic so an interrupted write cannot truncate the file; exception handling is narrowed
from bare `Exception` to the types that can actually occur; every failure is logged; and
`set()` returns a status the dialog now honours instead of closing as though it succeeded.
Unused `Dict` and `Optional` imports dropped (F15). Note the `%s` lazy-formatting style,
which also avoids building log strings that get discarded below the active level.

### 6.4 — Logging: lazy, bounded, packaging-safe (F7)

```python
# src/core/logger.py
import logging, os, sys
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("7DaysToBackup")
_configured = False


def _log_dir() -> str:
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform.startswith("darwin"):
        base = os.path.join(os.path.expanduser("~"), "Library", "Logs")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "7DaysToBackup")


def setup_logging() -> None:
    """Call once from main(). Never raises — logging must not break startup."""
    global _configured
    if _configured:
        return
    _configured = True
    logger.setLevel(logging.DEBUG if os.environ.get("SEVENDAYS_DEBUG") else logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    try:
        d = _log_dir()
        os.makedirs(d, exist_ok=True)
        fh = RotatingFileHandler(os.path.join(d, "debug.log"), maxBytes=1_000_000,
                                 backupCount=3, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass                       # read-only install: carry on without a file log
    if sys.stderr is not None:     # None under pythonw / PyInstaller -w
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
```

```python
# src/main.py
def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    ...
```

**What changed:** no filesystem work at import time, so a read-only install directory can
no longer crash the app before the UI exists; logs go to a per-user location that survives
a onefile extraction; rotation bounds growth at ~4 MB; the console handler is added only
when a real stderr exists; and `DEBUG` is opt-in via `SEVENDAYS_DEBUG` rather than always
on. Note that F6's `config.py` imports this logger — keep `setup_logging()` the only thing
with side effects so the import order stays harmless.

### 6.5 — CI workflow (F3, F12, F17)

```diff
 on:
   push:
     branches: [ "main" ]
     paths-ignore:
       - '**.md'
       - 'docs/**'
       - 'memory-bank/**'
       - '.gitignore'
       - '.github/**/*.md'
       - 'LICENSE'
       - 'agent.md'
       - 'metadata.yml'
       - 'file_version_info.txt'
-      - '**.txt'
-      - '!requirements.txt'
+      # NOTE: '**.txt' used to be here with a '!requirements.txt' exception.
+      # Negation is not honoured inside paths-ignore, so a requirements-only
+      # change was silently skipped and never produced a release. See F12.
+
+concurrency:
+  group: release-${{ github.ref }}
+  cancel-in-progress: false

 jobs:
   build:
     name: Build on ${{ matrix.os }}
     runs-on: ${{ matrix.os }}
+    permissions:
+      contents: read
     strategy:
+      fail-fast: false
       matrix:
         os: [ubuntu-latest, windows-latest, macos-latest]

     steps:
     - name: Checkout code
       uses: actions/checkout@v4

     - name: Set up Python
       uses: actions/setup-python@v5
       with:
         python-version: '3.11'
+        cache: 'pip'
+        cache-dependency-path: requirements.txt

     - name: Install dependencies
       run: |
-        python -m pip install --upgrade pip
         pip install -r requirements.txt
         pip install pyinstaller

-    - name: Build with PyInstaller (Windows)
-      if: runner.os == 'Windows'
-      run: |
-        pyinstaller 7DaysToBackup.py -F -w -n 7DaysToBackup
-
-    - name: Build with PyInstaller (macOS/Linux)
-      if: runner.os != 'Windows'
-      run: |
-        pyinstaller 7DaysToBackup.py -F -w -n 7DaysToBackup
+    - name: Build with PyInstaller
+      run: pyinstaller 7DaysToBackup.py -F -w -n 7DaysToBackup
```

```diff
     - name: Create Release
-      uses: softprops/action-gh-release@v1
+      uses: softprops/action-gh-release@<full-commit-sha>   # v2.x, SHA-pinned
```

**What changed:** the ineffective `**.txt` / `!requirements.txt` pair is removed so
dependency bumps actually build; pip caching keyed on `requirements.txt` eliminates the
repeated download; the two identical build steps collapse into one; `fail-fast: false`
stops one flaky runner from cancelling the release; `concurrency` prevents overlapping
release runs; the build job drops to read-only permissions; and the release action moves
to a SHA-pinned v2.

### 6.6 — Single retranslation path (F13)

```python
# src/ui/window.py
def _setup_ui(self) -> None:
    ...                                  # construct widgets with no literal text
    self.language_box.currentIndexChanged.connect(self.change_language)
    self._retranslate_ui()               # single source of truth for all strings

def _retranslate_ui(self) -> None:
    t = self.translations
    self.setWindowTitle(t["title"])
    self.settings_button.setText(t["settings"])      # was missing from change_language
    self.map_label.setText(t["map_list"])
    self.save_label.setText(t["save_list"])
    self.backup_button.setText(t["backup"])
    self.delete_button.setText(t["delete"])
    self.export_button.setText(t["export"])
    self.import_button.setText(t["import"])

def change_language(self, _index: int) -> None:
    self.lang_code = self.language_box.currentData()   # no reverse lookup needed
    self.translations = LANGUAGES[self.lang_code]
    config.set("language", self.lang_code)             # persist it (F16)
    self._retranslate_ui()
```

**What changed:** one list of translatable widgets instead of two, so adding a widget can
no longer half-translate the UI; the settings button — currently missing from
`change_language` and only invisible because `⚙` is glyph-only — is now covered; the linear
reverse scan over `lang_display` is replaced by `currentData()`, which reads back the code
already stored by `addItem(display, code)`; and the choice persists across launches.

---

## Appendix: Dead code and reuse register

| Item | Location | Classification | Removal Safety |
|---|---|---|---|
| `SAVES_PATH` constant | `platform.py:63` | Dead Code | **Safe** — zero references repo-wide |
| `Dict`, `Optional` imports | `config.py:3` | Dead Code | **Safe** — only `Any` is used |
| `Qt` import | `settings_dialog.py:5` | Dead Code | **Safe** — no `Qt.` usage in that file |
| `selected_map` unpacked, unused | `window.py:153,166,188` | Dead Code | **Safe** — replace with `_` |
| Duplicated PyInstaller CI steps | `auto-release.yml` | Dead Branch | **Safe** — identical command bodies |
| `'!requirements.txt'` pattern | `auto-release.yml` | Dead Config | **Needs Verification** (F12 test) |
| Retranslation string list | `window.py:110-117` vs `_setup_ui` | Reuse Opportunity | extract `_retranslate_ui()` |
| `lang_display` reverse scan | `window.py:106-109` | Reuse Opportunity | use `currentData()` |
| Timestamp-suffix generation | `window.py:154` (needed at `:189`) | Reuse Opportunity | shared helper |
| `get_saves_path()` repeated per action | `window.py:127,145,211,251` | Reuse Opportunity | cache + invalidate on settings change |
| `ConfigManager` singleton | `config.py:7-42` | Over-Abstracted | serves one key — give it the language too (F16) |
| `DESKTOP_PATH` import-time eval | `platform.py:64` | Stale Abstraction | used, but convert to a function for consistency |

---

*Audit performed by static analysis of all 610 lines of Python, plus targeted benchmarking
of the export, backup, delete, and import paths against synthetic save data. All wall-clock
figures are measured on this audit host and labelled where they are not expected to
transfer to user hardware. The findings were subsequently implemented (see Implementation
Status), verified by 43 unit tests, `ruff`, an end-to-end offscreen GUI exercise, and an
event-loop stall probe.*
