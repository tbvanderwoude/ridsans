from ridsans.batch_processing import *
from ridsans.reduce import *
from mantid.api import AnalysisDataService as ADS

for index in range(0, 4):
    i = index + 1
    mask = LoadMask("RIDSANS_Definition.xml", f"Q{i}_mask.xml",OutputWorkspace=f"Q{i}_mask")
    ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = load_batchfile_index_workspaces(
        index,
        "pixel-efficiency.txt.gz",
        "test.csv",
        directory="test-data",
    )
    print(index, ws_sample.name(), Q_range_index)

    reduction_setup_RIDSANS(ws_sample, ws_direct, mask_workspace=mask)

    reduced_ws_1D = reduce_RIDSANS_1D(ws_sample, ws_pixel_adj)
