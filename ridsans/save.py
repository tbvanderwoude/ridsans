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


def save_2D(workspace, file_name=None):
    """Wrapper around SaveNISTDAT that appends the .nxs extension to the filename if needed."""
    if file_name is None:
        file_name = f"{workspace.name()}.nxs"
    elif not file_name.endswith(".nxs"):
        file_name += ".nxs"
    # TODO: add proper file_name sanitization
    file_name = file_name.replace("/", "_").replace("\\", "_")
    return SANSSave(InputWorkspace=workspace,Filename=file_name,NXcanSAS=True)
