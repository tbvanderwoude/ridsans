from ridsans.batch_processing import *
from ridsans.reduce import *

# In this example, measurement indices corresponding to four Q ranges
# for one sample are processed in separate calls to load_batchfile_index_workspaces.
# This means that transmission factors are calculated for all four independently in
# the intensity correction.

for index in range(0, 4):
    ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = (
        load_batchfile_index_workspaces(
            index,
            "pixel-efficiency.npy",
            "test-data/test.csv",
            directory="test-data",
        )
    )
    mask = LoadMask(
        "RIDSANS_Definition.xml",
        f"Q{Q_range_index}_mask.xml",
        OutputWorkspace=f"Q{Q_range_index}_mask",
    )
    print(index, ws_sample.name(), Q_range_index)

    reduction_setup_RIDSANS(ws_sample, ws_direct, mask_workspace=mask)

    reduced_ws_1D = reduce_RIDSANS_1D(ws_sample, ws_pixel_adj)
