import os
import requests
from dotenv import load_dotenv

class Discord:

    def __init__(self):
        self.DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

    def SendEmbed(self, embed: dict):
        if not self.DISCORD_WEBHOOK_URL or self.DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
            print("DISCORD_WEBHOOK_URL not set")
            return

        webhook_data = {
            "embeds": [embed]
        }
        
        try:
            response = requests.post(self.DISCORD_WEBHOOK_URL, json=webhook_data, timeout=10)
            response.raise_for_status()
            print("Discord notification sent")
        except requests.RequestException as e:
            print(f"Error sending Discord notification: {e}")

if __name__ == "__main__":
    load_dotenv()
    test = Discord()

    embed = {
        "title": "Test embed",
        "description": "Description for the test embed",
        "fields": [ {
                "name": "Field 1",
                "value": "Value 1",
                "inline": True
            }, {
                "name": "Field 2",
                "value": "Value 2",
                "inline": True
            }

        ],
        "color": 0x0000FF
    }   
    test.SendEmbed(embed)
    


