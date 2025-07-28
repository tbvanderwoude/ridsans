from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *

def save(workspace, file_name=None):
    """Wrapper around SaveCanSAS1D that appends the .xml extension to the filename if needed."""
    if file_name is None:
        file_name = f"{workspace.name()}.xml"
    elif not file_name.endswith(".xml"):
        file_name += ".xml"
    return SaveCanSAS1D(workspace, file_name)

# def save_2D(workspace, file_name=None):
#     """Wrapper around SaveNXcanSAS that appends the .h5 extension to the filename if needed."""
#     if file_name is None:
#         file_name = f"{workspace.name()}.h5"
#     elif not file_name.endswith(".h5"):
#         file_name += ".h5"
    
#     # TODO: add proper file_name sanitization
#     file_name = file_name.replace("/", "_").replace("\\", "_")

#     # Convert the workspace to units of momentum transfer (in case it is not already)
#     workspace = ConvertUnits(workspace,Target="MomentumTransfer")

#     # Not the actual instrument, might break stuff. RIDSANS is not officially known anywhere yet
#     # so this needs to be set as otherwise SaveNXcanSAS complains no institute uses a RIDSANS 
#     LoadInstrument(workspace,False,InstrumentName="SANS2D")

#     # Save the file
#     SaveNXcanSAS(workspace,file_name)

# def save_2D(workspace, file_name=None):
#     """Wrapper around SaveNISTDAT that appends the .dat extension to the filename if needed."""
#     if file_name is None:
#         file_name = f"{workspace.name()}.dat"
#     elif not file_name.endswith(".dat"):
#         file_name += ".dat"
#     # TODO: add proper file_name sanitization
#     file_name = file_name.replace("/", "_").replace("\\", "_")
#     return SANSSave(workspace, file_name)



def save_2D(workspace, file_name=None):
    """Wrapper around SaveNISTDAT that appends the .nxs extension to the filename if needed."""
    if file_name is None:
        file_name = f"{workspace.name()}.nxs"
    elif not file_name.endswith(".nxs"):
        file_name += ".nxs"
    # TODO: add proper file_name sanitization
    file_name = file_name.replace("/", "_").replace("\\", "_")
    return SANSSave(InputWorkspace=workspace,Filename=file_name,NXcanSAS=True)
