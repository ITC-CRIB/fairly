"""DataFoundryClient class module."""
from typing import Any, Dict, List, Callable

import logging
import re
import requests
import urllib.parse
from collections import OrderedDict

from . import Client, ClientInfo
from ..metadata import Metadata
from ..dataset.remote import RemoteDataset
from ..file import safe_filename
from ..file.local import LocalFile
from ..file.remote import RemoteFile


CLASS_NAME = 'DataFoundryClient'


class DataFoundryClient(Client):
    """Data Foundry client class.

    Data Foundry uses projects to store multiple datasets. Hence, it has a
    different terminology. This client implementation uses a DF project as a
    fairly dataset, and DF datasets as individual files.
    """
    DOWNLOAD_TYPES = {
        'json': 'application/json',
        'csv': 'text/csv',
    }

    # REMARK: https://datafoundry.io.tudelft.nl/documentation/datasets
    DATASET_TYPES = {
        'ANNOTATION': "Annotation Dataset",
        'COMPLETE': "Existing Dataset",
        'DIARY': "Diary Dataset",
        'ENTITY': "Entity Dataset",
        # CHECK: Documentation also refers as `EXPERIENCE SAMPLING`.
        'ES': "Experience Sampling Dataset",
        'FITBIT': "Fitbit Dataset",
        'FORM': "Form Dataset",
        'GOOGLEFIT': "GoogleFit Dataset",
        'IOT': "IoT Dataset",
        'LINKED': "Linked Dataset",
        'MOVEMENT': "Movement Dataset",
        'MEDIA': "Media Dataset",
        # CHECK: Not mentioned in the documentation.
        'SURVEY': "N/A",
        # CHECK: Not mentioned in the documentation.
        'TIMESERIES': "N/A",
    }

    # REMARK: These licenses are listed in the API documentation.
    # CHECK: Are there any other licenses supported, i.e. is it free-text?
    LICENSES = {
        'MIT license': 'MIT',
        'CreativeCommons Attribution': 'CC-BY-4.0',
        'CreativeCommons Attribution ShareAlike': 'CC-BY-SA-4.0',
        'CreativeCommons Attribution-NoDerivs': 'CC-BY-ND-4.0',
        'CreativeCommons Attribution-NonCommercial': 'CC-BY-NC-4.0',
        'CreativeCommons Attribution-NonCommercial-ShareAlike': 'CC-BY-NC-SA-4.0',
        'CreativeCommons Attribution-NonCommercial-NoDerivs': 'CC-BY-NC-ND-4.0',
    }


    def __init__(self, repository_id: str=None, **kwargs):
        """Initializes Data Foundry client object.

        Args:
            repository_id (str): Repository id.
            **kwargs (Dict): Client-specific configuration arguments.
        """
        super().__init__(repository_id, **kwargs)


    @classmethod
    def get_client_info(cls) -> ClientInfo:
        """Returns client information."""
        return ClientInfo(
            name="Data Foundry",
            description="""
                Data Foundry is a design-specific infrastructure for
                prototyping and designing with data.
            """,
            url="https://data.id.tue.nl/documentation/about",
        )


    @classmethod
    def get_config_parameters(cls) -> Dict:
        """Returns configuration parameters.

        Returns:
            Dictionary of configuration parameters {name: description}.
        """
        return {**super().get_config_parameters(), **{
            'token': "Access token.",
        }}


    @classmethod
    def get_config(cls, **kwargs) -> Dict:
        """Returns client configuration.

        Args:
            **kwargs (Dict): Client-specific configuration arguments.

        Returns:
            Dictionary of configuration arguments {name: value}.
        """
        config = super().get_config(**kwargs)

        for key, val in kwargs.items():
            if key == 'token':
                config['token'] = val
            else:
                pass

        return config


    @classmethod
    def get_client(cls, url: str) -> 'DataFoundryClient':
        """Creates a repository client from the specified URL address.

        Args:
            url (str): URL address of the repository or dataset.

        Returns:
            Client object (DataFoundryClient).

        Raises:
            ValueError("Invalid repository."): If repository is not valid.
        """
        logging.info("Checking DataFoundry client for %s.", url)
        parts = urllib.parse.urlparse(url)

        url = parts.scheme + '://' + parts.netloc
        api_url = url + '/api/v2/'

        try:
            # REMARK: Data Foundy does not have an information endpoint.
            response = requests.get(api_url + 'swagger.json')
            response.raise_for_status()
            data = response.json()

        except:
            raise ValueError("Invalid repository.")

        if data.get('paths', {}).get('/wearables') is None:
            raise ValueError("Invalid repository.")

        logging.info("Repository found at %s.", api_url)
        client = DataFoundryClient(name=parts.hostname, url=url, api_url=api_url)

        return client


    def _create_session(self) -> requests.Session:
        """Creates a session.

        Returns:
            Session (requests.Session).
        """
        session = super()._create_session()

        # Set authentication token
        if self.config.get('token'):
            session.headers['X-API-Token'] = self.config['token']

        return session


    def _get_dataset_id(self, **kwargs) -> Dict:
        """Returns standard dataset identifier.

        Args:
            **kwargs (Dict): Dataset identifier arguments.

        Returns:
            Standard dataset identifier (Dict).

        Raises:
          ValueError("Invalid id")
          ValueError("Invalid URL address")
          ValueError("No identifier")
        """
        if 'id' in kwargs:
            if isinstance(kwargs['id'], int):
                id = kwargs['id']
            elif isinstance(kwargs['id'], str) and kwargs['id'].isdigit() and kwargs['id'].isascii():
                id = int(kwargs['id'])
            else:
                raise ValueError("Invalid id")

        elif 'url' in kwargs:
            parts = urlparse(kwargs['url']).path.strip('/').split('/')
            if len(parts) > 2 and parts[-1].isdigit() and parts[-1].isascii() and parts[-2] == 'projects':
                id = int(parts[-1])
            else:
                raise ValueError("Invalid URL address")

        else:
            raise ValueError("No identifier")

        return {'id': id}


    def _get_dataset_hash(self, id: Dict) -> str:
        """Returns hash of the standard dataset identifier.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Hash of the dataset identifier (str).
        """
        return str(id['id'])


    def _get_dataset_details(self, id: Dict) -> Dict:
        """Retrieves details of the dataset.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Dictionary of dataset details.

        Raises:
            ValueError("Invalid dataset id")
        """
        result, _ = self._request(f"projects/{id['id']}")

        if not result or result.get('id') != id['id']:
            raise ValueError("Invalid dataset id")

        return result


    def _create_dataset(self, metadata: Metadata) -> Dict:
        """Creates a dataset with the specified standard metadata.

        Args:
            metadata (Metadata): Standard metadata.

        Returns:
            Standard dataset identifier (Dict).

        Raises:
            ValueError("No access token")
            ValueError("Invalid response")
            requests.exceptions.HTTPError
        """
        # Raise exception if no access token
        if not self.config.get('token'):
            raise ValueError("No access token")

        # Create dataset with minimum metadata
        try:
            result, _ = self._request(
                'projects/add',
                'POST',
                data={
                    'title': "title",
                    'intro': "intro",
                    'license': "license",
                }
            )

        except requests.exceptions.HTTPError as err:
            # TODO: Add error handling
            raise

        # Get dataset id
        if result.get('id'):
            id = self.get_dataset_id(result['id'])
        else:
            raise ValueError("Invalid response")

        # Save metadata
        try:
            self.save_metadata(id, metadata)

        except:
            self.delete_dataset(id)
            raise

        # Return dataset id
        return id


    def _get_account_datasets(self) -> List[RemoteDataset]:
        """Retrieves list of account datasets.

        Returns:
            List of datasets related to the account ([RemoteDataset]).

        Raises:
            requests.exceptions.HTTPError
        """
        if "token" not in self.config:
            return []

        try:
            result, _ = self._request('projects')

        except requests.exceptions.HTTPError as err:
            # TODO: Add error handling.
            raise

        datasets = []

        # CHECK: What to do with archieved projects?
        for key in ['ownProjects', 'collaborations', 'subscriptions']:

            # CHECK: Can a project be listed in multiple categories?
            for id in result.get(key, []):

                dataset = RemoteDataset(self, id)
                datasets.append(dataset)

        return datasets


    def _get_versions(self, id: Dict) -> OrderedDict:
        """Returns standard dataset identifiers of the dataset versions.

        REMARK: Data Foundry does not support versions.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Ordered dictionary of dataset identifiers of the available versions {version: id}.
        """
        return OrderedDict([None, id])


    def _get_metadata(self, id: Dict) -> Dict:
        """Returns standard metadata attributes.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Dictionary of standard metadata attributes {name: value}.
        """
        key_lookup = {
            'name': 'title',
            'startDate': 'start_date',
            'endDate': 'end_date',
            'isPublic': 'is_public',
            'isShareable': 'is_shareable',
        }

        details = self._get_dataset_details(id)

        metadata = {}

        for key, val in details.items():
            metadata[key_lookup[key] if key in key_lookup else key] = val

        return metadata


    def save_metadata(self, id: Dict, metadata: Metadata) -> None:
        """Saves metadata of the specified dataset.

        Args:
            id (Dict): Standard dataset identifier.
            metadata (Metadata): Metadata to be saved.

        Raises:
            ValueError("No access token")
            NotImplementedError
        """
        # Raise exception if no access token
        if not self.config.get('token'):
            raise ValueError("No access token")

        raise NotImplementedError


    def validate_metadata(self, metadata: Metadata) -> Dict:
        """Validates metadata.

        Args:
            metadata (Metadata): Metadata to be validated.

        Returns:
            Dictionary of invalid metadata {field: error message}.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def get_files(self, id: Dict) -> List[RemoteFile]:
        """Retrieves list of files of a dataset.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            List of dataset files ([RemoteFile]).

        Raises:
            NotImplementedError
        """
        details = self._get_dataset_details(id)

        files = []

        # For each Data Foundry dataset
        for dataset_id in details.get('datasets', []):

            # Get dataset information
            result, _ = self._request(f"datasets/{dataset_id}")

            # Skip if invalid dataset
            if not result or result.get('id') != dataset_id or result.get('project_id') != id['id']:
                # TODO: Handle invalid dataset
                continue

            if result.get('data'):

                for item in result.get('data'):

                    file = RemoteFile(
                        url=(
                            self.config['api_url'].rstrip('/') +
                            f'/dataset/download/{dataset_id}/' +
                            urllib.parse.quote(item['name'])
                        ),
                        path=item['name'],
                        id=dataset_id
                    )
                    files.append(file)

            else:
                # Get safe filename
                filename = safe_filename(result['title'])

                # For each download type supported by Data Foundry
                for filetype, mimetype in self.DOWNLOAD_TYPES.items():

                    # Append file
                    file = RemoteFile(
                        url=self.config['api_url'].rstrip('/') + f'/dataset/download/{dataset_id}.{filetype}',
                        path=f'{filename}.{filetype}',
                        id=dataset_id,
                        type=mimetype,
                    )

                    files.append(file)

        return files


    def _upload_file(self, id: Dict, file: LocalFile, notify: Callable=None) -> RemoteFile:
        """Uploads a local file to a dataset at the repository.

        Args:
            id (Dict): Standard dataset identifier.
            file (LocalFile): File to be uploaded.
            notify (Callable): Notification method to provide status updates.

        Returns:
            Remote file object of the uploaded file.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
        """Deletes a file of a dataset from the repository.

        REMARK: Data Foundry only allows deleting entity datasets.

        REMARK: DELETE /datasets/entity/{id} endpoint requires resource_id and
            token, which does not seem to be logical.

        Args:
            id (Dict): Standard dataset identifier.
            file (RemoteFile): File to be deleted.

        Raises:
            PermissionError("Operation not supported")
        """
        raise PermissionError("Operation not supported")


    def _delete_dataset(self, id: Dict) -> None:
        """Deletes a dataset from the repository.

        REMARK: Data Foundry does not support deleting datasets.

        Args:
            id (Dict): Standard dataset identifier.

        Raises:
            PermissionError("Operation not supported")
        """
        raise PermissionError("Operation not supported")


    def get_details(self, id: Dict) -> Dict:
        """Returns standard details of a dataset.

        Details dictionary:
            - title (str): Title.
            - url (str): URL address.
            - doi (str): DOI.
            - status (str): Status.
            - size (int): Total size of data files in bytes.
            - created (datetime.datetime): Creation date and time.
            - modified (datetime.datetime): Last modification date and time.

        Possible statuses are as follows:
            - "draft": Dataset is not published yet.
            - "public": Dataset is published and is publicly available.
            - "embargoed": Dataset is published, but is under embargo.
            - "restricted": Dataset is published, but accessible only under certain conditions.
            - "closed": Dataset is published, but accessible only by the owners.
            - "error": Dataset is in an error state.
            - "unknown": Dataset is in an unknown state.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Details dictionary of the dataset.
        """
        details = self._get_dataset_details(id)

        out = {}

        out['title'] = details['name']
        out['url'] = self.config.get('url').rstrip('/') + f"/projects/{id['id']}"
        out['doi'] = details.get('doi') or None
        out['status'] = 'public' if details['isPublic'] == True else 'closed'
        # WARNING: Data Foundry does not provide project data size.
        out['size'] = None
        # WARNING: Data Foundry does not provide creation date.
        out['created'] = None
        # WARNING: Data Foundry does not provide modification date.
        out['modified'] = None

        return out


    @classmethod
    def supports_folders(cls) -> bool:
        """Returns if folders are supported.

        Returns:
            True if folders are supported, False otherwise.
        """
        return False
