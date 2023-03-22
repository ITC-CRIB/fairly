.. _installation:

Installation
================

The *Fairly Toolset* provides functionality for the core tasks of preparing, uploading and downloading datasets from research data repositories. The toolset currently provides integration with data repositories based on `Zenodo <https://zenodo.org/>`_ and `Figshare <https://figshare.com/>`_.

**What's Included:**

* fairly Python package
* Command Line Interface (CLI)
* JupyterLab extension

**Requirements:**

* Python 3.8 or higher
* pip 20.0 or higher

Installing the Toolset
------------------------

You can install the full toolset by installing the JupyterLab extension from PyPI. fairly package and CLI will be installed automatically.

Linux / MacOS
'''''''''''''''''''

Install the toolset using `pip`

.. code-block:: shell

   pip install jupyter-fairly


Windows
'''''''''''''''''''

1. Download the ZIP file with the `latest release <https://github.com/ITC-CRIB/jupyter-fairly/releases>`_ of the JupyterLab extension to a directory.
2. Unzip the content.
3. Using the **terminal**, go to the directory where the ZIP file is located and then to the `jupyter_fairly` sub-directory.
4. Type and run the following command. You need to add Python to the system PATH for this to work.

.. code-block:: shell

   python -m pip install .


Installing Python Package Only
--------------------------------

If all you need is the *fairly* Python package and the CLI, you can install them as following.

Linux / MacOS
'''''''''''''''''''

On the terminal type:

.. code-block:: shell

   pip install fairly


Installing from Source
'''''''''''''''''''''''''

Installing *fairly* from source requires `setuptools` version 49.0 or later and `pip`.

1. Clone or download the `source code <https://github.com/ITC-CRIB/fairly>`_:

.. code-block:: shell

   git clone https://github.com/ITC-CRIB/fairly.git


2. Unzip if necessary, and go to the `fairly` directory:

.. code-block:: shell

   cd fairly/


3. Install the package:

.. code-block:: shell

   pip install .

.. important::
   Currently, the toolset only supports data repositories based on `Zenodo <https://zenodo.org/>`_ and `Figshare <https://figshare.com/>`_. For examples on how to use the toolset, read the `Tutorials <index.rst>`_

