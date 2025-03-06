from ridsans.batch_processing import *

for index in range(4, 8):
    ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = (
        load_batchfile_index_workspaces(
            index,
            "pixel-efficiency.txt.gz",
            "sans-batchfile.csv",
            directory="sample-data",
        )
    )
