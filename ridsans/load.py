from mantid.simpleapi import *
from mantid.api import *
from mantid.kernel import *
from ridsans.sansdata import *
from multiprocessing import Pool


# A map on an Option type conceptually
def option_map(file_name):
    if file_name is not None:
        return SansData(str(file_name))
    else:
        return None


def load_measurement_files_sequential(
    file_list,
    plot_measurements=False,
):
    """Loads all needed measurement files as SansData objects and plots these if plot_measurements is set."""
    loaded_list = [option_map(file) for file in file_list]
    if plot_measurements:
        for x in loaded_list:
            if x is not None:
                x.plot_2d(True)
    return loaded_list


def load_measurement_files(
    file_list,
    plot_measurements=False,
):
    """Loads all needed measurement files as SansData objects and plots these if plot_measurements is set. Uses a multiprocessing pool to speed up loading of files."""

    with Pool(5) as p:
        loaded_list = p.map(
            option_map,
            file_list,
        )
    if plot_measurements:
        for x in loaded_list:
            if x is not None:
                x.plot_2d(True)
    return loaded_list


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


def compute_transmission_factor(sample_transmission, direct):
    """Compute tranmission factor assuming that the same attenuator is used, needs to be adjusted otherwise."""
    # Compensates for slight variations between beam intensity for sample and empty transmission measurements
    beam_variation_factor = direct.I_0 / sample_transmission.I_0
    # TODO: Consider ROI for more accurate tranmission estimate (less signal to noise)
    return np.sum(sample_transmission.I) / np.sum(direct.I) * beam_variation_factor


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
        sansdata.name, sansdata.I, sansdata.d, bins, detectors
    )


def workspace_from_measurement(
    sample_scatter,
    sample_transmission,
    can_scatter,
    can_transmission,
    direct,
    background,
    bins,
    detectors,
):
    """Creates a workspace with scaled intensity in counts/s"""
    # Sample transmission factor
    T_sample = compute_transmission_factor(sample_transmission, direct)
    # Can (container) transmission factor
    T_can = (
        1.0  # Ideally to be computed from can_transmission measurement, not present?
    )

    # If can transmission measurement is included
    if can_transmission is not None:
        T_can = compute_transmission_factor(can_transmission, direct)

    print(f"Transmission factors: T_sample = {T_sample}; T_can = {T_can}")

    # Compensate for a differing monitor flux-ratio between scatter and transmission measurement
    # The monitor count indicates what the total rate of neutrons
    # entering the instrument from the beamline is
    flux_factor = sample_scatter.I_0 / direct.I_0

    # Normalize scattering by the direct intensity
    # times the monitor flux ratio of scatter/transmission measurements
    # This effectively transforms the total detector count of the direct measurement
    # to an estimate of what the total detector count would be at the adjusted flux
    I_0 = flux_factor * np.sum(direct.I)

    # Corrected intensity considering background and tranmission factors of sample and can.
    if can_scatter is not None:
        # A can is used

        # There can be slight differences in the beamline intensity between can and sample
        # measurements, corrects for this
        sample_can_ratio = can_scatter.I_0 / sample_scatter.I_0
        if can_transmission is not None:
            I_corrected = (
                1 / (T_sample * T_can) * (sample_scatter.I - background.I)
                - 1 / T_can * (can_scatter.I*sample_can_ratio - background.I)
            ) / I_0

            # Ignore error T_sample, T_can and I_0
            # TODO: incorperate these errors for more accurate error calculation
            # TODO: correct formula as background contributions here are correlated and not independent
            dI_corrected = (
                np.sqrt(
                    (sample_scatter.dI**2 + background.dI**2) / (T_sample * T_can) ** 2
                    + ((can_scatter.dI * sample_can_ratio)**2 + background.dI**2) / (T_can) ** 2
                )
                / I_0
            )
        else:
            # Per the formula, when the same transmission is used for sample and can scattering,
            # the background cancels... Feels dubious
            # TODO: verify this is allowed
            I_corrected = (1 / T_sample * (sample_scatter.I - can_scatter.I)) / I_0

            # Ignore error T_sample, T_can and I_0
            # TODO: incorperate these errors for more accurate error calculation
            dI_corrected = (
                np.sqrt((sample_scatter.dI**2 + can_scatter.dI**2) / T_sample**2) / I_0
            )
    else:
        # Assume no can is used as when using solid samples, crystals etc. or that its effect is ignored
        I_corrected = 1 / T_sample * (sample_scatter.I - background.I) / I_0

        # Ignore error T_sample and I_0
        dI_corrected = (
            np.sqrt((sample_scatter.dI**2 + background.dI**2) / (T_sample)) / I_0
        )

    return monochromatic_workspace(
        sample_scatter.name,
        I_corrected,
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
    can_transmission,
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
        can_transmission,
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
    can_transmission_file,
    direct_file,
    background_file,
    efficiency_file,
):
    """Loads a RIDSANS measurement into a sample workspace (with corrected intensity),
    a direct measurement workspace for beam centre finding and a pixel adjustment workspace.

    Supports three variants of inputs:
    - A sample scatter and transmission (for samples that don't need a container)
    - A sample scatter and transmission and can scatter (neglects can transmission)
    - A sample and can scatter and transmission to make calculation of sample and can transmission factors possible
    """
    print("Starting load_RIDSANS")
    relative_pixel_efficiency = np.loadtxt(efficiency_file)
    file_list = [
        sample_scatter_file,
        sample_transmission_file,
        can_scatter_file,
        can_transmission_file,
        direct_file,
        background_file,
    ]
    (
        sample_scatter,
        sample_transmission,
        can_scatter,
        can_transmission,
        direct,
        background,
    ) = load_measurement_files(file_list)
    ws_sample, ws_direct, mon, ws_pixel_adj = load_RIDSANS_from_sansdata(
        sample_scatter,
        sample_transmission,
        can_scatter,
        can_transmission,
        direct,
        background,
        relative_pixel_efficiency,
    )
    del sample_scatter, sample_transmission, can_scatter, direct, background
    return ws_sample, ws_direct, mon, ws_pixel_adj
