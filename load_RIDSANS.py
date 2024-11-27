from mantid.simpleapi import *
from mantid.api import *
from mantid.kernel import *
from sansdata import *
from multiprocessing import Pool


def load_measurement_files(
    sample_scatter_file,
    sample_transmission_file,
    can_scatter_file,
    direct_file,
    background_file,
    plot_measurements=False,
):
    """Loads all needed measurement files as SansData objects and plots these if plot_measurements is set. Uses a multiprocessing pool to speed up loading of files."""
    with Pool(5) as p:
        sample_scatter, sample_transmission, can_scatter, direct, background = p.map(
            SansData,
            [
                sample_scatter_file,
                sample_transmission_file,
                can_scatter_file,
                direct_file,
                background_file,
            ],
        )
    if plot_measurements:
        sample_scatter.plot_2d(True)
        sample_transmission.plot_2d(True)
        can_scatter.plot_2d(True)
        direct.plot_2d(True)
    return sample_scatter, sample_transmission, can_scatter, direct, background


def create_pixel_adj_workspace(pixel_efficiencies, bins, detectors):
    """Creates a workspace from a NumPy array of pixel efficiencies to be used in Qxy or Q1D as PixelAdj."""
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
    """Compute tranmission factor assuming that the same attenuator is used, needs to be adjusted otherwise."""
    # TODO: Consider ROI for more accurate tranmission estimate (less noise)
    return np.sum(sample_transmission.I) / np.sum(direct.I)


def monochromatic_workspace(name, I, detector_position, bins, detectors, error=None):
    """Creates a monochromatic Mantid workspace from intensity I (can also be counts) together with precomputed bins and a detector position (relative to sample) along beam axis."""
    # Use the same bin for each detector
    x = np.tile(bins, detectors)

    ws = CreateWorkspace(
        OutputWorkspace=name,
        UnitX="Wavelength",
        DataX=x,
        DataY=I,
        DataE=error,
        NSpec=detectors,
    )
    mon = LoadInstrument(ws, FileName="RIDSANS_Definition.xml", RewriteSpectraMap=True)

    # Move sample to right position relative to detector
    # This needs to be set correctly for later reduction steps (Qxy/Q1D)
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
    # Sample transmission factor
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
    I_0 = np.sum(direct.I)

    # Ignore error T_sample, T_can and I_0
    # TODO: incorperate these errors for more accurate error calculation
    dI_corrected = (
        np.sqrt(
            (sample_scatter.dI**2 + background.dI**2) / (T_sample * T_can)
            + (can_scatter.dI**2 + background.dI**2) / (T_can)
        )
        / I_0
    )

    return monochromatic_workspace(
        sample_scatter.filename,
        I_corrected / I_0,
        sample_scatter.d,
        bins,
        detectors,
        error=dI_corrected,
    )


def create_monochrom_bin_bounds(L0, delta_L_over_L0=0.1):
    """Creates the wavelength bin boundaries from a central wavelength L0 with a certain spread."""
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
    """Loads a RIDSANS measurement into a sample workspace (with corrected intensity),
    a direct measurement workspace for beam centre finding and a pixel adjustment workspace.
    """
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
    del sample_scatter, sample_transmission, can_scatter, direct, background
    return ws_sample, ws_direct, mon, ws_pixel_adj
