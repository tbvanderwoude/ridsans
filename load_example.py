from load_RIDSANS import *

i = 3
sample_scatter_file = f"data/sample1_Q{i}.mpa"
sample_transmission_file = f"data/sample_transmission_Q{i}.mpa"
can_scatter_file = f"data/sample_empty_cuvette_Q{i}.mpa"
efficiency_file = "pixel-efficiency.txt.gz"
# I think this translates to direct, not sure
direct_file = f"data/no_cuvette_transmission_Q{i}.mpa"
background_file = f"data/old-data/09_07_24_backG_3600s_reactor_on_Fish_on.mpa"
ws_sample, ws_direct, mon, ws_pixel_adj = load_RIDSANS(
    sample_scatter_file,
    sample_transmission_file,
    can_scatter_file,
    direct_file,
    background_file,
    efficiency_file,
)
