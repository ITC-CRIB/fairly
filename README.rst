.. list-table::
   :widths: 25 25
   :header-rows: 1

   * - `fair-software.nl <https://fair-software.nl>`_ recommendations
     - Badges
   * - \1. Code repository
     - |GitHub Badge|
   * - \2. License
     - |License Badge|
   * - \3. Community Registry
     - |PyPI Badge|
   * - \4. Enable Citation
     - |Zenodo Badge|
   * - **Other best practices**
     -
   * - Continuous integration
     - |Python Build| |Python Publish|
   * - Documentation
     - |Documentation Status|

.. |GitHub Badge| image:: https://img.shields.io/github/v/release/ITC-CRIB/fairly
   :target: https://github.com/ITC-CRIB/fairly
   :alt: GitHub Badge

.. |License Badge| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License Badge

.. |PyPI Badge| image:: https://img.shields.io/pypi/v/fairly?colorB=blue
   :target: https://pypi.org/project/fairly/
   :alt: PyPI Badge

.. |Zenodo Badge| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.7759648.svg
   :target: https://doi.org/10.5281/zenodo.7759648
   :alt: Zenodo Badge

.. |Python Build| image:: https://img.shields.io/github/actions/workflow/status/ITC-CRIB/fairly/test_workflow.yaml
   :target: https://github.com/ITC-CRIB/fairly/actions/workflows/test_workflow.yaml
   :alt: Python Build

.. |Python Publish| image:: https://img.shields.io/github/actions/workflow/status/ITC-CRIB/fairly/publish.yaml
   :target: https://github.com/ITC-CRIB/fairly/actions/workflows/publish.yaml
   :alt: Python Publish

.. |Documentation Status| image:: https://readthedocs.org/projects/fairly/badge/?version=latest
   :target: https://fairly.readthedocs.io/en/latest/
   :alt: Documentation Status


fairly
======

A package to create, publish and clone research datasets.

|License: MIT|

Installation
------------

*fairly* requires Python 3.8 or later, and `ruamel.yaml` version *0.17.26* or later.  It can be installed directly
using pip.

.. code:: shell

   pip install fairly

Installing from source
~~~~~~~~~~~~~~~~~~~~~~

1. Clone or download the `source
   code <https://github.com/ITC-CRIB/fairly>`__:

   .. code:: shell

      git clone https://github.com/ITC-CRIB/fairly.git

2. Go to the root directory:

   .. code:: shell

      cd fairly/

3. Compile and install using pip:

   .. code:: shell

      pip install .

Usage
-----

Basic example to create a local research dataset and deposit it to a
repository:

.. code:: python

   import fairly

   # Initialize a local dataset
   dataset = fairly.init_dataset('/path/dataset')

   # Set metadata
   dataset.metadata['license'] = 'MIT'
   dataset.set_metadata(
       title='My dataset',
       keywords=['FAIR', 'research', 'data'],
       authors=[
           '0000-0002-0156-185X',
           {'name': 'John', 'surname': 'Doe'}
       ]
   )

   # Add data files
   dataset.includes.extend([
       'README.txt',
       '*.csv',
       'train/*.jpg'
   ])

   # Save dataset
   dataset.save()

   # Upload to a data repository
   remote_dataset = dataset.upload('zenodo')

Basic example to access a remote dataset and store it locally:

.. code:: python

   import fairly

   # Open a remote dataset
   dataset = fairly.dataset('doi:10.4121/21588096.v1')

   # Get dataset information
   dataset.id
   >>> {'id': '21588096', 'version': '1'}

   dataset.url
   >>> 'https://data.4tu.nl/articles/dataset/.../21588096/1'

   dataset.size
   >>> 33339

   len(dataset.files)
   >>> 6

   dataset.metadata
   >>> Metadata({'keywords': ['Earthquakes', 'precursor', ...], ...})

   # Update metadata
   dataset.metadata['keywords'] = ['Landslides', 'precursor']
   dataset.save_metadata()

   # Store dataset to a local directory (i.e. clone dataset)
   local_dataset = dataset.store('/path/dataset')

Currently, the package supports the following research data management
platforms:

-  `Zenodo <https://zenodo.org/>`__
-  `Figshare <https://figshare.com/>`__
-  `Djehuty <https://github.com/4TUResearchData/djehuty/>`__
   (experimental)

All research data repositories based on the listed platforms are
supported.

For more details and examples, consult the `package
documentation <https://fairly.readthedocs.io/en/latest/>`__.

Testing
-------

Unit tests can be run by using ``pytest`` command in the root directory.

Contributions
-------------

Read the `guidelines <CONTRIBUTING.md>`__ to know how you can be part of
this open source project.

JupyterLab Extension
--------------------

An extension for JupyerLab is being developed in a `different
repository. <https://github.com/ITC-CRIB/jupyter-fairly>`__

Citation
--------

Please cite this software using as follows:

*Girgin, S., Garcia Alvarez, M., & Urra Llanusa, J., fairly: a package
to create, publish and clone research datasets [Computer software]*

Acknowledgements
----------------

This research is funded by the `Dutch Research Council (NWO) Open
Science
Fund <https://www.nwo.nl/en/researchprogrammes/open-science/open-science-fund/>`__,
File No. 203.001.114.

Project members:

-  `Center of Expertise in Big Geodata Science, University of Twente,
   Faculty ITC <https://itc.nl/big-geodata/>`__
-  `Digital Competence Centre, TU Delft <https://dcc.tudelft.nl/>`__
-  `4TU.ResearchData <https://data.4tu.nl/>`__

.. |License: MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
