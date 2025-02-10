from ridsans.reduce import *
from mantid.api import AnalysisDataService as ADS

i = 3

ws_sample = ADS.retrieve(f"Niels_sample1_Q{i}")
ws_direct = ADS.retrieve(f"Niels_no_cuvette_transmission_Q{i}")
# mask_workspace = ADS.retrieve("MaskWorkspace")
ws_pixel_adj = ADS.retrieve("PixelAdj")

reduction_setup_RIDSANS(ws_sample, ws_direct, mask_workspace=None)

reduced_ws_2D = reduce_RIDSANS_1D(ws_sample, ws_pixel_adj)
