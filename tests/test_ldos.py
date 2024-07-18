"""Test the LDOS calculation of KITE"""
import pytest
import numpy as np
import pybinding as pb
import kite
import h5py
import os
from .lattices import square, read_ldos_files, hexagonal

settings = {
    '8-square-ldos': {
        'configuration': {
            'divisions': [2, 2],
            'length': [128, 128],
            'boundaries': ["periodic", "periodic"],
            'is_complex': False,
            'precision': 1,
            'spectrum_range': [-4.1, 4.1]
        },
        'calculation': {
            'ldos': {
                'energy': np.linspace(-1, 1, 100),
                'num_moments': 32,
                'num_disorder': 1,
                'position': [4, 3],
                'sublattice': 'A'
            }
        },
        'system': {'lattice': square(t=-1), 'filename': '8-square-ldos'},
        'random_seed': "ones"
    }
}


@pytest.mark.parametrize("params", settings.values(), ids=list(settings.keys()))
def test_ldos(params, baseline, tmp_path):
    configuration = kite.Configuration(**params['configuration'])
    calculation = kite.Calculation(configuration)
    config_system = params['system']
    config_system['calculation'] = calculation
    config_system['config'] = configuration
    config_system['filename'] = str((tmp_path / config_system['filename']).with_suffix(".h5"))
    for calc_name, calc_settings in params['calculation'].items():
        getattr(calculation, calc_name)(**calc_settings)
    kite.config_system(**params['system'])
    if 'random_seed' in params.keys():
        os.environ["SEED"] = params['random_seed']
    kite.execute.kitex(config_system['filename'])
    results = []
    with h5py.File(config_system['filename'], 'r') as hdf5_file:
        results.append(np.array(hdf5_file["/Calculation/ldos/lMU"][:]))
    kite.execute.kitetools("{0} --LDOS -N {1}".format(config_system['filename'], str(tmp_path / "ldos")))
    results.append(read_ldos_files(str(tmp_path)))
    expected = baseline(results)
    assert pytest.fuzzy_equal(results[0], expected[0], rtol=1e-6, atol=1e-10)
    keys_new = np.array([key for key in results[1].keys()])
    print(keys_new)
    for key_old in expected[1].keys():
        diff_vec = np.abs(keys_new - key_old)
        idx_min = np.argmin(diff_vec)
        key_new = keys_new[idx_min]
        assert diff_vec[idx_min] < 1e-10, "Key not found in results."
        assert pytest.fuzzy_equal(results[1][key_new], expected[1][key_old], rtol=1e-3, atol=1e-4), "Values not equal."



def create_sub_pos_matrix_8():
    pos_matrix, sub_matrix = [], []
    d1 = d2 = 32
    for i in range(-2, 2):
        for j in range(-2, 2):
            pos_matrix.append([d1 + i, d2 + j])
            pos_matrix.append([d1 + i, d2 + j])
            sub_matrix.append('A')
            sub_matrix.append('B')
    return pos_matrix, sub_matrix


settingssd = {
    '11-graphene-structuraldisorder': {
        'configuration': {
            'divisions': [2, 2],
            'length': [64, 64],
            'boundaries': ["periodic", "periodic"],
            'is_complex': True,
            'precision': 1,
            'spectrum_range': [-5, 5]
        },
        'calculation': {
            'ldos': {
                'energy': np.linspace(-2, -1.2, 10),
                'num_moments': 256,
                'num_disorder': 1,
                'position': create_sub_pos_matrix_8()[0],
                'sublattice': create_sub_pos_matrix_8()[1]
            }
        },
        'structural_disorder': {
            'setup': {'position': [[30, 30], [31, 31]]},
            'calls': [
                ('add_structural_disorder', [
                    ([0, 0], 'A', [0, 0], 'B', .2),
                    ([0, 0], 'A', [-1, 0], 'B', .1),
                    ([0, 0], 'A', [-1, 1], 'B', .1),
                    ([0, 0], 'A', .1)])
            ]
        },
        'system': {'lattice': hexagonal(onsite=(.2, .3)), 'filename': '11-graphene-structuraldisorder'},
        'random_seed': "3"
    }
}


@pytest.mark.parametrize("params", settingssd.values(), ids=list(settingssd.keys()))
def test_structuraldisorder(params, baseline, tmp_path):
    configuration = kite.Configuration(**params['configuration'])
    calculation = kite.Calculation(configuration)
    config_system = params['system']
    config_system['calculation'] = calculation
    config_system['config'] = configuration
    config_system['filename'] = str((tmp_path / config_system['filename']).with_suffix(".h5"))
    for calc_name, calc_settings in params['calculation'].items():
        getattr(calculation, calc_name)(**calc_settings)
    kite.config_system(**params['system'])
    if 'random_seed' in params.keys():
        os.environ["SEED"] = params['random_seed']
    if 'structural_disorder' in params.keys():
        # do the structural disorder
        structural_disorder = kite.StructuralDisorder(
            lattice=params['system']['lattice'],
            **params['structural_disorder']['setup']
        )
        for func_name, arguments in params['structural_disorder']['calls']:
            getattr(structural_disorder, func_name)(*arguments)
        config_system['disorder_structural'] = structural_disorder
    kite.execute.kitex(config_system['filename'])
    results = []
    kite.execute.kitetools("{0} --LDOS -N {1}".format(config_system['filename'], str(tmp_path / "ldos")))
    results.append(read_ldos_files(str(tmp_path)))
    expected = baseline(results)
    assert pytest.fuzzy_equal(results, expected, rtol=1e-6, atol=3e-2)
