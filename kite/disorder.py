"""Create disorder for the lattice"""
import numpy as np
import pybinding as pb
from typing import Optional

__all__ = ['StructuralDisorder', 'Disorder']


class StructuralDisorder:
    """Class that introduces Structural Disorder into the initially built lattice.

    The exported dataset StructuralDisorder has the following groups:
    - Concentration: concentration of disorder,
    - Position: If instead of concentration one want's to select an exact position of disorder,
    - NumBondDisorder: number of bond changes,
    - NumOnsiteDisorder: number of onsite energy,
    The disorder is represented through nodes, where each node represents and maps a single orbital.
    - NumNodes: total number of orbitals included in the disorded,
    - NodePosition: orbital associated with the node,
    - NodeFrom, and NodeTo: bond from and to with 2 columns and NumBondDisorder rows, where the second column is complex
    conjugated hopping,
    - Hopping: values of the new hopping, with 2 columns and NumBondDisorder rows where the hoppings in different
    columns are conjugated values,
    - NodeOnsite: array of nodes that have onsite disorder,
    - U0: value of the onsite disorder.

    Parameters
    ----------
    lattice : pb.Lattice
        The lattice to add the disorder onto
    concentration : float
        The concentration of the disorder. Default is 0.
    position : Optional[np.ndarray]
        The position for the disorder. If None, the position of [0, 0, 0] is taken. Default is None.
    """
    def __init__(self, lattice: pb.Lattice, concentration: float = 0., position: Optional[np.ndarray] = None):
        if (concentration != 0 and not(position is None)) or (position is None and concentration == 0):
            SystemExit('Either select concentration which results in random distribution or '
                       'the exact position of the defect!')

        self._lattice = lattice

        vectors = np.asarray(self._lattice.vectors)
        self._space_size = vectors.shape[0]

        if position is None:
            position = np.zeros(self._space_size)
            self._exact_position = False
        else:
            self._exact_position = True

        self._concentration = concentration
        self._position = np.asmatrix(position)

        self._num_bond_disorder_per_type = 0
        self._num_onsite_disorder_per_type = 0

        self._orbital_from = []
        self._orbital_to = []
        self._orbital_onsite = []

        self._idx_node = 0
        self._disorder_hopping = []
        self._disorder_onsite = []

        self._nodes_from = []
        self._nodes_to = []
        self._nodes_onsite = []

        # only used for scaling
        self._sub_from = []
        self._sub_to = []
        self._sub_onsite = []
        self._rel_idx_onsite = []
        self._rel_idx_to = []
        self._rel_idx_from = []
        self._onsite = []
        self._hopping = []

        self._orbital_vacancy = []
        self._orbital_vacancy_cell = []
        self._vacancy_sub = []

        self._num_nodes = 0
        self._nodes_map = dict()
        self._node_orbital = []
        num_orbitals = np.zeros(lattice.nsub, dtype=np.uint64)
        for name, sub in lattice.sublattices.items():
            # num of orbitals at each sublattice is equal to size of onsite energy
            num_energies = np.asarray(sub.energy).shape[0]
            num_orbitals[sub.alias_id] = num_energies
        self._num_orbitals_total = np.sum(np.asarray(num_orbitals))
        self._num_orbitals = np.asarray(num_orbitals)
        self._num_orbitals_before = np.cumsum(np.asarray(num_orbitals)) - num_orbitals
        self._lattice = lattice

        vectors = np.asarray(self._lattice.vectors)
        self._space_size = vectors.shape[0]

    def add_vacancy(self, *disorder):
        num_vacancy_disorder = 0
        for dis in disorder:
            if len(disorder) == 1:
                relative_index = [0, 0]
                dis = [relative_index, dis]

            # check if it's just concentration or sublatt
            num_vacancy_disorder += 1
            self.add_local_vacancy_disorder(*dis)

            if len(disorder) > 2:
                raise SystemExit('Vacancy disorder should be added in a form:'
                                 '\n sublattice name,'
                                 '\n or in a form of:'
                                 '\n ([rel. unit cell], sublattice_name)')

    def add_structural_disorder(self, *disorder):
        self._nodes_map = dict()

        num_bond_disorder_per_type = 0
        num_onsite_disorder_per_type = 0
        for dis in disorder:
            if len(dis) == 5:
                num_bond_disorder_per_type += 1
                self.add_local_bond_disorder(*dis)
            else:
                if len(dis) == 3:
                    num_onsite_disorder_per_type += 1
                    self.add_local_onsite_disorder(*dis)
                else:
                    raise SystemExit('Disorder should be added in a form of bond disorder:'
                                     '\n([rel. unit cell from], sublattice_from, [rel. unit cell to], sublattice_to, '
                                     'value),'
                                     '\n or in a form of disorder onsite energy:'
                                     '\n ([rel. unit cell], sublattice_name, '
                                     'onsite energy)')

        self._num_bond_disorder_per_type = num_bond_disorder_per_type
        self._num_onsite_disorder_per_type = num_onsite_disorder_per_type
        sorted_node_orb = sorted(self._nodes_map, key=lambda x: self._nodes_map[x])
        sorted_nodes = [self._nodes_map[x] for x in sorted_node_orb]

        sorted_dict = dict(zip(sorted_node_orb, sorted_nodes))
        self._nodes_map = sorted_dict
        self._node_orbital = sorted_node_orb

    def map_the_orbital(self, orb, nodes_map):
        idx_node = len(nodes_map)
        if not (orb in nodes_map):
            nodes_map[orb] = idx_node
            idx_node += 1
        self._nodes_map = nodes_map

        return idx_node

    def add_local_vacancy_disorder(self, relative_index, sub):
        orbital_vacancy = []
        orbital_vacancy_cell = []
        names, sublattices = zip(*self._lattice.sublattices.items())

        if sub not in names:
            raise SystemExit('Desired initial sublattice doesn\'t exist in the chosen lattice! ')

        indx = names.index(sub)
        lattice_sub = sublattices[indx]

        sub_id = lattice_sub.alias_id

        it = np.nditer(lattice_sub.energy, flags=['multi_index'])

        while not it.finished:
            orbit = int(self._num_orbitals_before[sub_id] + it.multi_index[0])
            if orbit not in orbital_vacancy:
                orbital_vacancy.append(orbit)
            it.iternext()

        self._orbital_vacancy.extend(orbital_vacancy)
        self._vacancy_sub.extend(sub)

    def add_local_bond_disorder(self, relative_index_from, from_sub, relative_index_to, to_sub, hoppings):

        # save the info used for manual scaling
        self._sub_from.append(from_sub)
        self._sub_to.append(to_sub)
        self._rel_idx_to.append(relative_index_to)
        self._rel_idx_from.append(relative_index_from)
        self._hopping.append(np.atleast_1d(hoppings))

        orbital_from = []
        orbital_to = []
        orbital_hop = []

        if not (np.all(np.abs(np.asarray(relative_index_from)) < 2) and
                np.all(np.abs(np.asarray(relative_index_to)) < 2)):
            raise SystemExit('When using structural disorder, only the distance between nearest unit cells are '
                             'supported, make the bond in the bond disorder shorter! ')

        names, sublattices = zip(*self._lattice.sublattices.items())

        if from_sub not in names:
            raise SystemExit('Desired initial sublattice doesnt exist in the chosen lattice! ')
        if to_sub not in names:
            raise SystemExit('Desired final sublattice doesnt exist in the chosen lattice! ')

        indx_from = names.index(from_sub)
        lattice_sub_from = sublattices[indx_from]

        indx_to = names.index(to_sub)
        lattice_sub_to = sublattices[indx_to]

        from_sub_id = lattice_sub_from.alias_id
        to_sub_id = lattice_sub_to.alias_id

        nodes_map = self._nodes_map

        nodes_from = []
        nodes_to = []

        h = np.nditer(hoppings, flags=['multi_index'])
        while not h.finished:
            relative_move_from = np.dot(np.asarray(relative_index_from) + 1,
                                        3 ** np.linspace(0, self._space_size - 1, self._space_size, dtype=np.int32))
            relative_move_to = np.dot(np.asarray(relative_index_to) + 1,
                                      3 ** np.linspace(0, self._space_size - 1, self._space_size, dtype=np.int32))

            if isinstance(hoppings, np.ndarray):
                orb_from = int(relative_move_from +
                               (self._num_orbitals_before[from_sub_id] + h.multi_index[0]) * 3 ** self._space_size)
                orb_to = int(relative_move_to +
                             (self._num_orbitals_before[to_sub_id] + h.multi_index[1]) * 3 ** self._space_size)

                self.map_the_orbital(orb_from, nodes_map)
                self.map_the_orbital(orb_to, nodes_map)

                orbital_from.append(orb_from)
                orbital_to.append(orb_to)

                nodes_from.append(nodes_map[orb_from])
                nodes_to.append(nodes_map[orb_to])

                # conjugate
                orbital_from.append(orb_to)
                orbital_to.append(orb_from)

                nodes_from.append(nodes_map[orb_to])
                nodes_to.append(nodes_map[orb_from])

                orbital_hop.append(h[0])
                orbital_hop.append(np.conj(np.transpose(h[0])))

            else:
                orb_from = int(relative_move_from + self._num_orbitals_before[from_sub_id] * 3 ** self._space_size)
                orb_to = int(relative_move_to + self._num_orbitals_before[to_sub_id] * 3 ** self._space_size)

                self.map_the_orbital(orb_from, nodes_map)
                self.map_the_orbital(orb_to, nodes_map)

                orbital_from.append(orb_from)
                orbital_to.append(orb_to)

                nodes_from.append(nodes_map[orb_from])
                nodes_to.append(nodes_map[orb_to])

                # conjugate
                orbital_from.append(orb_to)
                orbital_to.append(orb_from)

                nodes_from.append(nodes_map[orb_to])
                nodes_to.append(nodes_map[orb_from])

                orbital_hop.append(h[0])
                orbital_hop.append((h[0].conjugate()))

            h.iternext()

        self._orbital_from.append(orbital_from)
        self._orbital_to.append(orbital_to)

        self._disorder_hopping.append(orbital_hop)

        self._nodes_from.append(nodes_from)
        self._nodes_to.append(nodes_to)

        if len(nodes_map) > self._num_nodes:
            self._num_nodes = len(nodes_map)

    def add_local_onsite_disorder(self, relative_index, sub, value):

        # save the info used for manual scaling
        self._sub_onsite.append(sub)
        self._rel_idx_onsite.append(relative_index)
        self._onsite.append(np.atleast_1d(value))

        orbital_onsite = []
        orbital_onsite_en = []

        nodes_map = self._nodes_map

        names, sublattices = zip(*self._lattice.sublattices.items())

        if sub not in names:
            raise SystemExit('Desired initial sublattice doesnt exist in the chosen lattice! ')

        indx_sub = names.index(sub)
        lattice_sub = sublattices[indx_sub]

        sub_id = lattice_sub.alias_id

        nodes_onsite = []

        h = np.nditer(value, flags=['multi_index'])
        while not h.finished:
            relative_move = np.dot(np.asarray(relative_index) + 1,
                                   3 ** np.linspace(0, self._space_size - 1, self._space_size, dtype=np.int32))

            if isinstance(value, np.ndarray):
                orb = int(relative_move + (self._num_orbitals_before[sub_id] + h.multi_index[0]) * 3 ** self._space_size)

                self.map_the_orbital(orb, nodes_map)

                orbital_onsite_en.append(h[0])

                nodes_onsite.append(nodes_map[orb])
                orbital_onsite.append(orb)
            else:
                orb = int(relative_move + self._num_orbitals_before[sub_id] * 3 ** self._space_size)

                self.map_the_orbital(orb, nodes_map)

                orbital_onsite_en.append(h[0])
                nodes_onsite.append(nodes_map[orb])
                orbital_onsite.append(orb)
            h.iternext()

        self._orbital_onsite.append(orbital_onsite)

        self._disorder_onsite.append(orbital_onsite_en)

        self._nodes_onsite.append(nodes_onsite)

        if len(nodes_map) > self._num_nodes:
            self._num_nodes = len(nodes_map)


class Disorder:
    """Class that introduces Disorder into the initially built lattice.

    The information about the disorder are the type, mean value, and standard deviation. The function that you could use
    in the bulding of the lattice is add_disorder. The class method takes care of the shape of the disorder chosen (it
    needs to be same as the number of orbitals at a given atom), and takes care of the conversion to the c++ orbital-only
    format.

    Parameters
    ----------
    lattice : pb.Lattice"""
    def __init__(self, lattice: pb.Lattice):
        # type of the disorder, can be 'Gaussian', 'Uniform' and 'Deterministic'.
        self._type = []
        # type_id of the disorder, can be 'Gaussian': 1, 'Uniform': 2 and 'Deterministic': 3.
        self._type_id = []
        # mean value of the disorder.
        self._mean = []
        # standard deviation of the disorder.
        self._stdv = []
        # orbital that has the chosen disorder.
        self._orbital = []
        # sublattice that has the chosen disorder.
        self._sub_name = []

        num_orbitals = np.zeros(lattice.nsub, dtype=np.uint64)
        for name, sub in lattice.sublattices.items():
            # num of orbitals at each sublattice is equal to size of onsite energy
            num_energies = np.asarray(sub.energy).shape[0]
            num_orbitals[sub.alias_id] = num_energies
        self._num_orbitals_total = np.sum(np.asarray(num_orbitals))
        self._num_orbitals = np.asarray(num_orbitals)
        self._num_orbitals_before = np.cumsum(np.asarray(num_orbitals)) - num_orbitals
        self._lattice = lattice

    # class method that introduces the disorder to the lattice
    def add_disorder(self, sublattice, dis_type, mean_value, standard_deviation=0.):
        # make lists
        if not (isinstance(sublattice, list)):
            sublattice = [sublattice]
        if not (isinstance(dis_type, list)):
            dis_type = [dis_type]
            mean_value = [mean_value]
            standard_deviation = [standard_deviation]

        self.add_local_disorder(sublattice, dis_type, mean_value, standard_deviation)

    def add_local_disorder(self, sublattice_name, dis_type, mean_value, standard_deviation):

        vectors = np.asarray(self._lattice.vectors)
        space_size = vectors.shape[0]

        names, sublattices = zip(*self._lattice.sublattices.items())
        chosen_orbitals_single = -1 * np.ones((self._num_orbitals_total, len(dis_type)))  # automatically set to -1

        orbital_dis_mean = []
        orbital_dis_stdv = []
        orbital_dis_type_id = []

        for idx_sub, sub_name in enumerate(sublattice_name):
            if sub_name not in names:
                raise SystemExit('Desired sublattice doesnt exist in the chosen lattice! ')
            indx = names.index(sub_name)
            lattice_sub = sublattices[indx]
            size_orb = self._num_orbitals[lattice_sub.alias_id]

            hopping = {'relative_index': np.zeros(space_size, dtype=np.int32), 'from_id': lattice_sub.alias_id,
                       'to_id': lattice_sub.alias_id, 'mean_value': lattice_sub.energy}

            # number of orbitals before i-th sublattice, where is is the array index
            orbitals_before = self._num_orbitals_before

            orbital_from = []
            orbital_dis_mean = []
            orbital_dis_stdv = []
            orbital_dis_type_id = []

            dis_number = {'Gaussian': 1, 'Uniform': 2, 'Deterministic': 3, 'gaussian': 1, 'uniform': 2,
                          'deterministic': 3}
            for index, it in enumerate(mean_value):
                if len(mean_value) > 1:
                    chosen_orbitals_single[idx_sub, index] = orbitals_before[hopping['from_id']] + index
                else:
                    chosen_orbitals_single[idx_sub, index] = hopping['from_id']
                orbital_dis_mean.append(it)
                orbital_dis_stdv.append(standard_deviation[index])
                if dis_type[index] in dis_number:
                    orbital_dis_type_id.append(dis_number[dis_type[index]])
                    if dis_type[index] == 'Deterministic' or dis_type[index] == 'deterministic':
                        if standard_deviation[index] != 0:
                            raise SystemExit(
                                'Standard deviation of deterministic disorder must be 0.')
                else:
                    raise SystemExit(
                        'Disorder not present! Try between Gaussian, Deterministic, and Uniform case insensitive ')

            if not (all(np.asarray(i).shape == size_orb for i in [dis_type, mean_value, standard_deviation])):
                print('Shape of disorder', len(dis_type), len(mean_value), len(standard_deviation),
                      'is different than the number of orbitals at sublattice ', sublattice_name, 'which is', size_orb,
                      '\n')
                raise SystemExit('All parameters should have the same length! ')

        self._type_id.extend(orbital_dis_type_id)
        self._mean.extend(orbital_dis_mean)
        self._stdv.extend(orbital_dis_stdv)

        if len(self._orbital) == 0:
            self._orbital = chosen_orbitals_single
        else:
            self._orbital = np.column_stack((self._orbital, chosen_orbitals_single))