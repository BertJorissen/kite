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
        """Define basic parameters used in the calculation

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


def config_system(lattice, config, calculation, modification=None, **kwargs):
    """Export the lattice and related parameters to the *.h5 file

    Parameters
    ----------
    lattice : pb.Lattice
        Pybinding lattice object that carries the info about the unit cell vectors, unit cell cites, hopping terms and
        onsite energies.
    config : Configuration
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
    print('#                        Copyright 2022, KITE                                #')
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

    vectors = np.asarray(lattice.vectors)
    space_size = vectors.shape[0]
    vectors = vectors[:, 0:space_size]

    # iterate through all the sublattices and add onsite energies to hoppings list
    # count num of orbitals and read the atom positions.
    hoppings = []
    # get number of orbitals at each atom.
    num_orbitals = np.zeros(lattice.nsub, dtype=np.int64)
    # get all atom positions to the position array.
    position_atoms = np.zeros([lattice.nsub, space_size], dtype=np.float64)
    for name, sub in lattice.sublattices.items():
        # num of orbitals at each sublattice is equal to size of onsite energy
        num_energies = np.asarray(sub.energy).shape[0]
        num_orbitals[sub.alias_id] = num_energies
        # position_atoms is a list of vectors of size space_size
        position_atoms[sub.alias_id, :] = sub.position[0:space_size]
        # define hopping dict from relative hopping index from and to id (relative number of sublattice in relative
        # index lattice) and onsite
        # energy shift is substracted from onsite potential, this is later added to the hopping dictionary,
        # hopping terms shouldn't be substracted
        hopping = {'relative_index': np.zeros(space_size, dtype=np.int32), 'from_id': sub.alias_id,
                   'to_id': sub.alias_id, 'hopping_energy': sub.energy - config.energy_shift}
        hoppings.append(hopping)

    # num_orbitals = np.asarray(num_orbitals)
    position_atoms = np.array(position_atoms)
    # repeats the positions of atoms based on the number of orbitals
    position = np.repeat(position_atoms, num_orbitals, axis=0)

    # iterate through all the hoppings and add hopping energies to hoppings list
    for name, hop in lattice.hoppings.items():
        hopping_energy = hop.energy
        for term in hop.terms:
            hopping = {'relative_index': term.relative_index[0:space_size], 'from_id': term.from_id,
                       'to_id': term.to_id, 'hopping_energy': hopping_energy}
            hoppings.append(hopping)
            # if the unit cell is [0, 0]
            if np.linalg.norm(term.relative_index[0:space_size]) == 0:
                hopping = {'relative_index': term.relative_index[0:space_size], 'from_id': term.to_id,
                           'to_id': term.from_id, 'hopping_energy': np.conj(np.transpose(hopping_energy))}
                hoppings.append(hopping)
            # if the unit cell [i, j] is different than [0, 0] and also -[i, j] hoppings with opposite direction
            if np.linalg.norm(term.relative_index[0:space_size]):
                hopping = {'relative_index': -term.relative_index[0:space_size], 'from_id': term.to_id,
                           'to_id': term.from_id, 'hopping_energy': np.conj(np.transpose(hopping_energy))}
                hoppings.append(hopping)

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
            relative_move = np.dot(h['relative_index'] + 1,
                                   3 ** np.linspace(0, space_size - 1, space_size, dtype=np.int32))
            # if hopping_energy.size > 1:
            orbital_from.append(orbitals_before[h['from_id']] + it.multi_index[0])
            orbital_to.append(relative_move + (orbitals_before[h['to_id']] + it.multi_index[1]) * 3 ** space_size)
            # else:
            #     orbital_from.append(h['from_id'])
            #     orbital_to.append(relative_move + h['to_id'] * 3 ** space_size)

            orbital_hop.append(it[0] if complx else np.real(it[0]))

            it.iternext()

    # extract t - hoppings where each row corresponds to hopping from row number orbital and d - for each hopping it's
    # unique identifier
    t_list = []
    d_list = []
    # make a sparse matrix from orbital_hop, and (orbital_from, orbital_to) as it's easier to take nonzero hoppings from
    # sparse matrix
    matrix = coo_matrix((orbital_hop, (orbital_from, orbital_to)),
                        shape=(np.max(orbital_from) + 1, np.max(orbital_to) + 1))
    # num_hoppings is a vector where each value corresponds to num of hoppings from orbital equal to it's index
    num_hoppings = np.zeros(matrix.shape[0])
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
    d = np.zeros((matrix.shape[0], max_hop))
    t = np.zeros((matrix.shape[0], max_hop), dtype=matrix.data.dtype)
    for i_row, d_row in enumerate(d_list):
        t_row = t_list[i_row]
        d[i_row, :len(d_row)] = d_row
        t[i_row, :len(t_row)] = t_row

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
    grp.create_dataset('NHoppings', data=num_hoppings, dtype='u4')
    # distance
    grp.create_dataset('d', data=d, dtype='i4')
    # custom pot
    grp.create_dataset('CustomLocalEnergy', data=localEn, dtype=int)
    # custom pot
    grp.create_dataset('PrintCustomLocalEnergy', data=printlocalEn, dtype=int)

    if complx:
        # hoppings
        grp.create_dataset('Hoppings', data=(t.astype(config.type)) / config.energy_scale)
    else:
        # hoppings
        grp.create_dataset('Hoppings', data=(t.real.astype(config.type)) / config.energy_scale)
    # magnetic field
    if modification.magnetic_field or modification.flux:
        print('\n##############################################################################\n')
        print('MAGNETIC FIELD:\n')

        # find the minimum commensurate magnetic field
        hbar = 6.58211899 * 10 ** -16  #: [eV*s]
        phi0 = 2 * np.pi * hbar  #: [V*s] flux quantum
        unit_cell_area = np.linalg.norm(np.cross(vectors[0, :], vectors[1, :])) * 1e-18
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
                if item.shape[1] != space_size:
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

        position = np.squeeze(position)
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
            if item.shape[1] != space_size:
                raise SystemExit('The probing position for the LDOS should be selected with the '
                                 'relative index of length {}'.format(space_size))

        # Check if pos cell is valid
        if space_size == 1:
            if not all(0 <= np.squeeze(np.asarray(item))[0] < Lx for item in position):
                raise SystemExit('The probing position for the LDOS should be selected within the relative '
                                 'coordinates [[0, {}],[0, {}],[0, {}]] with the relative index '
                                 'of length {}'.format(Lx - 1, Ly - 1, Lz - 1, space_size))
        if space_size == 2:
            if not all(0 <= np.squeeze(np.asarray(item))[0] < Lx and 0 <= np.squeeze(np.asarray(item))[1] < Ly
                       for item in position):
                raise SystemExit('The probing position for the LDOS should be selected within the relative '
                                 'coordinates [[0, {}],[0, {}],[0, {}]] with the relative index '
                                 'of length {}'.format(Lx - 1, Ly - 1, Lz - 1, space_size))

        if space_size == 3:
            if not all(0 <= np.squeeze(np.asarray(item))[0] < Lx and 0 <= np.squeeze(np.asarray(item))[1] < Ly
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
        k_vector = np.asmatrix(np.asarray(k_vector))
        k_vector_rel = k_vector@vectors.transpose()/np.pi/2

        if len(calculation.get_arpes) > 1:
            raise SystemExit('Only a single function request of each type is currently allowed. Please use another '
                             'configuration file for the same functionality.')
        grpc_p.create_dataset('NumMoments', data=moments, dtype=np.int32)
        grpc_p.create_dataset('k_vector', data=np.asmatrix(np.asarray(k_vector_rel)), dtype=np.float32)
        grpc_p.create_dataset('NumDisorder', data=dis, dtype=np.int32)
        grpc_p.create_dataset('OrbitalWeights', data=np.asmatrix(np.asarray(spinor)))

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
        grpc_p.create_dataset('ProbingPoint', data=np.asmatrix(np.asarray(probing_points)).astype(np.float32))
        grpc_p.create_dataset('width', data=width, dtype=np.float)
        grpc_p.create_dataset('spinor', data=np.asmatrix(np.asarray(spinor)).astype(config.type))
        grpc_p.create_dataset('k_vector', data=np.asmatrix(np.asarray(k_vector)), dtype=np.float32)
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

    print('\n##############################################################################\n')
    print('OUTPUT:\n')
    print('\nExporting of KITE configuration to {} finished.\n'.format(filename))
    print('\n##############################################################################\n')
    f.close()
