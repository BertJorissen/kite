"""Functions to create a HDF5 file"""

import numpy as np
import h5py as hp
import pybinding as pb
from scipy.sparse import coo_matrix

import kite
from typing import Optional, Dict, Union, Literal
from .modification import Modification
from .utils.model import estimate_bounds
__all__ = ['config_system']


def extract_hamiltonian(
        lattice: pb.Lattice, complx: int = 1, energy_shift: float = 0, alias_lookup: Optional[np.ndarray] = None,
        nsub: int = 0, num_orbitals_ref: Optional[np.ndarray] = None,
) -> Dict[Literal["NHoppings", "d", "Hoppings", "num_orbitals"], Union[np.ndarray, int]]:
    """Extract the Hamiltonian from the lattice object

    Parameters
    ----------
    lattice : pb.Lattice
        Pybinding lattice object that carries the info about the unit cell vectors, unit cell cites, hopping terms and
        onsite energies.
    complx : int
        Hamiltonian is complex 1 or real 0
    energy_shift : float
        Shift factor for the hopping parameters
    alias_lookup : Optional[np.ndarray]
        Alias lookup for the sublattices
    nsub : int
        Number of sublattices
    num_orbitals : Optional[np.ndarray]
        Number of orbitals at each atom

    Returns
    -------
    Dict
        Dictionary with the Hamiltonian data
    """
    if nsub == 0:
        nsub = lattice.nsub
    if alias_lookup is None:
        alias_lookup = np.arange(nsub)

    # get number of orbitals at each atom.
    num_orbitals = np.zeros(nsub, dtype=np.int64) - 1

    space_size = lattice.ndim

    # iterate through all the sublattices and add onsite energies to hoppings list and count num of orbital
    # We save everything as hoppings, onsites are hoppings with zero shift.
    hoppings = []

    ############################
    # Extract all the Hoppings #
    ############################

    for name, sub in lattice.sublattices.items():
        # num of orbitals at each sublattice is equal to size of onsite energy
        num_energies = np.asarray(sub.energy).shape[0]
        num_orbitals[alias_lookup[sub.alias_id]] = num_energies
        # define hopping dict from relative hopping index from and to id (relative number of sublattice in relative
        # index lattice) and onsite
        # energy shift is substracted from onsite potential, this is later added to the hopping dictionary,
        # hopping terms shouldn't be substracted
        hopping = {'relative_index': np.zeros(space_size, dtype=np.int32), 'from_id': alias_lookup[sub.alias_id],
                   'to_id': alias_lookup[sub.alias_id], 'hopping_energy': sub.energy - energy_shift}
        hoppings.append(hopping)

    # check if the number of orbitals is the same as the reference array
    if num_orbitals_ref is not None:
        assert len(num_orbitals) == len(num_orbitals_ref), "Number of orbitals in the lattice object and the reference array are not the same!"
        for num_orb_idx, num_orb_ref in enumerate(num_orbitals_ref):
            if num_orbitals[num_orb_idx] == -1:
                num_orbitals[num_orb_idx] = num_orb_ref
            assert num_orbitals[num_orb_idx] == num_orb_ref, "Number of orbitals in the lattice object and the reference array are not the same!"
    else:
        for num_orb_idx, num_orb in enumerate(num_orbitals):
            assert num_orb != -1, "Number of orbitals at sublattice {} is not defined!".format(num_orb_idx)

    # iterate through all the hoppings and add hopping energies to hoppings list
    for name, hop in lattice.hoppings.items():
        hopping_energy = hop.energy
        for term in hop.terms:
            hopping = {'relative_index': term.relative_index[0:space_size], 'from_id': alias_lookup[term.from_id],
                       'to_id': alias_lookup[term.to_id], 'hopping_energy': hopping_energy}
            hoppings.append(hopping)
            # if the unit cell is [0, 0]
            if np.linalg.norm(term.relative_index[0:space_size]) == 0:
                hopping = {'relative_index': term.relative_index[0:space_size], 'from_id': alias_lookup[term.to_id],
                           'to_id': alias_lookup[term.from_id], 'hopping_energy': np.conj(np.transpose(hopping_energy))}
                hoppings.append(hopping)
            # if the unit cell [i, j] is different than [0, 0] and also -[i, j] hoppings with opposite direction
            if np.linalg.norm(term.relative_index[0:space_size]):
                hopping = {'relative_index': -term.relative_index[0:space_size], 'from_id': alias_lookup[term.to_id],
                           'to_id': alias_lookup[term.from_id], 'hopping_energy': np.conj(np.transpose(hopping_energy))}
                hoppings.append(hopping)

    ########################
    # Analyze the Hoppings #
    ########################

    orbital_from = []
    orbital_to = []
    orbital_hop = []
    # number of orbitals before i-th sublattice, where is is the array index
    orbitals_before = np.cumsum(num_orbitals) - num_orbitals
    # iterate through all hoppings, and define unique orbital hoppings
    # orbital_to in unit cell [i, j] is defined  as [i, j] x [1, 3] + relative_orbital_num*3**2 2D
    # orbital_to in unit cell [i, j, k] is defined  as [i, j, k] x [1, 3, 9] + relative_orbital_num*3**3 3D
    # relative index of orbital_from is unique as only hoppings from the orbitals in the initial unit cell are exported
    for h in hoppings:
        hopping_energy = h['hopping_energy']
        it = np.nditer(hopping_energy, flags=['multi_index'])
        while not it.finished:
            # get the indices of the hopping
            row_idx, col_idx = it.multi_index
            # get the shift of the hopping
            shift_vector = h['relative_index'] + 1
            # make the "grid" from the dimension of the space
            space_vector = 3 ** np.linspace(0, space_size - 1, space_size, dtype=np.int32)
            # apply the relative shifts (in units of the lattice vectors)
            relative_move = np.dot(shift_vector, space_vector)

            orbital_from.append(orbitals_before[h['from_id']] + row_idx)
            orbital_to.append(relative_move + (orbitals_before[h['to_id']] + col_idx) * 3 ** space_size)
            orbital_hop.append(it[0] if complx else np.real(it[0]))
            it.iternext()

    ###################################
    # Generate hopping lists for KITE #
    ###################################

    # extract:
    #   t - hoppings where each row corresponds to hopping from row number orbital
    #   d - for each hopping it's unique identifier
    t_list = []
    d_list = []

    # make a sparse matrix from orbital_hop, and (orbital_from, orbital_to)
    #   as it's easier to take nonzero hoppings from  sparse matrix
    # Onsites with energy = 0. will disapear as they are not added in the sparse matrix
    matrix = coo_matrix((orbital_hop, (orbital_from, orbital_to)),
                        shape=(np.max(orbital_from) + 1, np.max(orbital_to) + 1))

    # num_hoppings is a vector where each value corresponds to num of hoppings from orbital equal to it's index
    hop_shape = np.sum(num_orbitals)
    num_hoppings = np.zeros(hop_shape, dtype=np.int32)

    # iterate through all rows of matrix, number of row = number of orbital from
    for i in range(matrix.shape[0]):
        # all hoppings from orbital i
        row_mat = matrix.getrow(i)
        # number of hoppings from orbital i
        num_hoppings[i] = row_mat.size

        t_list.append(row_mat.data)
        d_list.append(row_mat.indices)

    # fix the size of hopping and distance matrices, where the number of columns is max number of hoppings
    max_hop = int(np.max(num_hoppings))
    d = np.zeros((hop_shape, max_hop))
    t = np.zeros((hop_shape, max_hop), dtype=matrix.data.dtype)
    for i_row, d_row in enumerate(d_list):
        t_row = t_list[i_row]
        d[i_row, :len(d_row)] = d_row
        t[i_row, :len(t_row)] = t_row
    return {
        "NHoppings": num_hoppings,
        "d": d,
        "Hoppings": t,
        "num_orbitals": num_orbitals
    }


def config_system(lattice: pb.Lattice, config: kite.Configuration, calculation: kite.Calculation,
                  modification: Optional[kite.Modification] = None, **kwargs):
    """Export the lattice and related parameters to the *.h5 file

    Parameters
    ----------
    lattice
        pb.Lattice: Pybinding lattice object that carries the info about the unit cell vectors, unit cell cites, hopping terms and
        onsite energies. :class:`pb.Lattice`
    config
        Configuration object, basic parameters defining size, precision, energy scale and number of decomposition parts
        in the calculation.
    calculation : Calculation
        Calculation object that defines the requested functions for the calculation.
    modification : Modification = None
        If specified modification object, has the magnetic field selection, either in terms of field, or in the number
        of flux quantum through the selected system.
    **kwargs: Optional arguments like filename, Disorder or Disorder_structural.

    """

    print('##############################################################################')
    print('#                        KITE | Release  1.1                                 #')
    print('#                        Kite home: quantum-kite.com                         #')
    print('#                                                                            #')
    print('#                        Copyright 2024, KITE                                #')
    print('##############################################################################')

    # hamiltonian is complex 1 or real 0
    complx = int(config.comp)
    localEn = config.custom_pot
    printlocalEn = config.print_custom_pot

    # check if there's complex hopping or magnetic field but identifier is_complex is 0
    imag_part = 0
    # loop through all hoppings
    for name, hop in lattice.hoppings.items():
        imag_part += np.linalg.norm(np.asarray(hop.energy).imag)
    if imag_part > 0 and complx == 0:
        print('Complex hoppings are added but is_complex identifier is 0. Automatically turning is_complex to 1!')
        config._is_complex = 1
        config.set_type()

    # set default value
    if not modification:
        modification = Modification(magnetic_field=False)

    # check if magnetic field is On
    if (modification.magnetic_field or modification.flux) and complx == 0:
        print('Magnetic field is added but is_complex identifier is 0. Automatically turning is_complex to 1!')
        config._is_complex = 1
        config.set_type()

    if calculation.get_arpes and complx == 0:
        print('ARPES is requested but is_complex identifier is 0. Automatically turning is_complex to 1!')
        config._is_complex = 1
        config.set_type()

    if calculation.get_gaussian_wave_packet and complx == 0:
        print('Wavepacket is requested but is_complex identifier is 0. Automatically turning is_complex to 1!')
        config._is_complex = 1
        config.set_type()


    # hamiltonian is complex 1 or real 0
    complx = int(config.comp)

    filename = kwargs.get('filename', 'kite_config.h5')

    disorder = kwargs.get('disorder', None)
    disorder_structural = kwargs.get('disorder_structural', None)
    print('\n##############################################################################\n')
    print('SCALING:\n')
    # if bounds are not specified, find a rough estimate
    if not config.energy_scale:
        print('\nAutomatic scaling is being done. If unexpected results are produced, consider '
              '\nselecting the bounds manually. '
              '\nEstimate of the spectrum bounds with a safety factor is: ')
        e_min, e_max = estimate_bounds(lattice, disorder, disorder_structural)
        print('({:.2f}, {:.2f} eV)\n'.format(e_min, e_max))
        # add a safety factor for a scaling factor
        config._energy_scale = (e_max - e_min) / (2 * 0.9)
        config._energy_shift = (e_max + e_min) / 2
    else:
        print('\nManual scaling is chosen. \n')
    print('\n##############################################################################\n')
    print('BOUNDARY CONDITIONS:\n')

    ###########################
    # Extract the Hamiltonian #
    ###########################

    space_size = lattice.ndim
    hamiltonian_data = extract_hamiltonian(lattice, complx, config.energy_shift)
    vectors = np.asarray(lattice.vectors)[:, 0:space_size]
    # get number of orbitals at each atom.
    num_orbitals = hamiltonian_data["num_orbitals"]

    # get all atom positions to the position array.
    position_atoms = np.zeros([lattice.nsub, space_size], dtype=np.float64)
    for name, sub in lattice.sublattices.items():
        # position_atoms is a list of vectors of size space_size
        position_atoms[sub.alias_id, :] = sub.position[0:space_size]

    position_atoms = np.array(position_atoms)
    # repeats the positions of atoms based on the number of orbitals
    position = np.repeat(position_atoms, num_orbitals, axis=0)

    ######################
    # create a HDF5 file #
    ######################

    f = hp.File(filename, 'w')

    f.create_dataset('IS_COMPLEX', data=complx, dtype='u4')
    # precision of hamiltonian float, double, long double
    f.create_dataset('PRECISION', data=config.prec, dtype='u4')
    # number of repetitions in each of the directions
    leng = config.leng
    if len(leng) != space_size:
        raise SystemExit('Select number of unit cells accordingly with the number of dimensions of your system!')
    f.create_dataset('L', data=leng, dtype='u4')
    # periodic boundary conditions, 0 - no, 1 - yes.
    bound, Twists = config.bound
    if len(bound) != space_size:
        raise SystemExit('Select boundary condition accordingly with the number of dimensions of your system!')
    if len(bound) == 3:
        bound_Name = [" ", " ", " "]
        for i in range(len(bound)):
            if bound[i] == 0:
                bound_Name[i] = "Open"
            if bound[i] == 1:
                if Twists[0]==0 and Twists[1] == 0 and Twists[2] == 0:
                    bound_Name[i] = "Periodic"
                else:
                    bound_Name[i] = "Fixed Twisted"
            if bound[i] == 2:
                bound_Name[i] = "Random Twisted"
        print('\nBoundary conditions along the lattice vectors are set to:\n ')
        print("a1:",bound_Name[0],"    a2:",bound_Name[1],"    a3:",bound_Name[2], '\n')

    if len(bound) == 2:
        bound_Name = [" ", " "]
        for i in range(len(bound)):
            if bound[i] == 0:
                bound_Name[i] = "Open"
            if bound[i] == 1:
                if Twists[0]==0 and Twists[1] == 0:
                    bound_Name[i] = "Periodic"
                else:
                    bound_Name[i] = "Fixed Twisted"
            if bound[i] == 2:
                bound_Name[i] = "Random Twisted"
        print('\nBoundary conditions along the lattice vectors are set to:\n ')
        print("a1:",bound_Name[0],"    a2:",bound_Name[1], '\n')
    f.create_dataset('Boundaries', data=bound, dtype='u4')
    f.create_dataset('BoundaryTwists', data=Twists, dtype=float) # JPPP Values of the Fixed Boundary Twists


    print('\n##############################################################################\n')
    print('DECOMPOSITION:\n')
    domain_dec = config.div
    if len(domain_dec) != space_size:
        # worst case 1 selected 3D case
        domain_dec.extend([1, 1])
        print('WARNING: Select number of decomposition parts accordingly with the number of dimensions '
              'of your system! They are chosen automatically to be {}.'.format(domain_dec[0:space_size]))
    # number of divisions of the in each direction of hamiltonian. nx x ny = num_threads
    print('\nChosen number of decomposition parts is:', domain_dec[0:space_size], '.'
                                                                                  '\nINFO: this product will correspond to the total number of threads. '
                                                                                  '\nYou should choose at most the number of processor cores you have.'
                                                                                  '\nWARNING: System size need\'s to be an integer multiple of \n'
                                                                                  '[TILE * ', domain_dec, '] '
                                                                                                          '\nwhere TILE is selected when compiling the C++ code. \n')

    f.create_dataset('Divisions', data=domain_dec[0:space_size], dtype='u4')
    # space dimension of the lattice 1D, 2D, 3D
    f.create_dataset('DIM', data=space_size, dtype='u4')
    # lattice vectors. Size is same as DIM
    f.create_dataset('LattVectors', data=vectors, dtype=np.float64)
    # position for each atom
    f.create_dataset('OrbPositions', data=position, dtype=np.float64)
    # total number of orbitals
    f.create_dataset('NOrbitals', data=np.sum(num_orbitals), dtype='u4')
    # scaling factor for the hopping parameters
    f.create_dataset('EnergyScale', data=config.energy_scale, dtype=np.float64)
    # shift factor for the hopping parameters
    f.create_dataset('EnergyShift', data=config.energy_shift, dtype=np.float64)

    # Hamiltonian group
    grp = f.create_group('Hamiltonian')
    # Hamiltonian group
    grp.create_dataset('NHoppings', data=hamiltonian_data["NHoppings"], dtype='u4')
    # distance
    grp.create_dataset('d', data=hamiltonian_data["d"], dtype='i4')
    # custom pot
    grp.create_dataset('CustomLocalEnergy', data=localEn, dtype=int)
    # custom pot
    grp.create_dataset('PrintCustomLocalEnergy', data=printlocalEn, dtype=int)

    if complx:
        # hoppings
        grp.create_dataset('Hoppings', data=(hamiltonian_data["Hoppings"].astype(config.type)) / config.energy_scale)
    else:
        # hoppings
        grp.create_dataset('Hoppings', data=(hamiltonian_data["Hoppings"].real.astype(config.type)) / config.energy_scale)
    # magnetic field
    if modification.magnetic_field or modification.flux:
        print('\n##############################################################################\n')
        print('MAGNETIC FIELD:\n')

        # find the minimum commensurate magnetic field
        hbar = 6.58211899 * 10 ** -16  #: [eV*s]
        phi0 = 2 * np.pi * hbar  #: [V*s] flux quantum
        vector1_3d = np.zeros(3)
        vector1_3d[:len(vectors[0, :])] = vectors[0, :]
        vector2_3d = np.zeros(3)
        vector2_3d[:len(vectors[1, :])] = vectors[1, :]
        unit_cell_area = np.linalg.norm(np.cross(vector1_3d, vector2_3d)) * 1e-18
        magnetic_field_min = phi0 / (leng[1] * unit_cell_area)
        print('For a selected system size, minimum field is: ', magnetic_field_min)

        multiply_bmin = 0
        if modification.magnetic_field:
            multiply_bmin = int(round(modification.magnetic_field / magnetic_field_min))

            if multiply_bmin == 0:
                raise SystemExit('The system is to small for a desired field.')
            print('Closest_field to the one you selected is {:.2f} T'.format(
                multiply_bmin * magnetic_field_min))

        if modification.flux:
            multiply_bmin = int(round(modification.flux * leng[1]))
            if multiply_bmin == 0:
                raise SystemExit('The system is to small for a desired field.')
            print('Closest_field to the one you selected is {:.2f} T which in the terms of flux quantum is {:.2f}'.
                  format(multiply_bmin * magnetic_field_min, multiply_bmin / leng[1]))
            print('Selected field is {:.2f} T'.format(multiply_bmin * magnetic_field_min))
        grp.create_dataset('MagneticFieldMul', data=int(multiply_bmin), dtype='u4')
        print('\n##############################################################################\n')

    grp_dis = grp.create_group('Disorder')

    if disorder:
        present = disorder._orbital > -1
        len_orb = np.max(np.sum(present, axis=0))
        disorder._orbital = disorder._orbital[0:len_orb, :]

        grp_dis.create_dataset('OnsiteDisorderModelType', data=disorder._type_id, dtype=np.int32)
        grp_dis.create_dataset('OrbitalNum', data=disorder._orbital, dtype=np.int32)
        # no need to substract config.energy_scale from mean value as it's already subtracted once from onsite energy
        grp_dis.create_dataset('OnsiteDisorderMeanValue',
                               data=(np.array(disorder._mean)) / config.energy_scale,
                               dtype=np.float64)
        grp_dis.create_dataset('OnsiteDisorderMeanStdv', data=np.array(disorder._stdv) / config.energy_scale,
                               dtype=np.float64)
    else:
        grp_dis.create_dataset('OnsiteDisorderModelType', (1, 0))
        grp_dis.create_dataset('OrbitalNum', (1, 0))
        grp_dis.create_dataset('OnsiteDisorderMeanValue', (1, 0))
        grp_dis.create_dataset('OnsiteDisorderMeanStdv', (1, 0))

    grp_dis_vac = grp.create_group('Vacancy')
    idx_vacancy = 0
    grp_dis = grp.create_group('StructuralDisorder')

    if disorder_structural:

        if isinstance(disorder_structural, list):
            num_dis = len(disorder_structural)
        else:
            num_dis = 1
            disorder_structural = [disorder_structural]

        for idx in range(num_dis):

            disorder_struct = disorder_structural[idx]

            fixed_positions = disorder_struct._position

            system_l = config._length
            Lx = system_l[0]
            Ly = 1
            Lz = 1

            if len(system_l) == 2:
                Ly = system_l[1]
            elif len(system_l) == 3:
                Ly = system_l[1]
                Lz = system_l[2]

            for item in fixed_positions:
                if item.shape[0] != space_size:
                    raise SystemExit('The position of the structural disorder should be selected with the '
                                     'relative index of length {}'.format(space_size))

            # Check if pos cell is valid
            if space_size == 1:
                if not all(0 <= np.squeeze(np.asarray(item))[0] < Lx for item in fixed_positions):
                    raise SystemExit('The position of the structural disorder should be selected within the relative '
                                     'coordinates [[0, {}],[0, {}],[0, {}]] with the relative index '
                                     'of length {}'.format(Lx - 1, Ly - 1, Lz - 1, space_size))
            if space_size == 2:
                if not all(0 <= np.squeeze(np.asarray(item))[0] < Lx and 0 <= np.squeeze(np.asarray(item))[1] < Ly
                           for item in fixed_positions):
                    raise SystemExit('The position of the structural disorder should be selected within the relative '
                                     'coordinates [[0, {}],[0, {}],[0, {}]] with the relative index '
                                     'of length {}'.format(Lx - 1, Ly - 1, Lz - 1, space_size))

            if space_size == 3:
                if not all(0 <= np.squeeze(np.asarray(item))[0] < Lx and 0 <= np.squeeze(np.asarray(item))[1] < Ly
                           and 0 <= np.squeeze(np.asarray(item))[2] < Lz for item in fixed_positions):
                    raise SystemExit('The position of the structural disorder should be selected within the relative '
                                     'coordinates [[0, {}],[0, {}],[0, {}]] with the relative index '
                                     'of length {}'.format(Lx - 1, Ly - 1, Lz - 1, space_size))

            # fixed_positions_index = [i, j, k] x [1, Lx, Lx*Ly]
            fixed_positions_index = np.asarray(np.dot(fixed_positions, np.array([1, Lx, Lx * Ly], dtype=np.int32)[0:space_size]),
                                               dtype=np.int32).reshape(-1)

            num_orb_vac = len(disorder_struct._orbital_vacancy)
            num_positions = len(fixed_positions_index)
            if num_orb_vac > 0:
                grp_dis_type = grp_dis_vac.create_group('Type{val}'.format(val=idx_vacancy))

                grp_dis_type.create_dataset('Orbitals', data=np.asarray(disorder_struct._orbital_vacancy,
                                                                        dtype=np.int32))

                if disorder_struct._exact_position:
                    grp_dis_type.create_dataset('FixPosition',
                                                data=np.asarray(fixed_positions_index,
                                                                dtype=np.int32))
                else:
                    grp_dis_type.create_dataset('Concentration', data=disorder_struct._concentration,
                                                dtype=np.float64)
                grp_dis_type.create_dataset('NumOrbitals', data=num_orb_vac, dtype=np.int32)
                idx_vacancy += 1

            num_bond_disorder = 2 * disorder_struct._num_bond_disorder_per_type
            num_onsite_disorder = disorder_struct._num_onsite_disorder_per_type
            if num_bond_disorder or num_onsite_disorder:

                for idx_from, idx_to in zip(disorder_struct._rel_idx_from, disorder_struct._rel_idx_to):
                    distance_rel = np.asarray(idx_from) - np.asarray(idx_to)

                    rel_norm = np.linalg.norm(distance_rel)
                    if rel_norm > 1:
                        print('WARNING: hopping distance inside structural disorder exceed the nearest neighbour! \n'
                              'The NGHOST flag inside the C++ code has at least to be equal to the norm of '
                              'the relative distance, \n'
                              'which in this case is between cells {} and {}'.format(idx_from, idx_to))

                # Type idx
                grp_dis_type = grp_dis.create_group('Type{val}'.format(val=idx))

                if disorder_struct._exact_position:

                    grp_dis_type.create_dataset('FixPosition',
                                                data=np.asarray(fixed_positions_index,
                                                                dtype=np.int32))

                else:
                    # Concentration of this type
                    grp_dis_type.create_dataset('Concentration', data=np.asarray(disorder_struct._concentration),
                                                dtype=np.float64)
                # Number of bond disorder
                grp_dis_type.create_dataset('NumBondDisorder',
                                            data=np.asarray(num_bond_disorder),
                                            dtype=np.int32)
                # Number of onsite disorder
                grp_dis_type.create_dataset('NumOnsiteDisorder',
                                            data=np.asarray(num_onsite_disorder),
                                            dtype=np.int32)

                # Node of the bond disorder from
                grp_dis_type.create_dataset('NodeFrom', data=np.asarray(disorder_struct._nodes_from).flatten(),
                                            dtype=np.int32)
                # Node of the bond disorder to
                grp_dis_type.create_dataset('NodeTo', data=np.asarray(disorder_struct._nodes_to).flatten(),
                                            dtype=np.int32)
                # Node of the onsite disorder
                grp_dis_type.create_dataset('NodeOnsite', data=np.asarray(disorder_struct._nodes_onsite),
                                            dtype=np.int32)

                # Num nodes
                grp_dis_type.create_dataset('NumNodes', data=disorder_struct._num_nodes, dtype=np.int32)
                # Orbital mapped for this node
                grp_dis_type.create_dataset('NodePosition', data=np.asarray(disorder_struct._node_orbital),
                                            dtype=np.uint32)

                # Onsite disorder energy
                grp_dis_type.create_dataset('U0',
                                            data=np.asarray(disorder_struct._disorder_onsite).real.astype(
                                                config.type) / config.energy_scale)
                # Bond disorder hopping
                disorder_hopping = disorder_struct._disorder_hopping
                if complx:
                    # hoppings
                    grp_dis_type.create_dataset('Hopping',
                                                data=np.asarray(disorder_hopping).astype(
                                                    config.type).flatten() / config.energy_scale)
                else:
                    # hoppings
                    grp_dis_type.create_dataset('Hopping',
                                                data=np.asarray(disorder_hopping).real.astype(
                                                    config.type).flatten() / config.energy_scale)

    # Calculation function defined with num_moments, num_random vectors, and num_disorder etc. realisations
    grpc = f.create_group('Calculation')
    if calculation.get_dos:
        grpc_p = grpc.create_group('dos')

        moments, random, point, dis, temp, direction = [], [], [], [], [], []
        for single_dos in calculation.get_dos:
            moments.append(single_dos['num_moments'])
            random.append(single_dos['num_random'])
            point.append(single_dos['num_points'])
            dis.append(single_dos['num_disorder'])

        if len(calculation.get_dos) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=moments, dtype=np.int32)
        grpc_p.create_dataset('NumRandoms', data=random, dtype=np.int32)
        grpc_p.create_dataset('NumPoints', data=point, dtype=np.int32)
        grpc_p.create_dataset('NumDisorder', data=dis, dtype=np.int32)

    if calculation.get_ldos:
        grpc_p = grpc.create_group('ldos')

        single_ldos = calculation.get_ldos[0]
        moments = single_ldos['num_moments']
        energy = single_ldos['energy']
        position = single_ldos['position']
        sublattice = single_ldos['sublattice']
        dis = single_ldos['num_disorder']

        if len(calculation.get_ldos) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')

        #position = np.squeeze(position)
        len_pos = np.array(position).shape[0]

        if isinstance(sublattice, list):
            len_sub = len(sublattice)
        else:
            len_sub = 1
            sublattice = [sublattice]

        if len_pos != len_sub and (len_pos != 1 and len_sub != 1):
            raise SystemExit('Number of sublattices and number of positions should either have the same '
                             'length or should be specified as a single value! Choose them accordingly.')

        # get the names and sublattices from the lattice
        names, sublattices_all = zip(*lattice.sublattices.items())

        # convert relative index and sublattice to orbital number
        orbitals = []
        system_l = config._length
        Lx = system_l[0]
        Ly = 1
        Lz = 1

        if len(system_l) == 2:
            Ly = system_l[1]
        elif len(system_l) == 3:
            Ly = system_l[1]
            Lz = system_l[2]

        for item in position:
            if item.shape[0] != space_size:
                raise SystemExit('The probing position for the LDOS should be selected with the '
                                 'relative index of length {}'.format(space_size))

        # Check if pos cell is valid
        if space_size == 1:
            if not np.all(0 <= np.squeeze(np.asarray(item))[0] < Lx for item in position):
                raise SystemExit('The probing position for the LDOS should be selected within the relative '
                                 'coordinates [[0, {}],[0, {}],[0, {}]] with the relative index '
                                 'of length {}'.format(Lx - 1, Ly - 1, Lz - 1, space_size))
        if space_size == 2:
            if not np.all(np.all(0 <= np.squeeze(np.asarray(item))[0] < Lx)
                          and np.all(0 <= np.squeeze(np.asarray(item))[1] < Ly) for item in position):
                raise SystemExit('The probing position for the LDOS should be selected within the relative '
                                 'coordinates [[0, {}],[0, {}],[0, {}]] with the relative index '
                                 'of length {}'.format(Lx - 1, Ly - 1, Lz - 1, space_size))

        if space_size == 3:
            if not np.all(0 <= np.squeeze(np.asarray(item))[0] < Lx and 0 <= np.squeeze(np.asarray(item))[1] < Ly
                       and 0 <= np.squeeze(np.asarray(item))[2] < Lz for item in position):
                raise SystemExit('The probing position for the LDOS should be selected within the relative '
                                 'coordinates [[0, {}],[0, {}],[0, {}]] with the relative index '
                                 'of length {}'.format(Lx - 1, Ly - 1, Lz - 1, space_size))

        # fixed_positions_index = [i, j, k] x [1, Lx, Lx*Ly]
        fixed_positions = np.asarray(np.dot(position, np.array([1, Lx, Lx * Ly], dtype=np.int32)[0:space_size]),
                                     dtype=np.int32).reshape(-1)
        # num_positions_ldos = fixed_positions.shape[0]
        for sub in sublattice:

            if sub not in names:
                raise SystemExit('Desired sublattice for LDOS calculation doesn\'t exist in the chosen lattice! ')

            indx = names.index(sub)
            lattice_sub = sublattices_all[indx]
            sub_id = lattice_sub.alias_id
            it = np.nditer(lattice_sub.energy, flags=['multi_index'])

            # orbit_idx = [i, j, k] x [1, Lx, Lx*Ly] + orbital * Lx*Ly*Lz
            orbitals_before = np.cumsum(num_orbitals) - num_orbitals
            while not it.finished:
                orbit = int(orbitals_before[sub_id] + it.multi_index[0])
                orbitals.append(orbit)
                it.iternext()
        # num_orbitals = np.asarray(orbitals).shape[0]
        if len(calculation.get_ldos) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=moments, dtype=np.int32)
        grpc_p.create_dataset('Energy', data=(np.asarray(energy) - config.energy_shift) / config.energy_scale, dtype=np.float32)
        if len_sub != len_pos:
            grpc_p.create_dataset('Orbitals', data=np.tile(np.asarray(orbitals),len_pos).reshape(-1), dtype=np.int32)
            grpc_p.create_dataset('FixPosition', data=np.repeat(np.asarray(fixed_positions),len_sub), dtype=np.int32)
        else:
            grpc_p.create_dataset('Orbitals', data=np.asarray(orbitals), dtype=np.int32)
            grpc_p.create_dataset('FixPosition', data=np.asarray(fixed_positions), dtype=np.int32)
        grpc_p.create_dataset('NumDisorder', data=dis, dtype=np.int32)

    if calculation.get_arpes:
        grpc_p = grpc.create_group('arpes')

        moments, k_vector, dis, spinor = [], [], [], []
        for single_arpes in calculation.get_arpes:
            moments.append(single_arpes['num_moments'])
            k_vector.append(single_arpes['k_vector'])
            dis.append(single_arpes['num_disorder'])
            spinor.append(single_arpes['weight'])

        # Get the k vectors written in terms of the reciprocal lattice vectors
        k_vector = np.atleast_2d(k_vector)
        k_vector_rel = k_vector @ vectors.T / (np.pi * 2)

        if len(calculation.get_arpes) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=moments, dtype=np.int32)
        grpc_p.create_dataset('k_vector', data=np.reshape(k_vector_rel.flatten(), (-1, space_size)), dtype=np.float64)
        grpc_p.create_dataset('NumDisorder', data=dis, dtype=np.int32)
        grpc_p.create_dataset('OrbitalWeights', data=np.atleast_2d(spinor))

    if calculation.get_gaussian_wave_packet:
        grpc_p = grpc.create_group('gaussian_wave_packet')

        num_moments, num_points, num_disorder, spinor, width, k_vector, mean_value, \
        probing_points = [], [], [], [], [], [], [], []
        timestep = []
        for single_gauss_wavepacket in calculation.get_gaussian_wave_packet:
            num_moments.append(single_gauss_wavepacket['num_moments'])
            num_points.append(single_gauss_wavepacket['num_points'])
            num_disorder.append(single_gauss_wavepacket['num_disorder'])
            spinor.append(single_gauss_wavepacket['spinor'])
            width.append(single_gauss_wavepacket['width'])
            k_vector.append(single_gauss_wavepacket['k_vector'])
            mean_value.append(single_gauss_wavepacket['mean_value'])
            timestep.append(single_gauss_wavepacket['timestep'])
            probing_points.append(single_gauss_wavepacket['probing_point'])
        if len(calculation.get_gaussian_wave_packet) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=num_moments, dtype=np.int32)
        grpc_p.create_dataset('NumPoints', data=num_points, dtype=np.int32)
        grpc_p.create_dataset('NumDisorder', data=num_disorder, dtype=np.int32)
        grpc_p.create_dataset('mean_value', data=mean_value, dtype=np.int32)
        grpc_p.create_dataset('ProbingPoint', data=np.array(probing_points, np.float64))
        grpc_p.create_dataset('width', data=width, dtype=np.float64)
        grpc_p.create_dataset('spinor', data=np.array(np.atleast_2d(spinor), dtype=config.type))
        grpc_p.create_dataset('k_vector', data=np.reshape(np.array(k_vector).flatten(), (-1, space_size)), dtype=np.float64)
        grpc_p.create_dataset('timestep', data=timestep, dtype=np.float32)

    if calculation.get_conductivity_dc:
        grpc_p = grpc.create_group('conductivity_dc')

        moments, random, point, dis, temp, direction = [], [], [], [], [], []
        for single_cond_dc in calculation.get_conductivity_dc:
            moments.append(single_cond_dc['num_moments'])
            random.append(single_cond_dc['num_random'])
            point.append(single_cond_dc['num_points'])
            dis.append(single_cond_dc['num_disorder'])
            temp.append(single_cond_dc['temperature'])
            direction.append(single_cond_dc['direction'])

        if len(calculation.get_conductivity_dc) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=np.asarray(moments), dtype=np.int32)
        grpc_p.create_dataset('NumRandoms', data=np.asarray(random), dtype=np.int32)
        grpc_p.create_dataset('NumPoints', data=np.asarray(point), dtype=np.int32)
        grpc_p.create_dataset('NumDisorder', data=np.asarray(dis), dtype=np.int32)
        grpc_p.create_dataset('Temperature', data=np.asarray(temp) / config.energy_scale, dtype=np.float64)
        grpc_p.create_dataset('Direction', data=np.asarray(direction), dtype=np.int32)

    if calculation.get_conductivity_optical:
        grpc_p = grpc.create_group('conductivity_optical')

        moments, random, point, dis, temp, direction = [], [], [], [], [], []
        for single_cond_opt in calculation.get_conductivity_optical:
            moments.append(single_cond_opt['num_moments'])
            random.append(single_cond_opt['num_random'])
            point.append(single_cond_opt['num_points'])
            dis.append(single_cond_opt['num_disorder'])
            temp.append(single_cond_opt['temperature'])
            direction.append(single_cond_opt['direction'])

        if len(calculation.get_conductivity_optical) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=np.asarray(moments), dtype=np.int32)
        grpc_p.create_dataset('NumRandoms', data=np.asarray(random), dtype=np.int32)
        grpc_p.create_dataset('NumPoints', data=np.asarray(point), dtype=np.int32)
        grpc_p.create_dataset('NumDisorder', data=np.asarray(dis), dtype=np.int32)
        grpc_p.create_dataset('Temperature', data=np.asarray(temp) / config.energy_scale, dtype=np.float64)
        grpc_p.create_dataset('Direction', data=np.asarray(direction), dtype=np.int32)

    if calculation.get_conductivity_optical_nonlinear:
        grpc_p = grpc.create_group('conductivity_optical_nonlinear')

        moments, random, point, dis, temp, direction, special = [], [], [], [], [], [], []
        for single_cond_opt_non in calculation.get_conductivity_optical_nonlinear:
            moments.append(single_cond_opt_non['num_moments'])
            random.append(single_cond_opt_non['num_random'])
            point.append(single_cond_opt_non['num_points'])
            dis.append(single_cond_opt_non['num_disorder'])
            temp.append(single_cond_opt_non['temperature'])
            direction.append(single_cond_opt_non['direction'])
            special.append(single_cond_opt_non['special'])

        if len(calculation.get_conductivity_optical_nonlinear) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=np.asarray(moments), dtype=np.int32)
        grpc_p.create_dataset('NumRandoms', data=np.asarray(random), dtype=np.int32)
        grpc_p.create_dataset('NumPoints', data=np.asarray(point), dtype=np.int32)
        grpc_p.create_dataset('NumDisorder', data=np.asarray(dis), dtype=np.int32)
        grpc_p.create_dataset('Temperature', data=np.asarray(temp) / config.energy_scale, dtype=np.float64)
        grpc_p.create_dataset('Direction', data=np.asarray(direction), dtype=np.int32)
        grpc_p.create_dataset('Special', data=np.asarray(special), dtype=np.int32)

    if calculation.get_singleshot_conductivity_dc:
        grpc_p = grpc.create_group('singleshot_conductivity_dc')

        moments, random, dis, energies, eta, direction, preserve_disorder = [], [], [], [], [], [], []

        for single_singlshot_cond in calculation.get_singleshot_conductivity_dc:

            energy_ = single_singlshot_cond['energy']
            eta_ = single_singlshot_cond['eta']
            preserve_disorder_ = single_singlshot_cond['preserve_disorder']
            moments_ = single_singlshot_cond['num_moments']

            # get the lengts
            len_en = energy_.size
            len_eta = eta_.size
            len_preserve_dis = preserve_disorder_.size
            len_moments = moments_.size

            lengths = np.array([len_en, len_eta, len_preserve_dis, len_moments])

            # find the max length
            max_length = np.max(lengths)

            # check if lenghts are consistent
            if (len_en != max_length and len_en != 1) or (len_eta != max_length and len_eta != 1) or \
                    (len_preserve_dis != max_length and len_preserve_dis != 1) or \
                    (len_moments != max_length and len_moments != 1):
                raise SystemExit('Number of moments, eta, energy and preserve_disorder should either have the same '
                                 'length or specified as a single value! Choose them accordingly.')

            # make all lists equal in length
            if len_en == 1:
                energy_ = np.repeat(energy_, max_length)
            if len_eta == 1:
                eta_ = np.repeat(eta_, max_length)
            if len_preserve_dis == 1:
                preserve_disorder_ = np.repeat(preserve_disorder_, max_length)
            if len_moments == 1:
                moments_ = np.repeat(moments_, max_length)

            moments.append(moments_)
            energies.append(energy_)
            eta.append(eta_)
            random.append(single_singlshot_cond['num_random'])
            dis.append(single_singlshot_cond['num_disorder'])
            direction.append(single_singlshot_cond['direction'])
            preserve_disorder.append(preserve_disorder_)

        if len(calculation.get_singleshot_conductivity_dc) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=np.asarray(moments), dtype=np.int32)
        grpc_p.create_dataset('NumRandoms', data=np.asarray(random), dtype=np.int32)
        grpc_p.create_dataset('NumDisorder', data=np.asarray(dis), dtype=np.int32)
        grpc_p.create_dataset('Energy', data=(np.asarray(energies) - config.energy_shift) / config.energy_scale,
                              dtype=np.float64)
        grpc_p.create_dataset('Gamma', data=np.asarray(eta) / config.energy_scale, dtype=np.float64)
        grpc_p.create_dataset('Direction', data=np.asarray(direction), dtype=np.int32)
        grpc_p.create_dataset('PreserveDisorder', data=np.asarray(preserve_disorder).astype(int), dtype=np.int32)

    if calculation.get_operators:
        grpc_spectraloperator = grpc.create_group("SpectralOperators")

        # The operator names (str) and operators (pb.Lattice)
        operator_names = [operator[0] for operator in calculation.get_operators]
        operator_values = [operator[1] for operator in calculation.get_operators]
        operator_hamiltonians: Dict[str, dict] = {}

        lat_name_to_alias = {k: v.alias_id for k, v in lattice.sublattices.items()}

        # check if the sublattices in the operator are defined in the 'main' lattice and the datatypes are as expected
        imag_part = 0
        print("ref")
        print(hamiltonian_data)
        for operator_value, operator_name in zip(operator_values, operator_names):
            assert isinstance(operator_value, pb.Lattice), \
                f"The operator {operator_name} is not a valid operator, pb.Lattice object expected."
            assert lattice.ndim == operator_value.ndim, \
                f"The operator {operator_name} has a different dimension than the lattice, {lattice.ndim} != {operator_value.ndim}."
            for hop in operator_value.hoppings.values():
                # check if there's complex hopping or magnetic field but identifier is_complex is 0
                imag_part += np.linalg.norm(np.asarray(hop.energy).imag)
            # conversion list
            lookup_alias = -1 * np.ones(operator_value.nsub, dtype=int)
            for operator_onsite_name, operator_onsite_sub in operator_value.sublattices.items():
                assert operator_onsite_name in lattice.sublattices,\
                    f"The sublattice {operator_onsite_name} for operator {operator_name} is not defined in the lattice."
                lookup_alias[operator_onsite_sub.alias_id] = lat_name_to_alias[operator_onsite_name]
            # check if the alias_id is defined in the lattice
            assert np.all(lookup_alias != -1),\
                f"Sublattice alias_id not defined in the lattice for operator {operator_name}"
            # place the operator in the dictionary
            operator_hamiltonians[operator_name] = extract_hamiltonian(
                operator_value,
                complx,
                alias_lookup=lookup_alias,
                nsub=lattice.nsub,
                num_orbitals_ref=num_orbitals
            )

        if imag_part > 0 and config._is_complex == 0:
            print("Complex hoppings are added in the operator, but 'is_complex' is 0. Unexpected behaviour expected.")

        operator_list_indices: List[List[Tuple[int, int]]] = []
        spectrum_list: List[Tuple[int, int, Tuple[int, int] | Tuple[np.ndarray, np.ndarray, np.ndarray]]] = []
        conversion_dict = {"vx": -1, "vy": -2, "vz": -3, "e": -4}

        def check_name(operator_name: str) -> int:
            # check if the operator_couple is in the operator_names
            if operator_name in operator_names:
                return operator_names.index(operator_name)
            # check if the operator_couple is in the conversion_dict
            elif operator_name in conversion_dict:
                return conversion_dict[operator_name]
            assert False, f"The operator {operator_couple} is not a defined operator"

        # extract the operators
        for operator_list in calculation.get_operator_vertices[0]["operators_list"]:
            # sort the list of operators and convert them to indices
            operator_list_indices_one_spectrum: List[Tuple[int, int]] = []
            for operator_couple in operator_list:
                # check whether the operator_couple is a string or a list/tuple
                if isinstance(operator_couple, str):
                    operator_list_indices_one_spectrum.append(
                        (check_name(operator_couple), conversion_dict["e"])
                    )
                else:
                    operator_list_indices_one_spectrum.append(
                        (check_name(operator_couple[0]), check_name(operator_couple[1]))
                    )
            operator_list_indices.append(operator_list_indices_one_spectrum)


        conversion_dict_spectrum = {"FullSpectrum": 0, "SingleShot": 1}
        conversion_dict_type = {"Dirac": 0, "Greens": 1}
        # extract the spectrum
        for spectrum in calculation.get_operator_vertices[0]["spectrum_list"]:
            # spectrum properties
            assert spectrum[0] in conversion_dict_spectrum, f"The spectrum type {spectrum[0]} is not defined."
            spectrum_one = conversion_dict_spectrum[spectrum[0]]
            assert spectrum[1] in conversion_dict_type, f"The spectrum type {spectrum[1]} is not defined."
            spectrum_one_type = conversion_dict_type[spectrum[1]]
            # FullSpectrum
            if spectrum_one == 0:
                assert len(spectrum[2]) == 2, "The spectrum should be a iterable of dimension 2, got {spectrum[2]}"
                for check_type, check_name in zip([spectrum[2][0], spectrum[2][1]], ["energy", "moments"]):
                    assert np.isscalar(check_type), f"Number of {check_name} should be a single value, got {check_type}"
                spectrum_one_data = spectrum[2]
            # SingleShot
            else:
                assert len(spectrum[2]) == 3, f"The spectrum should be a iterable of dimension 3, got {spectrum[2]}"
                energy = np.atleast_1d(spectrum[2][0])
                eta = np.atleast_1d(spectrum[2][1])
                moments = np.atleast_1d(spectrum[2][2])
                # find the max length
                max_length = np.max([energy.size, eta.size, moments.size])

                # check if lenghts are consistent
                for check_type, check_name in zip([energy, eta, moments], ["energy", "eta", "moments"]):
                    assert (check_type.size == max_length or check_type.size == 1), \
                        f"Number of {check_name} should either have the same length or specified as a single value, got {check_type.size} != {max_length} or 1"
                # make all lists equal in length
                if energy.size == 1:
                    energy = np.repeat(energy, max_length)
                if eta.size == 1:
                    eta = np.repeat(eta, max_length)
                if moments.size == 1:
                    moments = np.repeat(moments, max_length)
                spectrum_one_data = (energy, eta, moments)
            spectrum_list.append((spectrum_one, spectrum_one_type, spectrum_one_data))

        grpc_spectraloperator.create_dataset('NumRandom', data=np.asarray(calculation.get_operator_vertices[0]["num_random"]), dtype=np.int32)
        grpc_spectraloperator.create_dataset('NumDisorder', data=np.asarray(calculation.get_operator_vertices[0]["num_disorder"]), dtype=np.int32)
        grpc_spectraloperator.create_dataset('PreserveDisorder', data=np.asarray(calculation.get_operator_vertices[0]["preserve_disorder"]).astype(int), dtype=np.int32)

        # create the local operators
        grpcs_operators = grpc_spectraloperator.create_group('Operators')
        for idx, operator_name in enumerate(operator_names):
            grpcsi_operator = grpcs_operators.create_group(str(idx))
            # Hamiltonian group
            grpcsi_operator.create_dataset('NHoppings', data=operator_hamiltonians[operator_name]["NHoppings"], dtype='u4')
            # distance
            grpcsi_operator.create_dataset('d', data=operator_hamiltonians[operator_name]["d"], dtype='i4')
            if complx:
                # hoppings
                grpcsi_operator.create_dataset('Hoppings', data=(operator_hamiltonians[operator_name]["Hoppings"].astype(config.type)) / config.energy_scale)
            else:
                # hoppings
                grpcsi_operator.create_dataset('Hoppings', data=(operator_hamiltonians[operator_name]["Hoppings"].real.astype(config.type)) / config.energy_scale)

        grpcs_vertices = grpc_spectraloperator.create_group('Vertices')
        # create the spectral operators and the list of operations
        for vertex_idx, (operatorvertex, spectrum_vertex) in enumerate(zip(operator_list_indices, spectrum_list)):
            grpcsi_vertex = grpcs_vertices.create_group(str(vertex_idx))
            # create the list of operators
            grpcsi_vertex.create_dataset('Operators', data=np.asarray(operatorvertex), dtype='i4')
            # create the spectrum
            grpcsi_vertex.create_dataset('Spectrum', data=np.asarray(spectrum_vertex[0]), dtype='i4')
            grpcsi_vertex.create_dataset('SpectrumType', data=np.asarray(spectrum_vertex[1]), dtype='i4')
            # FullSpectrum
            if spectrum_vertex[0] == 0:
                moments, points = spectrum_vertex[2]
                grpcsi_vertex.create_dataset('NumMoments', data=np.asarray(moments), dtype=np.int32)
                grpcsi_vertex.create_dataset('NumPoints', data=np.asarray(points), dtype=np.int32)
            # SingleShot
            else:
                energy, eta, moments = spectrum_vertex[2]
                grpcsi_vertex.create_dataset('Energy', data=(np.asarray(energy) - config.energy_shift) / config.energy_scale, dtype=np.float64)
                grpcsi_vertex.create_dataset('Gamma', data=np.asarray(eta) / config.energy_scale, dtype=np.float64)
                grpcsi_vertex.create_dataset('NumMoments', data=np.asarray(moments), dtype=np.int32)

    print('\n##############################################################################\n')
    print('OUTPUT:\n')
    print('\nExporting of KITE configuration to {} finished.\n'.format(filename))
    print('\n##############################################################################\n')
    f.close()
