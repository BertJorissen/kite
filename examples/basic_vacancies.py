""" Honeycomb lattice with vacancy disorder

    ##############################################################################
    #                        Copyright 2022, KITE                                #
    #                        Home page: quantum-kite.com                         #
    ##############################################################################

    Units: Energy in units of hopping, |t| = 1
    Lattice: Honeycomb
    Configuration: Periodic boundary conditions, double precision,
                    automatic scaling, size of the system 512x512, without domain decomposition (nx=ny=1)
    Disorder: StructuralDisorder, vacancy with concentration 0.1 inside A and 0.05 inside B sublattices
    Calculation type: Average DOS
    Last updated: 13/07/2022
"""

__all__ = ["honeycomb_lattice", "main"]

import kite
import numpy as np
import pybinding as pb


def honeycomb_lattice(onsite=(0, 0), t=1):
    # Return lattice specification for a honeycomb lattice with nearest neighbor hoppings

    # define lattice vectors
    theta = np.pi / 3
    a1 = np.array([1 + np.cos(theta), np.sin(theta)])
    a2 = np.array([0, 2 * np.sin(theta)])

    # create a lattice with 2 primitive vectors
    lat = pb.Lattice(a1=a1, a2=a2)

    # add sublattices
    lat.add_sublattices(
        # name, position, and onsite potential
        ('A', [0, 0], onsite[0]),
        ('B', [1, 0], onsite[1])
    )

    # Add hoppings
    lat.add_hoppings(
        # inside the main cell, between which atoms, and the value
        ([0, 0], 'A', 'B', -t),
        # between neighboring cells, between which atoms, and the value
        ([-1, 0], 'A', 'B', -t),
        ([-1, 1], 'A', 'B', -t)
    )
    return lat


def main(onsite=(0, 0), t=1):
    # load lattice
    lattice = honeycomb_lattice(onsite, t)

    # add vacancy StructuralDisorder
    # In this manner we can distribute vacancy disorder
    # on a specific sublattice with a specific concentration.
    # unless you would like the same pattern of disorder at both sublatices,
    # each realisation should be specified as a separate object
    struc_disorder_A = kite.StructuralDisorder(lattice, concentration=0.1)
    struc_disorder_A.add_vacancy('A')
    struc_disorder_B = kite.StructuralDisorder(lattice, concentration=0.1)
    struc_disorder_B.add_vacancy('B')
    disorder_structural = [struc_disorder_A, struc_disorder_B]

    # number of decomposition parts [nx,ny] in each direction of matrix.
    # This divides the lattice into various sections, each of which is calculated in parallel
    nx = ny = 1
    # number of unit cells in each direction.
    lx = ly = 512

    # make config object which caries info about
    # - the number of decomposition parts [nx, ny],
    # - lengths of structure [lx, ly]
    # - boundary conditions [mode,mode, ... ] with modes:
    #   . "periodic"
    #   . "open"
    #   . "twist_fixed" -- this option needs the extra argument ths=[phi_1,..,phi_DIM] where phi_i \in [0, 2*M_PI]
    #   . "twist_random"
    # Boundary Mode
    mode = "periodic"

    # - specify precision of the exported hopping and onsite data, 0 - float, 1 - double, and 2 - long double.
    # - scaling, if None it's automatic, if present select spectrum_range=[e_min, e_max]
    configuration = kite.Configuration(divisions=[nx, ny],
                                       length=[lx, ly],
                                       boundaries=[mode, mode],
                                       is_complex=False,
                                       precision=1)

    # specify calculation type
    calculation = kite.Calculation(configuration)
    calculation.dos(num_points=1000,
                    num_moments=512,
                    num_random=5,
                    num_disorder=1)

    # configure the *.h5 file
    kite.config_system(lattice, configuration, calculation, filename='vacancies-data.h5',
                       disorder_structural=disorder_structural)

    # for generating the desired output from the generated HDF5-file, run
    # ../build/KITEx vacancies-data.h5
    # ../tools/build/KITE-tools vacancies-data.h5


if __name__ == "__main__":
    main()
