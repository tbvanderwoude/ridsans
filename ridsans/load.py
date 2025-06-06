from mantid.api import *
from mantid.api import AnalysisDataService as ADS
from mantid.kernel import *
from mantid.simpleapi import *

from ridsans.load_util import *
from ridsans.sansdata import *


def create_pixel_adj_workspace(pixel_efficiencies, bins, detectors, force_reload=False):
    """Creates a workspace from a NumPy array of pixel efficiencies to be used in Qxy or Q1D as PixelAdj. Retrieves it from the AnalysisDataService if it is already loaded and force_reload is not set."""
    x = np.tile(bins, detectors)
    y = pixel_efficiencies[:, :, 0]
    e = pixel_efficiencies[:, :, 1]
    y[y <= 0] = 1
    try:
        if force_reload:
            raise KeyError("force_reload is set")
        pixel_adj = ADS.retrieve("PixelAdj")
    except KeyError:
        pixel_adj = CreateWorkspace(
            OutputWorkspace="PixelAdj",
            UnitX="Wavelength",
            DataX=x,
            DataY=y,
            DataE=e,
            NSpec=detectors,
        )
    return pixel_adj


def compute_transmission_factor(sample_transmission, direct, background):
    """Compute tranmission factor assuming that the same attenuator is used, needs to be adjusted otherwise."""
    # Compensates for slight variations between beam intensity for sample and empty transmission measurements
    beam_variation_factor = direct.I_0 / sample_transmission.I_0
    # It is important to correct for background to avoid overestimating the transmission
    return np.sum(
        sample_transmission.I * beam_variation_factor - background.I
    ) / np.sum(direct.I - background.I)


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
    """Helper function to pass SansData fields into monochromatic_workspace"""
    return monochromatic_workspace(
        sansdata.name, sansdata.I, sansdata.d, bins, detectors
    )


def check_transmission_coefficients(T_sample, T_can):
    """Checks transmission coefficients, giving hard errors for values outside of the 0 to 1 range and correctness warnings for low coefficients."""
    # Hard errors for T_sample, T_can outside of 0 to 1 range
    if T_sample < 0.0:
        print(
            f"Warning: T_sample is greater smaller than 0 (T_can = {T_can}), signal strength might be too low."
        )
    if T_sample > 1.0:
        # In principle, there are samples that could give a netto increase in neutrons...
        print(
            f"Warning: T_sample is greater than one (T_can = {T_can}), signal strength might be too low."
        )
    if T_can < 0.0:
        print(
            f"Warning: T_can is greater smaller than 0 (T_can = {T_can}), signal strength might be too low."
        )
    if T_can > 1.0:
        print(
            f"Warning: T_can is greater than one (T_can = {T_can}), signal strength might be too low."
        )

    # Warnings for inadequate transmission coefficients, this indicates the single scattering limit does not exactly apply
    if T_can < 0.8:
        print(
            f"Warning: T_can is low (T_can = {T_can} < 0.8), multiple scattering cannot be neglected."
        )
    if T_sample < 0.8:
        print(
            f"Warning: T_sample is low (T_sample = {T_sample} < 0.8), multiple scattering cannot be neglected."
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
    transmissions=None,
):
    """Reduces the different measurements to a single corrected intensity following a formalism similar to that discussed in
    Dewhurst, C. D. (2023). J. Appl. Cryst. 56, 1595-1609. It returns this reduced scattering workspace in addition to a monitor
    object which is currently not used and the id of the Q range (1 - 4 currently).
    """
    if transmissions is not None:
        if len(transmissions) != 2:
            raise ValueError(
                "Length of transmissions passed to reduction should be two, a value of the form [T_sample, T_can] is expected."
            )
        T_sample, T_can = transmissions
        T_sample_can = T_sample * T_can
    else:
        # Transmission factor of sample and can together
        T_sample_can = compute_transmission_factor(
            sample_transmission, direct, background
        )
        # Can (container) transmission factor
        T_can = 1.0  # Ideally to be computed from can_transmission measurement, not present?

        # If can transmission measurement is included
        if can_transmission is not None:
            T_can = compute_transmission_factor(can_transmission, direct, background)
        if T_can == 0.0:
            raise ValueError("T_can is zero, please check your input workspaces.")
        T_sample = T_sample_can / T_can
    print(f"Transmission factors: T_sample = {T_sample}; T_can = {T_can}")

    check_transmission_coefficients(T_sample, T_can)

    # Compensate for a differing monitor flux-ratio between scatter and transmission measurement
    # The monitor count indicates what the total rate of neutrons
    # entering the instrument from the beamline is
    flux_factor = sample_scatter.I_0 / direct.I_0

    # Normalize scattering by the direct intensity
    # times the monitor flux ratio of scatter/transmission measurements
    # This effectively transforms the total detector count of the direct measurement
    # to an estimate of what the total detector count would be at the adjusted flux

    # In other words, this gives an estimate of the the total empty beam intensity
    # at the flux of the scattering measurement
    I_0 = flux_factor * np.sum(direct.I)

    # Corrected intensity considering background and tranmission factors of sample and can.
    if can_scatter is not None:
        # A can is used

        # There can be slight differences in the beamline intensity between can and sample
        # measurements, corrects for this
        sample_can_ratio = can_scatter.I_0 / sample_scatter.I_0
        if can_transmission is not None:
            I_corrected = (
                1 / (T_sample_can) * (sample_scatter.I - background.I)
                - 1 / T_can * (can_scatter.I * sample_can_ratio - background.I)
            ) / I_0

            # Ignore error T_sample, T_can and I_0
            # TODO: incorperate these errors for more accurate error calculation
            # TODO: correct formula as background contributions here are correlated and not independent
            dI_corrected = (
                np.sqrt(
                    (sample_scatter.dI**2 + background.dI**2) / (T_sample_can) ** 2
                    + ((can_scatter.dI * sample_can_ratio) ** 2 + background.dI**2)
                    / (T_can) ** 2
                )
                / I_0
            )
        else:
            # Per the formula, when the same transmission is used for sample and can scattering,
            # the background cancels...
            # TODO: verify this is allowed
            I_corrected = (
                1 / T_sample * (sample_scatter.I - can_scatter.I * sample_can_ratio)
            ) / I_0

            # Ignore error T_sample, T_can and I_0
            # TODO: incorperate these errors for more accurate error calculation
            dI_corrected = np.sqrt(
                sample_scatter.dI**2 + (can_scatter.dI * sample_can_ratio) ** 2
            ) / (T_sample * I_0)
    else:
        # Assume no can is used as when using solid samples, crystals etc. or that its effect is ignored
        I_corrected = 1 / T_sample * (sample_scatter.I - background.I) / I_0

        # Ignore error T_sample and I_0
        dI_corrected = np.sqrt(sample_scatter.dI**2 + background.dI**2) / (
            T_sample * I_0
        )
    ws, mon = monochromatic_workspace(
        sample_scatter.name,
        I_corrected,
        sample_scatter.d,
        bins,
        detectors,
        error=dI_corrected,
    )
    # Including the transmissions as property of the workspace enables easy retrieval for transmission factor reuse
    ws.getRun().addProperty("T_sample", float(T_sample), True)
    ws.getRun().addProperty("T_can", float(T_can), True)
    return (
        ws,
        mon,
        sample_scatter.Q_range_index,
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
    transmissions=None,
):
    """This is used by load_RIDSANS, taking SansData objects instead of filenames."""
    bins = create_monochrom_bin_bounds(sample_scatter.L0)
    detectors = sample_scatter.pixel_count
    pixel_adj = create_pixel_adj_workspace(relative_pixel_efficiency, bins, detectors)
    ws_sample, mon, Q_range_index = workspace_from_measurement(
        sample_scatter,
        sample_transmission,
        can_scatter,
        can_transmission,
        direct,
        background,
        bins,
        detectors,
        transmissions,
    )
    ws_direct, _ = workspace_from_sansdata(direct, bins, detectors)
    ws_sample.getRun().addProperty("Q_range_index", Q_range_index, True)
    ws_direct.getRun().addProperty("Q_range_index", Q_range_index, True)
    return ws_sample, ws_direct, mon, pixel_adj, Q_range_index


def load_RIDSANS(
    sample_scatter_file,
    sample_transmission_file,
    can_scatter_file,
    can_transmission_file,
    direct_file,
    background_file,
    efficiency_file,
    transmissions=None,
):
    """Loads a RIDSANS measurement into a sample workspace (with corrected intensity),
    a direct measurement workspace for beam centre finding and a pixel adjustment workspace.

    Supports three variants of inputs:
    - A sample scatter and transmission (for samples that do not need a container)
    - A sample scatter and transmission and can scatter (neglects can transmission)
    - A sample and can scatter and transmission to make calculation of sample and can transmission factors possible
    """
    print("Starting load_RIDSANS")
    relative_pixel_efficiency = np.load(efficiency_file)
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
    ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index = load_RIDSANS_from_sansdata(
        sample_scatter,
        sample_transmission,
        can_scatter,
        can_transmission,
        direct,
        background,
        relative_pixel_efficiency,
        transmissions,
    )
    del sample_scatter, sample_transmission, can_scatter, direct, background
    return ws_sample, ws_direct, mon, ws_pixel_adj, Q_range_index
