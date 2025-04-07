from ridsans.batch_processing import *
from ridsans.reduce import *

# This example is analogous to reduce_glassy_carbon_1D for a 2D reduction, which is useful for
# anisotropic samples.

for index in range(0, 4):
    ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = (
        load_batchfile_index_workspaces(
            index,
            "pixel-efficiency.npy",
            "test.csv",
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

    reduced_ws_2D = reduce_RIDSANS_2D(ws_sample, ws_pixel_adj, number_of_bins=64)
