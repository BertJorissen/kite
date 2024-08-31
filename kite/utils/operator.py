""" Some toughts"""
from typing import Tuple, Dict, List, Literal, Union



Operator = List[dict]  # too see
Velocities = Literal["vx", "vy", "vz", "ve"]
OperatorName = str
OperatorWithVelocity = Union[Tuple[OperatorName, Velocities], Tuple[Velocities, OperatorName]]
OperatorsDict = Dict[OperatorName, Operator]
OperatorsAll = List[List[OperatorWithVelocity]]
SpectrumType = Literal["FS", "SS"]
SpectrumOperatorType = Literal["Dirac", "Greens"]
SpectrumCoefsSS = List[float]  # list of the energies
SpectrumCoefsFS = int  # number of moments
SpectrumCoefs = Union[SpectrumCoefsSS, SpectrumCoefsFS]
SpectrumOne = Tuple[SpectrumType, SpectrumOperatorType, SpectrumCoefs]
SpectrumsAll = List[SpectrumOne]
OperationToKite = Tuple[SpectrumsAll, OperatorsAll]
# length of the spectrum type and OperatorsAllVector should be same


operator_a: Operator = [
    {
        'relative_index': [0, 0],
        'from_id': 'A',
        'to_id': 'B',
        'hopping_energy': 1j
    },
    {
        'relative_index': [0, 0],
        'from_id': 'A',
        'to_id': 'B',
        'hopping_energy': 1
    }
]

operators_dict: OperatorsDict = {
    "operator_a": operator_a,
    "operator_b": operator_a
}
opera_name_a: OperatorName = "operator_a"
opera_name_vx: Velocities = "vx"
operator_one: OperatorWithVelocity = (opera_name_a, opera_name_vx)
operator_two: OperatorWithVelocity = (opera_name_vx, opera_name_a)

operators_all: OperatorsAll = [
    [operator_one, operator_two],
    [operator_one, operator_two],
]

opera_2: OperatorsAll = [
    [("operator_a", "vx"), ("vy", "operator_b")],
    [("operator_b", "ve"), ("ve", "operator_a")],
]

# in HDF5: save the integers of the operators
# (save the operators in a list, with the index in the list associated with the operator)
# the velocities are zero (identity), -1, -2, -3 for vx, vy, vz, ve

spectrums: SpectrumsAll = [
    ("FS", "Dirac", 20),
    ("SS", "Greens", [1, 2, 3])
]

forward_to_kite: OperationToKite = (spectrums, operators_all)
