from datetime import datetime, timedelta
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
