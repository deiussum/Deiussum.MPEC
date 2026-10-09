# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Python script that tracks comets via the Minor Planet Center (MPC) API and posts Discord webhook notifications for new discoveries, naming/permid assignments, and magnitude threshold crossings. It is meant to be run periodically (e.g. from cron); state is kept between runs in `known_comets.csv`.

## Running

There is no requirements file, build step, linter config, or test suite. Dependencies: `requests`, `pandas`, `python-dotenv`.

Copy `.env.example` to `.env` and set `DISCORD_WEBHOOK_URL`. If it is unset, `Discord.SendEmbed` prints a message and skips sending.

```sh
python CometDiscovery.py                         # update from MPC, send notifications, rewrite known_comets.csv
python CometDiscovery.py --summarize             # post a summary of non-archived tracked comets to Discord
python CometDiscovery.py --summarize --skipsend  # print the summary embed instead of sending it
```

Each module has an `if __name__ == "__main__":` block used for manual testing. Running `python CometList.py` does a full update cycle against `test.csv` rather than `known_comets.csv`, so use it to try changes without touching real state. `MessageTesting.http` holds VS Code REST Client requests for the Discord webhook and the MPC API.

## Architecture

- `CometDiscovery.py`: entry point. `updateAndCheckNotifications()` loads the CSV, discovers or updates comets, refreshes observation data, sends a Discord embed for each notification bucket, then saves the CSV.
- `CometList.py`: holds the comet collection and the logic.
  - `loadRecentComets()` builds candidate designations (`C/<year> <half-month letter><1-5>` for the current half-month and the one ~15 days earlier, via `DesignationBuilder`), merges them with the saved designations, and queries MPC in one batch. Unknown comets go into `added`; comets whose name or permid changed go into `updated`.
  - `updateObservationData()` fetches observations for each comet as an ADES DataFrame, computes 1-day and 2-day average magnitudes relative to the latest observation, and sorts comets into the `binoc`/`nakedeye`/`spectacular`/`suddenincrease` lists when they cross the `*_MAGNITUDE` thresholds. Lower magnitude means brighter. It sleeps 0.5s between comets to rate-limit MPC calls.
- `MinorPlanetaryCenter.py`: thin MPC API wrappers. `DesignationIdentifierApi` calls `/api/query-identifier` and `ObservationsApi` calls `/api/get-obs`. Both send a JSON body on a GET request, as the MPC API expects.
- `Comet.py`: the comet record, with CSV (de)serialization via `toDict()`/the constructor. Datetimes are stored as `%Y-%m-%d %H:%M:%S` and parsed as UTC. Every CSV value loads as a string, so non-string fields need explicit parsing in the constructor (see `getFloat`, `getBool`, `getDateTime`).
- `Discord.py`: posts a single embed to the webhook.

## CSV state

`known_comets.csv` is the live state file and is committed to the repo. Columns are defined in `CometList.saveCsv`; when you add a field, update `Comet.__init__`, `Comet.toDict`, and that `fieldnames` list together. Comets are archived by hand by setting `archive` to `True` in the CSV.
