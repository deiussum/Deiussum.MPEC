# Deiussum.MPEC

Tracks comets using the [Minor Planet Center](https://minorplanetcenter.net/) (MPC) API and sends notifications to a
Discord webhook and/or an RSS feed. A static web page lists the tracked comets.

Live page: <https://comets.deiussum.com>

## What it notifies about

- **New comets**: newly announced `C/` and `P/` designations.
- **Name or number assigned**: a tracked comet gets a name or a permanent periodic number.
- **Returning comets**: known periodic comets coming up on perihelion that should reach magnitude 14 or brighter.
- **Brightness**: a comet's recent average magnitude crosses one of these thresholds:
  - 8: visible in binoculars
  - 6: visible to the naked eye
  - 2: spectacular
  - 1.5 magnitudes brighter than before: sudden brightening
- **Weekly summary** of every tracked comet (run with `--summarize`).

For each comet it also keeps the perihelion date from MPC's `CometEls.txt`, plus the closest approach to Earth and the
predicted peak brightness from [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/). Comets that haven't been observed for
90 days are archived and no longer checked.

## Setup

Requires Python 3 and these packages:

```sh
pip install requests pandas python-dotenv
```

Copy `.env.example` to `.env` and set the targets you want:

| Setting | Purpose |
|---|---|
| `DISCORD_WEBHOOK_URL` | Discord webhook to post to. Leave unset to disable Discord. |
| `RSS_FEED_PATH` | Path to write the RSS feed to. Leave unset to disable the feed. |
| `DEPLOY_TARGET` | scp destination (`user@host:/path`) that `run.sh` uploads the feed, page and CSV to. |

## Usage

```sh
python CometDiscovery.py                         # check MPC, send notifications, update known_comets.csv
python CometDiscovery.py --summarize             # send a summary of the tracked comets
python CometDiscovery.py --summarize --skipsend  # print the summary instead of sending it
```

State is kept in `known_comets.csv` between runs, so run it periodically. To try changes without touching the real
state, run `python CometList.py`, which does a full update against `test.csv`.

## Deploying

`run.sh` runs the update, sends the summary on Mondays, and uploads the files to `DEPLOY_TARGET`. It expects the project
to be installed in `/opt/discord-comets`. The `systemd` folder has a service and a timer that run it daily at 06:00:

```sh
sudo cp systemd/discord-comets.* /etc/systemd/system/
sudo systemctl enable --now discord-comets.timer
```

## Web page

`index.html` is a static page that reads `known_comets.csv` and shows the tracked comets in a sortable table, with rows
coloured by brightness. It has a light/dark theme toggle and a link to the RSS feed. Serve it from the same directory
as the CSV and `comets.xml`.
