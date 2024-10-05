# Useful resources
A list of useful resources related to SANS data reduction in Python

## NeXuS

Standard format for neutron experimental data Mantid uses. Current SANS measurement file format is non-standard

- [SAS NeXuS application definition for raw 2D SANS measurement](https://manual.nexusformat.org/classes/applications/NXsas.html)
- [Introduction to working with nexusformat in Python](https://nexpy.github.io/nexpy/pythonshell.html)
- [Related standard format for reduced SAS](https://wiki.cansas.org/index.php/NXcanSAS) that is [compatible with SasView ](https://www.sasview.org/docs/user/qtgui/MainWindow/data_formats_help.html) etc.

## Mantid

Mantid works using `.raw` and `.nxs` (NeXuS) files. These are HDF5 type files with additional metadata. Emphasis is on TOF but it should be possible to make it work for a basic SANS measurement.

- [Basic Mantid Python tutorial](https://docs.mantidproject.org/nightly/tutorials/python_in_mantid/index.html)
- [Mantid Python API documentation](https://docs.mantidproject.org/nightly/api/python/mantid/index.html)
- [Mantid project forum](https://forum.mantidproject.org/t/welcome-to-the-mantid-forums/8)
- [Practical discussion of ISIS SANS data analysis using the GUI](https://archive.mantidproject.org/SANS_Data_Analysis_at_ISIS.html)
- [Technical overview of ISIS SANS reduction backend](https://developer.mantidproject.org/ISISSANSReductionBackend.html#work-flow-algorithm-orchestration)

## Existing monochromatic SANS in Mantid
- Oak Ridge National Laboratory SANS
  - [Normal](https://docs.mantidproject.org/nightly/concepts/ORNL_SANS_Reduction.html)
  - [HFIR SANS specific](https://docs.mantidproject.org/nightly/algorithms/HFIRSANSReduction-v1.html#algm-hfirsansreduction)

## OpenCV
- [Thresholding in OpenCV (for detecting the beam stop?)](https://docs.opencv.org/3.4/d7/d4d/tutorial_py_thresholding.html)