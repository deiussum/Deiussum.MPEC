import csv
import os
from datetime import datetime, timedelta
from typing import List
from Comet import Comet
from MinorPlanetaryCenter import DesignationIdentifierApi, DesignationBuilder

class CometList:
    comets: List[Comet] = []
    added: List[str] = []
    updated: List[str] = []

    def loadCsv(self, filePath: str):
        if os.path.exists(filePath):
            try:
                self.comets = []

                with open(filePath, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.comets.append(Comet(row))
            except Exception as e:
                print(f"Error reading CSV: {e}")

    def saveCsv(self, filePath: str):
        fieldnames = ['designation', 'permid', 'name', 'discoverer']
        
        try:
            with open(filePath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for comet in self.comets:
                    writer.writerow(comet.toDict())
        except Exception as e:
            print(f"Error writing CSV: {e}")

    def loadRecentComets(self):
        designationBuilder = DesignationBuilder()

        saved_designations = [ c.designation for c in self.comets ]
        previous_designations = designationBuilder.GetCometDesignationRange(datetime.now() - timedelta(days=15), 1, 5)
        current_designations = designationBuilder.GetCometDesignationRange(datetime.now(), 1, 5)

        designations = saved_designations + previous_designations + current_designations
        unique_designations = list(dict.fromkeys(designations))

        designationApi = DesignationIdentifierApi()

        data = designationApi.queryMultiple(unique_designations)

        if not self.comets:
            self.comets = []

        for row in data:
            if row.found == 0:
                continue

            existingComets = self.findCometByDesignation(row.designation)

            if existingComets and len(existingComets) > 0 :
                existingComet = existingComets[0]

                if existingComet.name != (row.name or '') or existingComet.permid != (row.permId or ''):
                    print(f"updating {existingComet.permid} - {existingComet.name} to {row.permId} - {row.name}")

                    existingComet.name = row.name
                    existingComet.permid = row.permId
                    self.updated.append(row.designation)
            elif not existingComets or len(existingComets) == 0:
                comet = Comet({
                    'designation': row.designation,
                    'name': row.name,
                    'permid': row.permId
                })

                self.comets.append(comet)
                self.added.append(row.designation)

    def addComet(self, comet: Comet):
        self.comets.append(comet)

    def findCometByDesignation(self, designation: str) -> List[Comet]:
        matches = [ c for c in self.comets if c.designation == designation ]
        return matches


if __name__ == '__main__':
    cometList = CometList()

    cometList.loadCsv('test.csv')
    print(f"{len(cometList.comets)} comets loaded from csv")

    cometList.loadRecentComets()
    print(f"{len(cometList.comets)} comets loaded from recent")

    cometList.saveCsv('test.csv')


