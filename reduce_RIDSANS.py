from mantid.simpleapi import *
from mantid.api import *
from mantid.kernel import *
import numpy as np


def mask_rectangle(ws, w, h, negative=False, offset_x=0, offset_y=0):
    # Gets large for a 1024 x 1024 detector but at most ~30 MB
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
    # Gets large for a 1024 x 1024 detector but at most ~30 MB
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


def reduction_setup_RIDSANS(ws_sample, ws_direct, active_w, active_h, ROI=None):
    """Finds the beam center and applies a mask"""
    # STEP 1: find beam centre from direct beam
    # Compute the center position, which will be put in a table workspace

    # Uses direct beam method
    center = FindCenterOfMassPosition(
        ws_direct, Output="center", Tolerance=0.0005
    )
    center_x, center_y = center.column(1)
    print(f"(x, y) = ({center_x:.4f}, {center_y:.4f})")
    # Idea: move detector based on beamstop position to compensate for shift
    # Question: does this actually make sense?
    MoveInstrumentComponent(
        ws_sample,
        ComponentName="detector-bank",
        X=-center_x,
        Y=-center_y,
        Z=0.0,
        RelativePosition=False,
    )

    # STEP 2: apply mask
    mask_rectangle(ws_sample, active_w, active_h)

    if ROI is not None:
        # TODO: ensure that choice of circle center is correct
        mask_circle(ws_sample, ROI, True)


def reduce_RIDSANS_1D(ws_sample, ws_pixel_adj, active_w):
    """Performs a 1D reduction of the measurement. This assumes reduction_setup_RIDSANS has been run before."""
    # Directly get the sample position
    sample_position = ws_sample.getInstrument().getSample().getPos()

    # Output the sample position in (x, y, z) coordinates
    print(
        f"Sample position: x = {sample_position.X()}, y = {sample_position.Y()}, z = {sample_position.Z()}"
    )
    L_bins = ws_sample.dataX(0)
    L0 = (L_bins[1] + L_bins[0]) / 2
    # max_det_x = 0.140662/2
    # max_det_y = 0.140662/2
    ds_dist = -sample_position.Z()
    r = active_w / 2
    Q_max = 4 * np.pi / L0 * np.sin(np.arctan(r / (ds_dist)) / 2)
    Q_max  # AA-1
    output_binning = np.linspace(0, Q_max, 201)
    reduced_ws_1D = Q1D(
        ws_sample,
        PixelAdj=ws_pixel_adj,
        SolidAngleWeighting=True,
        OutputBinning=output_binning,
        AccountForGravity=True,
    )
    return reduced_ws_1D


def reduce_RIDSANS_2D(ws_sample, ws_pixel_adj, active_w):
    """Performs a 1D reduction of the measurement. This assumes reduction_setup_RIDSANS has been run before."""

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
    Q_max  # AA-1
    delta_Q = 0.0001 * 2
    # max_QXY = 0.01
    # N_Q_bins = int(np.floor(2*Q_max/delta_Q)+2)

    reduced_ws_2D = Qxy(
        ws_sample,
        PixelAdj=ws_pixel_adj,
        SolidAngleWeighting=True,
        MaxQxy=Q_max,
        DeltaQ=delta_Q,
        AccountForGravity=True,
    )
    return reduced_ws_2D
