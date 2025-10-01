
from datetime import datetime, timezone

DATETIME_FORMAT='%Y-%m-%d %H:%M:%S'

class Comet:
    designation: str
    name: str
    permid: str
    discoverer: str
    mag2davg: float
    mag1davg: float
    lastobs: datetime
    lastupdate: datetime

    def __init__(self, comet:dict):
        self.designation = comet['designation']
        self.permid = comet.get('permid', '')
        self.name = comet.get('name', '')
        self.discoverer = comet.get('discoverer', '')
        self.mag2davg = self.getFloat(comet.get('mag2davg', None))
        self.mag1davg = self.getFloat(comet.get('mag1davg', None))
        self.lastobs = self.getDateTime(comet.get('lastobs', None))
        self.lastupdate = self.getDateTime(comet.get('lastupdate', None))

    def toDict(self) -> dict:
        return {
            'designation': self.designation,
            'permid': self.permid,
            'name': self.name,
            'discoverer': self.discoverer,
            'mag2davg': self.mag2davg,
            'mag1davg': self.mag1davg,
            'lastobs': self.lastobs.strftime(DATETIME_FORMAT),
            'lastupdate': self.lastupdate.strftime(DATETIME_FORMAT)
        }

    def getFriendlyName(self) -> str:
        if self.permid and self.name:
            return f"{self.permid}/{self.name}"

        if self.discoverer:
            return f"{self.designation} ({self.discoverer})"

        return self.designation

    def getFloat(self, val) -> float:
        if val:
            return float(val)
        return None

    def getDateTime(self, val) -> float:
        if val:
            parsed= datetime.strptime(val, DATETIME_FORMAT)
            if parsed:
                return parsed.replace(tzinfo=timezone.utc)
        return None
        

if __name__== "__main__":
    comet = Comet({ 'designation': 'C/2025 R2', 'name': 'SWAN25' })
    print(f"{comet.designation} ({comet.name})")
    print(comet.toDict())

