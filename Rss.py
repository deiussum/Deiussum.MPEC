import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime

MAX_ITEMS = 50


class Rss:
    """
    Maintains an RSS 2.0 feed file. Existing items are read back from the
    file so the feed keeps its history between runs.
    """

    def __init__(self, filePath: str,
                 title: str = "Comet updates",
                 link: str = "https://minorplanetcenter.net/",
                 description: str = "New comet discoveries and brightness changes from the Minor Planet Center"):
        self.filePath = filePath
        self.title = title
        self.link = link
        self.description = description
        self.items = []
        self.dirty = False

        self.loadExisting()

    def loadExisting(self):
        if not os.path.exists(self.filePath):
            return

        try:
            tree = ET.parse(self.filePath)
            self.items = tree.getroot().findall('./channel/item')
        except ET.ParseError as e:
            print(f"Error reading RSS feed, starting a new one: {e}")

    def AddItem(self, title: str, description: str, link: str = None):
        now = datetime.now(timezone.utc)

        item = ET.Element('item')
        ET.SubElement(item, 'title').text = title
        ET.SubElement(item, 'description').text = description
        if link:
            ET.SubElement(item, 'link').text = link
        ET.SubElement(item, 'guid', isPermaLink='false').text = f"{title} {now.isoformat()}"
        ET.SubElement(item, 'pubDate').text = format_datetime(now)

        self.items.insert(0, item)
        self.dirty = True

    def Save(self):
        if not self.dirty:
            return

        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = self.title
        ET.SubElement(channel, 'link').text = self.link
        ET.SubElement(channel, 'description').text = self.description
        ET.SubElement(channel, 'lastBuildDate').text = format_datetime(datetime.now(timezone.utc))

        channel.extend(self.items[:MAX_ITEMS])

        tree = ET.ElementTree(rss)
        ET.indent(tree)

        # Write to a temp file first so a reader never sees a partial feed
        tempPath = f"{self.filePath}.tmp"
        try:
            tree.write(tempPath, encoding='utf-8', xml_declaration=True)
            os.replace(tempPath, self.filePath)
            self.dirty = False
            print(f"RSS feed written to {self.filePath}")
        except OSError as e:
            print(f"Error writing RSS feed: {e}")


if __name__ == "__main__":
    test = Rss('test_feed.xml')
    test.AddItem("Test item", "<p>Description for the <b>test</b> item</p>", "https://minorplanetcenter.net/")
    test.Save()
