import html
import os
from datetime import datetime
from typing import List

from Discord import Discord
from Rss import Rss


class Notifications:
    """
    Sends notifications to every configured target. Discord is enabled by
    DISCORD_WEBHOOK_URL and the RSS feed by RSS_FEED_PATH.
    """

    def __init__(self):
        self.discord = Discord() if os.getenv('DISCORD_WEBHOOK_URL') else None

        rssPath = os.getenv('RSS_FEED_PATH')
        self.rss = Rss(rssPath) if rssPath else None

        if not self.discord and not self.rss:
            print("No notification targets configured. Set DISCORD_WEBHOOK_URL and/or RSS_FEED_PATH")

    def Send(self, title: str, description: str, color: int, fields: List[dict], link: str = None):
        if self.discord:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "fields": fields,
                "timestamp": datetime.now().isoformat(),
            }
            if link:
                embed["url"] = link

            self.discord.SendEmbed(embed)

        if self.rss:
            self.rss.AddItem(title, self.toHtml(description, fields), link)

    def Save(self):
        if self.rss:
            self.rss.Save()

    def toHtml(self, description: str, fields: List[dict]) -> str:
        body = f"<p>{html.escape(description)}</p>"

        if fields:
            body += "<ul>"
            for field in fields:
                body += f"<li><b>{html.escape(str(field['name']))}</b>: {html.escape(str(field['value']))}</li>"
            body += "</ul>"

        return body
