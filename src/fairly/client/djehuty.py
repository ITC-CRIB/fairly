from typing import Dict

from .figshare import FigshareClient

import re
from urllib.parse import urlparse

CLASS_NAME = "DjehutyClient"

class DjehutyClient(FigshareClient):
    """

    4TU.ResearchData is using `custom_fields` to store the following
    information:

    - Contributors
    - Data Link
    - Derived From
    - Format
    - Geolocation Latitude
    - Geolocation Longitude
    - Geolocation
    - Language
    - Licence remarks
    - Organizations
    - Publisher
    - Same As
    - Time coverage

    From the developers:

    > The use of "Data Link" is inconsistent, so try to avoid using it. In
    > djehuty, we will assign "Data Link" values as "file links" where
    > applicable (so they show up under "files"). I think also "Organizations"
    > and "Publisher" are not entirely consistent and will have gone through
    > manual cleanup once djehuty goes live.

    """

    REGEXP_UUID = re.compile(r"^([a-f\d]+)(-[a-f\d]+)+$", re.IGNORECASE)

    def _get_dataset_id(self, **kwargs) -> Dict:
        """Returns standard dataset identifier.

        Args:
            **kwargs: Dataset identifier arguments

        Returns:
            Standard dataset identifier

        Raises:
            ValueError("Invalid id")
            ValueError("Invalid URL address")
            ValueError("No identifier")
            ValueError("Invalid version")
        """
        version = None

        if kwargs.get("uuid"):
            id = str(kwargs["uuid"])

        elif kwargs.get("url"):
            parts = urlparse(kwargs["url"]).path.strip("/").split("/")
            if parts[-1].isnumeric():
                if re.match(DjehutyClient.REGEXP_UUID, parts[-2]) or parts[-2].isnumeric():
                    id = parts[-2]
                    version = parts[-1]
                else:
                    id = parts[-1]

            elif re.match(DjehutyClient.REGEXP_UUID, parts[-1]):
                id = parts[-1]

            else:
                raise ValueError("Invalid URL address")

        else:
            return super()._get_dataset_id(**kwargs)

        return {"id": id, "version": version}