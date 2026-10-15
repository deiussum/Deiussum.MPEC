#!/bin/bash

#export DISCORD_WEBHOOK_URL=""

export RSS_FEED_PATH="comets.xml"

cd /opt/discord-comets

# Remember the feed's mtime so we only upload it if this run rewrote it
feed_mtime_before=$(stat -c %Y "$RSS_FEED_PATH" 2>/dev/null)

python CometDiscovery.py

current_day=$(date +%u)

# Send a summarization every Mon
if [ "$current_day" -eq 1 ]; then
    python CometDiscovery.py --summarize
fi

feed_mtime_after=$(stat -c %Y "$RSS_FEED_PATH" 2>/dev/null)

# DEPLOY_TARGET is the scp destination (user@host:/path), set in .env
if [ -z "$DEPLOY_TARGET" ]; then
    echo "DEPLOY_TARGET not set, skipping upload"
    exit 0
fi

if [ -n "$feed_mtime_after" ] && [ "$feed_mtime_after" != "$feed_mtime_before" ]; then
    scp "$RSS_FEED_PATH" "$DEPLOY_TARGET"
else
    echo "RSS feed unchanged, skipping upload"
fi

# The CSV is rewritten every run, so always upload it along with the page
scp index.html known_comets.csv "$DEPLOY_TARGET"

