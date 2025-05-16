import numpy as np
from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *

from ridsans.sansdata import active_w


def mask_rectangle(ws, w, h, negative=False, offset_x=0, offset_y=0):
    """Masks a rectangle of a given width and height centered at an offset on a given workspace."""
    mask_list = []
    for i in range(ws.getNumberHistograms()):
        detector = ws.getDetector(i)
        # Get the position of the detector
        position = detector.getPos()
        if (
            abs(position.getX() - offset_x) > w / 2
            or abs(position.getY() - offset_y) > h / 2
        ) == (not negative):
            mask_list.append(i + 1)
    MaskDetectors(Workspace=ws, SpectraList=mask_list)


def mask_circle(ws, r, negative=False, offset_x=0, offset_y=0):
    """Masks a circle of a given radius centered at an offset on a given workspace."""
    mask_list = []
    for i in range(ws.getNumberHistograms()):
        detector = ws.getDetector(i)
        # Get the position of the detector
        position = detector.getPos()
        dist = np.sqrt(
            (position.getX() - offset_x) ** 2 + (position.getY() - offset_y) ** 2
        )
        if (dist > r) == (not negative):
            mask_list.append(i + 1)
    MaskDetectors(Workspace=ws, SpectraList=mask_list)


def reduction_setup_RIDSANS(
    ws_sample, ws_direct, ROI=None, mask_workspace=None, center_workspace=None
):
    """Finds the beam center if no center_workspace is provided and optionally applies a mask"""
    # STEP 1: find beam centre from direct beam
    # Compute the center position, which will be put in a table workspace

    # Uses direct beam method
    if center_workspace is None:
        center = FindCenterOfMassPosition(ws_direct, Output="center", Tolerance=0.0005)
    else:
        center = center_workspace
    center_x, center_y = center.column(1)
    print(f"(x, y) = ({center_x:.4f}, {center_y:.4f})")

    # Idea: move detector based on beamstop position to compensate for shift
    # Does this actually make sense? It seems to be only valid assuming a small shift
    MoveInstrumentComponent(
        ws_sample,
        ComponentName="detector-bank",
        X=-center_x,
        Y=-center_y,
        Z=0.0,
        RelativePosition=False,
    )

    # STEP 2: apply masks
    if ROI is not None:
        # TODO: ensure that choice of circle center is correct
        mask_circle(ws_sample, ROI, True)

    if mask_workspace is not None:
        MaskDetectors(Workspace=ws_sample, MaskedWorkspace=mask_workspace)


def reduce_RIDSANS_1D(
    ws_sample, ws_pixel_adj, output_workspace=None, number_of_bins=200
):
    """Performs a 1D reduction of the measurement. This assumes reduction_setup_RIDSANS has been run before. The resulting workspace represents the macroscopic cross-section over sample thickness t."""
    # Directly get the sample position
    sample_position = ws_sample.getInstrument().getSample().getPos()

    # Output the sample position in (x, y, z) coordinates
    print(
        f"Sample position: x = {sample_position.X()}, y = {sample_position.Y()}, z = {sample_position.Z()}"
    )
    L_bins = ws_sample.dataX(0)
    L0 = (L_bins[1] + L_bins[0]) / 2
    ds_dist = -sample_position.Z()
    r = active_w / 2
    Q_max = 4 * np.pi / L0 * np.sin(np.arctan(r / (ds_dist)) / 2)  # AA-1
    dQ = Q_max / (number_of_bins + 1)
    output_binning = [0,dQ,Q_max]
    name = ws_sample.name() + "_dSigma/dOmega_1D"
    if output_workspace is not None:
        name = output_workspace
    reduced_ws_1D = Q1D(
        ws_sample,
        OutputWorkspace=name,
        PixelAdj=ws_pixel_adj,
        SolidAngleWeighting=True,
        OutputBinning=output_binning,
        AccountForGravity=True,
    )
    return reduced_ws_1D


def reduce_RIDSANS_2D(
    ws_sample, ws_pixel_adj, output_workspace=None, number_of_bins=200
):
    """Performs a 2D reduction of the measurement. This assumes reduction_setup_RIDSANS has been run before. Assuming the sample thickness t has already been divided out of the ws_sample workspace, the output represents the macroscopic cross-section."""

    # Directly get the sample position
    sample_position = ws_sample.getInstrument().getSample().getPos()

    # Output the sample position in (x, y, z) coordinates
    print(
        f"Sample position: x = {sample_position.X()}, y = {sample_position.Y()}, z = {sample_position.Z()}"
    )
    L_bins = ws_sample.dataX(0)
    L0 = (L_bins[1] + L_bins[0]) / 2
    ds_dist = -sample_position.Z()
    r = active_w / 2
    Q_max = 4 * np.pi / L0 * np.sin(np.arctan(r / (ds_dist)) / 2)
    delta_Q = Q_max / (number_of_bins / 2)
    name = ws_sample.name() + "_dSigma/dOmega_2D"
    if output_workspace is not None:
        name = output_workspace

    reduced_ws_2D = Qxy(
        ws_sample,
        OutputWorkspace=name,
        PixelAdj=ws_pixel_adj,
        SolidAngleWeighting=True,
        MaxQxy=Q_max,
        DeltaQ=delta_Q,
        AccountForGravity=True,
    )
    return reduced_ws_2D
