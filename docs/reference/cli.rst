.. _cli-reference:

CLI Reference
=============

The *fairly* package installs a command-line tool named :code:`fairly`. This page
documents all its commands and options. For a task-oriented introduction, see the
:doc:`CLI tutorial </tutorials/cli>`.

All example outputs on this page were captured with *fairly* 2.0.0.

Invocation and global options
-----------------------------

Running :code:`fairly` without arguments prints a banner followed by the list of
command groups:

.. code-block:: shell

   $ fairly
   ______ ___  ___________ _
   |  ___/ _ \|_   _| ___ \ |
   | |_ / /_\ \ | | | |_/ / |_   _
   |  _||  _  | | | |    /| | | | |
   | |  | | | |_| |_| |\ \| | |_| |
   \_|  \_| |_/\___/\_| \_|_|\__, |
                              __/ |
                             |___/

   Usage: fairly [OPTIONS] [COMMAND] [ARGS]...

     fairly command-line tool.

   Options:
     -v, --version  Show the version and exit.
     -h, --help     Show this message and exit.

   Commands:
     client      Client commands.
     dataset     Dataset commands.
     repository  Repository commands.

:code:`-v` / :code:`--version` prints the installed version:

.. code-block:: shell

   $ fairly --version
   fairly version 2.0.0

Every command and subcommand accepts :code:`-h` / :code:`--help`.

Output formats
--------------

The commands :code:`client list`, :code:`repository list`, and
:code:`repository config` accept a :code:`--format` option with the values
:code:`text` (default), :code:`json`, or :code:`yaml`. Use :code:`json` or
:code:`yaml` when the output is consumed by scripts or other tools.

fairly client
-------------

*Clients* are the connectors that *fairly* uses to talk to a type of data
repository (e.g. Invenio-based or figshare-based repositories).

fairly client list
''''''''''''''''''

Lists the supported clients with their identifiers and configuration parameters.

.. code-block:: shell

   $ fairly client list
   # Supported Clients

   ## Data Foundry (id = `datafoundry`)

   Data Foundry is a design-specific infrastructure for prototyping and
   designing with data.

   Supports folders: No

   **Configuration parameters:**

   - `name`: Repository name.
   - `url`: URL address of the repository.
   - `api_url`: API end-point URL address of the repository.
   - `token`: Access token.

   ## Dataverse (id = `dataverse`)
   ...

The available client identifiers are :code:`datafoundry`, :code:`dataverse`,
:code:`djehuty`, :code:`figshare`, :code:`invenio`, and :code:`zenodo`.

Machine-readable output is available with :code:`--format`:

.. code-block:: shell

   $ fairly client list --format yaml
   datafoundry:
     name: Data Foundry
     description: Data Foundry is a design-specific infrastructure for prototyping
       and designing with data.
     config_parameters:
       name: Repository name.
       url: URL address of the repository.
       api_url: API end-point URL address of the repository.
       token: Access token.
     supports_folders: false
   dataverse:
     name: Dataverse
   ...

fairly repository
-----------------

*Repositories* are the concrete data repositories you interact with (e.g. Zenodo,
4TU.ResearchData). Repositories are stored in the *fairly* configuration file
:code:`~/.fairly/config.json`, and each repository uses one of the supported
clients. A set of well-known repositories is pre-configured.

fairly repository list
''''''''''''''''''''''

Lists the repositories defined in the configuration files, including the
pre-configured ones.

.. code-block:: shell

   $ fairly repository list
   * 4tu
     - client_id: djehuty
     - url: https://data.4tu.nl
     - api_url: https://data.4tu.nl/v2
     - token: <your-access-token>

   * zenodo
     - client_id: zenodo
     - url: https://zenodo.org
     - api_url: https://zenodo.org/api
     - token: <your-access-token>

   ...

.. warning::
   The output includes the stored access tokens. Be careful when copying it into
   documents, terminal recordings, or issue reports.

fairly repository add
'''''''''''''''''''''

Adds a repository to the configuration file. The repository identifier is given
as an argument, the client and its configuration as options:

.. code-block:: shell

   $ fairly repository add myrepo --client_id invenio \
       --name "My Data Repository" \
       --url https://repository.example.com \
       --api_url https://repository.example.com/api
   
   Repository `myrepo` added to the configuration file.

Options:

- :code:`--client_id`: One of the supported client identifiers (see
  :code:`fairly client list`).
- :code:`--name`, :code:`--url`, :code:`--api_url`: Common configuration
  parameters supported by all clients.
- :code:`-p, --param KEY=VALUE`: Any other client-specific configuration
  parameter. Can be repeated.

Use :code:`fairly repository config` to inspect repository configurations.


fairly repository config
''''''''''''''''''''''''

Shows the configuration of a single repository:

.. code-block:: shell

   $ fairly repository config zenodo
   - id: zenodo
   - client_id: zenodo
   - url: https://zenodo.org
   - api_url: https://zenodo.org/api
   - token: <your-access-token>

An unknown identifier results in a usage error:

.. code-block:: shell

   $ fairly repository config nosuchrepo
   Usage: fairly repository config [OPTIONS] ID
   Try 'fairly repository config --help' for help.

   Error: Invalid repository id.

fairly repository token
'''''''''''''''''''''''

Stores the access token of a repository in the configuration file. This is
required before uploading, listing, or deleting datasets in your account. See
:doc:`how to obtain a token </package/account-token>` for the supported
repositories.

.. code-block:: shell

   $ fairly repository token zenodo <your-access-token>
   Access token of the `zenodo` repository is set as `<your-access-token>`.

fairly repository remove
''''''''''''''''''''''''

Removes a repository entry from the configuration file:

.. code-block:: shell

   $ fairly repository remove myrepo
   Repository `myrepo` is removed.

Removing an unknown repository results in a usage error:

.. code-block:: shell

   $ fairly repository remove myrepo
   Usage: fairly repository remove [OPTIONS] ID
   Try 'fairly repository remove --help' for help.

   Error: Repository `myrepo` not found in the configuration file.

fairly dataset
--------------

Commands to create local datasets, and to clone, upload, list, and delete
datasets in data repositories.

fairly dataset init
'''''''''''''''''''

Initializes a local dataset by creating a :code:`manifest.yaml` metadata file
from a template:

.. code-block:: shell

   $ fairly dataset init --path . --template zenodo
   $ ls
   manifest.yaml

Options:

- :code:`--path`: Directory where the dataset is initialized.
- :code:`--template`: Metadata template. Available templates are
  :code:`default`, :code:`figshare`, and :code:`zenodo`. The default template
  is compatible with all repositories.

The generated :code:`manifest.yaml` contains all metadata fields of the
template, with inline comments describing each field:

.. code-block:: yaml

   metadata:
       type: ""
           # Required.
           #
           # Controlled vocabulary:
           # ...

fairly dataset clone
''''''''''''''''''''

Clones (downloads) a dataset, including its metadata, by using its URL address,
DOI, or unique identifier:

.. code-block:: shell

   $ fairly dataset clone --id https://zenodo.org/records/7748718
   Cloning dataset https://zenodo.org/records/7748718...
   Dataset https://zenodo.org/records/7748718 is successfully cloned to 10.5281_zenodo.7748718.

If no :code:`--path` is given, the dataset is stored in a new directory named
after its DOI, with path separators replaced by underscores (e.g.
:code:`10.5281_zenodo.7748718`). The directory contains the dataset files and a
:code:`manifest.yaml` file with the dataset metadata.

A DOI works equally well, and :code:`--notify` reports download progress per
file:

.. code-block:: shell

   $ fairly dataset clone --id 10.5281/zenodo.7748718 --path trixi --notify
   Cloning dataset 10.5281/zenodo.7748718...
   trixi-framework/Trixi.jl-v0.5.14.zip, 262144/1487066
   trixi-framework/Trixi.jl-v0.5.14.zip, 524288/1487066
   trixi-framework/Trixi.jl-v0.5.14.zip, 786432/1487066
   trixi-framework/Trixi.jl-v0.5.14.zip, 1048576/1487066
   trixi-framework/Trixi.jl-v0.5.14.zip, 1310720/1487066
   trixi-framework/Trixi.jl-v0.5.14.zip, 1487066/1487066
   Dataset 10.5281/zenodo.7748718 is successfully cloned to trixi.

Other options:

- :code:`--repository`: Repository identifier; use together with a plain record
  identifier, e.g. :code:`fairly dataset clone --repository zenodo --id 7748718`.
- :code:`--token`: Access token, required only for restricted datasets.
- :code:`--extract`: Extract archive files after downloading.

fairly dataset upload
'''''''''''''''''''''

Uploads a local dataset (a directory with a :code:`manifest.yaml`) to a data
repository. The dataset is created as an *unpublished draft* in your account,
so you can review it before publishing it in the repository's web interface.

.. code-block:: shell

   $ fairly dataset upload --path . --repository zenodo
   Uploading dataset ....
   Dataset . is successfully uploaded at https://zenodo.org/uploads/1234567.


Options:

- :code:`--path`: Local dataset path.
- :code:`--repository`: Repository identifier (see
  :code:`fairly repository list`).
- :code:`--token`: Access token; if omitted, the token stored in the
  configuration is used.
- :code:`--notify`: Enable upload progress notification.

After a successful upload, a :code:`remotes:` section is added to
:code:`manifest.yaml` recording where the dataset has been uploaded.

fairly dataset list
'''''''''''''''''''

Lists the datasets of your account in a repository (an access token must be
configured). For each dataset, its title, DOI, and publication date are shown
in YAML format:

.. code-block:: shell

   $ fairly dataset list --repository zenodo
   title: Gravity measurements in the Atacama Desert
   doi: 10.5281/zenodo.1234567
   publication_date: '2025-03-14'


   title: Survey responses on research software practices
   doi: 10.5281/zenodo.7654321
   publication_date: '2024-11-02'


Unpublished drafts appear with their title only. If the account has no
datasets, the command prints :code:`There are no user datasets.`. An invalid
repository identifier is reported as an error:

.. code-block:: shell

   $ fairly dataset list --repository nosuchrepo
   Invalid client id
   Please specify a valid repository identifier.

fairly dataset delete
'''''''''''''''''''''

Deletes a dataset from a repository by its URL address, DOI, or unique
identifier.

.. warning::
   Deletion is performed on the repository side and cannot be undone. Published
   datasets usually cannot be deleted; this command is mainly useful for
   removing unpublished drafts.

.. code-block:: shell

   $ fairly dataset delete --id https://zenodo.org/deposit/1234567 --repository zenodo
   Deleting dataset https://zenodo.org/deposit/1234567...
   Dataset https://zenodo.org/deposit/1234567 is successfully deleted.


Options:

- :code:`--id`: Dataset identifier (URL, or unique ID).
- :code:`--repository`: Repository identifier.
- :code:`--token`: Access token; if omitted, the token stored in the
  configuration is used.
