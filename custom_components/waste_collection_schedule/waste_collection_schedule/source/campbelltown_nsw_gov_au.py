import datetime
import json

import requests
from bs4 import BeautifulSoup

# from requests.utils import requote_uri
from waste_collection_schedule import Collection

TITLE = "Campbelltown City Council (NSW)"
DESCRIPTION = "Source for Campbelltown City Council rubbish collection."
URL = "https://www.campbelltown.nsw.gov.au/"
TEST_CASES = {
    "Minto Mall": {
        "post_code": "2566",
        "suburb": "Minto",
        "street_name": "Brookfield Road",
        "street_number": "10",
    },
    "Campbelltown Catholic Club": {
        "post_code": "2560",
        "suburb": "Campbelltown",
        "street_name": "Camden Road",
        "street_number": "20-22",
    },
    "Australia Post Ingleburn": {
        "post_code": "2565",
        "suburb": "INGLEBURN",
        "street_name": "Oxford Road",
        "street_number": "34",
    },
}

# API_URLS = {
#     "address_search": "https://www.campbelltown.nsw.gov.au/api/v1/myarea/search?keywords={}",
#     "collection": "https://www.campbelltown.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU",
# }

API_URLS = {
    "address_search": "https://www.campbelltown.nsw.gov.au/api/v1/myarea/search",
    "collection": "https://www.campbelltown.nsw.gov.au/ocapi/Public/myarea/wasteservices",
}
HEADERS = {"user-agent": "Mozilla/5.0"}

ICON_MAP = {
    "General Waste": "trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}


class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str
    ):
        self.post_code = post_code
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):
        s = requests.Session()

        r = s.get(
            "https://www.campbelltown.nsw.gov.au/Services-and-Facilities/Waste-and-Recycling/Find-my-bin-day"
        )
        print(r.status_code, r.cookies)

        address = f"{self.street_number} {self.street_name} {self.suburb} NSW {self.post_code}"
        # address = "{} {} {} NSW {}".format(
        #     self.street_number, self.street_name, self.suburb, self.post_code
        # )
        params = {"keywords": address}
        r = s.get(API_URLS["address_search"], headers=HEADERS, params=params)
        print(r.text)

        # q = requote_uri(str(API_URLS["address_search"]).format(address))

        # Retrieve suburbs
        # r = requests.get(q, headers=HEADERS)

        data = json.loads(r.text)

        # Find the ID for our suburb
        locationId = 0
        for item in data["Items"]:
            locationId = item["Id"]
            break
        if locationId == 0:
            return []

        # Retrieve the upcoming collections for our property
        params = {
            "geolocationid": locationId,
            "ocsvclang": "en-AU",
            "pageLink": "/$B9015858-988C-48A4-9473-7C193DF083E4$/Services-and-Facilities/Waste-and-Recycling/Find-my-bin-day",
        }
        r = s.get(API_URLS["collection"], headers=HEADERS, params=params)

        # q = s.get(url,  payload=payload,
        #           )
        # q = requote_uri(str(API_URLS["collection"]).format(locationId))

        # r = requests.get(q, headers=HEADERS)

        data = json.loads(r.text)

        responseContent = data["responseContent"]

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []

        for item in services:
            # test if <div> contains a valid date. If not, is is not a collection item.
            date_text = item.find("div", attrs={"class": "next-service"})

            # The date format currently used on https://www.campbelltown.nsw.gov.au/Services-and-Facilities/Waste-and-Recycling/Check-my-collection-day
            date_format = "%a %d/%m/%Y"

            try:
                # Strip carriage returns and newlines out of the HTML content
                cleaned_date_text = (
                    date_text.text.replace("\r", "").replace("\n", "").strip()
                )

                # Parse the date
                date = datetime.datetime.strptime(cleaned_date_text, date_format).date()

            except ValueError:
                continue

            waste_type = item.find("h3").text.strip()

            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                )
            )

        return entries
