from reduce_RIDSANS import *
from mantid.api import AnalysisDataService as ADS

i = 2
active_w = 0.15  # m
active_h = 0.15  # m

ws_sample = ADS.retrieve(f"data/sample1_Q{i}.mpa")
ws_direct = ADS.retrieve(f"data/no_cuvette_transmission_Q{i}.mpa")
ws_pixel_adj = ADS.retrieve("PixelAdj")

reduction_setup_RIDSANS(ws_sample, ws_direct, active_w, active_h)

reduced_ws_1D = reduce_RIDSANS_1D(ws_sample, ws_pixel_adj, active_w)
