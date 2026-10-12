import csv
import os
import time
from datetime import datetime, timedelta, timezone
from typing import List

import pandas as pd
from Comet import Comet
from MinorPlanetaryCenter import CometElement, CometElementsApi, DesignationIdentifierApi, DesignationBuilder, ObservationsApi

BINOC_MAGNITUDE=8
NAKED_EYE_MAGNITUDE=6
SPECTACULAR_MAGNITUDE=2
SUDDEN_INCREASE_MAGNITUDE=1.5
ARCHIVE_AFTER_DAYS=90

# Periodic comets are tracked when their perihelion falls between
# PERIHELION_PAST_DAYS ago and PERIHELION_AHEAD_DAYS from now, and their
# estimated peak magnitude is at or below RETURNING_MAX_MAGNITUDE
PERIHELION_PAST_DAYS=60
PERIHELION_AHEAD_DAYS=120
RETURNING_MAX_MAGNITUDE=14

# Recent comets in CometEls.txt that loadRecentComets missed are added when
# their designation's half-month started within this many days
MISSED_LOOKBACK_DAYS=90


class CometList:
    comets: List[Comet]
    added: List[Comet]
    updated: List[Comet]
    returning: List[Comet]
    binoc: List[Comet]
    nakedeye: List[Comet]
    spectacular: List[Comet]
    suddenincrease: List[Comet]

    def __init__(self):
        self.comets = []
        self.added = []
        self.updated = []
        self.returning = []
        self.elements = None
        self.binoc = []
        self.nakedeye = []
        self.spectacular = []
        self.suddenincrease = []

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
                      'perihelion',
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
                    existingComet.lastupdate = datetime.now(timezone.utc)

                    self.updated.append(existingComet)
            elif not existingComets or len(existingComets) == 0:
                comet = Comet({
                    'designation': row.designation,
                    'name': row.name,
                    'permid': row.permId,
                    'mag2davg': None,
                    'mag1davg': None
                })
                comet.lastupdate = datetime.now(timezone.utc)

                self.comets.append(comet)
                self.added.append(comet)

    def getCometElements(self) -> List[CometElement]:
        # Downloaded once per run and shared by the checks that use it
        if self.elements is None:
            try:
                self.elements = CometElementsApi().query()
            except Exception as ex:
                print(f"Error getting comet elements: {ex}")
                self.elements = []

        return self.elements

    def loadMissedComets(self):
        """
        Backstop for loadRecentComets, which only guesses C/ designations
        1-5 for the last two half-months. Catches recent C/ and P/ comets
        announced late, numbered past 5, or periodic.
        """
        designationBuilder = DesignationBuilder()
        cutoff = datetime.now(timezone.utc) - timedelta(days=MISSED_LOOKBACK_DAYS)

        candidates = []
        for element in self.getCometElements():
            if element.isFragment:
                continue

            halfMonthStart = designationBuilder.GetHalfMonthStart(element.designation)
            if not halfMonthStart or halfMonthStart < cutoff:
                continue

            if not self.findCometByDesignation(element.designation):
                candidates.append(element.designation)

        if not candidates:
            return

        data = DesignationIdentifierApi().queryMultiple(candidates)

        for row in data:
            if row.found == 0 or self.findCometByDesignation(row.designation):
                continue

            comet = Comet({
                'designation': row.designation,
                'name': row.name,
                'permid': row.permId,
            })
            comet.lastupdate = datetime.now(timezone.utc)

            self.comets.append(comet)
            self.added.append(comet)

    def loadReturningComets(self):
        candidates = {}
        for element in self.getCometElements():
            if element.orbitType != 'P' or element.isFragment:
                continue

            if not self.isNearPerihelion(element.perihelion):
                continue

            peak = element.estimatedPeakMagnitude()
            if peak is None or peak > RETURNING_MAX_MAGNITUDE:
                continue

            candidates[element.designation] = element

        if not candidates:
            return

        data = DesignationIdentifierApi().queryMultiple(list(candidates))

        for row in data:
            if row.found == 0:
                continue

            # Numbered comets were queried as their permid (e.g. 12P), others
            # by their designation
            element = candidates.get(row.permId) or candidates.get(row.designation)
            if not element:
                continue

            existingComets = self.findCometByDesignation(row.designation)

            if existingComets:
                comet = existingComets[0]

                if comet.perihelion != element.perihelion:
                    comet.perihelion = element.perihelion
                    comet.lastupdate = datetime.now(timezone.utc)

                if comet.archive:
                    comet.archive = False
                    comet.lastupdate = datetime.now(timezone.utc)
                    self.returning.append(comet)
            else:
                comet = Comet({
                    'designation': row.designation,
                    'name': row.name,
                    'permid': row.permId,
                })
                comet.perihelion = element.perihelion
                comet.lastupdate = datetime.now(timezone.utc)

                self.comets.append(comet)
                self.returning.append(comet)

    def isNearPerihelion(self, perihelion: datetime) -> bool:
        if not perihelion:
            return False

        now = datetime.now(timezone.utc)
        return now - timedelta(days=PERIHELION_PAST_DAYS) <= perihelion <= now + timedelta(days=PERIHELION_AHEAD_DAYS)

    def updateObservationData(self):
        print("Updating observation data for known comets")

        obsApi = ObservationsApi()
        for comet in self.comets:
            if comet.archive:
                continue

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

                # Averages are None when no observation in the window reports
                # a magnitude, e.g. astrometry-only SOHO observations
                twoDayAvg = self.averageMagnitude(obs, twoDays)
                mag2delta = 0

                if twoDayAvg is not None:
                    self.checkMagnitudes(comet, comet.mag2davg, twoDayAvg)

                    if comet.mag2davg:
                        mag2delta = comet.mag2davg - twoDayAvg

                        # Only a change from a prior average counts as a sudden increase
                        if mag2delta >= SUDDEN_INCREASE_MAGNITUDE:
                            self.suddenincrease.append(comet)
                    else:
                        mag2delta = twoDayAvg

                    if mag2delta != 0:
                        comet.mag2davg = twoDayAvg

                oneDayAvg = self.averageMagnitude(obs, oneDay)
                mag1delta = 0

                if oneDayAvg is not None:
                    if comet.mag1davg:
                        mag1delta = comet.mag1davg - oneDayAvg
                    else:
                        mag1delta = oneDayAvg

                    if mag1delta != 0:
                        comet.mag1davg = oneDayAvg

                if mag1delta != 0 or mag2delta != 0:
                    comet.lastupdate = datetime.now(timezone.utc)

                # Pause before the next comet to avoid spamming the API
                time.sleep(0.5)
            except Exception as ex:
                print(f"Error getting observations for {comet.designation}: {ex}")

    def archiveStaleComets(self):
        cutoff = datetime.now(timezone.utc) - timedelta(days=ARCHIVE_AFTER_DAYS)

        for comet in self.comets:
            if comet.archive or not comet.lastobs or comet.lastobs >= cutoff:
                continue

            # A returning periodic comet's last observation is from its
            # previous apparition until it is recovered
            if self.isNearPerihelion(comet.perihelion):
                continue

            print(f"Archiving {comet.getFriendlyName()}, last observed {comet.lastobs}")
            comet.archive = True
            comet.lastupdate = datetime.now(timezone.utc)


    def averageMagnitude(self, obs: pd.DataFrame, since: datetime) -> float:
        if 'mag' not in obs.columns:
            return None

        mags = pd.to_numeric(obs.loc[obs['obstime'] >= since, 'mag'], errors='coerce').dropna()
        if mags.empty:
            return None

        return round(float(mags.mean()), 2)

    def checkMagnitudes(self, comet: Comet, priorMagnitude: float, newMagnitude: float):
        if self.checkThreshold(SPECTACULAR_MAGNITUDE, priorMagnitude, newMagnitude):
            self.spectacular.append(comet)
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

    cometList.loadMissedComets()
    print(f"{len(cometList.comets)} comets after checking for missed comets")

    cometList.loadReturningComets()
    print(f"{len(cometList.returning)} returning periodic comets")

    cometList.updateObservationData()
    cometList.archiveStaleComets()

    cometList.saveCsv('test.csv')


