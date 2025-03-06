from mantid.simpleapi import *
from mantid.api import *
from mantid.kernel import *

def save(workspace, file_name=None):
    """Wrapper around SaveCanSAS1D that appends the .xml extension to the filename if needed."""
    if file_name is None:
        file_name = f"{workspace.name()}.xml"
    elif not file_name.endswith('.xml'):
        file_name += '.xml'
    return SaveCanSAS1D(workspace, file_name)