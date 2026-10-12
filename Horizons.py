from datetime import datetime, timezone
from typing import List
import requests


class EphemerisRow:
    time: datetime
    tmag: float
    r: float
    delta: float

    def __init__(self, time: datetime, tmag: float, r: float, delta: float):
        self.time = time
        self.tmag = tmag
        self.r = r
        self.delta = delta


class EphemerisSummary:
    """
    Closest approach to Earth and predicted peak brightness within a window.
    Each is None when it falls on the first or last day, since the real
    extreme is then outside the window.
    """
    closeApproach: datetime
    closeDistance: float
    peakDate: datetime
    peakMagnitude: float

    def __init__(self, rows: List[EphemerisRow]):
        self.closeApproach = None
        self.closeDistance = None
        self.peakDate = None
        self.peakMagnitude = None

        closest = min(rows, key=lambda row: row.delta)
        if self.isInside(rows, closest):
            self.closeApproach = closest.time
            self.closeDistance = round(closest.delta, 3)

        magnitudes = [row for row in rows if row.tmag is not None]
        if magnitudes:
            brightest = min(magnitudes, key=lambda row: row.tmag)
            if self.isInside(rows, brightest):
                self.peakDate = brightest.time
                self.peakMagnitude = round(brightest.tmag, 1)

    def isInside(self, rows: List[EphemerisRow], row: EphemerisRow) -> bool:
        return row is not rows[0] and row is not rows[-1]


class HorizonsApi:
    baseUrl = 'https://ssd.jpl.nasa.gov/api/horizons.api'

    def queryEphemeris(self, designation: str, start: datetime, stop: datetime) -> List[EphemerisRow]:
        """
        Daily geocentric ephemeris for a comet, e.g. C/2026 A2 or 161P. CAP
        picks the apparition closest to now and NOFRAG skips fragments.
        """
        params = {
            'format': 'json',
            'COMMAND': f"'DES={designation};CAP;NOFRAG;'",
            'OBJ_DATA': 'NO',
            'MAKE_EPHEM': 'YES',
            'EPHEM_TYPE': 'OBSERVER',
            'CENTER': "'500@399'",
            'START_TIME': f"'{start:%Y-%m-%d}'",
            'STOP_TIME': f"'{stop:%Y-%m-%d}'",
            'STEP_SIZE': "'1 d'",
            # 9: T-mag/N-mag, 19: r (Sun distance), 20: delta (Earth distance)
            'QUANTITIES': "'9,19,20'",
            'CSV_FORMAT': 'YES',
        }

        response = requests.get(self.baseUrl, params=params)
        response.raise_for_status()

        result = response.json().get('result', '')
        if '$$SOE' not in result:
            # Unknown or ambiguous designations come back as a search result
            # instead of an ephemeris
            raise ValueError(f"No ephemeris from Horizons for {designation}")

        header, data = result.split('$$SOE')
        data = data.split('$$EOE')[0]

        # The column names are on the last non-separator line before $$SOE
        headerLine = [line for line in header.splitlines() if line.strip() and not line.startswith('*')][-1]
        columns = [name.strip() for name in headerLine.split(',')]
        timeIndex = columns.index('Date__(UT)__HR:MN')
        tmagIndex = columns.index('T-mag')
        rIndex = columns.index('r')
        deltaIndex = columns.index('delta')

        rows = []
        for line in data.strip().splitlines():
            fields = [field.strip() for field in line.split(',')]
            tmag = fields[tmagIndex]

            rows.append(EphemerisRow(
                datetime.strptime(fields[timeIndex], '%Y-%b-%d %H:%M').replace(tzinfo=timezone.utc),
                None if tmag == 'n.a.' else float(tmag),
                float(fields[rIndex]),
                float(fields[deltaIndex]),
            ))

        return rows


if __name__ == "__main__":
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    rows = HorizonsApi().queryEphemeris('161P', now - timedelta(days=90), now + timedelta(days=365))
    summary = EphemerisSummary(rows)

    print(f"Closest approach: {summary.closeApproach} at {summary.closeDistance} AU")
    print(f"Predicted peak: {summary.peakDate} at magnitude {summary.peakMagnitude}")
