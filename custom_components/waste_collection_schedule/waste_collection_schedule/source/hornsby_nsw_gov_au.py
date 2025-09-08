from datetime import datetime

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Hornsby Shire Council"
DESCRIPTION = "Source for Hornsby Shire Council."
URL = "https://hornsby.nsw.gov.au/"
TEST_CASES = {
    "randomHouse1": {"address": "1 Lisgar Road Hornsby"},
    "randomHouse2": {"address": "1 Old Beecroft Road Cheltenham"},
}
API_URL = "https://services6.arcgis.com/VKqP0BP08pVXloHq/arcgis/rest/services/WASTE_Cadastre_20240902_V6/FeatureServer/14/query"
ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Yellow": "mdi:recycle",
    "Green": "mdi:leaf",
    "Kerbside": "mdi:sofa",
}
DAYS = {
    "MONDAY": MO,
    "TUESDAY": TU,
    "WEDNESDAY": WE,
    "THURSDAY": TH,
    "FRIDAY": FR,
    "SATURDAY": SA,
    "SUNDAY": SU,
}
WEEKS = {
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "FOUR": 4,
    "FIVE": 5,
    "SIX": 6,
    "SEVEN": 7,
    "EIGHT": 8,
    "NINE": 9,
    "TEN": 10,
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def generate_dates(self, wd: str) -> list:
        yr = datetime.now().year
        start_date = datetime(yr, 1, 1)  # change to actual start date
        end_date = datetime(yr, 12, 31)  # change to start date +12 months
        date_list = list(
            rrule(
                freq=WEEKLY,
                byweekday=DAYS[wd.upper()],
                dtstart=start_date,
                until=end_date,
            )
        )
        return date_list

    def fetch(self):

        s = requests.Session()

        # get address collection days
        params = {
            "f": "json",
            "resultOffset": 0,
            "resultRecordCount": 100,
            "where": f"SearchAddress LIKE '%{self._address}%'",
            "outFields": "SearchAddress,GarbageDAY,Recycling_Day,Kerbside_Day,",
            "returnZ": "true",
            "spatialRel": "esriSpatialRelIntersects",
        }
        data = s.get(API_URL, params=params).json()

        # Extract waste collection days
        result = next(
            (
                {
                    "Garbage": feature["attributes"].get("GarbageDAY"),
                    "Recycling": feature["attributes"].get("Recycling_Day"),
                    "Kerbside": feature["attributes"].get("Kerbside_Day"),
                }
                for feature in data["features"]
                if feature["attributes"].get("SearchAddress") == self._address
            ),
            None,  # Default if not found
        )

        # create list of day dates
        date_list = self.generate_dates(result["Garbage"])

        # iterate through dates building schedule
        entries = []
        for idx, item in enumerate(date_list):
            # Garbage
            waste_type = "Refuse"
            entries.append(
                Collection(
                    date=item.date(), t=waste_type, icon=ICON_MAP.get(waste_type)
                )
            )
            # Recycling or Green Waste
            if "A" in result["Recycling"]:
                if idx % 2 == 0:  # Green Waste week
                    waste_type = "Green"
                else:  # Recycling week
                    waste_type = "Yellow"
            elif "B" in result["Recycling"]:
                if idx % 2 == 0:  # Recycling week
                    waste_type = "Yellow"
                else:  # Green Waste week
                    waste_type = "Green"
            entries.append(
                Collection(
                    date=item.date(), t=waste_type, icon=ICON_MAP.get(waste_type)
                )
            )
            # Kerbside - low week numbers are inconsistent format: "Week Two" vs "Week 2"
            try:
                wk = int(result["Kerbside"].split(" ")[1])  # "Week 2"
            except ValueError:
                wk = WEEKS[result["Kerbside"].split(" ")[1].upper()]  # "Week Two"
            if idx + 1 == wk:  # 0-based idx, 1-based week numbers
                waste_type = "Kerbside"
                entries.append(
                    Collection(
                        date=item.date(), t=waste_type, icon=ICON_MAP.get(waste_type)
                    )
                )

        return entries
