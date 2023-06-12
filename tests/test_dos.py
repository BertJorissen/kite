"""Test the DOS calculation of KITE"""
import numpy as np
import pybinding as pb
import kite
import os
import pathlib


def square(a: float=1., t: float=1.) -> pb.Lattice:
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


from contextlib import contextmanager
import os
import sys


@contextmanager
def block_output():
    with open(os.devnull, 'w') as output:
        init_output = os.dup(sys.stdout.fileno())
        os.dup2(output.fileno(), sys.stdout.fileno())
        try:
            yield
        finally:
            os.dup2(init_output, sys.stdout.fileno())


os.environ["SEED"] = "3"
def test_square(tmp_path: pathlib.Path):
    """Do the tests for the square lattice."""

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

    file = str((tmp_path / "config").with_suffix(".h5"))
    if os.path.exists(file):
        os.remove(file)
    kite.config_system(lattice, configuration, calculation, filename=file)
    # do the calculation, with the right random values
    # os.system("./cmake-build-debug/cppcore/kitex/KITEx {0}".format(file2))
    try:
        with block_output():
            import _kite
            _kite.kitex(file)
    except ValueError or Exception:
        raise ValueError("KITE is wrong lol")
    # check the contents for the file
    from tests.kitex.compare import compare
    hdf5_internal_dest = "/Calculation/dos/MU"
    ref_file = "tests/kitex/large000_KITEx_sq_dos/configREF.h5"
    assert compare([file, hdf5_internal_dest, ref_file, hdf5_internal_dest])[0] < 1e-8,\
        "The desired accuracy wasn't achieved."
