from datetime import datetime

# import brotli
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Eastleigh Borough Council"
DESCRIPTION = "Source for Eastleigh Borough Council."
URL = "https://eastleigh.gov.uk"
TEST_CASES = {
    "100060319000": {"uprn": 100060319000},
    "100060300958": {"uprn": "100060300958"},
}

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "cache-control": "private",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    # "referer":"https://www.eastleigh.gov.uk/waste-bins-and-recycling/collection-dates?Filters.PostalCode=SO505JH&Filters.House=&Filters.Street=&Filters.Town=&Submit=Search",
    "accept-encoding": "gzip, deflate, br, zstd",
}

ICON_MAP = {
    "Paper": "mdi:package-variant",
    "household": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "food": "mdi:food",
    "glass": "mdi:bottle-soda",
    "garden": "mdi:leaf",
}


API_URL = "https://eastleigh.gov.uk/waste-bins-and-recycling/collection-dates/your-waste-bin-and-recycling-collections"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        s = requests.Session()

        args = {"uprn": self._uprn}

        # get json file
        r = s.get(API_URL, headers=HEADERS, params=args)
        print(r.content)
        # decompressed = brotli.decompress(r.text)
        # print(decompressed)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        dls = soup.find_all("dl")

        entries = []

        for dl in dls:
            dts = dl.findAll("dt")
            for dt in dts:
                dd = dt.find_next_sibling("dd")
                if not dd:
                    continue

                try:
                    # Mon, 29 Apr 2024
                    date = datetime.strptime(dd.text, "%a, %d %b %Y").date()
                except ValueError:
                    continue

                icon = ICON_MAP.get(
                    dt.text.strip().split(" ")[0].lower()
                )  # Collection icon
                type = dt.text
                entries.append(Collection(date=date, t=type, icon=icon))

        return entries
