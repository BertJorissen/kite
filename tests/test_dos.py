"""Test the DOS calculation of KITE"""
import numpy as np
import pybinding as pb
import kite
import pathlib
import os
import sys
from contextlib import contextmanager
os.environ["SEED"] = "3"


def square(a: float = 1., t: float = 1.) -> pb.Lattice:
    """Make a square lattice to test the DOS.

    Parameters
    ----------
    a : float
        The unit vector length of the square lattice [nm].
    t : float
        The hopping strength between the nearest neighbours [eV].

    Returns
    ------
    pb.Lattice
        The lattice object containing the square lattice
    """

    a1, a2 = a * np.array([1, 0]), a * np.array([0, 1])
    lat = pb.Lattice(a1=a1, a2=a2)
    lat.add_one_sublattice('A', a * np.array([0, 0]), 0)
    lat.add_hoppings(
        ([0, 1], 'A', 'A', t),
        ([1, 0], 'A', 'A', t)
    )
    return lat


@contextmanager
def block_output():
    with open(os.devnull, 'w') as output:
        init_output = os.dup(sys.stdout.fileno())
        os.dup2(output.fileno(), sys.stdout.fileno())
        try:
            yield
        finally:
            os.dup2(init_output, sys.stdout.fileno())


def test_square(tmp_path: pathlib.Path):
    """Do the tests for the square lattice."""
    if isinstance(tmp_path, str):
        file = tmp_path
    else:
        file = str((tmp_path / "config").with_suffix(".h5"))
    # construct the lattice
    lattice = square()

    # set the parameters for the calculation with KITEx
    nx = ny = 2
    lx = ly = 256
    m = 1024
    configuration = kite.Configuration(
        divisions=[nx, ny],
        length=[lx, ly],
        boundaries=["periodic", "periodic"],
        is_complex=False,
        precision=1,
        spectrum_range=[-5, 5]
    )
    calculation = kite.Calculation(configuration)
    calculation.dos(
        num_points=1000,
        num_moments=m,
        num_random=1,
        num_disorder=1)

    # make the input file
    if os.path.exists(file):
        os.remove(file)
    kite.config_system(lattice, configuration, calculation, filename=file)
    kite.execute.kitex(file)
    # check the contents for the file
    from tests.kitex.compare import compare
    hdf5_internal_dest = "/Calculation/dos/MU"
    ref_file = "tests/kitex/large000_KITEx_sq_dos/configREF.h5"
    assert compare([file, hdf5_internal_dest, ref_file, hdf5_internal_dest])[0] < 1e-8,\
        "The desired accuracy wasn't achieved."


def test_magnetic(tmp_path: pathlib.Path):
    """Do the tests for the square lattice."""
    if isinstance(tmp_path, str):
        file = tmp_path
    else:
        file = str((tmp_path / "config").with_suffix(".h5"))
    # construct the lattice
    lattice = square()

    # set the parameters for the calculation with KITEx
    nx = ny = 2
    lx = ly = 512
    m = 4192
    configuration = kite.Configuration(
        divisions=[nx, ny],
        length=[lx, ly],
        boundaries=["periodic", "periodic"],
        is_complex=True,
        precision=1,
        spectrum_range=[-4.1, 4.1]
    )
    calculation = kite.Calculation(configuration)
    mod = kite.Modification(magnetic_field=9)
    calculation.dos(
        num_points=4096,
        num_moments=m,
        num_random=1,
        num_disorder=1)

    # make the input file
    if os.path.exists(file):
        os.remove(file)
    kite.config_system(lattice, configuration, calculation,  modification=mod, filename=file)
    kite.execute.kitex(file)
    # check the contents for the file
    from tests.kitex.compare import compare, compare_txt
    hdf5_internal_dest = "/Calculation/dos/MU"
    ref_file = "tests/kitex/large001_magdos2d/configREF.h5"
    assert compare([file, hdf5_internal_dest, ref_file, hdf5_internal_dest], set_abs=True)[0] < 1e-8, \
        "The desired accuracy wasn't achieved."
    kite.execute.kitetools(file)
    file3, file4 = "tests/kitex/large001_magdos2d/dos.dat", "tests/kitex/large001_magdos2d/dosREF.dat"
    assert compare_txt([file3, file4], set_abs=True)[0] < 1e-8, "The desired accuracy wasn't achieved, {0}".format(compare_txt([file3, file4], set_abs=True)[0])
