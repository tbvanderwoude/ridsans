from ridsans.batch_processing import *
from ridsans.reduce import *

# Identical to reduce_set_glassy_carbon_1D.py but it loads the sample thickness from the file, not the CSV.

indices = range(0, 4)

workspaces = load_measurement_set_workspaces(
    indices,
    "pixel-efficiency.npy",
    "test-data/test-thickness.csv",
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

    reduced_ws_1D = reduce_RIDSANS_1D(ws_sample, ws_pixel_adj)
