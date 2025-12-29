import csv
import os
import time
from datetime import datetime, timedelta, timezone
from typing import List

import pandas as pd
from Comet import Comet
from MinorPlanetaryCenter import DesignationIdentifierApi, DesignationBuilder, ObservationsApi

BINOC_MAGNITUDE=8
NAKED_EYE_MAGNITUDE=6
SPECTACULAR_MAGNITUDE=2
SUDDEN_INCREASE_MAGNITUDE=1.5


class CometList:
    comets: List[Comet] = []
    added: List[Comet] = []
    updated: List[Comet] = []
    binoc: List[Comet] = []
    nakedeye: List[Comet] = []
    spectacular: List[Comet] = []
    suddenincrease: List[Comet] = []

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
        fieldnames = ['designation',
                      'permid',
                      'name',
                      'discoverer',
                      'mag1davg',
                      'mag2davg',
                      'lastobs',
                      'lastupdate',
                      'archive'
                      ]

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

        saved_designations = [c.designation for c in self.comets]
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

            if existingComets and len(existingComets) > 0:
                existingComet = existingComets[0]

                if existingComet.name != (row.name or '') or existingComet.permid != (row.permId or ''):
                    existingComet.name = row.name
                    existingComet.permid = row.permId
                    existingComet.lastupdate = datetime.now()

                    self.updated.append(existingComet)
            elif not existingComets or len(existingComets) == 0:
                comet = Comet({
                    'designation': row.designation,
                    'name': row.name,
                    'permid': row.permId,
                    'mag2davg': None,
                    'mag1davg': None,
                    'lastupdated': datetime.now(timezone.utc)
                })

                self.comets.append(comet)
                self.added.append(comet)

    def updateObservationData(self):
        print("Updating observation data for known comets")

        obsApi = ObservationsApi()
        for comet in self.comets:
            try:
                obs = obsApi.query(comet.designation)

                obs['obstime'] = pd.to_datetime(obs['obstime'], format='ISO8601')

                lastObservation = obs['obstime'].max()
                lastObservation = lastObservation.replace(microsecond=0)

                twoDays = lastObservation - timedelta(days=2)
                oneDay = lastObservation - timedelta(days=1)

                if comet.lastobs and lastObservation <= comet.lastobs:
                    print(f"No new observations for {comet.getFriendlyName()} since {lastObservation}")
                    continue

                comet.lastobs = lastObservation

                twoDayData = obs[obs['obstime'] >= twoDays].copy()
                twoDayData['mag'] = pd.to_numeric(twoDayData['mag'], errors='coerce')

                # print(twoDayData['mag'])

                twoDayAvg = twoDayData['mag'].dropna().mean().round(2)

                self.checkMagnitudes(comet, comet.mag2davg, twoDayAvg)

                if comet.mag2davg:
                    mag2delta = comet.mag2davg - twoDayAvg
                else:
                    mag2delta = twoDayAvg

                if mag2delta != 0:
                    comet.mag2davg = twoDayAvg

                if mag2delta >= SUDDEN_INCREASE_MAGNITUDE:
                    self.suddenincrease.append(comet)

                oneDayData = obs[obs['obstime'] >= oneDay].copy()
                oneDayData['mag'] = pd.to_numeric(oneDayData['mag'], errors='coerce')

                oneDayAvg = oneDayData['mag'].dropna().mean().round(2)

                if comet.mag1davg:
                    mag1delta = comet.mag1davg - oneDayAvg
                else:
                    mag1delta = oneDayAvg

                if mag1delta != 0:
                    comet.mag1davg = oneDayAvg

                if mag1delta != 0 or mag2delta != 0:
                    comet.lastupdate = datetime.now()

                # Pause before the next comet to avoid spamming the API
                time.sleep(0.5)
            except Exception as ex:
                print(f"Error getting observations for {comet.designation}: {ex}")


    def checkMagnitudes(self, comet: Comet, priorMagnitude: float, newMagnitude: float):
        if self.checkThreshold(SPECTACULAR_MAGNITUDE, priorMagnitude, newMagnitude):
            self.binoc.append(comet)
        elif self.checkThreshold(NAKED_EYE_MAGNITUDE, priorMagnitude, newMagnitude):
            self.nakedeye.append(comet)
        elif self.checkThreshold(BINOC_MAGNITUDE, priorMagnitude, newMagnitude):
            self.binoc.append(comet)

    
    def checkThreshold(self, threshold: float, priorMagnitude: float, newMagnitude: float) -> bool:
        return priorMagnitude and newMagnitude and priorMagnitude > threshold and newMagnitude <= threshold

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

    cometList.updateObservationData()

    cometList.saveCsv('test.csv')


