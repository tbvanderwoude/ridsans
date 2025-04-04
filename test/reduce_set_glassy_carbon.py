from ridsans.batch_processing import *
from ridsans.reduce import *

# This could also be a list like [0,1,2,3] or any other iterable
indices = range(0, 4)
workspaces = load_measurement_set_workspaces(
    indices,
    "pixel-efficiency.txt.gz",
    "test.csv",
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
