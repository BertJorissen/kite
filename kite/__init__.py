try:
    from .lib import kitecore
except ImportError as e:
    import warnings
    warnings.warn("The KITE-executables for KITEx and KITE-tools were not found.", UserWarning)

from .calculation import *
from .configuration import *
from .disorder import *
from .modification import *
from .system import *
from .utils import *
from .execute import *


def tests(options=None, plugins=None):
    """Run the tests

    Parameters
    ----------
    options : list or str
        Command line options for pytest (excluding target file_or_dir).
    plugins : list
        Plugin objects to be auto-registered during initialization.
    """
    import pytest
    import pathlib
    import os
    from pybinding.utils import misc, pltutils
    args = options or []
    if isinstance(args, str):
        args = args.split()
    module_path = pathlib.Path(__file__).parent

    if (module_path / 'tests').exists():
        # tests are inside installed package -> use read-only mode
        args.append('--failpath=' + os.getcwd() + '/failed')
        with misc.cd(module_path), pltutils.backend('Agg'):
            args += ['-c', str(module_path / 'tests/local.cfg'), str(module_path)]
            error_code = pytest.main(args, plugins)
    else:
        # tests are in dev environment -> use development mode
        with misc.cd(module_path.parent), pltutils.backend('Agg'):
            error_code = pytest.main(args, plugins)

    return error_code or None
