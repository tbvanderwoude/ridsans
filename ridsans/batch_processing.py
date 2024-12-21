import pandas as pd
from pathlib import Path
from ridsans.load import *
from mantid.api import AnalysisDataService as ADS


def load_batchfile_index_workspaces(
    index,
    efficiency_file,
    batch_filename="sans-batchfile.csv",
    directory="data",
    force_reload=False,
):
    """Get needed workspaces for reduction, retrieving these from the AnalysisDataService if available and force_reload is not set."""
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
        ) = get_filenames_from_batchfile_index(index, batch_filename, directory)
        ws_sample, ws_direct, mon, ws_pixel_adj = load_RIDSANS(
            sample_scatter_file,
            sample_transmission_file,
            can_scatter_file,
            can_transmission_file,
            direct_file,
            background_file,
            efficiency_file,
        )
        return ws_sample, ws_direct, mon, ws_pixel_adj


def retrieve_batchfile_index_workspaces(
    index, batch_filename="sans-batchfile.csv", directory="data"
):
    sample_scatter, direct = get_workspace_names_from_batchfile_index(
        index, batch_filename, directory
    )
    ws_sample = ADS.retrieve(sample_scatter)
    ws_direct = ADS.retrieve(direct)
    ws_pixel_adj = ADS.retrieve("PixelAdj")
    return ws_sample, ws_direct, None, ws_pixel_adj


def get_workspace_names_from_batchfile_index(
    index, batch_filename="sans-batchfile.csv", directory="data"
):
    batch = pd.read_csv(batch_filename)
    row_list = [None if pd.isna(x) else x for x in batch.iloc[index].tolist()]
    x = [None if fname is None else fname for fname in row_list]
    (
        sample_scatter,
        _,
        _,
        _,
        direct,
        _,
    ) = tuple(x)
    return (sample_scatter, direct)


def get_filenames_from_batchfile_index(
    index, batch_filename="sans-batchfile.csv", directory="data"
):
    batch = pd.read_csv(batch_filename)
    directory_path = Path(directory)
    row_list = [None if pd.isna(x) else x for x in batch.iloc[index].tolist()]
    x = [
        None if fname is None else (directory_path / fname).with_suffix(".mpa")
        for fname in row_list
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
    )
