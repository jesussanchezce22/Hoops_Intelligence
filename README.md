# Hoops Intelligence — MVP 0.3

Independent, unofficial fantasy basketball analysis web app. Public branding intentionally excludes employer names. Project working reference: `PwC_PoD_Hoops_Intelligence` (do not publish that branding without authorization).

## Run

Open `index.html` in a browser, or serve the folder with any static web server. No build step, accounts, or API keys required.

## Features

- Stats Overview and searchable player rankings.
- Editable fantasy points formula; sample coefficients are **not** verified ESPN defaults.
- Import user-provided per-game stats CSV, optionally with `gp` and `games_next_week`.
- Fantasy points per game = sum of each stat × its scoring coefficient.
- Total fantasy points = FPPG × GP, if GP is supplied.
- Estimated weekly points = FPPG × games_next_week, if upcoming game count is supplied. This is **not** a forecast and ignores injury/role changes.
- Trade comparison by sum of FPPG; not a trade recommendation.
- Fantasy Academy as a separate view.

## Data provenance and limitations

The bundled player statistics are **invented demonstration data** and never represent current NBA statistics. User-imported CSV data is not independently verified. CSV processing is local to the browser session. No automatic updates, ESPN account connection, or verified schedule feed exist yet. Do not upload confidential, private, or improperly licensed data.

## CSV columns

Required: `name,team,pos,pts,reb,ast,stl,blk,tov` (per-game averages). Optional: `gp,games_next_week,source,season,as_of`. Missing optional values show as `—`.

## Deployment

A personal GitHub Pages repository can host these files with `index.html` at the root. Verify organizational policies before visiting or sharing from employer-managed devices.


## v0.4 visual refresh
Light theme inspired by the supplied reference: white surfaces, warm gray borders, orange accents, Arial typography. No PwC logo or official affiliation. Existing app logic and demo data remain unchanged.

## v0.5 — Optional NBA.com statistics pipeline

`update_nba_data.py` fetches **per-game season averages** through the unofficial `nba_api` client and writes `players.csv` beside `index.html`. Install `nba_api` on an authorized personal machine or runner, then run `python update_nba_data.py --season 2025-26`. Serve the folder via HTTP(S); when `players.csv` is present the web app attempts to load it automatically. On failure the app stays in clearly labeled demo mode. This pipeline has **not** been run against live NBA.com in this environment; access may be blocked or rate limited. Do not imply live updates until a schedule is configured and tested.

The NBA endpoint does not provide fantasy position in this call, so positions are shown as `N/A` and position filtering will not work on those records until a separate verified roster source is added. No next-week game count is supplied, so weekly projections remain unavailable. League scoring coefficients remain illustrative and must be matched to ESPN league settings. Check data redistribution rights before public hosting.

## v0.6 — Data pipeline validation (2026-10-12)

Run `python -m unittest -v test_data_pipeline.py` to validate the CSV mapping, metadata, and no-empty-dataset guard using **synthetic test fixtures only**. Run `node --check app.js` for JavaScript syntax validation if Node.js is installed. These tests do **not** validate NBA.com connectivity, ESPN scoring rules, fantasy positions, schedule, or browser behavior.

Live extraction attempt in the build environment was blocked: `nba_api` was not installed, and the package index was unreachable. Therefore **no `players.csv` with live NBA statistics is bundled**. To fetch real data, run `pip install nba_api` and `python update_nba_data.py --season 2025-26` on an authorized machine or CI runner with outbound connectivity. Check usage/redistribution terms before public publishing.


## v0.7 Dark Theme
Restores the original dark navy / orange appearance while preserving the v0.6 analytics and data pipeline. The NBA logo is referenced from a third-party image URL and therefore requires internet access; an NBA-text fallback is shown if the image fails. The official logo is a trademark of the NBA. This unofficial fan project is not affiliated with or endorsed by the NBA. Review logo licensing before public release, and replace with an original basketball mark if permission is unavailable.
