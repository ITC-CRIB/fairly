from __future__ import annotations
from typing import List, Dict
from collections.abc import Iterable, MutableMapping

import fairly

import re
import requests
import copy

class Person(MutableMapping):
    """Class to handle personal information, e.g. for authors, contributors, etc.

    Attributes:
        REGEXP_ORCID_ID: Regular expression to validate ORCID identifier
    """

    # TODO: Check the checksum digit
    # https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier
    REGEXP_ORCID_ID = re.compile(r"^(\d{4}-){3}\d{3}(\d|X)$")

    def __init__(self, **kwargs):
        """Initializes Person object.

        Full name is obtained from name and surname, if required.

        Name and surname are obtained from full name, if required.
        (see parse_fullname() method for details).

        Standard attributes:
            name (string): Name of the person
            surname (string): Surname of the person
            fullname (string): Full name of the person
            email (string): E-mail address of the person
            institution (string): Institution of the person
            orcid_id (string): ORCID identifier of the person

        Args:
            **kwargs: Person attributes
        """
        if "fullname" in kwargs:
            attrs = Person.parse_fullname(kwargs["fullname"])
            if attrs.get("name"):
                kwargs["name"] = attrs.get("name")
            if attrs.get("surname"):
                kwargs["surname"] = attrs.get("surname")

        elif "name" in kwargs and "surname" in kwargs:
            kwargs["fullname"] = (kwargs["name"] + " " + kwargs["surname"]).strip()

        for key, val in kwargs.items():
            if bool(val) or isinstance(val, (bool, int, float)):
                self.__dict__[key] = val


    def __setitem__(self, key, val):
        if bool(val) or isinstance(val, (bool, int, float)):
            self.__dict__[key] = self._normalize(key, val)
        elif hasattr(self.__dict__, key):
            del self.__dict__[key]


    def __getitem__(self, key):
        return self.__dict__[key]


    def __delitem__(self, key):
        del self.__dict__[key]


    def __iter__(self):
        return iter(self.__dict__)


    def __len__(self):
        return len(self.__dict__)


    def __str__(self):
        return str(self.__dict__)


    def __repr__(self):
        return f"Person({self.__dict__})"


    @classmethod
    def parse_fullname(cls, fullname:str) -> Dict:
        """Parses full name and extracts available person attributes

        The following attributes might be extracted:
            - name
            - surname
            - fullname

        Args:
            fullname: Full name of the person

        Returns:
            Dictionary of person attributes
        """
        fullname = fullname.strip()
        attrs = {"fullname": fullname}
        parts = [part.strip() for part in fullname.split(",")]
        if len(parts) == 2:
            attrs["surname"], attrs["name"] = parts
        return attrs


    @staticmethod
    def get_orcid_token(client_id: str=None, client_secret: str=None) -> str:
        config = fairly.get_config("orcid")
        if not client_id:
            client_id = config.get("client_id")
            if not client_id:
                raise ValueError("No client id")
        if not client_secret:
            client_secret = config.get("client_secret")
            if not client_secret:
                raise ValueError("No client secret")
        data = f"client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials&scope=/read-public"
        response = requests.post(
            "https://orcid.org/oauth/token",
            data=data,
            headers={"accept": "application/json"}
        )
        return response.json()


    @staticmethod
    def get_from_orcid_id(orcid_id: str, access_token: str=None) -> Person:
        # Get default access token if required
        if not access_token:
            config = fairly.get_config("orcid")
            access_token = config.get("token")
            if not access_token:
                raise ValueError("No access token")

        # Send request
        fields = ",".join(["orcid", "email", "given-names", "family-name", "current-institution-affiliation-name"])
        response = requests.get(
            f"https://pub.orcid.org/v3.0/expanded-search/?q=orcid:{orcid_id}&fl={fields}",
            headers={
                "Content-type": "application/vnd.orcid+json",
                "Authorization type and Access token": f"Bearer {access_token}"
            }
        )
        results = response.json().get("expanded-result")

        # Return if no results
        if not results:
            return None

        # Return the first person matching the ORCID identifier
        result = results[0]
        return Person(
            orcid_id=result.get("orcid-id"),
            name=result.get("given-names"),
            surname=result.get("family-names"),
            email=result.get("email"),
            institution=result["institution-name"][0] if result.get("institution-name") else None
        )


    @staticmethod
    def get_people(people) -> List[Person]:
        """Returns standard person list from custom people input

        A string or an iterable are accepted as input. If input is a string,
        it is split using semicolon and line feed as separators. For the items
        of the iterable, the following are performed:

            - If it is a Person object, a copy is created
            - If it is a string, it is parsed to a dictionary using parse_fullname()
            - If is is a dictionary, Person object is created

        Args:
            people: Custom people input

        Returns:
            List of person objects

        Raises:
            ValueError
        """
        if not people:
            return []

        if isinstance(people, str):
            people = re.split(r"[;\n]", people)

        if not isinstance(people, Iterable):
            raise ValueError

        persons = []
        for item in people:

            if not item:
                continue

            if isinstance(item, Person):
                person = copy.copy(item)

            else:
                if isinstance(item, str):
                    item = Person.parse_fullname(item)
                if not isinstance(item, Dict):
                    raise ValueError
                person = Person(**item)

            persons.append(person)

        return persons