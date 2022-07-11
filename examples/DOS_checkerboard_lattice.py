"""       
        ##############################################################################      
        #                        Copyright 2022, KITE                                #            
        #                        Home page: quantum-kite.com                         #        
        ##############################################################################      
"""
""" Density of states of a checkerboard lattice

    Units: Energy in units of hopping, |t| = 1
    Lattice: Checkerboard lattice
    Configuration: Periodic boundary conditions, double precision, automatic rescaling
    Calculation type: Average DOS
    Last updated: 10/07/2022
"""

import kite
import numpy as np
import pybinding as pb

def checkboard_lattice(onsite=(0, 0)):
    # Return lattice specification for a checkboard model with nearest neighbor hoppings

    a1=np.array([1, 0])
    a2=np.array([0, 1])
    
    # create a lattice with 2 primitive vectors
    lat = pb.Lattice(a1=a1, a2=a2)
    
    # add sublattices
    lat.add_sublattices(('A', [0,  0], onsite[0]),('B', [1/2,  1/2], onsite[1]))

    # Add hoppings
    lat.add_hoppings(
        # inside the main cell
        ([0,  0], 'A', 'B', -1),
        # between neighboring cells
        ([-1, 0], 'A', 'B',  -1),
        ([0, -1], 'A', 'B',  -1),
        ([-1, -1], 'A', 'B', -1))

    return lat

# load lattice
delta = 0.1 
lattice = checkboard_lattice((-delta,delta))
# number of decomposition parts [nx,ny,nz] in each direction of matrix. This divides the lattice into various sections,
# each of which is calculated in parallel
nx = ny = 2
# number of unit cells in each direction.
lx = ly = 512

# - boundary conditions [mode,mode, ... ] with modes:
#   . "periodic"
#   . "open"
#   . "twist_fixed" -- this option needs the extra argument ths=[phi_1,..,phi_DIM] where phi_i \in [0, 2*M_PI]  
#   . "twist_random"
# Boundary Mode
mode = "periodic"

configuration = kite.Configuration(divisions=[nx, ny], length=[lx, ly], boundaries=[mode,mode], is_complex=False, precision=1)
# specify calculation type
calculation = kite.Calculation(configuration)
calculation.dos(num_points=1000, num_moments=512, num_random=5, num_disorder=1)
# configure the *.h5 file
kite.config_system(lattice, configuration, calculation, filename='checkboard_lattice.h5')
