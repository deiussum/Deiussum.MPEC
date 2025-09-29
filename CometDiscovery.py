#!/usr/bin/env python3
"""
Comet Discovery Tracker
Monitors MPC for new comet discoveries and sends Discord notifications
"""

import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Set, Dict, List
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

def send_discord_notification(title: str, description: str, color, comet_data: Comet):
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

def main():
    """Main function to check for new comets and send notifications"""
    print(f"Checking for new comets at {datetime.now()}")

    load_dotenv()

    cometList = CometList()

    cometList.loadCsv(CSV_FILE)
    print(f"Loaded {len(cometList.comets)} previously known comets")

    cometList.loadRecentComets()
    print(f"Found {len(cometList.added)} new comets")
    print(f"Updated {len(cometList.updated)} comets")
    print(f"Total of {len(cometList.comets)} comets")

    for newDesignation in cometList.added:
        newComets = cometList.findCometByDesignation(newDesignation)

        if len(newComets) > 0:
            newComet = newComets[0]

            print(f"New discovery found: {newComet.designation}")
            
            title = f"🌟 New Comet Discovery: {newComet.getFriendlyName()}"
            description = "A new comet has been discovered!"
            color = 0x00FF00
            send_discord_notification(title, description, color, newComet)

    for updatedDesignation in cometList.added:
        updatedComets = cometList.findCometByDesignation(updatedDesignation)

        if len(updatedComets) > 0:
            updatedComet = updatedComets[0]
            
            title = f"🌟 Comet update: {newComet.getFriendlyName()}"
            description = "A comet has been named or given a permanent id!"
            color = 0x0000FF
            send_discord_notification(title, description, color, updatedComet)


    cometList.saveCsv(CSV_FILE)
    

if __name__ == "__main__":
    main()
