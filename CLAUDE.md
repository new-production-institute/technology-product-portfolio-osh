* You must always follow: doc/contributing/rules.md
* You must Always stay in Website branch.
* Role: front-end developer. Do not edit `spec/`, `src/script/`, `res/var/data/`, or `res/data/` (includes not editing `src/script/convert_construction.py`, `convert_food.py`, `convert_health.py`, `mirror_spreadsheet.py`). Presentation-only changes: layouts, styles, typography, colors, visual assets.
* Front-end code style: NASA/JPL-style functional programming with minimal side effects (pure functions, no hidden mutation, explicit data flow, small single-purpose functions, bounded loops, no dynamic code eval). Vanilla JS and HTML only — no frameworks or build-step dependencies. Must remain suitable for a plain static website (no server, no bundler required).

