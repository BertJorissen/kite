import pytest

from contextlib import suppress

import matplotlib as mpl
mpl.use('Agg')  # disable `plt.show()` popup window during testing
import matplotlib.pyplot as plt

import kite

from pybinding.tests.utils.path import path_from_fixture
from pybinding.tests.utils.compare_figures import CompareFigure
from pybinding.tests.utils.fuzzy_equal import FuzzyEqual

from pybinding.tests.conftest import *