from .lib import kitecore
import h5py as hp
import numpy as np
from typing import Union
from pathlib import Path
import warnings


def kitex(input: Union[Path, str]):
    """Wrapper from the KITEx-executable so that you can run KITEx through Python.

    Parameters
    ----------
    input : str or Path
        Name of the h5 file that will be processed with KITEx

    Examples
    --------
    The following computes the moments of a function speciied in config.h5
    >>> import kite
    >>> kite.execute.kitex("config.h5")

    Returns
    -------
    int
        0 if the function exited correctly
    """
    filename = input if isinstance(input, str) else str(input)
    is_complex: int
    precision: int
    dim: int
    with hp.File(filename, 'r') as h5file:
        a = h5file["/IS_COMPLEX"]
        print(h5file["/IS_COMPLEX"])
        is_complex = int(np.array(h5file["/IS_COMPLEX"]))
        precision = int(np.array(h5file["/PRECISION"]))
        dim = int(np.array(h5file["/DIM"]))

    # Verify if the values passed to the program are valid. If they aren't
    # the program should notify the user and exit with error 1.
    if (dim < 1) or (dim > 3):
        warnings.warn(
            "Invalid number of dimensions. The code is only valid for 2D or 3D, given {0}. Exiting".format(dim),
            UserWarning
        )
        return 1
    if (precision < 0) or (precision > 2):
        warnings.warn(
            "Use valid value for numerical precision. Accepted values: 0, 1, 2 - not {0}. Exiting.".format(precision),
            UserWarning
        )
        return 1
    if (is_complex != 0) and (is_complex != 1):
        warnings.warn(
            "Bad complex flag. It has to be either 0 or 1 - not {0}. Exiting.".format(is_complex),
            UserWarning
        )
        return 1
    index: int = dim - 1 + 3 * precision + is_complex * 3 * 3
    return kitecore.kitex(str(input), index)


def kitetools(input):
    """Calculates the reconstructed function from the moments obtained by KITEx and outputs a *.dat file
    
    Parameters
    ----------
    input : str or Path
        Label that defines which function with which parameters will be reconstructed
    
    Example
    -------
    The following reconstructs the DOS taking 1000 moments from config.h5.
    >>> import kite
    >>> kite.execute.kitetools("config.h5 --DOS -M 1000")
    
    Returns
    -------
    int
        0 if the function exited correctly
    """
    filename = input if isinstance(input, str) else str(input)
    return kitecore.kite_tools(filename.split())
