#!/usr/bin/env python3
"""
Comet Discovery Tracker
Monitors MPC for new comet discoveries and sends Discord and/or RSS notifications
"""
import argparse
from datetime import datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv
from Comet import Comet
from CometList import CometList
from Notifications import Notifications

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

def comet_link(comet: Comet) -> str:
    return f"https://minorplanetcenter.net/db_search/show_object?object_id={quote_plus(comet.designation)}"

def send_comet_notification(notifications: Notifications, title: str, description: str, color, comet_data: Comet):
    fields = []

    # Add fields if data is available
    if comet_data.permid:
        fields.append({
            "name": "PermId",
            "value": comet_data.permid,
            "inline": True
        })

    if comet_data.name:
        fields.append({
            "name": "Name",
            "value": comet_data.name,
            "inline": True
        })

    notifications.Send(title, description, color, fields, comet_link(comet_data))


def summarize(send: bool):
    _ = load_dotenv()

    cometList = CometList()

    cometList.loadCsv(CSV_FILE)

    title = "Comet summary"
    description = "Summary of currently tracked comets."
    fields = []

    for comet in cometList.comets:
        if comet.archive is True:
            continue

        fields.append({
            "name": comet.getFriendlyName(),
            "value": f"Last observation: {comet.lastobs} at an average magnitude of {comet.mag1davg}",
            "inline": True
        })

    if send:
        notifications = Notifications()
        notifications.Send(title, description, 0xFFFFFF, fields)
        notifications.Save()
    else:
        print(title)
        print(description)
        for field in fields:
            print(f"  {field['name']}: {field['value']}")

def updateAndCheckNotifications():
    print(f"Checking for new comets at {datetime.now()}")
    cometList = CometList()
    notifications = Notifications()

    cometList.loadCsv(CSV_FILE)
    print(f"Loaded {len(cometList.comets)} previously known comets")

    cometList.loadRecentComets()
    cometList.loadMissedComets()
    print(f"Found {len(cometList.added)} new comets")
    print(f"Updated {len(cometList.updated)} comets")

    cometList.loadReturningComets()
    print(f"Found {len(cometList.returning)} returning periodic comets")
    print(f"Total of {len(cometList.comets)} comets")

    for newComet in cometList.added:
        print(f"New discovery found: {newComet.designation}")

        title = f"🌟 New Comet Discovery: {newComet.getFriendlyName()}"
        description = "A new comet has been discovered!"
        color = 0x00FF00
        send_comet_notification(notifications, title, description, color, newComet)

    for updatedComet in cometList.updated:
        print(f"Updated comet: {updatedComet.designation} - PermId:{updatedComet.permid}, Name:{updatedComet.name}")

        title = f"🌟 Comet update: {updatedComet.getFriendlyName()}"
        description = "A comet has been named or given a permanent id!"
        color = 0x0000FF
        send_comet_notification(notifications,
                                title,
                                description,
                                color,
                                updatedComet)

    for returningComet in cometList.returning:
        print(f"Returning comet: {returningComet.designation}, perihelion {returningComet.perihelion}")

        title = f"☄️ Periodic comet returning: {returningComet.getFriendlyName()}"
        description = f"A periodic comet reaches perihelion on {returningComet.perihelion:%Y-%m-%d}."
        color = 0x00FFFF
        send_comet_notification(notifications, title, description, color, returningComet)

    # Update the observation data and check for comets reaching certain
    # thresholds
    cometList.updateObservationData()

    for comet in cometList.spectacular:
        print(f"Spectacular comet found: {comet.designation}, 2 day Mag average: {comet.mag2davg}")

        title = f"🌟 Comet magnitude change: {comet.getFriendlyName()}"
        description = f"The comet's magnitude has a 2 day average of {comet.mag2davg} and should be easily visible!"
        color = 0xFFFF00
        send_comet_notification(notifications, title, description, color, comet)

    for comet in cometList.nakedeye:
        print(f"Naked eye comet found: {comet.designation}, 2 day Mag average: {comet.mag2davg}")

        title = f"🌟 Comet magnitude change: {comet.getFriendlyName()}"
        description = f"The comet's magnitude has a 2 day average of {comet.mag2davg} and may be nearly visible with the naked eye!"
        color = 0xFFFF00
        send_comet_notification(notifications, title, description, color, comet)

    for comet in cometList.binoc:
        print(f"Binocular comet found: {comet.designation}, 2 day Mag average: {comet.mag2davg}")

        title = f"🌟 Comet magnitude change: {comet.getFriendlyName()}"
        description = f"The comet's magnitude has a 2 day average of {comet.mag2davg} and may be visible with binoculars."
        color = 0xABAB00
        send_comet_notification(notifications, title, description, color, comet)

    for comet in cometList.suddenincrease:
        print(f"Sudden brightening found: {comet.designation}, 2 day Mag average: {comet.mag2davg}")

        title = f"🌟 Comet brightening: {comet.getFriendlyName()}"
        description = f"The comet's 2 day average magnitude has suddenly brightened to {comet.mag2davg}!"
        color = 0xFF8000
        send_comet_notification(notifications, title, description, color, comet)

    cometList.archiveStaleComets()

    notifications.Save()
    cometList.saveCsv(CSV_FILE)

def main():
    load_dotenv()
    parser = argparse.ArgumentParser('A script for checking on Comet data and sending notifications to Discord and/or an RSS feed')

    parser.add_argument('--summarize', action='store_true', help='If set, the output will be summarized')
    parser.add_argument('--skipsend', action='store_true', help='If set, print the summary instead of sending it')

    args = parser.parse_args()

    if args.summarize:
        summarize(not args.skipsend)
    else:
        updateAndCheckNotifications()


if __name__ == "__main__":
    main()
