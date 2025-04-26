import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Norwich City Council"
DESCRIPTION = "Source for norwich.gov.uk"
URL = "https://www.norwich.gov.uk"
TEST_CASES = {
    "UPRN": {"uprn": "100090924499"},
    "Postcode & Number": {"postcode": "???", "house": "???"},
}

# API_URL = "https://maps.norwich.gov.uk/arcgis/rest/services/MyNorwich/PropertyDetails/FeatureServer/3/query"
API_URL = "https://bnr-wrp.whitespacews.com/mop.php#!"

COLLECTION_TYPES = {
    "waste and food waste": {
        "title": "Waste and Food Waste",
        "icon": "mdi:trash-can",
    },
    "recycling and food waste": {
        "title": "Recycling and Food Waste",
        "icon": "mdi:recycle",
    },
}


class Source:
    def __init__(self, uprn: str, postcode: str, house: str | int):
        self._uprn = uprn
        self._postcode = postcode
        self._house = house

    def get_postcode(self, s, u):
        """Return the postcode for a given uprn.

        Helps avoid a breaking change when Norwich altered their website back-end.
        Subsequent waste collection schedule search assumes all addresses within a given postcode are collected on the same day.
        """
        r = s.get(f"https://uprn.uk/{u}")
        soup = BeautifulSoup(r.content, "html.parser")
        a = soup.find_all("a", href=True)
        for item in a:
            if "postcode" in item["href"]:
                p = item.text
            else:
                # raise error message
                pass
        return p

    def fetch(self) -> list[Collection]:
        params = {
            "f": "json",
            "where": f"UPRN='{self._uprn}' or UPRN='0{self._uprn}'",
            "outFields": "WasteCollectionHtml",
        }
        response = requests.get(API_URL, params=params)
        response.raise_for_status()

        features = response.json()["features"]

        if len(features) != 1:
            raise Exception(f"Expected 1 feature, got {len(features)}")

        html = features[0]["attributes"]["WasteCollectionHtml"]

        date_match = re.search(r"Your next collection: <strong>(.*?)</strong>", html)
        if not date_match:
            raise Exception("No collection date found")
        date_str = date_match.group(1)
        type_match = re.search(r"We will be collecting: <strong>(.*?).</strong>", html)
        if not type_match:
            raise Exception("No collection type found")
        type_str = type_match.group(1)

        date = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()

        type = COLLECTION_TYPES.get(type_str) or {}

        entries = [
            Collection(
                date=date,
                t=type["title"],
                icon=type["icon"],
            ),
        ]

        return entries
