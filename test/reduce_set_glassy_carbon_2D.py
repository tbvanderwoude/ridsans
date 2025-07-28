from ridsans.batch_processing import *
from ridsans.reduce import *
from ridsans.save import * 

# This example is analogous to reduce_set_glassy_carbon_1D for a 2D reduction, which is useful for
# anisotropic samples.

indices = range(0, 4)

workspaces = load_measurement_set_workspaces(
    indices,
    "pixel-efficiency.npy",
    "test-data/test.csv",
    directory="test-data",
)
for ws_sample, ws_direct, _, ws_pixel_adj, Q_range_index in workspaces:
    mask = LoadMask(
        "RIDSANS_Definition.xml",
        f"Q{Q_range_index}_mask.xml",
        OutputWorkspace=f"Q{Q_range_index}_mask",
    )
    print(ws_sample.name(), Q_range_index)

    reduction_setup_RIDSANS(ws_sample, ws_direct, mask_workspace=mask)

    reduced_ws_2D = reduce_RIDSANS_2D(ws_sample, ws_pixel_adj, number_of_bins=64)
    save_2D(reduced_ws_2D)