"""Test the ARPES calculation of KITE"""
import pytest
import numpy as np
import kite
import h5py
import os
import pybinding as pb
from .lattices import square


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


settings = {
    'square-arpes': {
        'configuration': {
            'divisions': [2, 2],
            'length': [256, 256],
            'boundaries': ["periodic", "periodic"],
            'is_complex': True,
            'precision': 1,
            'spectrum_range': [-4.1, 4.1]
        },
        'calculation': {
            'arpes': {
                'k_vector': pb.results.make_path(
                    np.array([0, 0]),
                    np.sum(np.array(square().reciprocal_vectors()), axis=0)[:2],
                    step=.2
                ),
                'weight': [1.5],
                'num_moments': 256,
                'num_disorder': 1
            }
        },
        'system': {'lattice': square(t=-1), 'filename': 'square-arpes'},
        'random_seed': "3"
    },
}


@pytest.mark.parametrize("params", settings.values(), ids=list(settings.keys()))
def test_arpes(params, baseline, plot_if_fails, tmp_path):
    configuration = kite.Configuration(**params['configuration'])
    calculation = kite.Calculation(configuration)
    config_system = params['system']
    config_system['calculation'] = calculation
    config_system['config'] = configuration
    config_system['filename'] = str((tmp_path / config_system['filename']).with_suffix(".h5"))
    for calc_name, calc_settings in params['calculation'].items():
        getattr(calculation, calc_name)(**calc_settings)
    if 'modification' in params.keys():
        # do the modification
        config_system['modification'] = kite.Modification(**params['modification'])
    if 'disorder' in params.keys():
        # do the disorder
        disorder = kite.Disorder(params['system']['lattice'])
        for realisation in settings['disorder']:
            disorder.add_disorder(**realisation)
        config_system['disorder'] = disorder
    if 'structural_disorder' in params.keys():
        # do the structural disorder
        structural_disorder = kite.StructuralDisorder(
            lattice=params['system']['lattice'],
            **params['structural_disorder']['setup']
        )
        for func_name, arguments in params['structural_disorder']['calls']:
            getattr(structural_disorder, func_name)(**arguments)
        config_system['disorder_structural'] = structural_disorder
    kite.config_system(**params['system'])
    if 'random_seed' in params.keys():
        os.environ["SEED"] = params['random_seed']
    kite.execute.kitex(config_system['filename'])
    results = []
    kite.execute.kitetools("{0} --ARPES -K green 0.1 -E -10 10 2048 -F 100 -N {1}".format(
        config_system['filename'], str(tmp_path / "arpes"))
    )
    results.append(read_text_and_matrices(str(tmp_path / "arpes.dat")))
    expected = baseline(results)
    assert pytest.fuzzy_equal(results, expected, rtol=1e-3, atol=1e-6)
