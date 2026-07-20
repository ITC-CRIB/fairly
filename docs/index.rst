.. fairly documentation master file, created by
   sphinx-quickstart on Mon Oct  3 21:00:21 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Fairly Toolset Documentation
==================================

A toolset for creating, publishing and cloning research datasets. It provides a structured yet flexible 
way to document datasets durig data analysis, prepare datasets for publication and archiving to multiple 
research data reposities. Fairly supports repositories based on the following technologies: 
**Invenio (Zenodo), Figshare, Dejhuty (4TU.ResearchData), Data Foundry** and **Dataverse**. 

The toolset consist of:

* **Fairly Package.** A Python package with the core functionally which can be used directly on the Python interpreter. 
* **Fairly CLI.** A command line interface for the terminal or shell bundled with the Python package.
* **Jupyter-Fairly.** An extesion for JupyterLab and Jupyter Notebook. It provides a graphical interface with basic functionality.


.. toctree::
   :maxdepth: 2
   :caption: Quick Start

   installation

.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   tutorials/jupyterlab
   tutorials/cli
   tutorials/python-api

.. toctree::
   :maxdepth: 1
   :caption: References

   reference/cli
   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
