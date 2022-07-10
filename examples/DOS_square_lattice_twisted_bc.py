"""       
        ##############################################################################      
        #                        KITE | Release  1.1                                 #      
        #                                                                            #      
        #                        Kite home: quantum-kite.com                         #           
        #                                                                            #      
        #  Developed by: Simao M. Joao, Joao V. Lopes, Tatiana G. Rappoport,         #       
        #  Misa Andelkovic, Lucian Covaci, Aires Ferreira, 2018-2022                 #      
        #                                                                            #      
        ##############################################################################      
"""
""" Density of states of a square lattice model 

    Units: arbitrary (energy in units of hopping, |t| = 1)
    Lattice: Square lattice
    Configuration: Twisted boundary conditions, double precision, automatic Hamiltonian rescaling;
    Calculation type: Average DOS;
    Last updated: 10/07/2022
"""

import kite
import numpy as np
import pybinding as pb

def square_lattice(onsite=(0, 0)):
    # Return lattice specification for a square lattice with nearest neighbor hoppings

    a1 = np.array([1, 0])
    a2 = np.array([0, 1])

    # create a lattice with 2 primitive vectors
    lat = pb.Lattice(a1=a1, a2=a2)

    # Add sublattices
    lat.add_sublattices(('A', [0, 0], onsite[0]))

    # Add hoppings
    lat.add_hoppings(([1, 0], 'A', 'A', - 1),
                     ([0, 1], 'A', 'A', - 1))

    return lat

# load lattice
lattice = square_lattice()
# number of decomposition parts in each direction of matrix. This divides the lattice into various sections,
# each of which is calculated in parallel
nx = ny = 1
# number of unit cells in each direction.
lx = ly = 32

# - boundary conditions [mode,mode, ... ] with modes:
#   . "periodic"
#   . "open"
#   . "twist_fixed"     this option needs the extra argument ths=[phi_1,..,phi_DIM] where phi_i \in [0, 2*M_PI]  
#   . "twist_random"
# Boundary Mode
mode = "twisted"
# Twists in each direction
twsx = twsy = twsz = np.pi/2.0

configuration = kite.Configuration(divisions=[nx, ny], length=[lx, ly], boundaries=[mode,mode], is_complex=True, precision=1, angles=[twsx, twsy])
# specify calculation type
calculation = kite.Calculation(configuration)
calculation.dos(num_points=4000, num_moments=256, num_random=256, num_disorder=1)
# configure the *.h5 file
kite.config_system(lattice, configuration, calculation, filename='square_lattice.h5')