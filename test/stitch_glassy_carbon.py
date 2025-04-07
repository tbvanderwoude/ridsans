from mantid.api import *
from mantid.api import AnalysisDataService as ADS
from mantid.kernel import *
from mantid.simpleapi import *

from ridsans.save import save
from ridsans.stitch import *

# After running one of the reduction scripts, the scattering workspaces can
# be retrieved from the AnalysisDataService

workspaces = [
    ADS.retrieve(f"scattering_0_25mm_glassy_C_Q{i}_dSigma/dOmega_1D")
    for i in range(1, 5)
]
stitched_ws, scale_factors = stitch_Q_ranges_1D(workspaces)
print(scale_factors)
save(stitched_ws, "glassy_carbon")
