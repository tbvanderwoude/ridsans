from batch_processing_RIDSANS import *
from reduce_RIDSANS import *
from mantid.api import AnalysisDataService as ADS

# mask_workspace = ADS.retrieve('MaskWorkspace')
for index in range(0, 4):
    ws_sample, ws_direct, mon, ws_pixel_adj = load_batchfile_index_workspaces(
        index, "pixel-efficiency.txt.gz", "sans-batchfile.csv"
    )
    print(index, ws_sample.name())
    
    reduction_setup_RIDSANS(ws_sample, ws_direct,mask_workspace = None)

    reduced_ws_1D = reduce_RIDSANS_1D(ws_sample, ws_pixel_adj)