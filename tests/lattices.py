import numpy as np
import pybinding as pb
from typing import Tuple
import os

def read_ldos_files(directory):
    ldos_files = [filename for filename in os.listdir(directory) if filename.startswith('ldos') and filename.endswith('.dat')]

    data_dict = {}

    for filename in ldos_files:
        # Extracting the value of <E> from the filename
        e_value = float(filename[4:-4])

        # Building the file path
        file_path = os.path.join(directory, filename)

        # Reading file contents using np.loadtxt()
        contents = np.loadtxt(file_path)

        # Adding contents to the dictionary
        data_dict[e_value] = contents

    return data_dict


def read_text_and_matrices(filename):
    data_dict = {}
    current_key = None
    current_matrix = []
    is_matrix_data = False

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()

            if not line[0].isdigit():
                # Line with text
                if current_key is not None and current_matrix:
                    # Add the previous matrix to the dictionary
                    data_dict[current_key] = np.array(current_matrix)
                    current_matrix = []
                current_key = line
                is_matrix_data = False
            else:
                # Matrix data
                if not is_matrix_data:
                    # First line of matrix
                    is_matrix_data = True
                matrix_row = [float(value) for value in line.split()]
                current_matrix.append(matrix_row)

    # Add the last matrix to the dictionary
    if current_key is not None and current_matrix:
        data_dict[current_key[:-1]] = np.array(current_matrix)

    return data_dict


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


def hexagonal(a: float = 1., t: complex = 1., t_nn: complex = 0, onsite: Tuple[float, float] = (0., 0.)) -> pb.Lattice:
    """Make a cubic lattice

    Parameters
    ----------
    a : float
        The unit vector length of the square lattice [nm].
    t : complex
        The hopping strength between the nearest neighbours [eV].
    t_nn : complex
        The hopping strength between the next nearest neighbours [eV].
    onsite : Tuple[float, float]
        The onsite energy for the orbitals [eV].

    Returns
    ------
    pb.Lattice
        The lattice object containing the square lattice
    """

    a1, a2 = a * np.array([1, 0]), a * np.array([-.5, np.sqrt(3) / 2])
    lat = pb.Lattice(a1=a1, a2=a2)
    lat.add_sublattices(
        ('A', a * np.array([0, 0]), onsite[0]),
        ('B', a * np.array([.5, np.sqrt(3) / 6]), onsite[0])
    )
    lat.register_hopping_energies(
        {'t': t, 't_nn': t_nn}
    )
    lat.add_hoppings(
        ([0, 0], 'A', 'B', 't'),
        ([-1, 0], 'A', 'B', 't'),
        ([-1, -1], 'A', 'B', 't'),
        ([1, 0], 'A', 'A', 't_nn'),
        ([0, 1], 'A', 'A', 't_nn'),
        ([-1, -1], 'A', 'A', 't_nn'),
        ([-1, 0], 'B', 'B', 't_nn'),
        ([0, -1], 'B', 'B', 't_nn'),
        ([1, 1], 'B', 'B', 't_nn')
    )
    return lat
