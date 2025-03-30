from ridsans.batch_processing import *
from ridsans.reduce import *

# mask_workspace = ADS.retrieve('MaskWorkspace')
for index in range(4, 8):
    ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = (
        load_batchfile_index_workspaces(
            index,
            "pixel-efficiency.txt.gz",
            "sans-batchfile.csv",
            directory="sample-data",
        )
    )
    print(index, ws_sample.name())

    reduction_setup_RIDSANS(ws_sample, ws_direct, mask_workspace=None)

    reduced_ws_1D = reduce_RIDSANS_1D(ws_sample, ws_pixel_adj)
