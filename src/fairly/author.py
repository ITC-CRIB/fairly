from typing import Dict

import fairly
import re
import requests

class Author:

    # TODO: Check the checksum digit
    # https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier    
    REGEXP_ORCID_ID = re.compile(r"^(\d{4}-){3}\d{3}(\d|X)$")
    
    def __init__(self, name: str=None, surname: str=None, fullname: str=None, email: str=None, institution: str=None, orcid_id: str=None):
        if fullname:
            attrs = Author.parse_fullname(fullname)
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


    @property
    def name(self) -> str:
        return self._name


    @property
    def surname(self) -> str:
        return self._surname


    @property
    def fullname(self) -> str:
        return self._fullname


    @property
    def email(self) -> str:
        return self._email


    @property
    def institution(self) -> str:
        return self._institution


    @property
    def orcid_id(self) -> str:
        return self._orcid_id


    @classmethod
    def parse_fullname(cls, fullname:str) -> Dict:
        attrs = {}
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
        if not access_token:
            config = fairly.get_config("orcid")
            access_token = config.get("token")
            if not access_token:
                raise ValueError("No access token")
        fields = ",".join(["orcid", "email", "given-names", "family-name", "current-institution-affiliation-name"])
        response = requests.get(
            f"https://pub.orcid.org/v3.0/expanded-search/?q=orcid:{orcid_id}&fl={fields}",
            headers={
                "Content-type": "application/vnd.orcid+json",
                "Authorization type and Access token": f"Bearer {access_token}"
            }
        )
        results = response.json().get("expanded-result")
        if not results:
            return None
        result = results[0]
        return Author(
            orcid_id=result.get("orcid-id"),
            name=result.get("given-names"),
            surname=result.get("family-names"),
            email=result.get("email"),
            institution=result["institution-name"][0] if result.get("institution-name") else None
        )