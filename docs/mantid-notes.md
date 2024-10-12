# Mantid development notes

## 1. High-level reduction workflow
Practical reduction scripts appear to use the [reduction_workflow](https://github.com/mantidproject/mantid/tree/25060ccc17bbc3bba4ed9c564b9407fa84395513/scripts/reduction_workflow) package (in the `scripts/` folder of mantid). Command interfaces are defined (e.g. for [HFIR SANS at ORNL](https://github.com/mantidproject/mantid/blob/25060ccc17bbc3bba4ed9c564b9407fa84395513/scripts/reduction_workflow/instruments/sans/hfir_command_interface.py)) that as a rule manipulate a [`Reducer`](https://github.com/mantidproject/mantid/blob/25060ccc17bbc3bba4ed9c564b9407fa84395513/scripts/reduction_workflow/reducer.py) singleton called [`ReductionSingleton`](https://github.com/mantidproject/mantid/blob/25060ccc17bbc3bba4ed9c564b9407fa84395513/scripts/reduction_workflow/command_interface.py#L15).

[`Reducer`](https://github.com/mantidproject/mantid/blob/25060ccc17bbc3bba4ed9c564b9407fa84395513/scripts/reduction_workflow/reducer.py)is a high-level class that is responsible for four key things
- Loading the instrument
- Storing all the [reduction_properties] or settings that are fed into the reduction process
- Running any reduction setup algorithm like [SetupHFIRReduction](https://docs.mantidproject.org/v3.10.1/algorithms/SetupHFIRReduction-v1.html). 
- feeding the right files into specific reduction algorithms like [HFIRSANSReduction](https://docs.mantidproject.org/nightly/algorithms/HFIRSANSReduction-v1.html#algm-hfirsansreduction)

Looking at a [SANS command interface](https://github.com/mantidproject/mantid/blob/25060ccc17bbc3bba4ed9c564b9407fa84395513/scripts/reduction_workflow/instruments/sans/hfir_command_interface.py), almost all of the commands after initialization set `reduction_properties` of the singleton. They also get instrument properties through calls like 
```python
sample_spreader_data = find_data(sample_spreader, instrument = ReductionSingleton().get_instrument())
```

`reduction_properties` are fed into the chosen setup algorithm once for all data in the `Reducer.pre_process` step. 

## 2. Setup and reduction algorithm
There is a C++ API used by older algorithms and a newer Python API that appears to be used typically now. For instance, [SetupHFIRReduction](https://github.com/mantidproject/mantid/blob/ff859df4a5faa6fa5e3cecb8f2efeb4c4aa53864/Framework/WorkflowAlgorithms/src/SetupHFIRReduction.cpp) is written in C++ whereas [HFIRSANSReduction](https://github.com/mantidproject/mantid/blob/25060ccc17bbc3bba4ed9c564b9407fa84395513/Framework/PythonInterface/plugins/algorithms/WorkflowAlgorithms/HFIRSANSReduction.py) is written in Python. Both interfaces can subscribe algorithms to the `AlgorithmFactory`, making the distinction invisible when using them (except for performance etc.). This `AlgorithmFactory` contains the algorithms which are executed by the `Reducer`. 

## 3. Bolts and nuts of monochromatic Sans

GPSANS etc. use a custom XML format called Spice2D. This is loaded by [LoadSpice2D](https://github.com/mantidproject/mantid/blob/c581f90f7efa314220c83ad80b7f332baec7a80f/Framework/DataHandling/src/LoadSpice2D.cpp). This creates a WorkSpace2D. "Note that this type of data doesn't use TOD, so that we use a single dummy bin in X. Each detector is defined as a spectrum of length 1."

Workspaces can be created using [CreateWorkspace](https://docs.mantidproject.org/nightly/algorithms/CreateWorkspace-v1.html#algm-createworkspace), using the trick used by LoadSpice2D to simply have a single bin per 