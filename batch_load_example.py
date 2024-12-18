from batch_processing_RIDSANS import *

for index in range(4,8):
    ws_sample, ws_direct, mon, ws_pixel_adj = load_batchfile_index_workspaces(
        index, "pixel-efficiency.txt.gz", "sans-batchfile.csv", directory = "sample-data"
    )