import numpy as np
import warnings
import h5py as hp
import pybinding as pb
from .utils.warnings import LoudDeprecationWarning
from .modification import Modification
from .utils.model import make_pybinding_model
from scipy.sparse import coo_matrix

__all__ = ['Configuration']


class Configuration:

    def __init__(self, divisions=(1, 1, 1), length=(1, 1, 1), boundaries=('open', 'open', 'open'),
                 is_complex=False, precision=1, spectrum_range=None, angles=(0, 0, 0), custom_local=False,
                 custom_local_print=False):
        r"""Define basic parameters used in the calculation

       Parameters
       ----------
       divisions : int, tuple(int, int), tuple(int, int, int)
           Number of decomposition parts of the system.
       length : int, tuple(int, int), tuple(int, int, int)
           Number of unit cells in each direction.
       boundaries : str, tuple(str, str), tuple(str, str, srt)
           Periodic boundary conditions each direction:
               "periodic"
               "open"
               "twisted" -- this option needs the extra argument angles=[phi_1,..,phi_DIM] where phi_i \in [0, 2*M_PI]
               "random"
       is_complex : bool
           Boolean that reflects whether the type of Hamiltonian is complex or not.
       precision : int
            Integer which defines the precision of the number used in the calculation. Float - 0, double - 1,
            long double - 2.
       spectrum_range : Optional[tuple(float, float)]
            Energy scale which defines the scaling factor of all the energy related parameters. The scaling is done
            automatically in the background after this definition. If the term is not specified, a rough estimate of the
            bounds is found.
       """

        if spectrum_range:
            self._energy_scale = (spectrum_range[1] - spectrum_range[0]) / 2
            self._energy_shift = (spectrum_range[1] + spectrum_range[0]) / 2
        else:
            self._energy_scale = None
            self._energy_shift = None

        # promote to lists
        if not (isinstance(length, list)):
            length = [length]
        if not (isinstance(divisions, list)):
            divisions = [divisions]
        if not (isinstance(boundaries, list)):
            boundaries = [boundaries]

        self._is_complex = int(is_complex)
        self._precision = precision
        self._divisions = divisions
        self._boundaries = boundaries
        self._Twists = np.array(angles, dtype=np.float64)
        self._custom_local = custom_local
        self._print_custom_local = custom_local_print

        self._length = length
        self._htype = np.float32
        self.set_type()

    def set_type(self, ):
        if self._is_complex == 0:
            if self._precision == 0:
                self._htype = np.float32
            elif self._precision == 1:
                self._htype = np.float64
            elif self._precision == 2:
                self._htype = np.float128
            else:
                raise SystemExit('Precision should be 0, 1 or 2')
        else:
            if self._precision == 0:
                self._htype = np.complex64
            elif self._precision == 1:
                self._htype = np.complex128
            elif self._precision == 2:
                self._htype = np.complex256

    @property
    def energy_scale(self):
        """Returns the energy scale of the hopping parameters."""
        return self._energy_scale

    @property
    def energy_shift(self):
        """Returns the energy shift of the hopping parameters around which the spectrum is centered."""
        return self._energy_shift

    @property
    def comp(self):  # -> is_complex:
        """Returns 0 if hamiltonian is real and 1 elsewise."""
        return self._is_complex

    @property
    def prec(self):  # -> precision:
        """Returns 0, 1, 2 if precision if float, double, and long double respectively."""
        return self._precision

    @property
    def div(self):  # -> divisions:
        """Returns the number of decomposed elements of matrix in x, y and/or z direction. Their product gives the total
        number of threads spawn."""
        return self._divisions

    @property
    def bound(self):  # -> boundaries:
        """Returns the boundary conditions in each direction, 0 - no boundary condtions, 1 - peridoc bc. """
        Bounds_tmp = np.zeros(len(self._boundaries), dtype=np.float64)
        BoundTwists = np.zeros(len(self._boundaries), dtype=np.float64)
        for i, b in enumerate(self._boundaries):
            if b == "open":
                Bounds_tmp[i] = 0
            elif b == "periodic":
                Bounds_tmp[i] = 1
            elif b == "twisted":
                Bounds_tmp[i] = 1
                BoundTwists[i] = self._Twists[i]
            elif b == "random":
                Bounds_tmp[i] = 2
            elif b and isinstance(b, bool):
                warnings.warn("Use 'periodic' instead of 'True' for specifying the boundary.",
                              LoudDeprecationWarning, stacklevel=2)
                Bounds_tmp[i] = 1
            elif not b and isinstance(b, bool):
                warnings.warn("Use 'open' instead of 'False' for specifying the boundary.",
                              LoudDeprecationWarning, stacklevel=2)
                Bounds_tmp[i] = 0
            else:
                print("Badly Defined Boundaries!")
                exit()
        return Bounds_tmp, BoundTwists

    @property
    def leng(self):  # -> length:
        """Return the number of unit cell repetitions in each direction. """
        return self._length

    @property
    def type(self):  # -> type:
        """Return the type of the Hamiltonian complex or real, and float, double or long double. """
        return self._htype

    @property
    def custom_pot(self):  # -> potential
        """Return custom potential flag"""
        return self._custom_local

    @property
    def print_custom_pot(self):  # -> potential
        """Return print custom potential flag"""
        return self._print_custom_local


def estimate_bounds(lattice, disorder=None, disorder_structural=None):
    model = make_pybinding_model(lattice, disorder, disorder_structural)
    kpm = pb.kpm(model)
    a, b = kpm.scaling_factors
    return -a + b, a + b
