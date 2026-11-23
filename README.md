# AAST Triton ROVs – Ground Control Station

Phase 1: headless input skeleton (event bus, config, gamepad and keyboard sampling,
dead-zones, hot-plugging, mapping profiles).

## Requirements
- Python 3.12 (pygame has no pre-built packages for 3.14 yet)

## Setup
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Run
```powershell
python -m gcs                      # uses config/default.yaml
python -m gcs --config my.yaml     # use another config file
```
Press Ctrl+C to stop.

## Develop
```powershell
python -m pytest
python -m ruff check .
```

## Layout
- `src/gcs/core`: event bus, event types, config loader, logging setup
- `src/gcs/input`: devices, sampler thread, dead-zones, mappings, profiles
- `config/`: `default.yaml` (settings) and `profiles/*.json` (mapping profiles)
- `scripts/`: manual test tools (gamepad probe, hot-plug demo and diagnostic)
- `tests/`: pytest suite

## Mapping profiles
Profiles are JSON files in `config/profiles/`. Each one maps raw inputs (`axis_1`, `button_0`,
`key_w`) to action names (`surge`, `light_toggle`), with optional invert, scale and per-axis
dead-zone. A profile that lists a controller name under `"controllers"` loads automatically when
that controller connects. Edits to the active profile file apply without restarting.