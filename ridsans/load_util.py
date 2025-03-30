from multiprocessing import Pool

from ridsans.sansdata import *


def option_map(file_name):
    """Conceptually, this is a map on an Option type. So it passes None's but turns strings into SansData objects"""
    if file_name is not None:
        return SansData(str(file_name))
    else:
        return None


def load_measurement_files(
    file_list, plot_measurements=False, load_parallel=True, mp_pool_size=5
):
    """Loads all needed measurement files as SansData objects and plots these if plot_measurements is set. Uses a multiprocessing pool by default to speed up loading of files."""
    if load_parallel:
        with Pool(mp_pool_size) as p:
            loaded_list = p.map(
                option_map,
                file_list,
            )
    else:
        loaded_list = [option_map(file) for file in file_list]

    if plot_measurements:
        for x in loaded_list:
            if x is not None:
                x.plot_2d(True)
    return loaded_list
