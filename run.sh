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

if [ -n "$feed_mtime_after" ] && [ "$feed_mtime_after" != "$feed_mtime_before" ]; then
    scp "$RSS_FEED_PATH" deiussum@roguex.local:/var/www/comets.deiussum.com
else
    echo "RSS feed unchanged, skipping upload"
fi

# The CSV is rewritten every run, so always upload it along with the page
scp index.html known_comets.csv deiussum@roguex.local:/var/www/comets.deiussum.com

