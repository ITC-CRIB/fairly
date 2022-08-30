from typing import Dict, List, Callable

from . import Client
from ..metadata import Metadata
from ..person import Person
from ..dataset.remote import RemoteDataset
from ..file.local import LocalFile
from ..file.remote import RemoteFile

from urllib.parse import urlparse
from requests import Session
from requests.exceptions import HTTPError
from collections import OrderedDict
from requests_toolbelt.multipart.encoder import MultipartEncoderMonitor

CLASS_NAME = "ZenodoClient"

class ZenodoClient(Client):

    PAGE_SIZE = 100

    upload_types = {
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

    grant_doi_prefixes: {
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
        if "token" in self.config:
            session.headers["Authorization"] = f"Bearer {self.config['token']}"

        return session


    def _get_dataset_id(self, **kwargs) -> Dict:
        """

        Returns:
          Dataset identifier

        Raises:
          ValueError

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
            # TODO: Find id from DOI
            # https://docs.figshare.com/#private_articles_search
            raise NotImplementedError
        else:
            raise ValueError("No identifier")
        return {"id": id}


    def _get_dataset_hash(self, id: Dict) -> str:
        return id["id"]


    def _create_dataset(self, metadata: Metadata) -> RemoteDataset:
        raise NotImplementedError


    def _get_entities(self, endpoint: str, page_size: int=None, process: Callable=None):
        """Retrieves all entities available at the specified endpoint

        Arguments:
            endpoint (str) : Path of the endpoint

            page_size (int) : Page size for each retrieval step. Default page
                size is used if set to None. Page size is set to the number of
                records if set to 0 (zero).

            process (Callable): Callback function to process each entity.
                Retrieved entity is provided as the argument and returned value
                is stored as the entity. Retrieval is terminated if returned
                value is False.

        """
        # Set default page size if required
        if page_size is None or page_size < 0:
            page_size = self.PAGE_SIZE

        # Set page size to retrieve all records at once if required
        if page_size == 0:
            content, _ = self._request(f"{endpoint}?page=1&size=1")
            if not content or not content["hits"]:
                raise ValueError("Invalid endpoint")
            page_size = content["hits"]["total"]

        page = 1
        entities = []

        while True:

            try:
                content, _ = self._request(f"{endpoint}?page={page}&size={page_size}")

            except HTTPError as err:
                if page > 1 and err.response.status_code in [400, 403, 404]:
                    break
                raise

            if not content or not content["hits"] or not content["hits"]["hits"]:
                break

            for item in content["hits"]["hits"]:
                if process:
                    entity = process(item)
                    if item is False:
                        break
                else:
                    entity = item
                entities.append(entity)
            else:
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
            page += 1
        return datasets


    def _get_dataset_details(self, id: Dict) -> Dict:
        endpoints = [f"records/{id['id']}"]
        if "token" in self.config:
            endpoints.insert(0, f"deposit/depositions/{id['id']}")

        details = None
        for endpoint in endpoints:
            try:
                details, _ = self._request(endpoint)
                break
            except HTTPError as err:
                if err.response.status_code in [403, 404]:
                    continue
                raise

        if not details:
            raise ValueError("Invalid dataset id")

        return details


    def _get_licenses(self) -> List[Dict]:
        """Retrieves the list of available licenses

        License dictionary:
            - id (str) : Unique id
            - name (str) : Name of the license
            - url (str) : URL address of the license (optional)

        For the complete list of data fields check the JSON schema available at:
        http://zenodo.org/schemas/licenses/license-v1.0.0.json

        Returns:
            List of license dictionaries

        Raises:
            None
        """
        # REMARK: It looks like license names are not unique
        return self._get_entities("licenses", page_size = 0, process=lambda item : {
            "id": item["metadata"]["id"],
            "name": item["metadata"]["title"],
            "url": item["metadata"]["url"],
        })


    def get_communities(self) -> List[Dict]:
        """Retrieves the list of available communities

        WARNING: This is a slow function due to downloads

        Community dictionary:
            - id (str) : Unique id
            - name (str) : Name of the community
            - url (str) : URL address of the community page at Zenodo
            - logo_url (str) : URL address of the community logo
            - created (str) : Creation date of the community
            - last_record_accepted (str) : Date of the last record accepted
            - description (str) : Short description of the community
            - about (str) : Long description of the community
            - curation_policy (str) : Curation policy of the community

        Returns:
            List of community dictionaries

        Raises:
            None
        """
        return self._get_entities("communities", page_size=2000, process=lambda item : {
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
        return self._get_entities("funders", page_size=2000, process=lambda item : {
            # REMARK: Zenodo uses DOI to identify funders
            "id": item["metadata"]["doi"],
            "name": item["metadata"]["name"],
            "type": item["metadata"]["type"],
            "subtype": item["metadata"]["subtype"],
            "country": item["metadata"]["country"],
            "acronyms": item["metadata"]["acronyms"],
        })

    def _get_categories(self) -> List:
        # REMARK: Zenodo does not have an endpoint to list recognized categories
        return {}


    def _get_versions(self, id: Dict) -> OrderedDict:
        details = self._get_dataset_details(id)
        query=f"q=conceptrecid:{details['conceptrecid']}&all_versions=true&sort=version"
        endpoints = [f"records/?{query}"]
        if "token" in self.config:
            endpoints.insert(0, f"deposit/depositions/?{query}")
        versions = OrderedDict()
        for endpoint in endpoints:
            try:
                page = 1
                while True:
                    items, _ = self._request(f"{endpoint}&page={page}&size={self.PAGE_SIZE}")
                    if not items or not items["hits"]["hits"]:
                        break
                    for item in items["hits"]["hits"]:
                        versions[item["metadata"]["version"]] = {"id": item["id"]}
                    page += 1
                break
            except HTTPError as err:
                if err.response.status_code in [403, 404]:
                    continue
                raise
        return versions


    def get_metadata(self, id: Dict) -> Metadata:
        details = self._get_dataset_details(id)

        _metadata = details["metadata"]

        # Set standard metadata fields
        metadata = {
        }

        # Set repository-specific metadata fields
        metadata["zenodo"] = {
            "prereserve_doi": _metadata["prereserve_doi"],
            "notes": _metadata["notes"],
            "related_identifiers": _metadata["related_identifiers"],
            "contributors": _metadata["contributors"],
        }

        # Set thesis metadata fields if required
        if _metadata["publication_type"] == "thesis":
            metadata["zenodo"]["thesis"] = {
                "supervisors": _metadata["thesis_supervisors"],
                "university": _metadata["thesis_university"],
            }

        return Metadata(**metadata)


    def _serialize_persons(self, persons: List[Person]) -> List[Dict]:
        out = []

        for person in persons:
            item = {}

            if person.name:
                if person.surname:
                    item["name"] = f"{person.surname}, {person.name}"
                else:
                    item["name"] = person.name
            elif person.surname:
                item["name"] = person.surname
            else:
                item["name"] = person.fullname

            if person.institution:
                item["affiliation"] = person.institution

            if person.orcid_id:
                item["orcid"] = person.orcid_id

            out.append(item)

        return out

    def _serialize_metadata(self, metadata: Metadata) -> Dict:
        out = {}

        def _serialize(key: str, default: None):
            if key in metadata:
                out[key] = metadata[key]
            elif default is not None:
                out[key] = default

        _serialize("title", "")

        _serialize("description", "")

        out["authors"] = self._serialize_persons(metadata.get("authors", []))

        out["contributors"] = self._serialize_persons(metadata.get("contributors", []))

        type = metadata.get("type")

        if type in self.image_types:
            out["upload_type"] = "image"
            out["image_type"] = type

        elif type in self.publication_types:
            out["upload_type"] = "publication"
            out["publication_type"] = type

        else:
            out["upload_type"] = type
            if type == "image":
                out["image_type"] = "other"
            elif type == "publication":
                out["publication_type"] = "other"

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

        # TODO: Serialize "communities"
        # TODO: Serialize "grants"
        # TODO: Serialize "related_identifiers"
        # TODO: Serialize "locations"
        # TODO: Serialize "dates"

        _serialize("method")

        if type in {"book", "report", "section"}:
            _serialize("imprint_publisher")
            _serialize("imprint_place")
            _serialize("imprint_isbn")

        if type == "section":
            _serialize("partof_title")
            _serialize("partof_pages")

        if type == "conferencepaper":
            _serialize("conference_title")
            _serialize("conference_acronym")
            _serialize("conference_dates")
            _serialize("conference_place")
            _serialize("conference_url")
            _serialize("conference_session")
            _serialize("conference_session_part")

        if type == "article":
            _serialize("journal_title")
            _serialize("journal_volume")
            _serialize("journal_issue")
            _serialize("journal_pages")

        if type == "thesis":
            _serialize("thesis_university")
            out["thesis_supervisors"] = self._serialize_persons(metadata.get("thesis_supervisors", []))

        return out


    def set_metadata(self, id: Dict, metadata: Metadata) -> None:
        raise NotImplementedError


    def validate_metadata(self, metadata: Metadata) -> Dict:
        result = {}

        if not metadata.get("title"):
            result["title"] = "Title is required."

        if not metadata.get("authors"):
            result["authors"] = "At least one author is required."

        if not metadata.get("description"):
            results["description"] = "Description is required."

        if not metadata.get("access_type"):
            results["access_type"] = "Access type is required."

        if not metadata.get("license"):
            if metadata["access_type"] in ["open", "embargoed"]:
                results["license"] = "License if required."
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

        return remote_file


    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
        if not file.id:
            raise ValueError("No file id")

        result, response = self._request(f"deposit/depositions/{id['id']}/files/{file.id}", "DELETE")