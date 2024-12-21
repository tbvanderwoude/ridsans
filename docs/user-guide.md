# User guide
There are two main ways of using the libraries in this repository to reduce RIDSANS data
1. Running Python scripts in the Mantid workbench
2. Using Jupyter notebooks together with the Mantid Python API

Option 1 has the advantage of making it easier to perform tasks like drawing masks on the measurement workspaces in a user-friendly interface whereas option 2 might be more familiar to those that have never used Mantid before. Notebooks can also be more convenient when making plots, as Mantid plotting by default is more suited for time-of-flight rather than 2D monochromatic scattering data.

Both options assume your data is stored in the `data` folder inside this repository and file and workspace names are relative to this. In some examples, all used file names are seperately specified as in [load_example.py](load_example.py). To facilitate processing of multiple measurements in a way [similar to that used at ISIS](https://www.isis.stfc.ac.uk/Pages/SANSdataReduction.aspx), the different file names for each measurement set can be specified in [sans-batchfile.csv](sans-batchfile.csv). For samples without a can (container), the `can scatter,can trans` columns can simply be left blank. You can simply enter the measurement numbers or if you prefer you can first rename all `.mpa` files to their respective sample names using the provided [data-renamer.py](data-renamer.py) script. 

### Method 1: Scripts in the workbench
To open the Mantid workbench, run
```bash
mantidworkbench
```
You can close the pop-up and go to File to open a script such as [load_example.py](load_example.py) or [batch_load_example.py](batch_load_example.py) if you want to use the batchfile approach to load data. Similarly, the [reduce_example.py](reduce_example.py) and [batch_reduce_example.py](batch_reduce_example.py) show how to reduce the data to workspaces that can be saved and viewed in SasView

### Method 2: Jupyter notebook
As an alternative, you can use a notebook like [reduction-example.ipynb](reduction-example.ipynb) to load and process various files and make plots. 