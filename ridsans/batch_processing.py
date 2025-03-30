from pathlib import Path

import pandas as pd
from mantid.api import AnalysisDataService as ADS

from ridsans.load import *


def load_batchfile_index_workspaces(
    index,
    efficiency_file,
    batch_filename="sans-batchfile.csv",
    directory="data",
    force_reload=False,
):
    """Given a row index (starting at 0), this will read the provided batchfile and retrieve the workspaces either by loading them or 
    retrieving them from the AnalysisDataService if available and force_reload is not set."""
    try:
        # Emulate absent workspace when force_reload is set
        if force_reload:
            raise KeyError("force_reload is set")
        return retrieve_batchfile_index_workspaces(index, batch_filename, directory)
    except KeyError:
        (
            sample_scatter_file,
            sample_transmission_file,
            can_scatter_file,
            can_transmission_file,
            direct_file,
            background_file,
            thickness,
        ) = get_file_data_from_batchfile_index(index, batch_filename, directory)
        ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = load_RIDSANS(
            sample_scatter_file,
            sample_transmission_file,
            can_scatter_file,
            can_transmission_file,
            direct_file,
            background_file,
            efficiency_file,
        )
        # Divides out the thickness from the sample to get result in units of
        # macroscopic scattering crossection [cm^-1]
        ws_sample /= thickness
        return ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index


def retrieve_batchfile_index_workspaces(
    index, batch_filename="sans-batchfile.csv", directory="data"
):
    """Retrieves previously loaded workspaces from the AnalysisDataService."""
    sample_scatter, direct, _ = get_workspace_data_from_batchfile_index(
        index, batch_filename, directory
    )
    ws_sample = ADS.retrieve(sample_scatter)
    ws_direct = ADS.retrieve(direct)
    ws_pixel_adj = ADS.retrieve("PixelAdj")
    Q_range_index = ws_sample.run().getProperty("Q_range_index").value
    return ws_sample, ws_direct, None, ws_pixel_adj, Q_range_index


def dataframe_row_map(filename_list):
    """In the batchfile, unnecessary files are indicated by the empty string. This is here converted to a None type for better semantics."""
    return [None if pd.isna(x) else x for x in filename_list]


def get_workspace_data_from_batchfile_index(
    index, batch_filename="sans-batchfile.csv", directory="data"
):
    """Gets the workspace names that can be used to retrieve previously loaded data."""
    batch = pd.read_csv(batch_filename)
    row_list = dataframe_row_map(batch.iloc[index].tolist())
    *file_names, thickness = row_list
    (
        sample_scatter,
        _,
        _,
        _,
        direct,
        _,
    ) = tuple(file_names)
    return (sample_scatter, direct, thickness)


def get_file_data_from_batchfile_index(
    index, batch_filename="sans-batchfile.csv", directory="data"
):
    """Gets the filenames needed to load the measurement workspaces."""
    batch = pd.read_csv(batch_filename)
    directory_path = Path(directory)
    row_list = dataframe_row_map(batch.iloc[index].tolist())
    *file_names, thickness = row_list
    x = [
        None if fname is None else (directory_path / fname).with_suffix(".mpa")
        for fname in file_names
    ]
    (
        sample_scatter_file,
        sample_transmission_file,
        can_scatter_file,
        can_transmission_file,
        direct_file,
        background_file,
    ) = tuple(x)
    return (
        sample_scatter_file,
        sample_transmission_file,
        can_scatter_file,
        can_transmission_file,
        direct_file,
        background_file,
        thickness,
    )
