import math
from datetime import datetime, timedelta, timezone
from typing import List
import requests
import json
import pandas as pd

class DesignationInfo:
    found: bool
    objectType: str
    objectTypeIndex: int
    orbfitName: str
    name: str
    designation: str
    permId: str
    packedPermId: str
    packedPrimaryProvisionalDesignation: str
    packedSecondaryProvisionalDesignations: List[str]
    unpackedPrimaryProvisionalDesignation: str
    unpackedSecondaryProvisionalDesignations: List[str]
    disambiguationList: List[dict]

    def __init__(self, designation: dict):
        self.found = designation['found']

        if designation['object_type'] and len(designation['object_type']) > 0:
            self.objectType = designation['object_type'][0]
            self.objectTypeIndex = designation['object_type'][1]

        self.orbfitName = designation['orbfit_name']
        self.name = designation['name']
        self.designation = designation['iau_designation']
        self.permId = designation['permid']
        self.packedPermId = designation['packed_permid']
        self.packedPrimaryProvisionalDesignation= designation['packed_primary_provisional_designation']
        self.packedSecondaryProvisionalDesignations= designation['packed_secondary_provisional_designations']
        self.unpackedPrimaryProvisionalDesignation= designation['unpacked_primary_provisional_designation']
        self.unpackedSecondaryProvisionalDesignations= designation['unpacked_secondary_provisional_designations']
        self.disambiguationList = designation['disambiguation_list']

    def toDict(self):
        return {
            'found': self.found,
            'objectType': self.objectType,
            'object_type': [ self.objectType, self.objectTypeIndex ],
            'orbfit_name': self.orbfitName,
            'name': self.name,
            'iau_designation': self.designation,
            'permid': self.permId,
            'packed_permid': self.packedPermId,
            'packed_primary_provisional_designation': self.packedPrimaryProvisionalDesignation,
            'packed_secondary_provisional_designations': self.packedSecondaryProvisionalDesignations,
            'unpacked_primary_provisional_designation': self.unpackedPrimaryProvisionalDesignation,
            'unpacked_secondary_provisional_designations': self.unpackedSecondaryProvisionalDesignations,
            'disambiguation_list': self.disambiguationList
        }


class DesignationBuilder:
    # All half-month letters (I and Z are skipped in MPC system)
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y']

    def GetMonthDesignation(self, forDate: datetime) -> str:
        designationIndex = (forDate.month - 1) * 2
        if forDate.day > 15:
            designationIndex += 1

        return self.letters[designationIndex]

    def GetCometDesignationRange(self, forDate: datetime, startIndex: int, endIndex: int) -> List[str]:
        month_designation = self.GetMonthDesignation(forDate)

        return [f"C/{forDate.year} {month_designation}{index}" for index in range(startIndex, endIndex + 1)]

class DesignationIdentifierApi:
    baseUrl = "https://data.minorplanetcenter.net/api/query-identifier"

    def querySingle(self, designation: str) -> DesignationInfo:
        response = requests.get(self.baseUrl, data=designation)

        response.raise_for_status()
        return DesignationInfo(response.json())

    def queryMultiple(self, designations: List[str]) -> List[DesignationInfo]:
        response = requests.get(self.baseUrl, json={ 'ids': designations })
        response.raise_for_status()

        results = []
        data = response.json()
        for row in data:
            results.append(DesignationInfo(data[row]))

        return results


class CometElement:
    """
    One line of MPC's CometEls.txt, in MPC's one-line comet orbit format.
    """
    orbitType: str
    designation: str
    isFragment: bool
    perihelion: datetime
    q: float
    H: float
    K: float

    def __init__(self, line: str):
        number = line[0:4].strip()
        provisional = line[5:12].strip()

        self.orbitType = line[4]
        self.isFragment = bool(number and provisional)

        # Numbered comets are queried by number alone (e.g. 12P), others by
        # their provisional designation (e.g. P/2026 N2)
        if number:
            self.designation = f"{int(number)}{self.orbitType}"
        else:
            self.designation = line[102:158].split(' (')[0].strip()

        day = float(line[22:29])
        perihelion = datetime(int(line[14:18]), int(line[19:21]), 1, tzinfo=timezone.utc) + timedelta(days=day - 1)
        # Match the whole-second precision perihelion is saved with in the CSV
        self.perihelion = perihelion.replace(microsecond=0)
        self.q = float(line[30:39])

        H = line[91:95].strip()
        K = line[96:100].strip()
        self.H = float(H) if H else None
        self.K = float(K) if K else None

    def estimatedPeakMagnitude(self) -> float:
        """
        Rough magnitude at perihelion, assuming the comet is 1 AU from Earth.
        Only good for ranking comets, not for predicting what will be seen.
        """
        if self.H is None or self.K is None:
            return None

        return self.H + 2.5 * self.K * math.log10(self.q)


class CometElementsApi:
    url = 'https://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'

    def query(self) -> List[CometElement]:
        response = requests.get(self.url)
        response.raise_for_status()

        elements = []
        for line in response.text.splitlines():
            if not line.strip():
                continue

            try:
                elements.append(CometElement(line))
            except ValueError as e:
                print(f"Skipping unreadable comet element line: {line!r} ({e})")

        return elements


class ObservationsApi:
    baseUrl = 'https://data.minorplanetcenter.net/api/get-obs'

    def query(self, designation: str) -> pd.DataFrame:
        cleanedDesignation = designation.removeprefix('(').removesuffix(')')

        json = { 'desigs': [ cleanedDesignation ], 'output_format': [ 'ADES_DF' ] }
        response = requests.get(self.baseUrl, json=json)
        
        response.raise_for_status()

        data = pd.DataFrame(response.json()[0]['ADES_DF'])
        return data
            
    def queryObs80(self, designation: str) -> str:
        cleanedDesignation = designation.removeprefix('(').removesuffix(')')

        json = { 'desigs': [ cleanedDesignation ], 'output_format': [ 'OBS80' ] }
        response = requests.get(self.baseUrl, json=json)
        
        response.raise_for_status()

        data = response.json()[0]['OBS80']
        return data



if __name__ == "__main__":
    # designationApi = DesignationIdentifierApi()

    # single = designationApi.querySingle('C/2025 R3')
    # multiple = designationApi.queryMultiple(['C/2025 R1', 'C/2025 R2', '3I'])

    # print(json.dumps(single.toDict(), indent=2))

    # for row in multiple:
    #     print(json.dumps(row.toDict(), indent=2))

    obsApi = ObservationsApi()

    print(obsApi.queryObs80('C/2025 A6'))
