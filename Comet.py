
class Comet:
    designation = ''
    name=''

    def __init__(self, comet:dict):
        self.designation = comet['designation']
        self.name = comet.get('name', '')

    def toDict(self) -> dict:
        return {
            'designation': self.designation,
            'name': self.name
        }
        

if __name__== "__main__":
    comet = Comet({ 'designation': 'C/2025 R2', 'name': 'SWAN25' })
    print(f"{comet.designation} ({comet.name})")
    print(comet.toDict())

