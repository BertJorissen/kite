"""Calculation specification"""
import numpy as np
import pybinding as pb
from .configuration import Configuration
from typing import Optional, List, Dict, Tuple,Literal

__all__ = ['Calculation']


class Calculation:
    """TODO: add a docstring"""
    def __init__(self, configuration: Optional[Configuration] = None):

        if configuration is not None and not isinstance(configuration, Configuration):
            raise TypeError("You're forwarding a wrong type!")

        self._scaling_factor: Optional[float] = configuration.energy_scale
        self._energy_shift: Optional[float] = configuration.energy_shift
        self._dos: List[dict] = []
        self._ldos: List[dict] = []
        self._arpes: List[dict] = []
        self._conductivity_dc: List[dict] = []
        self._conductivity_optical: List[dict] = []
        self._conductivity_optical_nonlinear: List[dict] = []
        self._gaussian_wave_packet: List[dict] = []
        self._singleshot_conductivity_dc: List[dict] = []
        self._operators: List[Tuple[str, pb.Lattice]] = []
        self._operator_vertices: List[dict] = []

        self._avail_dir_full: Dict[str, int] = {
            'xx': 0, 'yy': 1, 'zz': 2, 'xy': 3, 'xz': 4, 'yx': 5, 'yz': 6, 'zx': 7, 'zy': 8}
        self._avail_dir_nonl: Dict[str, int] = {
            'xxx': 0, 'xxy': 1, 'xxz': 2, 'xyx': 3, 'xyy': 4, 'xyz': 5, 'xzx': 6, 'xzy': 7,
            'xzz': 8, 'yxx': 9, 'yxy': 10, 'yxz': 11, 'yyx': 12, 'yyy': 13, 'yyz': 14, 'yzx': 15,
            'yzy': 16, 'yzz': 17, 'zxx': 18, 'zxy': 19, 'zxz': 20, 'zyx': 21, 'zyy': 22, 'zyz': 23,
            'zzx': 24, 'zzy': 25, 'zzz': 26}
        self._avail_dir_sngl: Dict[str, int] = {'xx': 0, 'yy': 1, 'zz': 2}

    @property
    def get_dos(self) -> List[dict]:
        """Returns the requested DOS functions."""
        return self._dos

    @property
    def get_ldos(self) -> List[dict]:
        """Returns the requested LDOS functions."""
        return self._ldos

    @property
    def get_arpes(self) -> List[dict]:
        """Returns the requested ARPES functions."""
        return self._arpes

    @property
    def get_gaussian_wave_packet(self) -> List[dict]:
        """Returns the requested wave packet time evolution function, with a gaussian wavepacket mutiplied with different
        plane waves."""
        return self._gaussian_wave_packet

    @property
    def get_conductivity_dc(self) -> List[dict]:
        """Returns the requested DC conductivity functions."""
        return self._conductivity_dc

    @property
    def get_conductivity_optical(self) -> List[dict]:
        """Returns the requested optical conductivity functions."""
        return self._conductivity_optical

    @property
    def get_conductivity_optical_nonlinear(self) -> List[dict]:
        """Returns the requested nonlinear optical conductivity functions."""
        return self._conductivity_optical_nonlinear

    @property
    def get_singleshot_conductivity_dc(self) -> List[dict]:
        """Returns the requested singleshot DC conductivity functions."""
        return self._singleshot_conductivity_dc

    @property
    def get_operators(self) -> List[Tuple[str, pb.Lattice]]:
        """Returns the requested operators."""
        return self._operators

    @property
    def get_operator_vertices(self) -> List[dict]:
        """Returns the requested operator vertices."""
        return self._operator_vertices

    def dos(self, num_points, num_moments, num_random, num_disorder=1):
        """Calculate the density of states as a function of energy

        Parameters
        ----------
        num_points : int
            Number of energy point inside the spectrum at which the DOS will be calculated.
        num_moments : int
            Number of polynomials in the Chebyshev expansion.
        num_random : int
            Number of random vectors to use for the stochastic evaluation of trace.
        num_disorder : int
            Number of different disorder realisations.
        """

        self._dos.append({'num_points': num_points, 'num_moments': num_moments, 'num_random': num_random,
                          'num_disorder': num_disorder})

    def ldos(self, energy, num_moments, position, sublattice, num_disorder=1):
        """Calculate the local density of states as a function of energy

        Parameters
        ----------
        energy : list or np.array
            List of energy points at which the LDOS will be calculated.
        num_moments : int
            Number of polynomials in the Chebyshev expansion.
        num_disorder : int
            Number of different disorder realisations.
        position : list
            Relative index of the unit cell where the LDOS will be calculated.
        sublattice : str or list
            Name of the sublattice at which the LDOS will be calculated.
        """

        self._ldos.append({'energy': energy, 'num_moments': num_moments,
                           'position': np.reshape(np.array(position).flatten(), (-1, np.shape(position)[-1])),
                           'sublattice': sublattice, 'num_disorder': num_disorder})

    def arpes(self, k_vector, weight, num_moments, num_disorder=1):
        """Calculate the spectral contribution for given k-points and weights.

        Parameters
        ----------
        k_vector : List
            List of K points with respect to reciprocal vectors b0 and b1 at which the band structure will be calculated.
        weight : List
            List of orbital weights used for ARPES.
        num_moments : int
            Number of polynomials in the Chebyshev expansion.
        num_disorder : int
            Number of different disorder realisations.
        """

        self._arpes.append({'k_vector': k_vector, 'weight': weight, 'num_moments': num_moments, 'num_disorder': num_disorder})

    def gaussian_wave_packet(self, num_points, num_moments, timestep, k_vector, spinor, width, mean_value,
                             num_disorder=1, **kwargs):
        """Calculate the time evolution function of a wave packet

        Parameters
        ----------
        num_points : int
            Number of time points for the time evolution.
        num_moments : int
            Number of polynomials in the Chebyshev expansion.
        timestep : float
            Timestep for calculation of time evolution.
        k_vector : np.array
            Different wave vectors, components corresponding to vectors b0 and b1.
        spinor : np.array
            Spinors for each of the k vectors.
        width : float
            Width of the gaussian.
        mean_value : [float, float]
            Mean value of the gaussian envelope.
        num_disorder : int
            Number of different disorder realisations.

            Optional parameters, forward probing point, defined with x, y coordinate were the wavepacket will be checked
            at different timesteps.

        """
        probing_point = kwargs.get('probing_point', 0)

        self._gaussian_wave_packet.append(
            {'num_points': num_points, 'num_moments': num_moments,
             'timestep': timestep, 'num_disorder': num_disorder, 'spinor': spinor, 'width': width, 'k_vector': k_vector,
             'mean_value': mean_value, 'probing_point': probing_point})

    def conductivity_dc(self, direction, num_points, num_moments, num_random, num_disorder=1, temperature=0):
        """Calculate the DC conductivity for a given direction

        Parameters
        ----------
        direction : str
            direction in xyz coordinates along which the conductivity is calculated.
            Supports 'xx', 'yy', 'zz', 'xy', 'xz', 'yx', 'yz', 'zx', 'zy'.
        num_points : int
            Number of energy point inside the spectrum at which the DOS will be calculated.
        num_moments : int
            Number of polynomials in the Chebyshev expansion.
        num_random : int
            Number of random vectors to use for the stochastic evaluation of trace.
        num_disorder : int
            Number of different disorder realisations.
        temperature : float
            Value of the temperature at which we calculate the response.
        """
        if direction not in self._avail_dir_full:
            print('The desired direction is not available. Choose from a following set: \n',
                  self._avail_dir_full.keys())
            raise SystemExit('Invalid direction!')
        else:
            self._conductivity_dc.append(
                {'direction': self._avail_dir_full[direction], 'num_points': num_points, 'num_moments': num_moments,
                 'num_random': num_random, 'num_disorder': num_disorder,
                 'temperature': temperature})

    def conductivity_optical(self, direction, num_points, num_moments, num_random, num_disorder=1, temperature=0):
        """Calculate optical conductivity for a given direction

        Parameters
        ----------
        direction : string
            direction in xyz coordinates along which the conductivity is calculated.
            Supports 'xx', 'yy', 'zz', 'xy', 'xz', 'yx', 'yz', 'zx', 'zy'.
        num_points : int
            Number of energy point inside the spectrum at which the DOS will be calculated.
        num_moments : int
            Number of polynomials in the Chebyshev expansion.
        num_random : int
            Number of random vectors to use for the stochastic evaluation of trace.
        num_disorder : int
            Number of different disorder realisations.
        temperature : float
            Value of the temperature at which we calculate the response.
        """
        if direction not in self._avail_dir_full:
            print('The desired direction is not available. Choose from a following set: \n',
                  self._avail_dir_full.keys())
            raise SystemExit('Invalid direction!')
        else:
            self._conductivity_optical.append(
                {'direction': self._avail_dir_full[direction], 'num_points': num_points, 'num_moments': num_moments,
                 'num_random': num_random, 'num_disorder': num_disorder,
                 'temperature': temperature})

    def conductivity_optical_nonlinear(self, direction, num_points, num_moments, num_random, num_disorder=1,
                                       temperature=0, **kwargs):
        """Calculate nonlinear optical conductivity for a given direction

        Parameters
        ----------
        direction : string
            direction in xyz coordinates along which the conductivity is calculated.
            Supports all the combinations of the direction x, y and z with length 3 like 'xxx','zzz', 'xxy', 'xxz' etc.
        num_points : int
            Number of energy point inside the spectrum at which the DOS will be calculated.
        num_moments : int
            Number of polynomials in the Chebyshev expansion.
        num_random : int
            Number of random vectors to use for the stochastic evaluation of trace.
        num_disorder : int
            Number of different disorder realisations.
        temperature : float
            Value of the temperature at which we calculate the response.

            Optional parameters, forward special, a parameter that can simplify the calculation for some materials.
        """

        if direction not in self._avail_dir_nonl:
            print('The desired direction is not available. Choose from a following set: \n',
                  self._avail_dir_nonl.keys())
            raise SystemExit('Invalid direction!')
        else:
            special = kwargs.get('special', 0)

            self._conductivity_optical_nonlinear.append(
                {'direction': self._avail_dir_nonl[direction], 'num_points': num_points,
                 'num_moments': num_moments, 'num_random': num_random, 'num_disorder': num_disorder,
                 'temperature': temperature, 'special': special})

    def singleshot_conductivity_dc(self, energy, direction, eta, num_moments, num_random, num_disorder=1,
                                   preserve_disorder=False):
        """Calculate the DC conductivity using KITEx for a fiven direction and energy

        Parameters
        ----------
        energy : ndarray or float
            Array or a single value of energies at which singleshot_conductivity_dc will be calculated.
        direction : string
            direction in xyz coordinates along which the conductivity is calculated.
            Supports 'xx', 'yy', 'zz'.
        eta : Float
            Parameter that affects the broadening of the kernel function.
        num_moments : int
            Number of polynomials in the Chebyshev expansion.
        num_random : int
            Number of random vectors to use for the stochastic evaluation of trace.
        num_disorder : int
            Number of different disorder realisations.
        preserve_disorder : bool
            If True, preverse the disorder configuration for calculations with different random vectors. Default False.
        """

        if direction not in self._avail_dir_sngl:
            print('The desired direction is not available. Choose from a following set: \n',
                  self._avail_dir_sngl.keys())
            raise SystemExit('Invalid direction!')
        else:
            self._singleshot_conductivity_dc.append(
                {'energy': (np.atleast_1d(energy)),
                 'direction': self._avail_dir_sngl[direction],
                 'eta': np.atleast_1d(eta), 'num_moments': np.atleast_1d(num_moments),
                 'num_random': num_random, 'num_disorder': num_disorder,
                 'preserve_disorder': np.atleast_1d(preserve_disorder)})

    def add_operator(self, operator: pb.Lattice, name: str):
        """Add an operator to the calculation

        Parameters
        ----------
        operator : pb.Lattice
            Operator to be added to the calculation.
        name : str
            Name of the operator.
        """

        self._operators.append((name, operator))

    def vertex(
            self,
            operators: List[List[Tuple[str, str] | str]],
            spectrum: List[Tuple[
                Literal["FullSpectrum", "SingleShot"],
                Literal["Dirac", "Greens"],
                Tuple[int, int] | Tuple[np.ndarray, np.ndarray, np.ndarray]
            ]],
            num_random: int,
            num_disorder: int,
            preserve_disorder: bool = False
    ):
        """Add an operator to the calculation

        Parameters
        ----------

        operators : List[Tuple[str, str] | str]
            List of operators to be added to the calculation.
        spectrum : Tuple[Literal["FullSpectrum", "SingleShot"], Literal["Dirac", "Greens"], Tuple[int, int] | Tuple[np.ndarray, np.ndarray, np.ndarray]]
            Tuple of the type of spectrum, type of operator and the coefficients of the spectrum.
            If FullSpectrum, the last part is the number of moments and the number of points.
            If SingleShot, the last part is the coefficients of the spectrum, given as energy, eta and the moments
        num_random : int
            Number of random vectors to use for the stochastic evaluation of trace.
        num_disorder : int
            Number of different disorder realisations. Only the first entry is used.
        preserve_disorder : bool
            If True, preverse the disorder configuration for calculations with different random vectors. Default False
        """

        self._operator_vertices.append(
            {"num_random": num_random, "num_disorder": num_disorder, "preserve_disorder": preserve_disorder,
             "operators_list": operators, "spectrum_list": spectrum})