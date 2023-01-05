"""Person class module.

Person class is used to store person (e.g. author) information in a standardized
manner.

Usage example:

    >>> person = Person("Doe, John")
    >>> person = Person(fullname="Doe, Jon", orcid_id="xxx")
    >>> person.affiliation = "fairly Community"

"""
from __future__ import annotations
from typing import List, Dict
from collections.abc import Iterable, MutableMapping

import fairly

import re
import requests
import copy

class Person(MutableMapping):
    """Class to handle person information, e.g. for authors, contributors, etc.

    Class Attributes:
        REGEXP_ORCID_ID: Regular expression to validate ORCID identifier.
        REGEXP_EMAIL: Regular expression to validate e-mail address.
    """

    # TODO: Check the checksum digit
    # https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier
    REGEXP_ORCID_ID = re.compile(r"^(\d{4}-){3}\d{3}(\d|X)$")
    REGEXP_EMAIL = re.compile(r"^[\w\.+-]+@([\w-]+\.)+[\w-]{2,}$")


    def __init__(self, person: str=None, **kwargs):
        """Initializes Person object.

        Full name is obtained from name and surname, if required.

        Name and surname are obtained from full name, if required.
        (see `parse()` method for details).

        Standard attributes:
            name (string): Name of the person.
            surname (string): Surname of the person.
            fullname (string): Full name of the person.
            email (string): E-mail address of the person.
            institution (string): Institution of the person.
            orcid_id (string): ORCID identifier of the person.

        Args:
            person: Person identifier.
            **kwargs: Person attributes.
        """
        attrs = Person.parse(person) if person else {}

        if kwargs.get("fullname"):
            attrs.update(Person.parse(kwargs["fullname"]))

        attrs.update(kwargs)

        if not attrs.get("fullname") and attrs.get("name") and attrs.get("surname"):
            attrs["fullname"] = (attrs["name"] + " " + attrs["surname"]).strip()

        for key, val in attrs.items():
            if bool(val) or isinstance(val, (bool, int, float)):
                self.__dict__[key] = val


    def __setitem__(self, key, val):
        if bool(val) or isinstance(val, (bool, int, float)):
            self.__dict__[key] = val
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
    def parse(cls, person: str) -> Dict:
        """Parses person identifier and extracts available person attributes.

        The following attributes might be extracted:
            - name
            - surname
            - fullname
            - orcid_id

        Args:
            person: Person identifier (e.g. fullname)

        Returns:
            Dictionary of person attributes.
        """
        person = person.strip()

        if re.match(Person.REGEXP_ORCID_ID, person):
            return {"orcid_id": person}

        if re.match(Person.REGEXP_EMAIL, person):
            return {"email": person}

        attrs = {"fullname": person}
        parts = [part.strip() for part in person.split(",")]
        if len(parts) == 2:
            attrs["surname"], attrs["name"] = parts

        return attrs


    @staticmethod
    def get_orcid_token(client_id: str=None, client_secret: str=None) -> str:
        """Retrieves ORCID access token by using ORCID client id and secret.

        ORCID access token is required to retrieve person information by using
        an ORCID ID.

        If not specified, `client_id` and `client_secret` are read from fairly
        configuration.

        Args:
            client_id: ORCID client id.
            client_secret: ORCID client secret.

        Returns:
            ORCID access token.

        Raises:
            ValueError("No client id"): If client id is not available.
            ValueError("No client secret"): If client secret is not available.
            ValueError("Invalid response"): If access token is not retrieved.
        """
        config = fairly.get_config("fairly")

        if not client_id:
            client_id = config.get("orcid_client_id")
            if not client_id:
                raise ValueError("No client id")

        if not client_secret:
            client_secret = config.get("orcid_client_secret")
            if not client_secret:
                raise ValueError("No client secret")

        response = requests.post(
            "https://orcid.org/oauth/token",
            data=f"client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials&scope=/read-public",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

        json = response.json()

        if "access_token" not in json:
            raise ValueError("Invalid response")

        return json["access_token"]


    @staticmethod
    def from_orcid_id(orcid_id: str, token: str=None) -> Person:
        """Retrieves person information from ORCID identifier.

        If not specified, `token` is read from fairly configuration. If it is
        also not available, it is retrieved by using `get_orcid_token()` method.

        Args:
            orcid_id: ORCID identifier.
            token: ORCID access token.

        Returns:
            Person object if valid ORCID identifier, otherwise None.

        Raises:
            ValueError("No access token"): If access token is not available.
            ValueError("Invalid ORCID identifier"): If ORCID identified is not valid.
        """
        # Get default access token if required
        if not token:
            config = fairly.get_config("fairly")
            token = config.get("orcid_token")
            if not token:
                try:
                    token = Person.get_orcid_token()
                except:
                    raise ValueError("No access token")

        # Send request
        fields = ",".join(["orcid", "email", "given-names", "family-name", "current-institution-affiliation-name"])
        response = requests.get(
            f"https://pub.orcid.org/v3.0/expanded-search/?q=orcid:{orcid_id}&fl={fields}",
            headers={
                "Content-type": "application/vnd.orcid+json",
                "Authorization type and Access token": f"Bearer {token}"
            }
        )
        results = response.json().get("expanded-result")

        # Raise exception if no results
        if not results:
            raise ValueError("Invalid ORCID Id")

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
    def get_persons(people) -> List[Person]:
        """Returns standard person list from the people argument.

        A string or an iterable are accepted as input. If input is a string,
        it is split using semicolon and line feed as separators. For the items
        of the iterable, the following are performed:

            - If it is a Person object, a copy is created.
            - If it is a string, it is parsed to a dictionary using parse().
            - If is is a dictionary, Person object is created.

        Args:
            people: People argument.

        Returns:
            List of person objects.

        Raises:
            ValueError: If people argument is invalid.
        """
        if not people:
            return PersonList()

        if isinstance(people, str):
            people = re.split(r"[;\n]", people)

        if not isinstance(people, Iterable):
            raise ValueError

        persons = PersonList()
        for item in people:

            if not item:
                continue

            if isinstance(item, Person):
                person = copy.copy(item)

            else:
                if isinstance(item, str):
                    item = Person.parse(item)
                if not isinstance(item, Dict):
                    raise ValueError
                person = Person(**item)

            persons.append(person)

        return persons


    def autocomplete(self, overwrite: bool=False, orcid_token: str=None) -> Dict:
        """Completes missing information by using the ORCID identifier.

        Args:
            overwrite: If True existing attributes are overwritten.

        Returns:
            A dictionary of attributes set by method.
        """
        if not self.get("orcid_id"):
            return {}

        person = Person.from_orcid_id(self["orcid_id"], token=orcid_token)

        updated = {}
        for key, val in person.__dict__.items():
            if key not in self.__dict__ or overwrite:
                self.__dict__[key] = updated[key] = val

        return updated


    def serialize(self) -> Dict:
        """Serializes person as a dictionary.

        Returns:
            Person dictionary.
        """
        return self.__dict__.copy()


class PersonList(list):
    def _person(self, item):
        if isinstance(item, Person):
            return item

        if isinstance(item, str):
            return Person(item)

        if isinstance(item, dict):
            return Person(**item)

        raise ValueError

    def __init__(self, iterable=None):
        if iterable:
            super().__init__(self._person(item) for item in iterable)

    def __setitem__(self, index, item):
        super().__setitem__(index, self._person(item))

    def insert(self, index, item):
        super().insert(index, self._person(item))

    def append(self, item):
        super().append(self._person(item))

    def extend(self, other):
        if isinstance(other, type(self)):
            super().extend(other)
        else:
            super().extend(self._person(item) for item in other)