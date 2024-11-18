from mantid.simpleapi import *

# from mantid.api import AnalysisDataService as ADS
from mantid.api import *
from mantid.kernel import *
from sansdata import *


def load_measurement_files(
    sample_scatter_file,
    sample_transmission_file,
    can_scatter_file,
    direct_file,
    background_file,
    plot_measurements=False,
):
    sample_scatter = SansData(sample_scatter_file)
    sample_transmission = SansData(sample_transmission_file)
    can_scatter = SansData(can_scatter_file)
    direct = SansData(direct_file)
    background = SansData(background_file)
    if plot_measurements:
        sample_scatter.plot_2d(True)
        sample_transmission.plot_2d(True)
        can_scatter.plot_2d(True)
        direct.plot_2d(True)
    return sample_scatter, sample_transmission, can_scatter, direct, background


def create_pixel_adj_workspace(pixel_efficiencies, bins, detectors):
    x = np.tile(bins, detectors)
    y = pixel_efficiencies
    y[y <= 0] = 1
    pixel_adj = CreateWorkspace(
        OutputWorkspace="PixelAdj",
        UnitX="Wavelength",
        DataX=x,
        DataY=y,
        NSpec=detectors,
    )
    return pixel_adj


def compute_tranmission_factor(sample_transmission, direct):
    """Compute tranmission factor assuming that the same attenuator is used, needs to be adjusted otherwise"""
    # TODO: Consider ROI for more accurate tranmission estimate (less noise)
    return np.sum(sample_transmission.I) / np.sum(direct.I)


def monochromatic_workspace(name, I, detector_position, bins, detectors):
    # Use the same bin for each detector
    x = np.tile(bins, detectors)

    ws = CreateWorkspace(
        OutputWorkspace=name, UnitX="Wavelength", DataX=x, DataY=I, NSpec=detectors
    )
    mon = LoadInstrument(ws, FileName="RIDSANS_Definition.xml", RewriteSpectraMap=True)
    MoveInstrumentComponent(
        ws,
        ComponentName="sample-position",
        X=0.0,
        Y=0.0,
        Z=-detector_position,
        RelativePosition=False,
    )
    return ws, mon


def workspace_from_sansdata(sansdata, bins, detectors):
    return monochromatic_workspace(
        sansdata.filename, sansdata.I, sansdata.d, bins, detectors
    )


def workspace_from_measurement(
    sample_scatter,
    sample_transmission,
    can_scatter,
    direct,
    background,
    bins,
    detectors,
):
    """Creates a workspace with scaled intensity in counts/s"""
    # Use the same bin for each detector
    x = np.tile(bins, detectors)
    # Can (container) transmission factor
    T_sample = compute_tranmission_factor(sample_transmission, direct)
    # Can (container) transmission factor
    T_can = (
        1.0  # Ideally to be computed from can_transmission measurement, not present?
    )

    print(f"Transmission factor: T_sample = {T_sample}")

    # Corrected intensity considering background and tranmission factors of sample and can.
    I_corrected = 1 / (T_sample * T_can) * (
        sample_scatter.I - background.I
    ) - 1 / T_can * (can_scatter.I - background.I)
    return monochromatic_workspace(
        sample_scatter.filename, I_corrected, sample_scatter.d, bins, detectors
    )


def create_monochrom_bin_bounds(L0, delta_L_over_L0=0.1):
    bin_lower = L0 * (1.0 - delta_L_over_L0 / 2)
    bin_upper = L0 * (1.0 + delta_L_over_L0 / 2)
    return [bin_lower, bin_upper]


def load_RIDSANS_from_sansdata(
    sample_scatter,
    sample_transmission,
    can_scatter,
    direct,
    background,
    relative_pixel_efficiency,
):
    bins = create_monochrom_bin_bounds(sample_scatter.L0)
    detectors = sample_scatter.pixel_count
    pixel_adj = create_pixel_adj_workspace(relative_pixel_efficiency, bins, detectors)
    ws_sample, mon = workspace_from_measurement(
        sample_scatter,
        sample_transmission,
        can_scatter,
        direct,
        background,
        bins,
        detectors,
    )
    ws_direct, _ = workspace_from_sansdata(direct, bins, detectors)
    return ws_sample, ws_direct, mon, pixel_adj


def load_RIDSANS(
    sample_scatter_file,
    sample_transmission_file,
    can_scatter_file,
    direct_file,
    background_file,
    efficiency_file,
):
    print("Starting load_RIDSANS")
    relative_pixel_efficiency = np.loadtxt(efficiency_file)
    sample_scatter, sample_transmission, can_scatter, direct, background = (
        load_measurement_files(
            sample_scatter_file,
            sample_transmission_file,
            can_scatter_file,
            direct_file,
            background_file,
        )
    )
    ws_sample, ws_direct, mon, ws_pixel_adj = load_RIDSANS_from_sansdata(
        sample_scatter,
        sample_transmission,
        can_scatter,
        direct,
        background,
        relative_pixel_efficiency,
    )
    return ws_sample, ws_direct, mon, ws_pixel_adj


if __name__ == "__main__":
    i = 3
    sample_scatter_file = f"data/sample1_Q{i}.mpa"
    sample_transmission_file = f"data/sample_transmission_Q{i}.mpa"
    can_scatter_file = f"data/sample_empty_cuvette_Q{i}.mpa"
    efficiency_file = "pixel-efficiency.txt.gz"
    # I think this translates to direct, not sure
    direct_file = f"data/no_cuvette_transmission_Q{i}.mpa"
    background_file = f"data/old-data/09_07_24_backG_3600s_reactor_on_Fish_on.mpa"
    load_RIDSANS(
        sample_scatter_file,
        sample_transmission_file,
        can_scatter_file,
        direct_file,
        background_file,
        efficiency_file,
    )
