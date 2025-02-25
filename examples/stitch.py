from mantid.api import AnalysisDataService as ADS
from mantid.simpleapi import *
from mantid.api import *
from mantid.kernel import *

workspaces = [ADS.retrieve(f"scattering_glassyC_Q{i}_Sigma/t_1D") for i in range(1, 5)]
trimmed_workspaces = []
intervals = []

for i, ws in enumerate(workspaces):
    print(i)
    Q_axis = np.array(ws.dataX(0))[:-1]
    Iq_array = ws.dataY(0)
    # Find indices where Iq_array is not NaN and not zero.
    valid_indices = np.where((~np.isnan(Iq_array)) & (Iq_array != 0))[0]
    first_valid_index = valid_indices[0] if valid_indices.size > 0 else 0
    first_valid_Q = (
        Q_axis[first_valid_index] if first_valid_index < len(Q_axis) else np.min(Q_axis)
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
        OutputWorkspace=f"timmed_workspace_{i}",
        Params=f"{Q_min_trim},{Q_step_trim},{Q_max_trim}",
    )
    trimmed_workspaces.append(trimmed_workspace)

OutScaleFactors = []
st, OutScaleFactors = Stitch1DMany(trimmed_workspaces, OutScaleFactors=OutScaleFactors)

print(OutScaleFactors)

# sum_ws = sum(ws_rebinned)
