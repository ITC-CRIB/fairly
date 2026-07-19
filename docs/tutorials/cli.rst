Using the CLI
=====================

This tutorial shows how to use the *fairly* Command Line Interface (CLI) to clone, and create datasets, and to edit their metadata.
See the :ref:`cli-reference` for a complete list of CLI commands.

.. important::
   **Windows Users.** For the following to work, you need Pyton in the PATH environment variable on Windows. If your not sure that is the case. Open the Shell, and type :code:`python --version`. You should see the version of Python on the screen. If you see otherwise, follow these steps to `add Python to the PATH on Windows <https://realpython.com/add-python-to-path/#how-to-add-python-to-path-on-windows>`_

1. Open a *Terminal* or *Shell*

2. Test the *fairly* CLI is accessible in your terminal, by calling the help command:

.. code:: shell
   
   fairly --help


You should see the following:

   .. code:: shell

      Usage: fairly [OPTIONS] [COMMAND] [ARGS]...

      fairly command-line tool.

      Options:
      -v, --version  Show the version and exit.
      -h, --help     Show this message and exit.

      Commands:
      client      Client commands.
      dataset     Dataset commands.
      repository  Repository commands.
        

Cloning a Dataset
--------------------

1. Create a new directory and subdirectory :code:`tutorial/clone` 

   .. code:: shell

      # On Windows
      mkdir tutorial
      mkdir tutorial\clone

      # On Linux/MacOS
      mkdir -p  tutorial/clone

2. Go to the :code:`clone` directory

   .. code:: shell

      # On Windows
      cd tutorial\clone

      # On Linux/MacOS
      cd  tutorial/clone

3. Clone this `Zenodo dataset <https://zenodo.org/records/21363476>`_, using its URL:

   .. code:: shell

      fairly dataset clone --id https://zenodo.org/records/21363476 --notify 

4. Explore the content of the dataset, notice that file(s)  of the dataset have been downloaded to a directory named after the dataset DOI (:code:`10.5281_zenodo.21363476`). The directory also contains metadata in the :code:`manifest.yaml` file.

   .. code:: shell
     
     # Content dataset directory:
      manifest.yaml   trixi-framework


Creating a Local fairly Dataset
--------------------------------------

We can use the CLI to initialize a new dataset.

   1. Create a new directory called :code:`mydataset` inside the *tutorial* directory. Then move to into the directory

   .. code:: shell

      # On Windows/Linux/McOS
      mkdir mydataset
      cd mydataset

   2. Create a local dataset using the Zenodo metadata template, as follows

   .. code:: shell

      fairly dataset init --path ./mydataset --template zenodo

Valid templates include: :code:`default`, :code:`figshare`, and  :code:`zenodo`

Include Files in your Dataset
''''''''''''''''''''''''''''''''

Add some folders and files the :code:`mydataset-cli` directory.  You can do this using the file explorer/browser. You can add files of your own, but be careful not to include anything that you want to keep confidential. Also consider the total size of the files you will add, the larger the size the longer the upload will take. Keep in mind that a data repository may set size limits to files and datasets, if your dataset exceed such limits uploading will fail. 

If you do not want to use you own files, you can download and use the `dummy-data <https://drive.google.com/drive/folders/160N6MCmiKV3g-74idCgyyul9UdoPRO8T?usp=share_link>`_ 

Editing the Manifest
''''''''''''''''''''''

The :code:`manifest.yaml` file contains several sections to describe the medatadata of a dataset. Some of the sections and fields are compulsory (they are required by the data repository), others are optional. In this example, you started a *fairly* dataset using the template for the Zenodo repository, but you could also do so for 4TU.ResearchData. 

However, if you are not sure which repository you will use to publish a dataset, use the :guilabel:`default` template. This template contains the most common sections and fields for the repositories supported by *fairly*

.. tip::
   Independently of which template you use to start a dataset, the :code:`manifest.yaml` file is **interoperable** between data repositories, with very few exceptions. This means that you can use the same manifest file for various data repositories. Different templates are provided only as a guide to indicate what metadata is more relevant for a data repository. 


1. Open the :code:`manifest.yaml` using a text editor. On Linux/MacOS you can use **nano** or **vim**. On Windows use **notepad**.

2. Replace the content of the :code:`manifest.yaml` with the text below.  *Here, we use only a small set of fields that are possible for Zenodo.*
   
.. code-block:: yaml

   metadata:
     type: dataset
     publication_date: '2026-07-22'
     title: My Title CLI
     authors:
     - fullname: Surname, FirstName
       affiliation: Your institution
     description: A dataset from the Fairly Toolset tutorial
     access_type: open
     license: CC0-1.0
     doi: ''
     prereserve_doi:
     keywords:
     - tutorial
     - dummy data
     notes: ''
     related_identifiers: []
     communities: []
     grants: []
     subjects: []
     version: 1.0.0
     language: eng
   template: zenodo
   files:
     includes:
     - ARP1_.info
     - ARP1_d01.zip
     - my_code.py
     - Survey_AI.csv
     - wind-mill.jpg
     excludes: []


3. Edit the dataset metadata by typing the information you want to add. For example, you can change the title, authors, description, etc. Save the file when you are done.

.. important:: 
   * The :code:`includes`  field must list the files  and directories (folders) you want to include as part of the dataset. *Included files and directories will be uploaded to the data repository* 
   * The :code:`excludes` field can be used for explicitly indicating what files or directories you **don't want to be part  of the dataset**, for example, files that contain sensitive information. Excluded files and directories will never be uploaded to the data repository. 
   * Files and directories that are not listed in either :code:`includes` or :code:`excludes` will be ignored by *fairly*.


Upload Dataset to Data Repository
-----------------------------------

Here, we explain how to upload a dataset to an existing account in Zenodo. If you do not have an account yet, you can `sign up in this webpage. <https://zenodo.org/signup/>`_

To upload datasets you need a *Token* associated with the account. See  :ref:`create-token` to know how to create a token. 

Register the token for the Zenodo repository:

.. code:: shell

   fairly repository token zenodo <your-token>

.. note::
   You can check which token are registered in the configuration file using :code:`fairly repository list`

Upload Dataset
''''''''''''''''

1. On the terminal or command prompt, type:

   .. code:: shell

      fairly dataset upload --path mydataset/ --repository zenodo 

2. Go to your Zenodo account and click on :guilabel:`My dashboard` :guilabel:`Uploads`. The `My dataset CLI` dataset should be listed there. 

.. image:: ../img/zenodo-cli-upload.png


Explore the dataset and notice that all the files and metadata you added to :code:`manifest.yaml` has been uploaded. You should also notice that the dataset is not **published**, this is on purpose. This gives you the oportunity to review the dataset before deciding to publish it, and if necessary to make changes. 

.. note:: 
   If you try to upload the dataset again, you will see an error message. This is because the dataset already exists in Zenodo. You can see this reflected in the :code:`manifest.yaml` file;  the section :code:`remotes:` is added to the file after succesfully uploading a dataset. It lists the names and ids of the repositories where the dataset has been uploaded.
   In the future, we will add a feature to allow users to update and sync datasets between repositories.

   .. code:: yaml

      # manifest.yaml 
      ...
      remotes:
         zenodo:
            id: '21446136'


Listing and Deleting Datasets
''''''''''''''''''''''''''''''

You can list the datasets in you account as follows. You will see all your *drafts* and *publisned* dataset, or a message indicating that there are no datasets in your account. 

.. code:: shell

   fairly dataset list --repository zenodo

   # Datasets
   title: My Title CLI
   publication_date: '2026-07-22'


   title: Mock Dataset
   publication_date: '2026-07-17'


Finally, you can delete a *draft* dataset in your account. Deleting a dataset is a PERMANENT operation and you should be careful. However, published dataset are usually protected and cannot be deleted. Deleting a dataset from a repository  will not delete your local copy. 

.. code:: shell

   fairly dataset delete --id https://zenodo.org/uploads/<dataset-id> --repository zenodo 
   
   # Confirmation message:
   Deleting dataset https://zenodo.org/uploads/21446136...
   Dataset https://zenodo.org/uploads/21446136 is successfully deleted.


