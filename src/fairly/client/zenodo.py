from typing import Dict, List, Callable

from . import Client
from ..metadata import Metadata
from ..person import Person, PersonList
from ..dataset.remote import RemoteDataset
from ..file.local import LocalFile
from ..file.remote import RemoteFile

import re
from urllib.parse import urlparse
from requests import Session
from requests.exceptions import HTTPError
from collections import OrderedDict
from requests_toolbelt.multipart.encoder import MultipartEncoderMonitor
from datetime import datetime

CLASS_NAME = "ZenodoClient"

class ZenodoClient(Client):

    """
    Attributes:
        _details (Dict): Record details cache
    """

    PAGE_SIZE = 100

    KEEP_ALIVE = 10

    record_types = {
        "dataset": "Dataset",
        "image": "Image",
        "lesson": "Lesson",
        "physicalobject": "Physical object",
        "poster": "Poster",
        "presentation": "Presentation",
        "publication": "Publication",
        "software": "Software",
        "video": "Video/Audio",
        "other": "Other",
    }

    publication_types = {
        "annotationcollection": "Annotation collection",
        "article": "Journal article",
        "book": "Book",
        "conferencepaper": "Conference paper",
        "datamanagementplan": "Data management plan",
        "deliverable": "Project deliverable",
        "milestone": "Project milestone",
        "patent": "Patent",
        "preprint": "Preprint",
        "proposal": "Proposal",
        "report": "Report",
        "section": "Book section",
        "softwaredocumentation": "Software documentation",
        "taxonomictreatment": "Taxonomic treatment",
        "technicalnote": "Technical note",
        "thesis": "Thesis",
        "workingpaper": "Working paper",
    }

    image_types = {
        "diagram": "Diagram",
        "drawing": "Drawing",
        "figure": "Figure",
        "photo": "Photo",
        "plot": "Plot",
    }

    access_rights = {
        "open": "Open Access",
        "embargoed": "Embargoed Access",
        "restricted": "Restricted Access",
        "closed": "Closed Access",
    }

    grant_dois: {
        "10.13039/501100000923": "Australian Research Council",
        "10.13039/501100002428": "Austrian Science Fund",
        "10.13039/501100000780": "European Commission",
        "10.13039/501100000806": "European Environment Agency",
        "10.13039/501100002341": "Academy of Finland",
        "10.13039/501100004488": "Hrvatska Zaklada za Znanost",
        "10.13039/501100001871": "Fundação para a Ciência e a Tecnologia",
        "10.13039/501100004564": "Ministarstvo Prosvete, Nauke i Tehnološkog Razvoja",
        "10.13039/501100006588": "Ministarstvo Znanosti, Obrazovanja i Sporta",
        "10.13039/501100000925": "National Health and Medical Research Council",
        "10.13039/100000002": "National Institutes of Health",
        "10.13039/100000001": "National Science Foundation",
        "10.13039/501100003246": "Nederlandse Organisatie voor Wetenschappelijk Onderzoek",
        "10.13039/501100000690": "Research Councils",
        "10.13039/501100001711": "Schweizerischer Nationalfonds zur Förderung der wissenschaftlichen Forschung",
        "10.13039/501100001602": "Science Foundation Ireland",
        "10.13039/100004440": "Wellcome Trust",
    }

    # REMARK: Some of the relations are the same as Dublin Core properties
    relations: {
        "isCitedBy": "is cited by",
        "cites": "cites",
        "isSupplementTo": "is supplement to",
        "isSupplementedBy": "is supplemented by",
        "isContinuedBy": "is continued by",
        "continues": "continues",
        "isDescribedBy": "is described by",
        "describes": "describes",
        "hasMetadata": "has metadata",
        "isMetadataFor": "is metadata for",
        "isNewVersionOf": "is new version of",
        "isPreviousVersionOf": "is previous version of",
        "isPartOf": "is part of",
        "hasPart": "has part",
        "isReferencedBy": "is referenced by",
        "references": "references",
        "isDocumentedBy": "is documented by",
        "documents": "documents",
        "isCompiledBy": "is compiled by",
        "compiles": "compiles",
        "isVariantFormOf": "is variant form of",
        "isOriginalFormof": "is original form of",
        "isIdenticalTo": "is identical to",
        "isAlternateIdentifier": "is alternative identifier",
        "isReviewedBy": "is reviewed by",
        "reviews": "reviews",
        "isDerivedFrom": "is derived from",
        "isSourceOf": "is source of",
        "requires": "requires",
        "isRequiredBy": "is required by",
        "isObsoletedBy": "is obsoleted by",
        "obsoletes": "obsoletes",
    }


    def __init__(self, repository_id: str=None, **kwargs):
        super().__init__(repository_id, **kwargs)

        self._details = {}


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
            session.headers["Authorization"] = f"Bearer {self.config['token']}"

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

        """
        if "id" in kwargs:
            id = str(kwargs["id"])
            if not id.isnumeric():
                raise ValueError("Invalid id")
        elif "url" in kwargs:
            parts = urlparse(kwargs["url"]).path.strip("/").split("/")
            if parts[-1].isnumeric():
                id = parts[-1]
            else:
                raise ValueError("Invalid URL address")
        elif "doi" in kwargs:
            # REMARK: zenodo in the regular expression may not be always valid
            match = re.search(r"\/zenodo\.(\d+)$", kwargs["doi"])
            if match:
                id = match.group(1)
            else:
                raise ValueError("Invalid DOI")
        else:
            raise ValueError("No identifier")
        return {"id": id}


    def _get_dataset_hash(self, id: Dict) -> str:
        """Returns hash of the standard dataset identifier

        Args:
            id (Dict): Standard dataset identifier

        Returns:
            Hash string of the dataset identifier
        """
        return id["id"]


    def _set_details(self, id: Dict, details: Dict) -> None:
        """Stores dataset details in the cache.

        Args:
            id (Dict): Standard dataset id.
            details (Dict): Dataset details. Set None to clear the cached details.

        Returns:
            None
        """
        hash = self._get_dataset_hash(id)

        if details:
            self._details[hash] = [details, datetime.now()]

        else:
            if hash in self._details:
                del self._details[hash]


    def _get_details(self, id: Dict) -> Dict:
        """Returns cached dataset details.

        Args:
            id (Dict): Standard dataset id.

        Returns:
            Dataset details dictionary if cache is valid, None otherwise.
        """
        hash = self._get_dataset_hash(id)

        if hash not in self._details:
            return None

        details, time = self._details[hash]

        if (datetime.now() - time).total_seconds() > self.KEEP_ALIVE:
            del self._details[hash]
            return None

        return details


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

        # Create empty dataset
        try:
            result, _ = self._request("deposit/depositions", "POST", data={})

        except HTTPError as err:
            # TODO: Add error handling
            raise

        # Get dataset id
        id = self.get_dataset_id(result["id"])

        # Save metadata
        try:
            self.save_metadata(id, metadata)

        except:
            self.delete_dataset(id)
            raise

        return id


    def _get_entities(self, endpoint: str, page_size: int=None, key: str=None, process: Callable=None):
        """Retrieves all entities available at the specified endpoint

        Args:
            endpoint (str): Path of the endpoint

            page_size (int): Page size for each retrieval step. Default page
                size is used if set to None.

            process (Callable): Callback function to process each entity.
                Retrieved entity is provided as the argument and returned value
                is stored as the entity. Retrieval is terminated if returned
                value is False.

        """
        # Set argument separator
        sep = "&" if "?" in endpoint else "?"

        # Set default page size if required
        if page_size is None or page_size < 0:
            page_size = self.PAGE_SIZE

        page = 1
        entities = {} if key else []

        while True:

            try:
                content, _ = self._request(f"{endpoint}{sep}page={page}&size={page_size}")

            except HTTPError as err:
                if page > 1 and err.response.status_code in [400, 403, 404]:
                    break
                raise

            if not content:
                break

            if isinstance(content, list):
                items = content
            elif not content["hits"] or not content["hits"]["hits"]:
                break
            else:
                items = content["hits"]["hits"]

            for item in items:
                if process:
                    entity = process(item)
                    if item is False:
                        break
                else:
                    entity = item

                if key:
                    entities[entity[key]] = entity
                else:
                    entities.append(entity)

            else:
                if len(entities) < page_size:
                    break

                page += 1
                continue
            break

        return entities


    def _get_account_datasets(self) -> List[RemoteDataset]:
        if "token" not in self.config:
            return []

        datasets = []
        page = 1
        while True:
            # TODO: Add error handling
            items, _ = self._request(f"deposit/depositions?page={page}&page_size={self.PAGE_SIZE}")

            if not items:
                break

            for item in items:
                id = self.get_dataset_id(**item)
                dataset = RemoteDataset(self, id)
                datasets.append(dataset)

                # Store details
                self._set_details(id, item)

                # Prevent unnecessary requests by triggering the use of available details
                dataset.title
                dataset.metadata
                dataset.files

            if len(items) < self.PAGE_SIZE:
                break

            page += 1

        return datasets


    def _get_dataset_details(self, id: Dict) -> Dict:
        """Retrieves dataset details

        Args:
            id (Dict): Standard dataset id

        Returns:
            Dictionary of dataset details

        Raises:
            ValueError("Invalid dataset id")
        """
        details = self._get_details(id)
        if details:
            return details

        endpoints = [f"records/{id['id']}"]
        if self.config.get("token"):
            endpoints.insert(0, f"deposit/depositions/{id['id']}")

        details = None
        for endpoint in endpoints:
            try:
                details, _ = self._request(endpoint)
                break
            except HTTPError as err:
                if err.response.status_code in [401, 403, 404]:
                    continue
                raise

        if not details:
            raise ValueError("Invalid dataset id")

        self._set_details(id, details)

        return details


    def _get_licenses(self) -> Dict:
        """Retrieves the list of available licenses

        License dictionary:
            - id (str): Unique id
            - name (str): Name of the license
            - url (str): URL address of the license (optional)

        For the complete list of data fields check the JSON schema available at:
        http://zenodo.org/schemas/licenses/license-v1.0.0.json

        Returns:
            Dictionary of available licenses

        Raises:
            None
        """
        # REMARK: It looks like license names are not unique
        return self._get_entities("licenses", page_size = 2000, key = "id", process=lambda item: {
            "id": item["metadata"]["id"],
            "name": item["metadata"]["title"],
            "url": item["metadata"]["url"],
        })


    def get_communities(self) -> List[Dict]:
        """Retrieves the list of available communities

        WARNING: This is a slow function due to downloads

        Community dictionary:
            - id (str): Unique id
            - name (str): Name of the community
            - url (str): URL address of the community page at Zenodo
            - logo_url (str): URL address of the community logo
            - created (str): Creation date of the community
            - last_record_accepted (str): Date of the last record accepted
            - description (str): Short description of the community
            - about (str): Long description of the community
            - curation_policy (str): Curation policy of the community

        Returns:
            List of community dictionaries

        Raises:
            None
        """
        return self._get_entities("communities", page_size=2000, process=lambda item: {
            "id": item["id"],
            "name": item["title"],
            "url": item["links"]["html"],
            "logo_url": item["logo_url"],
            "created": item["created"],
            "last_record_accepted": item["last_record_accepted"],
            "description": item["description"],
            "about": item["page"],
            "curation_policy": item["curation_policy"],
        })


    def get_funders(self) -> List[Dict]:
        """Retrieves the list of available funders

        WARNING: This is a slow function due to downloads

        Funder dictionary:
            - id (str): Unique id (= DOI)
            - name (str): Name of the funder
            - type (str): Type of the funder
            - subtype (str): Subtype of the funder
            - country (str): Country code of the funder
            - acronyms (list): Acronyms of the funder

        For the complete list of data fields check the JSON schema available at:
        http://zenodo.org/schemas/funders/funder-v1.0.0.json

        Returns:
            List of funder dictionaries

        Raises:
            None
        """
        return self._get_entities("funders", page_size=2000, process=lambda item: {
            # REMARK: Zenodo uses DOI to identify funders
            "id": item["metadata"]["doi"],
            "name": item["metadata"]["name"],
            "type": item["metadata"]["type"],
            "subtype": item["metadata"]["subtype"],
            "country": item["metadata"]["country"],
            "acronyms": item["metadata"]["acronyms"],
        })


    def _get_versions(self, id: Dict) -> OrderedDict:
        """Returns standard dataset identifiers of the dataset versions

        Args:
            id (Dict): Dataset id

        Returns:
            Ordered dictionary of dataset identifiers of the available versions.
            Keys are the versions, values are the dataset identifiers.
        """
        details = self._get_dataset_details(id)

        query=f"?q=conceptrecid:{details['conceptrecid']}&all_versions=true&sort=version"
        endpoints = [f"records/{query}"]
        if self.config.get("token"):
            endpoints.insert(0, f"deposit/depositions/{query}")

        versions = OrderedDict()
        for endpoint in endpoints:
            try:
                items = self._get_entities(endpoint)

            except HTTPError as err:
                if err.response.status_code in [403, 404]:
                    continue
                raise

            for item in items:
                version_id = {"id": item["id"]}

                versions[item["metadata"]["version"]] = version_id

                self._set_details(version_id, item)

        return versions


    def _get_metadata(self, id: Dict) -> Dict:
        # Get dataset details
        details = self._get_dataset_details(id)

        # Get dataset metadata
        metadata = details["metadata"]

        # Set metadata attributes

        # REMARK: Attributes follow the order of the Zenodo API documentation
        # https://developers.zenodo.org/#deposit-metadata
        attrs = {}

        def _set(key: str, val=None, source_key: str=None):
            attrs[key] = metadata.get(source_key if source_key else key, val)

        def _get_person(item: Dict) -> Person:
            return Person(
                fullname = item.get("name"),
                institution = item.get("affiliation"),
                orcid_id = item.get("orcid"),
                gnd_id = item.get("gnd"),
                role = item.get("type")
            )

        # Common attributes

        # Record type
        type = metadata["upload_type"]
        if type == "publication":
            if metadata["publication_type"] != "other":
                type = metadata["publication_type"]
        elif type == "image":
            if metadata["image_type"] != "other":
                type = metadata["image_type"]
        attrs["type"] = type

        # Date of publication in ISO8601 format (YYYY-MM-DD)
        _set("publication_date")

        # Title
        _set("title")

        # List of authors
        attrs["authors"] = PersonList([_get_person(item) for item in metadata.get("creators", [])])

        # Description
        _set("description")

        # Access type
        _set("access_type", source_key="access_right")

        # License (if `access_type` in ["open", "embargoed"])
        _set("license")

        # Embargo deadline (if `access_type` == "embargoed")
        _set("embargo_date")

        # Digital Object Identifier
        _set("doi")

        # Keywords
        _set("keywords", [])

        # Client-specific attributes

        # Access conditions (if `access_type` == "restricted")
        _set("access_conditions")

        # Reserved Digital Object Identifier
        _set("prereserve_doi")

        # Notes
        _set("notes")

        # List of related identifiers [{identifier, relation, resource_type}]
        _set("related_identifiers")

        # List of contributors
        attrs["contributors"] = [_get_person(item) for item in metadata.get("contributors", [])]

        # List of references
        _set("references", [])

        # List of communities the record appear
        attrs["communities"] = [item["identifier"] for item in metadata.get("communities", [])]

        # List of OpenAIRE-supported grants that funded the research
        attrs["grants"] = [item["id"] for item in metadata.get("grants", [])]

        # Journal article attributes
        if type == "article":
            _set("journal_title")
            _set("journal_volume")
            _set("journal_issue")
            _set("journal_pages")

        # Conference paper attributes
        if type == "conferencepaper":
            _set("conference_title")
            _set("conference_acronym")
            _set("conference_dates")
            _set("conference_place")
            _set("conference_url")
            _set("conference_session")
            _set("conference_session_part")

        # Imprint attributes
        if type in {"book", "report", "section"}:
            _set("imprint_publisher")
            _set("imprint_isbn")
            _set("imprint_place")

        # Book section attributes
        if type == "section":
            _set("partof_title")
            _set("partof_pages")

        # Thesis attributes
        if type == "thesis":
            attrs["thesis_supervisors"] = [_get_person(item) for item in metadata.get("thesis_supervisors", [])]
            _set("thesis_university")

        # List of subjects
        attrs["subjects"] = [{"term": item["term"], "identifier": item["identifier"]} for item in metadata.get("subjects", [])]

        # Version
        # REMARK: Zenodo does not use `version` as an identifier
        _set("version")

        # Main language of the record as ISO 639-2 or 639-3 code
        _set("language")

        # List of locations, [{lat, lon, place, description}]
        _set("locations")

        # List of date intervals, [{start, end, type, description}]
        _set("dates")

        # Methodology employed for the research
        _set("method")

        # Return metadata attributes
        return attrs


    def _serialize_persons(self, persons: List[Person]) -> List[Dict]:
        out = []

        for person in persons:
            item = {}

            if "name" in person:
                if "surname" in person:
                    item["name"] = f"{person['surname']}, {person['name']}"
                else:
                    item["name"] = person["name"]
            elif "surname" in person:
                item["name"] = person["surname"]
            else:
                item["name"] = person["fullname"]

            if "institution" in person:
                item["affiliation"] = person["institution"]

            if "orcid_id" in person:
                item["orcid"] = person["orcid_id"]

            out.append(item)

        return out


    def _serialize_metadata(self, metadata: Metadata) -> Dict:
        """Serializes dataset metadata for client use

        Args:
            metadata (Metadata): Dataset metadata

        Returns:
            Client-specific dictionary of the metadata
        """
        out = {}

        def _serialize(key: str, default=None):
            if key in metadata:
                out[key] = metadata[key]
            elif default is not None:
                out[key] = default

        _serialize("title", "")

        _serialize("description", "")

        out["creators"] = self._serialize_persons(metadata.get("authors", []))

        out["contributors"] = self._serialize_persons(metadata.get("contributors", []))

        type = metadata.get("type")

        if type in self.image_types:
            out["upload_type"] = "image"
            out["image_type"] = type

        elif type in self.publication_types:
            out["upload_type"] = "publication"
            out["publication_type"] = type

        else:
            if type:
                out["upload_type"] = type
            if type == "image" or type == "publication":
                out["image_type"] = "other"

        # License
        _serialize("license")

        _serialize("doi")
        # TODO: Serialize "prereserve_doi"

        _serialize("publication_date")

        # REMARK: Version is part of Zenodo metadata
        _serialize("version")

        _serialize("language")

        _serialize("keywords", [])

        # TODO: Serialize "subjects"

        _serialize("references")

        _serialize("notes")

        val = []
        for item in metadata.get("communities", []):
            val.append({"identifier": item})
        out["communities"] = val

        # TODO: Serialize "communities"
        # TODO: Serialize "grants"
        # TODO: Serialize "related_identifiers"
        # TODO: Serialize "locations"
        # TODO: Serialize "dates"

        _serialize("method")

        if type == "article":
            _serialize("journal_title")
            _serialize("journal_volume")
            _serialize("journal_issue")
            _serialize("journal_pages")

        if type == "conferencepaper":
            _serialize("conference_title")
            _serialize("conference_acronym")
            _serialize("conference_dates")
            _serialize("conference_place")
            _serialize("conference_url")
            _serialize("conference_session")
            _serialize("conference_session_part")

        if type in {"book", "report", "section"}:
            _serialize("imprint_publisher")
            _serialize("imprint_place")
            _serialize("imprint_isbn")

        if type == "section":
            _serialize("partof_title")
            _serialize("partof_pages")

        if type == "thesis":
            _serialize("thesis_university")
            out["thesis_supervisors"] = self._serialize_persons(metadata.get("thesis_supervisors", []))

        return out


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
        data = {"metadata": self._serialize_metadata(metadata)}

        # Save metadata
        try:
            result, _ = self._request(f"deposit/depositions/{id['id']}", "PUT", data=data)

        except HTTPError as err:
            if err.response.status_code == 400:
                raise ValueError(err.response.content)
            raise

        # Update details cache
        self._set_details(id, result)


    def validate_metadata(self, metadata: Metadata) -> Dict:
        result = {}

        if not metadata.get("title"):
            result["title"] = "Title is required."

        if not metadata.get("authors"):
            result["authors"] = "At least one author is required."

        if not metadata.get("description"):
            result["description"] = "Description is required."

        if not metadata.get("type"):
            result["type"] = "Type is required."

        if not metadata.get("access_type"):
            result["access_type"] = "Access type is required."

        if not metadata.get("license"):
            if metadata.get("access_type") in ["open", "embargoed"]:
                result["license"] = "License is required."
        else:
            # TODO: Validate license
            pass

        return result


    def get_files(self, id: Dict) -> List[RemoteFile]:
        details = self._get_dataset_details(id)
        if "files" not in details:
            return []
        files = []
        for item in details["files"]:
            # REMARK: Depending on the endpoint file information differs
            if "id" in item:
                file = RemoteFile(
                    id=item["id"],
                    url=item["links"]["download"],
                    path=item["filename"],
                    size=item["filesize"],
                    md5=item["checksum"],
                )
            else:
                file = RemoteFile(
                    url=item["links"]["self"],
                    path=item["key"],
                    size=item["size"],
                    md5=item["checksum"][4:],
                )
            files.append(file)
        return files


    def _upload_file(self, id: Dict, file: LocalFile, notify: Callable=None) -> RemoteFile:
        # REMARK: requests_toolbelt MultipartEncoder is used to stream data
        # ref: https://stackoverflow.com/questions/22915295/python-requests-post-and-big-content
        # ref: https://stackoverflow.com/questions/12385179/how-to-send-a-multipart-form-data-with-requests-in-python

        def _notify(monitor):
            if notify:
                notify(file, monitor.bytes_read)

        encoder = MultipartEncoderMonitor.from_fields(
            fields={
                'file': (file.path, open(file.fullpath, 'rb'), file.type),
            },
            callback=_notify
        )

        # TODO: Add IO error handling
        result, _ = self._request(
            endpoint=f"deposit/depositions/{id['id']}/files",
            method="POST",
            data=encoder,
            serialize=False,
            headers={'Content-Type': encoder.content_type},
        )

        remote_file = RemoteFile(
            url=result["links"]["download"],
            id=result["id"],
            path=result["filename"],
            size=result["filesize"],
            md5=result["checksum"],
        )

        if file.size != remote_file.size or file.md5 != remote_file.md5:
            self._delete_file(id, remote_file)
            raise IOError("Invalid file upload")

        # Invalidate details cache
        self._set_details(id, None)

        return remote_file


    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
        if not file.id:
            raise ValueError("No file id")

        # TODO: Add error handling
        result, response = self._request(f"deposit/depositions/{id['id']}/files/{file.id}", "DELETE")

        # Invalidate details cache
        self._set_details(id, None)


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
        # REMARK: Only unpublished depositions can be deleted
        try:
            result, response = self._request(f"deposit/depositions/{id['id']}", "DELETE")

        except HTTPError as err:
            if err.response.status_code == 403:
                raise ValueError("Operation not permitted")
            elif err.response.status_code == 404:
                raise ValueError("Invalid dataset id")
            raise

        # Invalidate details cache
        self._set_details(id, None)


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
            - "error": Dataset is in an error state.
            - "unknown": Dataset is in an unknown state.

        Args:
            id (Dict): Standard dataset id

        Returns:
            Details dictionary of the dataset.
        """
        details = self._get_dataset_details(id)

        statuses = {
            "inprogress": "draft",
            "unsubmitted": "draft",
            "error": "error",
            "open": "public",
            "embargoed": "embargoed",
            "restricted": "restricted",
            "closed": "closed",
        }
        state = details["state"] if details["state"] != "done" else details["metadata"]["access_right"]
        status = statuses.get(state, "unknown")

        # Calculate data size
        size = 0
        for file in details.get("files", []):
            size += file["filesize"]

        return {
            "title": details["title"],
            "url": details["links"].get("html"),
            "doi": details.get("doi"),
            "status": status,
            "size": size,
            "created": datetime.fromisoformat(details["created"]),
            "modified": datetime.fromisoformat(details["modified"]),
        }


    @classmethod
    def supports_folder(cls) -> bool:
        return False