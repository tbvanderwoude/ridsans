# `ridsans`: SANS data reduction using Mantid
Data reduction logic for measurements done at the TU Delft Reactor Institute with the new [SANS instrument](https://www.tudelft.nl/en/faculty-of-applied-sciences/business/facilities/tu-delft-reactor-institute/research-tools-tu-delft-reactor-institute/sans) using [Mantid](https://github.com/mantidproject/mantid). Enables loading generated .mpa files as Mantid workspaces and reducing these to [NeXuS files](https://www.nexusformat.org/) that can be loaded into [SasView](https://www.sasview.org/) and similar tools for analysis.

## Installation
First, Mantid v6.10 needs to be installed. The recommended way is to install it as a conda package as explained on the [Mantid installation page](https://www.mantidproject.org/installation). As Mantid specifically requires Python 3.10, it is recommended to first [install Mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html) and use this instead of [Conda](https://github.com/conda/conda). The reason for this is that Mamba is better at resolving specific requirements such as the specific Python version, meaning that you might run into errors when trying to create an environment using `conda` commands. 
### Installing Mamba
The recommended way to install Mamba is to use the latest version of the installer for your platform found in [conda-forge distribution](https://github.com/conda-forge/miniforge). 

### Creating a Mantid environment
Upon successful installation of Mamba, Mantid can be installed using
```bash
mamba create -n mantid_env -c mantid mantidworkbench
```
This environment can then be activated using
```bash
mamba activate mantid_env
```

### Cloning the repository and installing the `ridsans` package
Having installed Mantid, this repository can be cloned (or downloaded) 
Finally, the main `ridsans` package can be installed together with its dependencies  using
```bash
pip install -e .
```

Make sure to do this within the previously created environment by activating it if needed.


## Usage
For usage instructions, have a look at the [manual](docs/manual.md).

## Development
[ruff](https://docs.astral.sh/ruff/) is used as a formatter and linter and can be installed using `pip install ruff`.