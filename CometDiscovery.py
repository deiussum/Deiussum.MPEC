#!/usr/bin/env python3
"""
Comet Discovery Tracker
Monitors MPC for new comet discoveries and sends Discord notifications
"""
import requests
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from Comet import Comet
from CometList import CometList
from Discord import Discord

# Configuration
CSV_FILE = "known_comets.csv"

def get_recent_comets() -> CometList:
    recentComets = CometList()

    recentComets.loadRecentComets()

    return recentComets

def load_known_comets() -> CometList:
    knownComets = CometList()

    knownComets.loadCsv(CSV_FILE)

    return knownComets

def send_discord_comet_notification(title: str, description: str, color, comet_data: Comet):
    discord = Discord()
    
    # Create Discord embed
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": [],
        "timestamp": datetime.now().isoformat(),
    }
    
    # Add fields if data is available
    if comet_data.permid:
        embed["fields"].append({
            "name": "PermId",
            "value": comet_data.permid,
            "inline": True
        })

    if comet_data.name:
        embed["fields"].append({
            "name": "Name",
            "value": comet_data.name,
            "inline": True
        })
    
    try:
        discord.SendEmbed(embed)
        print(f"Discord notification sent for {comet_data.designation}")
    except requests.RequestException as e:
        print(f"Error sending Discord notification: {e}")

def summarize():
    load_dotenv()

    cometList = CometList()
    discord = Discord()

    cometList.loadCsv(CSV_FILE)

    embed = {
        "title": "Comet summary",
        "description": "Summary of currently tracked comets.",
        "color": 0xFFFFFF,
        "fields": [],
        "timestamp": datetime.now().isoformat(),
    }

    for comet in cometList.comets:
        embed["fields"].append({
            "name": comet.getFriendlyName(),
            "value": f"Last observation: {comet.lastobs} at an average magnitude of {comet.mag1davg}",
            "inline": True
        })

    discord.SendEmbed(embed)

def updateAndCheckNotifications():
    print(f"Checking for new comets at {datetime.now()}")
    cometList = CometList()

    cometList.loadCsv(CSV_FILE)
    print(f"Loaded {len(cometList.comets)} previously known comets")

    cometList.loadRecentComets()
    print(f"Found {len(cometList.added)} new comets")
    print(f"Updated {len(cometList.updated)} comets")
    print(f"Total of {len(cometList.comets)} comets")

    for newComet in cometList.added:
        print(f"New discovery found: {newComet.designation}")
        
        title = f"🌟 New Comet Discovery: {newComet.getFriendlyName()}"
        description = "A new comet has been discovered!"
        color = 0x00FF00
        send_discord_comet_notification(title, description, color, newComet)

    for updatedComet in cometList.added:
        print(f"Updated comet: {updatedComet.designation} - PermId:{updatedComet.permid}, Name:{updatedComet.name}")

        title = f"🌟 Comet update: {updatedComet.getFriendlyName()}"
        description = "A comet has been named or given a permanent id!"
        color = 0x0000FF
        send_discord_comet_notification(title, description, color, updatedComet)

    # Update the observation data and check for comets reaching certain thresholds
    cometList.updateObservationData()

    for comet in cometList.spectacular:
        print(f"Spectacular comet found: {comet.designation}, 2 day Mag average: {comet.mag2davg}")

        title = f"🌟 Comet magnitude change: {comet.getFriendlyName()}"
        description = f"The comet's magnitude has a 2 day average of {comet.mag2davg} and should be easily visible!"
        color = 0xFFFF00
        send_discord_comet_notification(title, description, color, comet)

    for comet in cometList.nakedeye:
        print(f"Naked eye comet found: {comet.designation}, 2 day Mag average: {comet.mag2davg}")

        title = f"🌟 Comet magnitude change: {comet.getFriendlyName()}"
        description = f"The comet's magnitude has a 2 day average of {comet.mag2davg} and may be nearly visible with the naked eye!"
        color = 0xFFFF00
        send_discord_comet_notification(title, description, color, comet)

    for comet in cometList.binoc:
        print(f"Binocular comet found: {comet.designation}, 2 day Mag average: {comet.mag2davg}")

        title = f"🌟 Comet magnitude change: {comet.getFriendlyName()}"
        description = f"The comet's magnitude has a 2 day average of {comet.mag2davg} and may be visible with binoculars."
        color = 0xABAB00
        send_discord_comet_notification(title, description, color, comet)

    cometList.saveCsv(CSV_FILE)

def main():
    load_dotenv()
    parser = argparse.ArgumentParser('A script for checking on Comet data and sending notifications to a Discord channel')

    parser.add_argument('--summarize', action='store_true', help='If set, the output will be summarized')

    args = parser.parse_args()

    if args.summarize:
        summarize()
    else:
        updateAndCheckNotifications()


if __name__ == "__main__":
    main()
