"""Test the DOS calculation of KITE"""
import pytest
import numpy as np
import kite
import h5py
import os
from .lattices import square, cube


settings = {
    'square-large': {
        'configuration': {
            'divisions': [2, 2],
            'length': [256, 256],
            'boundaries': ["periodic", "periodic"],
            'is_complex': False,
            'precision': 1,
            'spectrum_range': [-5, 5]
        },
        'calculation': {
            'dos': {'num_points': 1000, 'num_moments': 1024, 'num_random': 1, 'num_disorder': 1}
        },
        'system': {'lattice': square(), 'filename': 'square-large'},
        'random_seed': "3"
    },
    'square-mag2d': {
        'configuration': {
            'divisions': [2, 2],
            'length': [512, 512],
            'boundaries': ["periodic", "periodic"],
            'is_complex': True,
            'precision': 1,
            'spectrum_range': [-4.1, 4.1]
        },
        'calculation': {
            'dos': {'num_points': 4096, 'num_moments': 4192, 'num_random': 1, 'num_disorder': 1}
        },
        'modification': {'magnetic_field': 9},
        'system': {'lattice': square(t=-1), 'filename': 'square-mag2d'},
        'random_seed': "3"
    },
    'cube-mag3d': {
        'configuration': {
            'divisions': [2, 2, 2],
            'length': [64, 32, 64],
            'boundaries': ["periodic", "periodic", "periodic"],
            'is_complex': True,
            'precision': 1,
            'spectrum_range': [-6.1, 6.1]
        },
        'calculation': {
            'dos': {'num_points': 1000, 'num_moments': 16384, 'num_random': 1, 'num_disorder': 1}
        },
        'modification': {'magnetic_field': 65},
        'system': {'lattice': cube(t=-1), 'filename': 'cube-mag3d'},
        'random_seed': "3"
    }
}


@pytest.mark.parametrize("params", settings.values(), ids=list(settings.keys()))
def test_dos(params, baseline, plot_if_fails, tmp_path):
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
    with h5py.File(config_system['filename'], 'r') as hdf5_file:
        results.append(np.array(hdf5_file["/Calculation/dos/MU"][:]))
    kite.execute.kitetools("{0} --DOS -N {1}".format(config_system['filename'], str(tmp_path / "dos.dat")))
    results.append(np.loadtxt(str(tmp_path / "dos.dat")))
    expected = baseline(results)
    assert pytest.fuzzy_equal(results, expected, rtol=1e-3, atol=1e-6)
