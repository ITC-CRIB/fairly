from __future__ import annotations
from typing import List, Dict
from collections.abc import Iterable

import fairly

import re
import requests
import copy
import textwrap

class Person:

    # TODO: Check the checksum digit
    # https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier
    REGEXP_ORCID_ID = re.compile(r"^(\d{4}-){3}\d{3}(\d|X)$")

    def __init__(self, name: str=None, surname: str=None, fullname: str=None, email: str=None, institution: str=None, orcid_id: str=None):
        """Initializes Person object.

        Full name is obtained from name and surname, if required.

        Name and surname are obtained from full name, if required.
        (see parse_fullname() method for details).

        Arguments:
            name (string): Name of the person
            surname (string): Surname of the person
            fullname (string): Full name of the person
            email (string): E-mail address of the person
            institution (string): Institution of the person
            orcid_id (string): ORCID identifier of the person

        """
        if fullname:
            attrs = Person.parse_fullname(fullname)
            if not name:
                name = attrs.get("name")
            if not surname:
                surname = attrs.get("surname")

        elif name and surname:
            fullname = (name + " " + surname).strip()

        self._name = name
        self._surname = surname
        self._fullname = fullname
        self._email = email
        self._institution = institution
        self._orcid_id = orcid_id


    def __repr__(self):
        attrs = {}
        for key in ["name", "surname", "fullname", "email", "institution", "orcid_id"]:
            val = getattr(self, key)
            if val:
                attrs[key] = val

        attrs = ", ".join(f"{key}={val!r}" for key, val in attrs.items())

        return f"Person({attrs})"


    @property
    def name(self) -> str:
        """
        Name of the person.
        """
        return self._name


    @property
    def surname(self) -> str:
        """
        Surname of the person.
        """
        return self._surname


    @property
    def fullname(self) -> str:
        """
        Full name of the person.
        """
        return self._fullname


    @property
    def email(self) -> str:
        """
        E-mail address of the person.
        """
        return self._email


    @property
    def institution(self) -> str:
        """
        Institution of the person.
        """
        return self._institution


    @property
    def orcid_id(self) -> str:
        """
        ORCID identifier of the person.
        """
        return self._orcid_id


    @classmethod
    def parse_fullname(cls, fullname:str) -> Dict:
        """Parses full name and extracts available person attributes

        The following attributes might be extracted:
            - name
            - surname
            - fullname

        Arguments:
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
    def get_from_orcid_id(orcid_id: str, access_token: str=None) -> Dict:
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
        if not people:
            return []

        if isinstance(people, str):
            people = re.split(r"[;\n]", people)

        if not isinstance(people, Iterable):
            raise ValueError

        persons = []
        for item in people:
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