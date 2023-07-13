import numpy as np
import pybinding as pb


def square(a: float = 1., t: float = 1., onsite: float = 0.) -> pb.Lattice:
    """Make a square lattice

    Parameters
    ----------
    a : float
        The unit vector length of the square lattice [nm].
    t : float
        The hopping strength between the nearest neighbours [eV].
    onsite : float
        The onsite energy for the orbital [eV].

    Returns
    ------
    pb.Lattice
        The lattice object containing the square lattice
    """

    a1, a2 = a * np.array([1, 0]), a * np.array([0, 1])
    lat = pb.Lattice(a1=a1, a2=a2)
    lat.add_one_sublattice('A', a * np.array([0, 0]), onsite)
    lat.add_hoppings(
        ([1, 0], 'A', 'A', t),
        ([0, 1], 'A', 'A', t)
    )
    return lat


def cube(a: float = 1., t: float = 1., onsite: float = 0.) -> pb.Lattice:
    """Make a cubic lattice

    Parameters
    ----------
    a : float
        The unit vector length of the square lattice [nm].
    t : float
        The hopping strength between the nearest neighbours [eV].
    onsite : float
        The onsite energy for the orbital [eV].

    Returns
    ------
    pb.Lattice
        The lattice object containing the square lattice
    """

    a1, a2, a3 = a * np.array([1, 0, 0]), a * np.array([0, 1, 0]), a * np.array([0, 0, 1])
    lat = pb.Lattice(a1=a1, a2=a2, a3=a3)
    lat.add_one_sublattice('A', a * np.array([0, 0, 0]), onsite)
    lat.add_hoppings(
        ([1, 0, 0], 'A', 'A', t),
        ([0, 1, 0], 'A', 'A', t),
        ([0, 0, 1], 'A', 'A', t)
    )
    return lat