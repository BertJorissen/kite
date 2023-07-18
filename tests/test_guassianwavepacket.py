"""Test the Guassian Wave Packet calculation of KITE"""
import pytest
import numpy as np
import pybinding as pb
import kite
import h5py
import os
from .lattices import square

k_vector = pb.results.make_path(
    np.array([0, 0]),
    np.sum(np.array(square().reciprocal_vectors()), axis=0)[:2],
    step=.2
)
# settings = {
#     'square-gwp': {
#         'configuration': {
#             'divisions': [2, 2],
#             'length': [32, 32],
#             'boundaries': ["periodic", "periodic"],
#             'is_complex': True,
#             'precision': 1,
#             'spectrum_range': [-4.1, 4.1]
#         },
#         'calculation': {
#             'gaussian_wave_packet': {
#                 'num_points': 256,
#                 'num_moments': 32,
#                 'num_disorder': 1,
#                 'k_vector': k_vector * 1,
#                 'spinor': k_vector[:, 0] * 0.5,
#                 'width': .1,
#                 'timestep': .001,
#                 'mean_value': [1, 1]
#             }
#         },
#         'system': {'lattice': square(t=-1), 'filename': 'square-gwp'},
#         'random_seed': "3"
#     }
# }
#
#
# @pytest.mark.parametrize("params", settings.values(), ids=list(settings.keys()))
# def test_guassianwavepacket(params, baseline, tmp_path):
#     configuration = kite.Configuration(**params['configuration'])
#     calculation = kite.Calculation(configuration)
#     config_system = params['system']
#     config_system['calculation'] = calculation
#     config_system['config'] = configuration
#     config_system['filename'] = str((tmp_path / config_system['filename']).with_suffix(".h5"))
#     for calc_name, calc_settings in params['calculation'].items():
#         getattr(calculation, calc_name)(**calc_settings)
#     kite.config_system(**params['system'])
#     if 'random_seed' in params.keys():
#         os.environ["SEED"] = params['random_seed']
#     kite.execute.kitex(config_system['filename'])
#     results = []
#     with h5py.File(config_system['filename'], 'r') as hdf5_file:
#         results.append(np.array(hdf5_file["/Calculation/gaussian_wave_packet/mean_valuex"][:]))
#         results.append(np.array(hdf5_file["/Calculation/gaussian_wave_packet/mean_valuey"][:]))
#         results.append(np.array(hdf5_file["/Calculation/gaussian_wave_packet/Varx"][:]))
#         results.append(np.array(hdf5_file["/Calculation/gaussian_wave_packet/Vary"][:]))
#     expected = baseline(results)
#     assert pytest.fuzzy_equal(results, expected, rtol=1e-3, atol=1e-5)
