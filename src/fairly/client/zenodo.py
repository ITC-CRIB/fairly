from typing import Dict, List, Callable

from . import Client
from ..metadata import Metadata
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

    PAGE_SIZE = 25

    upload_types = {
        "publication": "Publication",
        "poster": "Poster",
        "presentation": "Presentation",
        "dataset": "Dataset",
        "image": "Image",
        "video": "Video/Audio",
        "software": "Software",
        "lesson": "Lesson",
        "physicalobject": "Physical object",
        "other": "Other",
    }

    publication_types = {
        "annotationcollection": "Annotation collection",
        "book": "Book",
        "section": "Book section",
        "conferencepaper": "Conference paper",
        "datamanagementplan": "Data management plan",
        "article": "Journal article",
        "patent": "Patent",
        "preprint": "Preprint",
        "deliverable": "Project deliverable",
        "milestone": "Project milestone",
        "proposal": "Proposal",
        "report": "Report",
        "softwaredocumentation": "Software documentation",
        "taxonomictreatment": "Taxonomic treatment",
        "technicalnote": "Technical note",
        "thesis": "Thesis",
        "workingpaper": "Working paper",
        "other": "Other",
    }

    image_types = {
        "figure": "Figure",
        "plot": "Plot",
        "drawing": "Drawing",
        "diagram": "Diagram",
        "photo": "Photo",
        "other": "Other",
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


    def _get_licenses(self) -> List:
        licenses = []
        page = 1
        while True:
            # REMARK: Page size is set to a high number to retrieve all licenses at once, if possible
            # TODO: It looks like license names are not unique, check what we are missing
            items, _ = self._request(f"licenses?page={page}&size=1000")
            if not items or not items["hits"]["hits"]:
                break
            for item in items["hits"]["hits"]:
                licenses.append({
                    "name": item["metadata"]["title"],
                    "id": item["metadata"]["id"],
                    "url": item["metadata"]["url"],
                })
            page += 1
        return licenses


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

        # TODO: Filter raw metadata
        metadata = details["metadata"]

        return Metadata(**metadata)


    def set_metadata(self, id: Dict, metadata: Metadata) -> None:
        raise NotImplementedError


    def validate_metadata(self, metadata: Metadata) -> Dict:
        raise NotImplementedError


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