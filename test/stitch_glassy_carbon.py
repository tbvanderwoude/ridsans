from mantid.api import AnalysisDataService as ADS
from mantid.simpleapi import *
from mantid.api import *
from mantid.kernel import *
from ridsans.stitch import *

workspaces = [ADS.retrieve(f"scattering_glassyC_Q{i}_Sigma/t_1D") for i in range(1, 5)]
stitched_ws, scale_factors = stitch_Q_ranges(workspaces)
