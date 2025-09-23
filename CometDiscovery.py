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

def send_discord_notification(comet_data: Comet):
    discord = Discord()
    
    # Create Discord embed
    embed = {
        "title": f"🌟 New Comet Discovery: {comet_data.designation}",
        "description": "A new comet has been discovered!",
        "color": 0x00FF00,
        "fields": [],
        "timestamp": datetime.now().isoformat(),
    }
    
    # Add fields if data is available
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
    
    # Load previously known comets
    known_comets = load_known_comets()
    print(f"Loaded {len(known_comets.comets)} previously known comets")
    
    # Method 1: Use hardcoded test data (for initial testing)
    recent_comets = get_recent_comets()
    print(f"Found {len(recent_comets.comets)} recent comets")
    
    # Check for new discoveries
    new_discoveries = CometList()
    
    for comet in recent_comets.comets:
        matches = known_comets.findCometByDesignation(comet.designation)

        if len(matches) == 0:
            print(f"New discovery found: {comet.designation}")
            new_discoveries.addComet(comet)
            known_comets.addComet(comet)
            
            # Get detailed info and send notification
            send_discord_notification(comet)
    
    # # Update the CSV with all current comets (including new ones)
    if len(new_discoveries.comets) > 0:
        known_comets.saveCsv(CSV_FILE)
    
    print(f"Processing complete. Found {len(new_discoveries.comets)} new discoveries.")

if __name__ == "__main__":
    main()
