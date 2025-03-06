from mantid.simpleapi import *
from mantid.api import *
from mantid.kernel import *


def stitch_Q_ranges(workspaces, bins=50):
    """Stitches together workspaces corresponding to different Q ranges, first trimming each workspace to the unmasked Q interval."""
    trimmed_workspaces = []
    Q_stitched_max = -1.0
    Q_stitched_min = 10000
    for i, ws in enumerate(workspaces):
        print(i)
        Q_axis = np.array(ws.dataX(0))[:-1]
        Iq_array = ws.dataY(0)
        # Find indices where Iq_array is not NaN and not zero.
        valid_indices = np.where((~np.isnan(Iq_array)) & (Iq_array != 0))[0]
        first_valid_index = valid_indices[0] if valid_indices.size > 0 else 0
        first_valid_Q = (
            Q_axis[first_valid_index]
            if first_valid_index < len(Q_axis)
            else np.min(Q_axis)
        )
        steps = len(Q_axis) - first_valid_index + 1
        Q_min_trim = first_valid_Q
        Q_max_trim = np.max(Q_axis)
        Q_step_trim = (Q_max_trim - Q_min_trim) / steps
        # The reason why this trimming is needed is quite complex and appears to be related to
        # masked values giving NaN's in the masked bins. NaN arithmetic has the property that
        # the NaNs 'spread', making the outcome of any operation NaN. This means that without
        # this trimming, the output of Stitch1D would only be part of the last stitched
        # workspace.
        trimmed_workspace = Rebin(
            ws,
            OutputWorkspace=f"trimmed_workspace_{i}",
            Params=f"{Q_min_trim},{Q_step_trim},{Q_max_trim}",
        )
        trimmed_workspaces.append(trimmed_workspace)
        Q_stitched_min = min(Q_stitched_min, Q_min_trim)
        Q_stitched_max = max(Q_stitched_max, Q_max_trim)

    Q_stitched_step = (Q_stitched_max - Q_stitched_min) / bins
    OutScaleFactors = []
    workspace_name = workspaces[0].name().rsplit("_", 1)[0] + "_stitched"
    st, scale_factors = Stitch1DMany(
        trimmed_workspaces,
        OutputWorkspace=workspace_name,
        OutScaleFactors=OutScaleFactors,
        Params=f"{Q_stitched_min},{Q_stitched_step},{Q_stitched_max}",
    )
    return st, scale_factors
