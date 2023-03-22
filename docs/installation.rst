.. _installation:

Installation
================

The *Fairly Toolset* provides functionality for the core tasks of prepararing, uploading and donwloading datasets from research data repositories. The package currently provides integration with `Zenodo <https://zenodo.org/>`_, `4TU.ReseachData <https://data.4tu.nl/>`_  and Figshare repositories.

**What's Included:**

* Fairly Python package
* Command Line Interface (CLI)
* JupyterLab extension 

**Requirements:**

* Python 3.8 or higher
* pip 20.0 or higher

Installing the Toolset
------------------------

You can install the full toolset from PyPI.

Linux / MacOS
'''''''''''''''''''

Install the toolset using `pip`
.. code-block:: shell

   pip install jupyter-fairly


Windows
'''''''''''''''''''

1. Download the ZIP file with the `latest release <https://github.com/ITC-CRIB/jupyter-fairly/releases>`_ of the toolset, to a directory.
2. Unzip the content
3. Using the **terminal**, go to the unzip directory and then to `jupyter_fairly`
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

Installing *fairly* from source requires `setuptool` version 49.0 or later and `pip`. 

1. Clone or download the `source code <https://github.com/ITC-CRIB/fairly>`_:
   
.. code-block:: shell

   git clone https://github.com/ITC-CRIB/fairly.git
    

2. Unzip if necessary, and move to the root directory:

.. code-block:: shell
   
   cd fairly/
    

3. Install the package:

.. code-block:: shell
   
   pip install .
    
.. important::
   Currently, the toolset only supports the `Zenodo <https://zenodo.org/>`_ and `4TU.ResearchDAata <https://data.4tu.nl/>`_ repositories. For examples on how how to use the Toolset, read the `Tutorials <index.rst>`_

