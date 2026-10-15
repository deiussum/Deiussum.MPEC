# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Python script that tracks comets via the Minor Planet Center (MPC) API and sends notifications (Discord webhook and/or an RSS feed file) for new discoveries, naming/permid assignments, and magnitude threshold crossings. It is meant to be run periodically (e.g. from cron); state is kept between runs in `known_comets.csv`.

## Running

There is no requirements file, build step, linter config, or test suite. Dependencies: `requests`, `pandas`, `python-dotenv`.

Copy `.env.example` to `.env`. Each notification target is enabled by its own setting: `DISCORD_WEBHOOK_URL` for Discord and `RSS_FEED_PATH` for the RSS feed. Set either or both. `DEPLOY_TARGET` (an scp `user@host:/path`) makes `run.sh` upload the feed, `index.html` and the CSV; it reads it from the environment, which the systemd unit loads from `.env`.

```sh
python CometDiscovery.py                         # update from MPC, send notifications, rewrite known_comets.csv
python CometDiscovery.py --summarize             # send a summary of non-archived tracked comets
python CometDiscovery.py --summarize --skipsend  # print the summary embed instead of sending it
```

Each module has an `if __name__ == "__main__":` block used for manual testing. Running `python CometList.py` does a full update cycle against `test.csv` rather than `known_comets.csv`, so use it to try changes without touching real state. `MessageTesting.http` holds VS Code REST Client requests for the Discord webhook and the MPC API.

## Architecture

- `CometDiscovery.py`: entry point. `updateAndCheckNotifications()` loads the CSV, discovers or updates comets, refreshes observation data, sends a notification for each notification bucket, then saves the RSS feed and the CSV.
- `CometList.py`: holds the comet collection and the logic.
  - `loadRecentComets()` builds candidate designations (`C/<year> <half-month letter><1-5>` for the current half-month and the one ~15 days earlier, via `DesignationBuilder`), merges them with the saved designations, and queries MPC in one batch. Unknown comets go into `added`; comets whose name or permid changed go into `updated`.
  - `loadMissedComets()` is a backstop for `loadRecentComets()`: any `C/` or `P/` comet in MPC's `CometEls.txt` whose designation half-month started within `MISSED_LOOKBACK_DAYS` and isn't in the CSV goes into `added`. This catches late announcements, indexes past 5, and new periodic comets.
  - `loadReturningComets()` uses `CometEls.txt` (downloaded once per run by `getCometElements()`, parsed by `CometElement`) and tracks periodic comets whose perihelion is within `PERIHELION_PAST_DAYS`/`PERIHELION_AHEAD_DAYS` of now and whose rough estimated peak magnitude is at most `RETURNING_MAX_MAGNITUDE`. Newly tracked or un-archived comets go into `returning`. Comets near perihelion are never auto-archived, since their last observation may be from the previous apparition.
  - `updatePerihelionDates()` sets `perihelion` on every tracked comet listed in `CometEls.txt`, matching numbered comets by permid and others by designation. It runs after the discovery steps so new comets have it before notifications go out.
  - `updateObservationData()` fetches observations for each comet as an ADES DataFrame, computes 1-day and 2-day average magnitudes relative to the latest observation, and sorts comets into the `binoc`/`nakedeye`/`spectacular`/`suddenincrease` lists when they cross the `*_MAGNITUDE` thresholds. Lower magnitude means brighter. It sleeps 0.5s between comets to rate-limit MPC calls.
  - `updateEphemerides()` fetches a daily JPL Horizons ephemeris for each non-archived comet and stores the closest approach to Earth (`closeapproach`, `closedist` in AU) and predicted peak brightness (`peakdate`, `peakmag`). It refreshes each comet every `EPHEMERIS_REFRESH_DAYS`, tracked by `ephemupdate`. Values are left blank when the extreme falls on the edge of the window, or when Horizons has no magnitude model.
- `Horizons.py`: `HorizonsApi` calls the JPL Horizons API (`ssd.jpl.nasa.gov/api/horizons.api`); `EphemerisSummary` picks the closest approach and brightest day from its rows.
- `MinorPlanetaryCenter.py`: thin MPC API wrappers. `DesignationIdentifierApi` calls `/api/query-identifier`, `ObservationsApi` calls `/api/get-obs`, and `CometElementsApi` downloads `CometEls.txt`. The two API wrappers send a JSON body on a GET request, as the MPC API expects.
- `Comet.py`: the comet record, with CSV (de)serialization via `toDict()`/the constructor. Datetimes are stored as `%Y-%m-%d %H:%M:%S` and parsed as UTC. Every CSV value loads as a string, so non-string fields need explicit parsing in the constructor (see `getFloat`, `getBool`, `getDateTime`).
- `Notifications.py`: sends to every configured target. Callers pass a title, description, Discord color, a list of Discord-style `{name, value, inline}` fields and an optional link; the RSS target renders the fields as HTML. Call `Save()` once at the end of a run to write the feed.
- `Rss.py`: maintains an RSS 2.0 file. It reads existing items back from the file so history persists between runs (newest `MAX_ITEMS` kept), and writes via a temp file plus `os.replace`.
- `Discord.py`: posts a single embed to the webhook.

## CSV state

`known_comets.csv` is the live state file and is committed to the repo. Columns are defined in `CometList.saveCsv`; when you add a field, update `Comet.__init__`, `Comet.toDict`, and that `fieldnames` list together. `archiveStaleComets()` sets `archive` to `True` once a comet's last observation is older than `ARCHIVE_AFTER_DAYS`; comets can also be archived by hand in the CSV. Archived comets are skipped by `updateObservationData()` and the summary.
