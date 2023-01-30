# fairly
A package to create, publish and clone research datasets.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## Installation

*fairly* requires Python 3.8 or later, and it can be installed directly using PIP.

```shell
pip install fairly
```

### Installing from source

1. Clone or download the [source code](https://github.com/ITC-CRIB/fairly):

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

Basic example to create a local research dataset and deposit it to a repository:

```python
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
```

Basic example to access a remote dataset and store it locally:

```python
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
dataset.save()

# Store dataset to a local directory (i.e. clone dataset)
local_dataset = dataset.store('/path/dataset')
```

Currently, the package supports the following research data management platforms:

- [Zenodo](https://zenodo.org/)
- [Figshare](https://figshare.com/)
- [Djehuty](https://github.com/4TUResearchData/djehuty/)

All research data repositories based on the listed platforms are supported.

For more details and examples, consult the [package documentation](https://jupyterfair.readthedocs.io/en/latest/package/installation.html).


## Testing

Unit tests can be run by using `pytest` command in the root directory.


## Contributions

Read the [guidelines](CONTRIBUTING.md) to know how you can be part of this open source project.


## Citation

Please cite this software using as follows:

*Girgin, S., Garcia Alvarez, M., & Urra Llanusa, J., fairly: a package to create, publish and clone research datasets [Computer software]*


## Acknowledgements

This research is funded by the [Dutch Research Council (NWO) Open Science Fund](https://www.nwo.nl/en/researchprogrammes/open-science/open-science-fund/), File No. 203.001.114.

Project members:

- [Center of Expertise in Big Geodata Science, University of Twente, Faculty ITC](https://itc.nl/big-geodata/)
- [Digital Competence Centre, TU Delft](https://dcc.tudelft.nl/)
- [4TU.ResearchData](https://data.4tu.nl/)