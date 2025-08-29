# import json
from datetime import datetime
from typing import TypedDict

import requests
from dateutil.parser import parse
from waste_collection_schedule import Collection

TITLE = "London Borough of Waltham Forest"
DESCRIPTION = (
    "Source for waste collection services for London Borough of Waltham Forest."
)
URL = "https://www.walthamforest.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": 100022559099},
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

BASE_URL = "https://portal.walthamforest.gov.uk"
INTIAL_URL = f"{BASE_URL}/service/Your_bin_collection_days"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
AUTH_TEST = f"{BASE_URL}/apibroker/domain/portal.walthamforest.gov.uk"
API_URL = f"{BASE_URL}/apibroker/runLookup"


ICON_MAP = {
    "Domestic Waste": "mdi:trash-can",
    "Domestic Recycling": "mdi:recycle",
    "Food Waste": "mdi:food",
    "Textiles and Small WEEE": "mdi:tshirt-crew",
}


class CollectionResult(TypedDict):
    Date: str
    Service1: str
    Service2: str
    Service3: str


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()
        self._session = requests.Session()

    def _init_session(self) -> str:
        self._session = requests.Session()
        r = self._session.get(INTIAL_URL, headers=HEADERS)
        r.raise_for_status()
        params: dict[str, str | int] = {
            "uri": r.url,
            "hostname": "portal.walthamforest.gov.uk",
            "withCredentials": "true",
        }
        r = self._session.get(AUTH_URL, params=params, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        session_key = data["auth-session"]
        # params = {
        #     "sid": session_key,
        #     "_": int(datetime.now().timestamp() * 1000),
        # }
        # r = self._session.get(AUTH_TEST, params=params, headers=HEADERS)
        # r.raise_for_status()
        return session_key

    # https://portal.walthamforest.gov.uk/apibroker/runLookup?id=672b4376b3610&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_=1756484376820&sid=602209b26e9172e39b7d237

    def get_collections(self, session_key: str) -> list[Collection]:
        params: dict[str, int | str] = {
            # "id":"612647c8bc5ec",
            "id": "672b4376b3610",
            # "id": "5e59316b3263e",
            "repeat_against": "",
            "noRetry": "false",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": int(datetime.now().timestamp() * 1000),
            "sid": session_key,
        }
        # payload = {
        #     "formValues": {
        #         "Section 1": {
        #             "UPRN": {"value": self._uprn},
        #         }
        #     }
        # }
        payload = {
            "formValues": {
                "Section 1": {
                    "inputUPRN": {"value": self._uprn},
                }
            }
        }
        r = self._session.post(API_URL, params=params, json=payload, headers=HEADERS)
        r.raise_for_status()
        return list(r.json()["integration"]["transformed"]["rows_data"].values())

    def fetch(self) -> list[Collection]:
        session_key = self._init_session()
        collections = self.get_collections(session_key)

        entries = []
        for collection in collections:
            print(collection)
            date = parse(collection["Date"], dayfirst=True).date()
            for service in [
                collection["Service1"],
                collection["Service2"],
                collection["Service3"],
            ]:
                if not service:
                    continue
                service = service.removesuffix(" Collection Service")
                icon = ICON_MAP.get(service)
                entries.append(Collection(date=date, t=service, icon=icon))

        return entries
