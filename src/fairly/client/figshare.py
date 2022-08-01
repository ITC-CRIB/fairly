from typing import List, Dict, Callable

from . import Client
from ..metadata import Metadata
from ..dataset.remote import RemoteDataset
from ..file.local import LocalFile
from ..file.remote import RemoteFile

from urllib.parse import urlparse
import requests
from requests import Session
from requests.exceptions import HTTPError
from collections import OrderedDict
import time

CLASS_NAME = "FigshareClient"

class FigshareClient(Client):

    PAGE_SIZE = 25

    LOCKED_SLEEP = 5
    LOCKED_TRIES = 5
    

    def __init__(self, repository_id: str=None, **kwargs):
        # Call parent method
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
            session.headers["Authorization"] = f"token {self.config['token']}"

        return session


    def _get_dataset_id(self, **kwargs) -> Dict:
        """

        Returns:
          Dataset identifier

        Raises:
          ValueError

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
        if id["version"]:
            return f"{id['id']}_{id['version']}"
        else:
            return id["id"]


    def _get_dataset_details(self, id: Dict) -> Dict:
        endpoints = []
        if id["version"]:
            endpoint = f"articles/{id['id']}/versions/{id['version']}"
        else:
            endpoint = f"articles/{id['id']}"
        endpoints.append(endpoint)
        if "token" in self.config:
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
                dataset = RemoteDataset(self, id)
                datasets.append(dataset)
            page += 1
        return datasets


    def _get_licenses(self) -> List:
        # REMARK: Private endpoint returns both public and private licenses
        endpoint = "account/licenses" if "token" in self.config else "licenses"
        licenses = []
        for item, _ in self._request(endpoint):
            licenses.append({
                "name": item["name"],
                "id": item["value"],
                "url": item["url"],
            })
        return licenses


    def _get_categories(self) -> List:
        # REMARK: Private endpoint returns both public and private categories
        # REMARK: Public endpoint does not return parent categories
        endpoint = "account/categories" if "token" in self.config else "categories"
        categories = []
        for item, _ in self._request(endpoint):
            categories.append({
                "name": item["title"],
                "id": item["id"],
                "parent_id": item["parent_id"],
                "selectable": item["is_selectable"],
            })
        return categories


    def _get_versions(self, id: Dict) -> OrderedDict:
        versions = OrderedDict()
        items, _ = self._request(f"articles/{id['id']}/versions")
        for item in items:
            versions[item["version"]] = {
                "id": id["id"],
                "version": item["version"],
            }
        return versions


    def get_metadata(self, id: Dict) -> Metadata:
        details = self._get_dataset_details(id)
        metadata = {}
        for key, val in details.items():
            if key == "files":
                continue
            elif key == "authors":
                authors = []
                for author in val:
                    authors.append({
                        "fullname": author["full_name"],
                        "orcid_id": author["orcid_id"],
                    })
                val = authors
            metadata[key] = val
        return Metadata(**metadata)


    def set_metadata(self, id: Dict, metadata: Metadata) -> None:
        data = metadata.serialize()

        try:
            result = self._request(f"account/articles/{id['id']}", "PUT", data=data)

        except HTTPError as err:
            # TODO: Error handling
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


    def _create_dataset(self, metadata: Metadata) -> RemoteDataset:
        if not self.config.get("token"):
            raise ValueError("No access token")

        if metadata is None:
            metadata = Metadata()
        elif not isinstance(metadata, Metadata):
            raise ValueError("Invalid metadata")

        result = self.validate_metadata(metadata)
        if result:
            raise ValueError("Invalid metadata", result)

        data = metadata.serialize()

        try:
            result, _ = self._request("account/articles", "POST", data=data)

        except HTTPError as err:
            # TODO: Error handling
            raise

        dataset = self.get_dataset(result["entity_id"])

        return dataset


    def _upload_file(self, id: Dict, file: LocalFile, notify: Callable=None) -> RemoteFile:
        # REMARK: Figshare does not have a versioned endpoint
        if id["version"]:
            raise ValueError("Uploading file to a versioned dataset is not supported")

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
            total_size = 0
            
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
                    
                    total_size += part_size
                    
                    if notify:
                        notify(file, total_size)
                
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