.. _installation:
Installation
########################

*Fairly* is a Python package that provides functionality for the core tasks of prepararing, uploading and donwloading datasets from research data repositories. The package currently provides integration with `Zenodo <https://zenodo.org/>`_ and Figshare repositories such as `4TU.ReseachData <https://data.4tu.nl/>`_  

Installing using Pip
========================
The easier way to install *fairly* is using `pip`, it requires Python 3.8 or later. 

On the terminal type: 

.. code-block:: shell

   pip install fairly


Installing from Source
==========================

Installing *fairly* from source requires `setuptool` version 49.0 or later and `pip`. 

1. Clone or download the `source code <https://github.com/ITC-CRIB/JupyterFAIR>`_:
   
.. code-block:: shell

   git clone https://github.com/ITC-CRIB/fairly.git
    

2. Unzip if necessary, and move to the root directory:

.. code-block:: shell
   
   cd fairly/
    

3. Compile and install by doing:

.. code-block:: shell
   
   pip install .
    
.. note::
   Currently, the package only supports the `Zenodo <https://zenodo.org/>`_ and `4TU.ResearchDAata <https://data.4tu.nl/>`_ repositories. For more details on how tu use *fairy* and some examples, see the **Quick Start** section.


