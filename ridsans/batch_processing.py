from pathlib import Path

import pandas as pd
from mantid.api import AnalysisDataService as ADS

from ridsans.load import *


def load_measurement_set_workspaces(
    indices,
    efficiency_file,
    batch_filename="sans-batchfile.csv",
    directory="data",
    force_reload=False,
):
    """Given indices of a measurement set, this will read the provided batchfile and retrieve the workspaces either by loading them or
    retrieving them from the AnalysisDataService if available and force_reload is not set. It will automatically detect which of the
    indices corresponds to the widest Q range and use its measurement files for transmission factor calculation"""
    try:
        # Emulate absent workspace when force_reload is set
        if force_reload:
            raise KeyError("force_reload is set")
        return [
            retrieve_batchfile_index_workspaces(index, batch_filename, directory)
            for index in indices
        ]
    except KeyError:
        # Figure out how the indices map to Q ranges, sort these to start reducing the highest Q range
        index_to_Q = []
        for index in indices:
            Q_range = get_Q_range_id_from_batchfile_index(
                index, batch_filename, directory
            )
            index_to_Q.append((index, int(Q_range)))
        sorted_list = sorted(index_to_Q, key=lambda x: -x[1])
        print(sorted_list)

        transmissions = None
        result_list = []
        for index, _ in sorted_list:
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
                transmissions,
            )
            # The measurement that is first reduced (with the highest Q range due to sorting) determines the used transmission
            # factor for the other measurements
            if transmissions is None:
                T_sample = ws_sample.run().getProperty("T_sample").value
                T_can = ws_sample.run().getProperty("T_can").value
                transmissions = (T_sample, T_can)
            # Divides out the thickness from the sample to get result in units of
            # macroscopic scattering crossection [cm^-1]
            ws_sample /= thickness
            result_list.append((ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index))
        return result_list


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


def get_Q_range_id_from_batchfile_index(
    index, batch_filename="sans-batchfile.csv", directory="data"
):
    """Gets the Q range corresponding to a batchfile index."""
    batch = pd.read_csv(batch_filename)
    directory_path = Path(directory)
    row_list = dataframe_row_map(batch.iloc[index].tolist())
    *file_names, thickness = row_list
    x = [
        None if fname is None else (directory_path / fname).with_suffix(".mpa")
        for fname in file_names
    ]
    sample_scatter_file = x[0]
    sansdata = SansData(str(sample_scatter_file))
    return sansdata.Q_range_index


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
