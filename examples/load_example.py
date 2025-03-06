from ridsans.load import *

i = 3
sample_scatter_file = f"sample-data/Niels_sample1_Q{i}.mpa"
sample_transmission_file = f"sample-data/Niels_sample_transmission_Q{i}.mpa"
can_scatter_file = f"sample-data/Niels_sample_empty_cuvette_Q{i}.mpa"
efficiency_file = "pixel-efficiency.txt.gz"
# I think this translates to direct, not sure
direct_file = f"sample-data/Niels_no_cuvette_transmission_Q{i}.mpa"
background_file = f"sample-data/Background_Q{i}.mpa"
ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = load_RIDSANS(
    sample_scatter_file,
    sample_transmission_file,
    can_scatter_file,
    None,
    direct_file,
    background_file,
    efficiency_file,
)
