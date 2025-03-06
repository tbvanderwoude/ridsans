from ridsans.batch_processing import *
from ridsans.reduce import *
from mantid.api import AnalysisDataService as ADS

for index in range(0, 4):
    # Requires mask files to be previously created and saved to files named
    # Q1_mask.xml, Q2_mask.xml etc.
    # These can be drawn and saved using the 'View Instrument' GUI 
    # on a scattering workspace 
    ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = load_batchfile_index_workspaces(
        index, "pixel-efficiency.txt.gz", "sans-batchfile.csv", directory="sample-data"
    )
    mask = LoadMask("RIDSANS_Definition.xml", f"Q{Q_range_index}_mask.xml")

    print(index, ws_sample.name())
    reduction_setup_RIDSANS(ws_sample, ws_direct, mask_workspace=mask)
    reduced_ws_1D = reduce_RIDSANS_1D(ws_sample, ws_pixel_adj)
