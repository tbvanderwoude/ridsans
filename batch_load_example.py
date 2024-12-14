from batch_processing_RIDSANS import *

for index in range(0, 4):
    ws_sample, ws_direct, mon, ws_pixel_adj = load_batchfile_index_workspaces(
        index, "pixel-efficiency.txt.gz", "sans-batchfile.csv"
    )