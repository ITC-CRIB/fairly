# Fairly
A package to create, publish and download research datasets.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

*Fairly* requires Python 3.8 or later, and it can be installed directly using PIP.

```shell
pip install fairly
```

### Installing from Source

1. Clone or download the [source code](https://github.com/ITC-CRIB/JupyterFAIR):
   
    ```shell
    git clone https://github.com/ITC-CRIB/fairly.git
    ```

2. Go to the root directory:
    ```shell
    cd fairly/
    ```

3. Compile and install using PIP:


    ```shell
    pip install .
    ```

## Usage

```python
import fairly
```

Currently, the package only supports the [Zenodo](https://zenodo.org/) and [4TU.ResearchDAata](https://data.4tu.nl/) repositories. For more details and examples, consult the [package documentation](https://jupyterfair.readthedocs.io/en/latest/package/installation.html).

## Testing

Unit tests can be run by using `pytest` command in the root directory.

## Contributions

Read the [guidelines](CONTRIBUTING.md) to know how you can be part of this open source project.

## Citation
Please cite this software using as follows:

*Girgin, S., Garcia Alvarez, M., & Urra Llanusa, J. Fairly [Computer software]*

## Acknowledgements

- [NWO Open Science Fund](https://www.nwo.nl/en/researchprogrammes/open-science/open-science-fund/)
- [Center of Expertise in Big Geodata Science, University of Twente, Faculty ITC](https://itc.nl/big-geodata/)
- [Digital Competence Centre, TU Delft](https://dcc.tudelft.nl/)
- [4TU.ResearchData](https://data.4tu.nl/)