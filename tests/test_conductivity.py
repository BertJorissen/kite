"""Test the ARPES calculation of KITE"""
import pytest
import numpy as np
import kite
import os
import h5py
from .lattices import hexagonal, read_text_and_matrices, square


settings = {
    '5-graphene-optcond': {
        'configuration': {
            'divisions': [2, 2],
            'length': [32, 32],
            'boundaries': ["periodic", "periodic"],
            'is_complex': False,
            'precision': 1,
            'spectrum_range': [-3.1, 3.1]
        },
        'calculation': {
            'conductivity_optical': {
                'num_points': 256,
                'num_moments': 32,
                'num_disorder': 1,
                'num_random': 1,
                'direction': 'yy'
            }
        },
        'system': {'lattice': hexagonal(), 'filename': '5-graphene-optcond'},
        'random_seed': "ones"
    }
}


@pytest.mark.parametrize("params", settings.values(), ids=list(settings.keys()))
def test_optical(params, baseline, tmp_path):
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
        for realisation in params['disorder']:
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
        results.append(np.array(hdf5_file["/Calculation/conductivity_optical/Gammayy"][:]))
        results.append(np.array(hdf5_file["/Calculation/conductivity_optical/Lambdayy"][:]))
    kite.execute.kitetools("{0} --CondOpt -N {1}".format(config_system['filename'], str(tmp_path / "CondOpt.dat")))
    results.append(read_text_and_matrices(str(tmp_path / "CondOpt.dat")))
    expected = baseline(results)
    assert pytest.fuzzy_equal(results, expected, rtol=1e-6, atol=1e-10)


settingsnl = {
    '6-graphene-optnonl': {
        'configuration': {
            'divisions': [2, 2],
            'length': [32, 32],
            'boundaries': ["periodic", "periodic"],
            'is_complex': False,
            'precision': 0,
            'spectrum_range': [-3.1, 3.1]
        },
        'calculation': {
            'conductivity_optical_nonlinear': {
                'num_points': 100,
                'num_moments': 32,
                'num_disorder': 1,
                'num_random': 1,
                'direction': 'yyy',
                'temperature': 0.01
            }
        },
        'system': {'lattice': hexagonal(t=-1, onsite=(-0.2, -0.1)), 'filename': '6-graphene-optnonl'},
        'random_seed': "ones"
    }
}


@pytest.mark.parametrize("params", settingsnl.values(), ids=list(settingsnl.keys()))
def test_opticalnonlinear(params, baseline, tmp_path):
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
        for realisation in params['disorder']:
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
        results.append(np.array(hdf5_file["/Calculation/conductivity_optical_nonlinear/Gamma0yyy"][:]))
        results.append(np.array(hdf5_file["/Calculation/conductivity_optical_nonlinear/Gamma1yyy"][:]))
        results.append(np.array(hdf5_file["/Calculation/conductivity_optical_nonlinear/Gamma2yyy"][:]))
        results.append(np.array(hdf5_file["/Calculation/conductivity_optical_nonlinear/Gamma3yyy"][:]))
    kite.execute.kitetools("{0} --CondOpt2 -N {1}".format(config_system['filename'], str(tmp_path / "CondOpt2.dat")))
    results.append(read_text_and_matrices(str(tmp_path / "CondOpt2.dat")))
    expected = baseline(results)
    assert pytest.fuzzy_equal(results, expected, rtol=1e-6, atol=1e-10)


settingssscdc = {
    '7-graphene-sconddc': {
        'configuration': {
            'divisions': [2, 2],
            'length': [32, 32],
            'boundaries': ["periodic", "periodic"],
            'is_complex': False,
            'precision': 0,
            'spectrum_range': [-4.0, 4.0]
        },
        'calculation': {
            'singleshot_conductivity_dc': {
                'energy': [(n/100.0 - 0.5)*2 for n in range(11)],
                'num_moments': 64,
                'num_disorder': 1,
                'num_random': 1,
                'direction': 'xx',
                'eta': 0.02
            }
        },
        'disorder': [
            ('add_disorder', {
                'sublattice': 'B', 'dis_type': 'Uniform', 'mean_value': 0., 'standard_deviation': .5/np.sqrt(3)
            }),
            ('add_disorder', {
                'sublattice': 'A', 'dis_type': 'Uniform', 'mean_value': 0., 'standard_deviation': .5/np.sqrt(3)
            })
        ],
        'system': {'lattice': hexagonal(t=-1), 'filename': '7-graphene-sconddc'},
        'random_seed': "ones"
    }
}


@pytest.mark.parametrize("params", settingssscdc.values(), ids=list(settingssscdc.keys()))
def test_singleshotconddc(params, baseline, tmp_path):
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
        for realisation in params['disorder']:
            getattr(disorder, realisation[0])(**realisation[1])
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
        results.append(np.array(hdf5_file["/Calculation/singleshot_conductivity_dc/SingleShot"][:]))
    expected = baseline(results)
    assert pytest.fuzzy_equal(results, expected, rtol=1e-6, atol=1e-10)


settingscdc = {
    '9-square-dc': {
        'configuration': {
            'divisions': [2, 2],
            'length': [64, 64],
            'boundaries': ["periodic", "periodic"],
            'is_complex': True,
            'precision': 1,
            'spectrum_range': [-4.1, 4.1]
        },
        'calculation': {
            'conductivity_dc': {
                'num_points': 1000,
                'num_moments': 32,
                'num_random': 1,
                'direction': 'xy',
                'temperature': 0.01
            }
        },
        'modification': {'magnetic_field': 40},
        'system': {'lattice': square(t=-1), 'filename': '9-square-dc'},
        'random_seed': "ones"
    }
}


@pytest.mark.parametrize("params", settingscdc.values(), ids=list(settingscdc.keys()))
def test_dc(params, baseline, tmp_path):
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
        for realisation in params['disorder']:
            getattr(disorder, realisation[0])(**realisation[1])
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
        results.append(np.array(hdf5_file["/Calculation/conductivity_dc/Gammaxy"][:]))
    kite.execute.kitetools("{0} --CondDC -N {1}".format(config_system['filename'], str((tmp_path / "cond_dc.dat"))))
    results.append(np.loadtxt(str((tmp_path / "cond_dc.dat"))))
    expected = baseline(results)
    assert pytest.fuzzy_equal(results, expected, rtol=1e-6, atol=1e-10)