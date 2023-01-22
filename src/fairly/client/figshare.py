from typing import Any, List, Dict, Callable

from . import Client
from ..metadata import Metadata
from ..person import Person, PersonList
from ..dataset.remote import RemoteDataset
from ..file.local import LocalFile
from ..file.remote import RemoteFile

import re
from urllib.parse import urlparse
import requests
from requests import Session
from requests.exceptions import HTTPError
from collections import OrderedDict
import time
import warnings
import dateutil.parser

CLASS_NAME = "FigshareClient"

class FigshareClient(Client):

    PAGE_SIZE = 25

    LOCKED_SLEEP = 5
    LOCKED_TRIES = 5

    record_types = {
        "book": "Book",
        "conference contribution": "Conference Contribution",
        "dataset": "Dataset",
        "figure": "Figure",
        "journal contribution": "Journal Contribution",
        "media": "Media",
        "online resource": "Online Resource",
        "poster": "Poster",
        "preprint": "Preprint",
        "presentation": "Presentation",
        "software": "Software",
        "thesis": "Thesis",
    }

    record_type_lookup = {
        "conference contribution": "conferencepaper",
        "journal contribution": "article",
        "media": "video",
        "online resource": "onlineresource",
    }

    def __init__(self, repository_id: str=None, **kwargs):
        # Call parent method
        super().__init__(repository_id, **kwargs)

        # Initialize properties
        self._categories = None


    @classmethod
    def get_config_parameters(cls) -> Dict:
        """Returns configuration parameters

        Args:
            None

        Returns:
            Dictionary of configuration parameters.
            Keys are the parameter names, values are the descriptions.
        """
        return {**super().get_config_parameters(), **{
            "token": "Access token.",
        }}


    @classmethod
    def get_config(cls, **kwargs) -> Dict:
        config = super().get_config(**kwargs)

        for key, val in kwargs.items():
            if key == "token":
                config["token"] = val
            else:
                pass

        return config


    def _create_session(self) -> Session:
        session = super()._create_session()

        # Set authentication token
        if self.config.get("token"):
            session.headers["Authorization"] = f"token {self.config['token']}"

        return session


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
        if "id" in kwargs:
            id = str(kwargs["id"])
            if not id.isnumeric():
                raise ValueError("Invalid id")
        elif "url" in kwargs:
            parts = urlparse(kwargs["url"]).path.strip("/").split("/")
            if parts[-1].isnumeric():
                if parts[-2].isnumeric():
                    id = parts[-2]
                    version = parts[-1]
                else:
                    id = parts[-1]
            else:
                raise ValueError("Invalid URL address")
        elif "doi" in kwargs:
            match = re.search(r"(\.figshare\.|\/)(\d+)(\.v(\d+))?$", kwargs["doi"])
            if match:
                id = match.group(2)
                version = match.group(4)
            else:
                # TODO: Find id from DOI
                # https://docs.figshare.com/#private_articles_search
                raise NotImplementedError
        else:
            raise ValueError("No identifier")
        if version is None and "version" in kwargs and kwargs["version"]:
            version = str(kwargs["version"])
            if not version.isnumeric():
                raise ValueError("Invalid version")
        return {"id": id, "version": version}


    def _get_dataset_hash(self, id: Dict) -> str:
        """Returns hash of the standard dataset identifier.

        Args:
            id (Dict): Standard dataset identifier

        Returns:
            Hash string of the dataset identifier
        """
        if id["version"]:
            return f"{id['id']}_{id['version']}"
        else:
            return id["id"]


    def _get_dataset_details(self, id: Dict) -> Dict:
        """Retrieves details of the dataset.

        Args:
            id (Dict): Standard dataset identifier

        Returns:
            Dictionary of dataset details

        Raises:
            ValueError("Invalid dataset id")
            HTTPError
        """
        endpoints = []
        if id["version"]:
            endpoint = f"articles/{id['id']}/versions/{id['version']}"
        else:
            endpoint = f"articles/{id['id']}"
        endpoints.append(endpoint)
        if self.config.get("token"):
            endpoints.append(f"account/{endpoint}")

        details = None
        for endpoint in endpoints:
            try:
                details, _ = self._request(endpoint)
                break
            except HTTPError as err:
                if err.response.status_code != 404:
                    raise

        if not details:
            raise ValueError("Invalid dataset id")

        return details


    def _get_account_datasets(self) -> List[RemoteDataset]:
        """Retrieves list of account datasets

        Returns:
            List of datasets related to the account
        """
        if "token" not in self.config:
            return []
        datasets = []
        page = 1
        while True:
            # TODO: Add error handling
            items, _ = self._request(f"account/articles?page={page}&page_size={self.PAGE_SIZE}")
            if not items:
                break
            for item in items:
                id = self.get_dataset_id(**item)
                dataset = RemoteDataset(self, id, {
                    "title": item.get("title"),
                    "url": item.get("url_public_html", item.get("url_private_html")),
                    "doi": item.get("doi"),
                })
                datasets.append(dataset)
            page += 1
        return datasets


    def _get_licenses(self) -> Dict:
        """Retrieves list of available licenses

        License dictionary:
            - id (int): License identifier
            - name (str): Name of the license
            - url (str): URL address of the license

        Returns:
            List of license dictionaries
        """
        # REMARK: Private endpoint returns both public and private licenses
        endpoints = ["account/licenses"] if self.config.get("token") else []
        endpoints.append("licenses")

        for endpoint in endpoints:
            try:
                items, _ = self._request(endpoint)
                break
            except HTTPError as err:
                if err.response.status_code != 403:
                    raise

        licenses = {}

        for item in items:
            licenses[item["value"]] = {
                "id": item["value"],
                "name": item["name"],
                "url": item["url"],
            }

        return licenses


    def _get_categories(self) -> Dict:
        """Retrieves available categories

        Category dictionary:
            - id (int): Category identifier
            - name (str): Name of the category
            - parent_id (int): Parent category identifier
            - source_id (int): Source identifier
            - selectable (bool): True if category is selectable

        Returns:
            Dictionary of category dictionaries. Keys are category identifiers.
        """
        # REMARK: Private endpoint returns both public and private categories
        # REMARK: Public endpoint does not return parent categories
        endpoints = ["account/categories"] if self.config.get("token") else []
        endpoints.append("categories")

        for endpoint in endpoints:
            try:
                items, _ = self._request(endpoint)
                break
            except HTTPError as err:
                if err.response.status_code != 403:
                    raise

        categories = {}

        for item in items:

            categories[item["id"]] = {
                "id": item["id"],
                "name": item["title"],
                "parent_id": item["parent_id"],
                "source_id": item["source_id"],
                "selectable": item["is_selectable"],
            }

        return categories


    def get_categories(self, refresh: bool=False) -> Dict:
        if self._categories is None or refresh:
            self._categories = self._get_categories()
        return self._categories


    @property
    def categories(self) -> Dict:
        return self.get_categories()


    def _get_versions(self, id: Dict) -> OrderedDict:
        """Returns standard dataset identifiers of the dataset versions

        Args:
            id (Dict): Dataset id

        Returns:
            Ordered dictionary of dataset identifiers of the available versions.
            Keys are the versions, values are the dataset identifiers.
        """
        items, _ = self._request(f"articles/{id['id']}/versions")

        versions = OrderedDict()

        for item in items:
            versions[str(item["version"])] = {
                "id": str(id["id"]),
                "version": str(item["version"]),
            }

        return versions


    def _get_metadata(self, id: Dict) -> Dict:
        # Get record details
        details = self._get_dataset_details(id)

        # Set metadata attributes
        attrs = {}

        def _set(key: str, val=None, source_key: str=None):
            attrs[key] = details.get(source_key if source_key else key, val)

        # Common attributes

        # Authors (editable)
        val = PersonList()
        for item in details.get("authors", []):
            person = Person(
                fullname = item.get("full_name"),
                orcid_id = item.get("orcid_id"),
                figshare_id = item.get("id")
            )
            val.append(person)
        attrs["authors"] = val

        # Keywords (editable)
        _set("keywords", [], source_key="tags")

        # Description (editable)
        _set("description", "")

        # Embargo deadline
        _set("embargo_date")

        # License
        val = details.get("license")
        if val:
            licenses = self.get_licenses()
            if isinstance(val, dict):
                if val["value"] in licenses:
                    val = val["name"]
                else:
                    val = {
                        "id": val["value"],
                        "name": val["name"],
                        "url": val["url"],
                    }
            else:
                if val in licenses:
                    val = val["name"]
            attrs["license"] = val

        # References (editable)
        _set("references", [])

        # Title (editable)
        _set("title", "")

        # Digital Object Identifier
        _set("doi")

        # Record type (editable)
        val = details.get("defined_type_name")
        if val in self.record_type_lookup:
            val = self.record_type_lookup[val]
        attrs["type"] = val

        # Access type (editable)
        val = "open"
        if details.get("is_embargoed"):
            if details.get("embargo_date") == 0:
                val = "closed"
            elif details.get("embargo_options"):
                val = "restricted"
            else:
                val = "embargoed"
        attrs["access_type"] = val

        # Client-specific attributes

        # Custom fields (editable)
        val = {}
        for item in details.get("custom_fields", []):
            val[item["name"]] = item["value"]
        attrs["custom_fields"] = val

        # Embargo options
        _set("embargo_options")

        # Embargo type
        _set("embargo_type")

        # Funding (editable)
        _set("funding")

        # Funding list (editable)
        # TODO: Funding ids should be made human-friendly.
        # REMARK: There is only funding search endpoint available.
        # https://docs.figshare.com/#private_funding_search
        _set("funding_list")

        # Embargo title
        _set("embargo_title")

        # Embargo reason
        _set("embargo_reason")

        # Categories
        # REMARK: Categories can be made human-friendly only if original repository is used
        val = []
        categories = self.get_categories()
        for item in details.get("categories", []):
            val.append(categories[item["id"]]["name"] if item["id"] in categories else item["id"])
        attrs["categories"] = val

        # Timeline
        val = details.get("timeline", {})
        if "firstOnline" in val:
            attrs["online_date"] = val["firstOnline"]
        if "publisherPublication" in val:
            attrs["publication_date"] = val["publisherPublication"]
        if "publisherAcceptance" in val:
            attrs["acceptance_date"] = val["publisherAcceptance"]

        # Ignored attributes:
        #
        # - account_id
        # - figshare_url
        # - resource_title: not applicable for regular users
        # - resource_doi: not applicable for regular users
        # - files
        # - citation
        # - confidential_reason (DEPRECATED)
        # - is_confidential (DEPRECATED)
        # - size
        # - version
        # - is_active
        # - is_metadata_record
        # - metadata_reason
        # - status
        # - is_embargoed
        # - is_public
        # - modified_date
        # - created_date
        # - has_linked_file
        # - id
        # - handle: not applicable for regular users
        # - group_id: not applicable for regular users
        # - url: not needed
        # - url_public_html: not needed
        # - url_public_api: not needed
        # - url_private_html: not needed
        # - url_private_api: not needed
        # - published_date: Posted date
        # - thumb: Thumbnail image (not needed)
        # - defined_type: Type of article identifier (`defined_type_name` is used)
        # - timeline.posted: Posted date (not editable)
        # - timeline.submission: Submission date in curation (not editable)
        # - timeline.revision: Revision date from curation (not editable)

        # Return metadata attributes
        return attrs


    def save_metadata(self, id: Dict, metadata: Metadata) -> None:
        """Saves metadata of the specified dataset

        Args:
            id (Dict): Standard dataset id
            metadata (Metadata): Metadata to be saved

        Returns:
            None

        Raises:
            ValueError("No access token")
        """
        # Raise exception if no access token
        if not self.config.get("token"):
            raise ValueError("No access token")

        # Serialize metadata
        data = self._serialize_metadata(metadata)

        # REMARK: More than 10 authors is not supported while setting metadata
        # https://docs.figshare.com/#private_article_create (see Body Schema)
        if len(data["authors"]) > 10:
            authors = data["authors"]
            del data["authors"]
        else:
            authors = []

        # Save metadata
        try:
            result, _ = self._request(f"account/articles/{id['id']}", "PUT", data=data)

        except HTTPError as err:
            # TODO: Add error handling
            print(err.response.content)
            raise

        # Add article authors if required
        # https://docs.figshare.com/#private_article_authors_add
        if authors:
            try:
                result, _ = self._request(f"account/articles/{id['id']}/authors", "POST", data={"authors": authors})

            except HTTPError as err:
                # TODO: Add error handling
                print(err.response.content)
                raise

        # Set embargo attributes

        # REMARK: Setting an article under whole embargo does not imply that
        #   the article will be published when the embargo will expire. You
        #   must explicitly call the publish endpoint to enable this
        #   functionality.
        # https://docs.figshare.com/#private_article_embargo_update

        access_type = metadata.get("access_type", "open")

        if access_type == "open":
            try:
                result, _ = self._request(f"account/articles/{id['id']}/embargo", "DELETE")

            except HTTPError as err:
                # TODO: Add error handling
                print(err.response.content)
                raise
        else:
            data = {
                "is_embargoed": True,
                "embargo_type": metadata.get("embargo_type", "article"),
                "embargo_title": metadata.get("embargo_title", ""),
                "embargo_reason": metadata.get("embargo_reason", ""),
                "embargo_date": metadata.get("embargo_date", ""),
                "embargo_options": metadata.get("embargo_options", []),
            }
            if access_type == "closed":
                data["embargo_date"] = "0"
            elif access_type == "restricted":
                # REMARK: `embargo_options` should be set if restricted access
                pass

            try:
                result, _ = self._request(f"account/articles/{id['id']}/embargo", "PUT", data=data)

            except HTTPError as err:
                # TODO: Add error handling
                print(err.response.content)
                raise


    def validate_metadata(self, metadata: Metadata) -> Dict:
        result = {}

        if not metadata.get("title"):
            result["title"] = "Title is required."

        return result


    def get_files(self, id: Dict) -> List[RemoteFile]:
        # REMARK: Uses article details endpoint instead of files endpoint to support versions
        details = self._get_dataset_details(id)
        if "files" not in details:
            return []
        files = []
        for item in details["files"]:
            file = RemoteFile(
                url=item["download_url"],
                id=item["id"],
                path=item["name"],
                size=item["size"],
                md5=item["computed_md5"],
            )
            files.append(file)
        return files


    def _get_license_id(self, license) -> int:
        """Returns license id from license information, e.g. name, url, id

        Args:
            license : License information

        Returns:
            License id

        Raises:
            ValueError("Invalid license")
        """
        if not license:
            return None
        elif isinstance(license, int):
            return license
        elif isinstance(license, str):
            if license.isnumeric():
                return int(license)
            for id, item in self.get_licenses().items():
                if license == item["name"] or license == item["url"]:
                    return id
        elif isinstance(license, dict):
            return license["id"]
        raise ValueError("Invalid license")


    def _serialize_metadata(self, metadata: Metadata) -> Dict:
        """Serializes dataset metadata for client use

        Args:
            metadata (Metadata): Dataset metadata

        Returns:
            Client-specific dictionary of the metadata
        """
        out = {}

        def _serialize(key: str, target_key=None):
            if key in metadata:
                out[key] = metadata[target_key if target_key else key]

        def _serialize_person(person: Person) -> Dict:
            try:
                if person["figshare_id"]:
                    return {"id": person["figshare_id"]}
            except:
                pass

            item = {}
            # TODO: Check if first_name and last_name are ignored if name
            #   is specified.
            if "fullname" in person:
                item["name"] = person["fullname"]
            if "name" in person:
                item["first_name"] = person["name"]
            if "surname" in person:
                item["last_name"] = person["surname"]
            # REMARK: `email` is not supported (422 Client Error: Unprocessable Entity)
            if "orcid_id" in person:
                item["orcid_id"] = person["orcid_id"]
            return item

        # Title
        _serialize("title")

        # Description
        _serialize("description")

        # Keywords
        _serialize("keywords")

        # References
        _serialize("references")

        # TODO: Serialize "categories"

        # Authors
        out["authors"] = [_serialize_person(item) for item in metadata.get("authors", [])]

        # TODO: Serialize "custom_fields"

        # Record type
        type = metadata.get("type")
        if type:
            for key, val in self.record_type_lookup.items():
                if type == val:
                    type = key
                    break
            # REMARK: Figshare doesn't have "other" type. Therefore,
            #   `defined_type` is set only if `type` is a valid Figshare type.
            if type in self.record_types:
                out["defined_type"] = type
            else:
                # REMARK: POTENTIAL DATA LOSS!
                warnings.warn("Unknown dataset type, `defined_type` is not set.")

        # Funding
        _serialize("funding")

        # TODO: Serialize "funding_list"

        # License
        license = self._get_license_id(metadata.get("license"))
        if license:
            out["license"] = license

        # Timeline
        timeline = {}
        if "publication_date" in metadata:
            timeline["publisherPublication"] = metadata["publication_date"]
        if "acceptance_date" in metadata:
            timeline["publisherAcceptance"] = metadata["acceptance_date"]
        if "online_date" in metadata:
            timeline["firstOnline"] = metadata["online_date"]
        if timeline:
            out["timeline"] = timeline

        return out


    def _create_dataset(self, metadata: Metadata) -> Dict:
        """Creates a dataset with the specified standard metadata

        Args:
            metadata (Metadata): Standard metadata

        Returns:
            Standard identifier of the dataset

        Raises:
            ValueError("No access token")
        """
        # Raise exception if no access token
        if not self.config.get("token"):
            raise ValueError("No access token")

        # Create dataset with minimum metadata
        try:
            result, _ = self._request("account/articles", "POST", data={"title": metadata.get("title", "")})

        except HTTPError as err:
            # TODO: Add error handling
            raise

        # Get dataset id
        id = self.get_dataset_id(result["entity_id"])

        # Save metadata
        try:
            self.save_metadata(id, metadata)

        except:
            self.delete_dataset(id)
            raise

        # Return dataset id
        return id


    def _upload_file(self, id: Dict, file: LocalFile, notify: Callable=None) -> RemoteFile:
        # REMARK: Figshare does not have a versioned endpoint
        if id["version"]:
            raise ValueError("Uploading file to a versioned dataset is not supported")

        # REMARK: Figshare does not allow uploading of empty files
        if not file.size:
            raise ValueError("Uploading an empty file is not supported")

        # Initiate file upload
        result, _ = self._request(
            endpoint=f"account/articles/{id['id']}/files",
            method="POST",
            data={
                "name": file.path,
                "size": file.size,
                "md5": file.md5,
            }
        )

        # TODO: Add response code check if required (201 = Created)

        # Get file id
        file_id = result["location"].split("/")[-1]
        if not file_id.isnumeric():
            raise ValueError("Invalid file id")

        # Get upload token and URL
        result, _ = self._request(f"account/articles/{id['id']}/files/{file_id}")

        # REMARK: Upload URL includes the upload token
        upload_url = result["upload_url"]

        with open(file.fullpath, "rb") as stream:

            tries = 0
            current_size = 0

            while True:
                # Get upload information
                response = requests.get(upload_url)
                response.raise_for_status()

                info = response.json()

                done = True
                locked = False

                for part in info["parts"]:

                    if part["status"] == "COMPLETE":
                        continue

                    if part["locked"]:
                        done = False
                        locked = True
                        continue

                    part_size = part["endOffset"] - part["startOffset"] + 1

                    stream.seek(part["startOffset"])
                    data = stream.read(part_size)

                    response = requests.put(f"{upload_url}/{part['partNo']}", data=data)
                    response.raise_for_status()

                    current_size += part_size

                    if notify:
                        notify(file, current_size)

                if done:
                    break

                if locked:
                    time.sleep(self.LOCKED_SLEEP)
                    tries += 1
                    if tries == self.LOCKED_TRIES:
                        # TODO: Clean up (e.g. remove uploaded parts)
                        raise IOError("Too many tries to upload a part")

        # REMARK: POST request does not return a valid JSON content, therefore raw content is used
        result, response = self._request(f"account/articles/{id['id']}/files/{file_id}", "POST", format="raw")
        if response.status_code != 202:
            raise IOError("File upload cannot be completed")

        result, _ = self._request(f"account/articles/{id['id']}/files/{file_id}")

        remote_file = RemoteFile(
            url=result["download_url"],
            id=result["id"],
            path=result["name"],
            size=result["size"],
            md5=result["computed_md5"],
        )

        return remote_file


    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
        # REMARK: Figshare does not have a versioned endpoint
        if id["version"]:
            raise ValueError("Deleting file from a versioned dataset is not supported")

        if not file.id:
            raise ValueError("No file id")

        result, response = self._request(f"account/articles/{id['id']}/files/{file.id}", "DELETE")


    def _delete_dataset(self, id: Dict) -> None:
        """Deletes dataset specified by the standard identifier from the repository

        Args:
            id (Dict): Standard dataset identifier

        Returns:
            None

        Raises:
            ValueError("Operation not permitted")
            ValueError("Invalid dataset id")
        """
        # REMARK: Only private articles can be deleted
        # https://help.figshare.com/article/ive-accidentally-set-my-data-to-public-what-should-i-do

        # REMARK: Specific versions cannot be deleted
        # https://help.figshare.com/article/can-i-edit-or-delete-my-research-after-it-has-been-made-public
        if id.get("version"):
            versions = self._get_versions(id)
            last_version = next(reversed(versions))
            if id["version"] != last_version:
                raise ValueError("Operation not permitted")

        try:
            result, response = self._request(f"account/articles/{id['id']}", "DELETE")

        except HTTPError as err:
            if err.response.status_code == 403:
                raise ValueError("Operation not permitted")
            elif err.response.status_code == 404:
                raise ValueError("Invalid dataset id")
            raise


    def get_details(self, id: Dict) -> Dict:
        """Returns standard details of the specified dataset.

        Details dictionary:
            - title (str): Title
            - url (str): URL address
            - doi (str): DOI
            - status (str): Status
            - size (int): Total size of data files in bytes
            - created (datetime.datetime): Creation date and time
            - modified (datetime.datetime): Last modification date and time

        Possible statuses are as follows:
            - "draft": Dataset is not published yet.
            - "public": Dataset is published and is publicly available.
            - "embargoed": Dataset is published, but is under embargo.
            - "restricted": Dataset is published, but accessible only under certain conditions.
            - "closed": Dataset is published, but accessible only by the owners.
            - "unknown": Dataset is in an unknown state.

        Args:
            id (Dict): Standard dataset id

        Returns:
            Details dictionary of the dataset.
        """
        details = self._get_dataset_details(id)

        # REMARK: figshare API documentation does not provide information on
        # possible status values.
        status = details["status"]

        if status == "draft":
            pass

        elif status == "public":

            if details["is_embargoed"]:
                if details["embargo_date"]:
                    status = "restricted" if details["embargo_options"] else "embargoed"
                else:
                    status = "restricted" if details["embargo_options"] else "closed"

            # REMARK: is_confidential flag is deprecated
            # https://docs.figshare.com/#private_article_confidentiality_details
            elif details["is_confidential"]:
                status = "restricted"

            # REMARK: There doesn't seem to be additional flags, but testing is
            # required.
            else:
                status = "public"

        else:
            status = "unknown"

        # Calculate data size
        size = 0
        for file in details.get("files", []):
            size += file["size"]

        # REMARK: dateutil.parser is required, because figshare dates are not
        # fully ISO 8601 compliant (there is a timezone indicator at the end).
        return {
            "title": details["title"],
            "url": details["url_public_html"] if "url_public_html" in details else details["url_private_url"],
            "doi": details["doi"],
            "status": status,
            "size": size,
            "created": dateutil.parser.isoparse(details["created_date"]),
            "modified": dateutil.parser.isoparse(details["modified_date"]),
        }


    @classmethod
    def supports_folder(cls) -> bool:
        return False