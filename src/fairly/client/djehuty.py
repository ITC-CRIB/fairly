from typing import Dict

from .figshare import FigshareClient

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
    pass