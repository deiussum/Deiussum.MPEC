
class Comet:
    designation: str
    name: str
    permid: str
    discoverer: str

    def __init__(self, comet:dict):
        self.designation = comet['designation']
        self.permid = comet.get('permid', '')
        self.name = comet.get('name', '')
        self.discoverer = comet.get('discoverer', '')

    def toDict(self) -> dict:
        return {
            'designation': self.designation,
            'permid': self.permid,
            'name': self.name,
            'discoverer': self.discoverer
        }

    def getFriendlyName(self) -> str:
        if self.permid and self.name:
            return f"{self.permid}/{self.name}"

        if self.discoverer:
            return f"{self.designation} ({self.discoverer})"

        return self.designation
        

if __name__== "__main__":
    comet = Comet({ 'designation': 'C/2025 R2', 'name': 'SWAN25' })
    print(f"{comet.designation} ({comet.name})")
    print(comet.toDict())

