from .__about__ import (__authors__, __copyright__, __email__, __license__, __summary__, __title__, __url__,
                        __version__)

from .calculation import *
from .configuration import *
from .disorder import *
from .modification import *
from .system import *
from .utils import *

import warnings

try:
    import _kite as execute
except ImportError as e:
    warnings.warn("The KITE-executables for KITEx and KITE-tools were not found.", UserWarning)
