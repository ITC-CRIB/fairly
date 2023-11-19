.. _installation:
Installation
########################

*fairly* is a Python package that provides functionality for the core tasks of preparing, uploading and downloading datasets from research data repositories. The package currently provides integration with `Invenio <https://inveniosoftware.org/>`_ and Figshare repositories.

Installing using pip
========================
The easier way to install *fairly* is using `pip`, it requires Python 3.8 or later.

On the terminal type:

.. code-block:: shell

   pip install fairly


Installing from source
==========================

Installing *fairly* from source requires `setuptools` version 49.0 or later and `pip`.

1. Clone or download the `source code <https://github.com/ITC-CRIB/fairly>`_:

.. code-block:: shell

   git clone https://github.com/ITC-CRIB/fairly.git


2. Unzip if necessary, and move to the root directory:

.. code-block:: shell

   cd fairly/


3. Compile and install by doing:

.. code-block:: shell

   pip install .

.. note::
   Currently, the package only supports repositories based on `Zenodo <https://zenodo.org/>`_ and `Figshare <https://figshare.com/>`_. For more details on how to use *fairy* and some examples, see the **Quick Start** section.


