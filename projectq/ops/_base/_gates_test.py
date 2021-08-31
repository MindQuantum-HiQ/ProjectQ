# -*- coding: utf-8 -*-
#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#   Copyright 2021 <Huawei Technologies Co., Ltd>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Tests for projectq.ops._gates."""

import cmath
import math
from copy import deepcopy

import numpy as np
import pytest
import sympy
from sympy.core.basic import Basic as SympyBase

from projectq import MainEngine

from .._parametric import _parametric_base as _param
from . import _gates, _metagates


def test_class_descriptor():
    assert _gates.HGate.klass is _gates.HGate
    assert _gates.H.klass is _gates.HGate

    assert _gates.Ph.klass is _gates.Ph
    assert _gates.Ph(1).klass is _gates.Ph
    assert _gates.Ph(sympy.Symbol('x')).klass is _gates.Ph

    assert _gates.Rx.klass is _gates.Rx
    assert _gates.Rx(1).klass is _gates.Rx
    assert _gates.Rx(sympy.Symbol('x')).klass is _gates.Rx

    assert _gates.Ry.klass is _gates.Ry
    assert _gates.Ry(1).klass is _gates.Ry
    assert _gates.Ry(sympy.Symbol('y')).klass is _gates.Ry

    assert _gates.Rz.klass is _gates.Rz
    assert _gates.Rz(1).klass is _gates.Rz
    assert _gates.Rz(sympy.Symbol('z')).klass is _gates.Rz

    assert _gates.Rxx.klass is _gates.Rxx
    assert _gates.Rxx(1).klass is _gates.Rxx
    assert _gates.Rxx(sympy.Symbol('x')).klass is _gates.Rxx

    assert _gates.Ryy.klass is _gates.Ryy
    assert _gates.Ryy(1).klass is _gates.Ryy
    assert _gates.Ryy(sympy.Symbol('x')).klass is _gates.Ryy

    assert _gates.Rzz.klass is _gates.Rzz
    assert _gates.Rzz(1).klass is _gates.Rzz
    assert _gates.Rzz(sympy.Symbol('x')).klass is _gates.Rzz


def test_h_gate():
    gate = _gates.HGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "H"
    assert np.array_equal(gate.matrix, 1.0 / math.sqrt(2) * np.matrix([[1, 1], [1, -1]]))
    assert isinstance(_gates.H, _gates.HGate)


def test_x_gate():
    gate = _gates.XGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "X"
    assert np.array_equal(gate.matrix, np.matrix([[0, 1], [1, 0]]))
    assert isinstance(_gates.X, _gates.XGate)
    assert isinstance(_gates.NOT, _gates.XGate)


def test_y_gate():
    gate = _gates.YGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "Y"
    assert np.array_equal(gate.matrix, np.matrix([[0, -1j], [1j, 0]]))
    assert isinstance(_gates.Y, _gates.YGate)


def test_z_gate():
    gate = _gates.ZGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "Z"
    assert np.array_equal(gate.matrix, np.matrix([[1, 0], [0, -1]]))
    assert isinstance(_gates.Z, _gates.ZGate)


def test_s_gate():
    gate = _gates.SGate()
    assert str(gate) == "S"
    assert np.array_equal(gate.matrix, np.matrix([[1, 0], [0, 1j]]))
    assert isinstance(_gates.S, _gates.SGate)
    assert isinstance(_gates.Sdag, type(_gates.get_inverse(gate)))
    assert isinstance(_gates.Sdagger, type(_gates.get_inverse(gate)))


def test_t_gate():
    gate = _gates.TGate()
    assert str(gate) == "T"
    assert np.array_equal(gate.matrix, np.matrix([[1, 0], [0, cmath.exp(1j * cmath.pi / 4)]]))
    assert isinstance(_gates.T, _gates.TGate)
    assert isinstance(_gates.Tdag, type(_gates.get_inverse(gate)))
    assert isinstance(_gates.Tdagger, type(_gates.get_inverse(gate)))


def test_sqrtx_gate():
    gate = _gates.SqrtXGate()
    assert str(gate) == "SqrtX"
    assert gate.tex_str() == r"$\sqrt{X}$"
    assert np.array_equal(gate.matrix, np.matrix([[0.5 + 0.5j, 0.5 - 0.5j], [0.5 - 0.5j, 0.5 + 0.5j]]))
    assert np.array_equal(gate.matrix * gate.matrix, np.matrix([[0j, 1], [1, 0]]))
    assert isinstance(_gates.SqrtX, _gates.SqrtXGate)


def test_swap_gate():
    gate = _gates.SwapGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "Swap"
    assert gate.interchangeable_qubit_indices == [[0, 1]]
    assert np.array_equal(gate.matrix, np.matrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]))
    assert isinstance(_gates.Swap, _gates.SwapGate)


def test_sqrtswap_gate():
    sqrt_gate = _gates.SqrtSwapGate()
    swap_gate = _gates.SwapGate()
    assert str(sqrt_gate) == "SqrtSwap"
    assert np.array_equal(sqrt_gate.matrix * sqrt_gate.matrix, swap_gate.matrix)
    assert np.array_equal(
        sqrt_gate.matrix,
        np.matrix(
            [
                [1, 0, 0, 0],
                [0, 0.5 + 0.5j, 0.5 - 0.5j, 0],
                [0, 0.5 - 0.5j, 0.5 + 0.5j, 0],
                [0, 0, 0, 1],
            ]
        ),
    )
    assert isinstance(_gates.SqrtSwap, _gates.SqrtSwapGate)


def test_engangle_gate():
    gate = _gates.EntangleGate()
    assert str(gate) == "Entangle"
    assert isinstance(_gates.Entangle, _gates.EntangleGate)


def _cos(angle):
    if isinstance(angle, SympyBase):
        return sympy.cos(angle)
    return math.cos(angle)


def _sin(angle):
    if isinstance(angle, SympyBase):
        return sympy.sin(angle)
    return math.sin(angle)


def _exp(arg):
    if isinstance(arg, SympyBase):
        return sympy.exp(arg)
    return cmath.exp(arg)


def create_matrix(angle, matrix_gen):
    if isinstance(angle, SympyBase):
        return sympy.Matrix(matrix_gen(angle))
    return np.array(matrix_gen(angle))


def angle_idfn(val):
    if isinstance(val, SympyBase):
        return 'sym({})'.format(val)
    return 'num({})'.format(val)


@pytest.mark.parametrize(
    "klass, matrix_gen",
    [
        (_gates.Ph, lambda angle: [[_exp(1j * angle), 0], [0, _exp(1j * angle)]]),
        (_gates.R, lambda angle: [[1, 0], [0, _exp(1.0j * angle)]]),
        (
            _gates.Rx,
            lambda angle: [[_cos(0.5 * angle), -1j * _sin(0.5 * angle)], [-1j * _sin(0.5 * angle), _cos(0.5 * angle)]],
        ),
        (_gates.Ry, lambda angle: [[_cos(0.5 * angle), -_sin(0.5 * angle)], [_sin(0.5 * angle), _cos(0.5 * angle)]]),
        (_gates.Rz, lambda angle: [[_exp(-0.5 * 1j * angle), 0], [0, _exp(0.5 * 1j * angle)]]),
        (
            _gates.Rxx,
            lambda angle: [
                [_cos(0.5 * angle), 0, 0, -1j * _sin(0.5 * angle)],
                [0, _cos(0.5 * angle), -1j * _sin(0.5 * angle), 0],
                [0, -1j * _sin(0.5 * angle), _cos(0.5 * angle), 0],
                [-1j * _sin(0.5 * angle), 0, 0, _cos(0.5 * angle)],
            ],
        ),
        (
            _gates.Ryy,
            lambda angle: [
                [_cos(0.5 * angle), 0, 0, 1j * _sin(0.5 * angle)],
                [0, _cos(0.5 * angle), -1j * _sin(0.5 * angle), 0],
                [0, -1j * _sin(0.5 * angle), _cos(0.5 * angle), 0],
                [1j * _sin(0.5 * angle), 0, 0, _cos(0.5 * angle)],
            ],
        ),
        (
            _gates.Rzz,
            lambda angle: [
                [_exp(-0.5 * 1j * angle), 0, 0, 0],
                [0, _exp(0.5 * 1j * angle), 0, 0],
                [0, 0, _exp(0.5 * 1j * angle), 0],
                [0, 0, 0, _exp(-0.5 * 1j * angle)],
            ],
        ),
    ],
)
@pytest.mark.parametrize(
    "angle",
    [
        0,
        0.2,
        2.1,
        4.1,
        2 * math.pi,
        4 * math.pi,
        sympy.Float(0),
        sympy.Float(2.1),
        2 * sympy.pi,
        4 * sympy.pi,
        sympy.Symbol('x'),
    ],
    ids=angle_idfn,
)
def test_rotation_gates(klass, matrix_gen, angle):
    NumKlass, ParamKlass = klass.__subclasses__()
    if not issubclass(ParamKlass, _param.ParametricGate):
        ParamKlass, NumKlass = NumKlass, ParamKlass

    gate = klass(angle)
    expected_matrix = create_matrix(angle, matrix_gen)

    assert gate.matrix.shape == expected_matrix.shape
    if not isinstance(angle, SympyBase):
        assert np.allclose(gate.matrix, expected_matrix)
        assert gate.__class__ is NumKlass
    else:
        gate_copy = deepcopy(gate)
        assert gate.__class__ is ParamKlass
        assert gate.matrix == expected_matrix
        gate_evald = gate.evaluate({angle: 1})
        assert gate_evald is not gate
        assert gate == gate_copy
        assert gate_evald.__class__ is NumKlass

        # Make sure they have the same dispatch class
        assert gate_evald.klass is gate.klass

        try:
            _ = float(angle)
        except TypeError:
            # Only test equality if angle is a symbol and not a sympy
            # integer/floating point
            assert gate_evald == NumKlass(1)

            assert gate.evaluate({angle: 0}).is_identity()
            assert gate.evaluate({angle: 4 * math.pi}).is_identity()


def test_flush_gate():
    gate = _gates.FlushGate()
    assert str(gate) == ""


def test_measure_gate():
    gate = _gates.MeasureGate()
    assert str(gate) == "Measure"
    assert isinstance(_gates.Measure, _gates.MeasureGate)


def test_allocate_qubit_gate():
    gate = _gates.AllocateQubitGate()
    assert str(gate) == "Allocate"
    assert gate.get_inverse() == _gates.DeallocateQubitGate()
    assert isinstance(_gates.Allocate, _gates.AllocateQubitGate)


def test_deallocate_qubit_gate():
    gate = _gates.DeallocateQubitGate()
    assert str(gate) == "Deallocate"
    assert gate.get_inverse() == _gates.AllocateQubitGate()
    assert isinstance(_gates.Deallocate, _gates.DeallocateQubitGate)


def test_allocate_dirty_qubit_gate():
    gate = _gates.AllocateDirtyQubitGate()
    assert str(gate) == "AllocateDirty"
    assert gate.get_inverse() == _gates.DeallocateQubitGate()
    assert isinstance(_gates.AllocateDirty, _gates.AllocateDirtyQubitGate)


def test_barrier_gate():
    gate = _gates.BarrierGate()
    assert str(gate) == "Barrier"
    assert gate.get_inverse() == _gates.BarrierGate()
    assert isinstance(_gates.Barrier, _gates.BarrierGate)


def test_flip_bits_equality_and_hash():
    gate1 = _gates.FlipBits([1, 0, 0, 1])
    gate2 = _gates.FlipBits([1, 0, 0, 1])
    gate3 = _gates.FlipBits([0, 1, 0, 1])
    assert gate1 == gate2
    assert hash(gate1) == hash(gate2)
    assert gate1 != gate3
    assert gate1 != _gates.X


def test_flip_bits_str():
    gate1 = _gates.FlipBits([0, 0, 1])
    assert str(gate1) == "FlipBits(4)"


def test_error_on_tuple_input():
    with pytest.raises(ValueError):
        _gates.FlipBits(2) | (None, None)


flip_bits_testdata = [
    ([0, 1, 0, 1], '0101'),
    ([1, 0, 1, 0], '1010'),
    ([False, True, False, True], '0101'),
    ('0101', '0101'),
    ('1111', '1111'),
    ('0000', '0000'),
    (8, '0001'),
    (11, '1101'),
    (1, '1000'),
    (-1, '1111'),
    (-2, '0111'),
    (-3, '1011'),
]


@pytest.mark.parametrize("bits_to_flip, result", flip_bits_testdata)
def test_simulator_flip_bits(bits_to_flip, result):
    eng = MainEngine()
    qubits = eng.allocate_qureg(4)
    _gates.FlipBits(bits_to_flip) | qubits
    eng.flush()
    assert pytest.approx(eng.backend.get_probability(result, qubits)) == 1.0
    _metagates.All(_gates.Measure) | qubits


def test_flip_bits_can_be_applied_to_various_qubit_qureg_formats():
    eng = MainEngine()
    qubits = eng.allocate_qureg(4)
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0000', qubits)) == 1.0
    _gates.FlipBits([0, 1, 1, 0]) | qubits
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0110', qubits)) == 1.0
    _gates.FlipBits([1]) | qubits[0]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('1110', qubits)) == 1.0
    _gates.FlipBits([1]) | (qubits[0],)
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0110', qubits)) == 1.0
    _gates.FlipBits([1, 1]) | [qubits[0], qubits[1]]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('1010', qubits)) == 1.0
    _gates.FlipBits(-1) | qubits
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0101', qubits)) == 1.0
    _gates.FlipBits(-4) | [qubits[0], qubits[1], qubits[2], qubits[3]]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0110', qubits)) == 1.0
    _gates.FlipBits(2) | [qubits[0]] + [qubits[1], qubits[2]]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0010', qubits)) == 1.0
    _metagates.All(_gates.Measure) | qubits


@pytest.mark.parametrize(
    "gate_class", [_gates.Ph, _gates.Rx, _gates.Ry, _gates.Rz, _gates.Rxx, _gates.Ryy, _gates.Rzz, _gates.R], ids=str
)
def test_sanity_check_dispatch_get_merged(gate_class):
    # Make sure that if dispatching works properly for these classes

    x = sympy.symbols('x')
    y = 1.12
    z = x + y

    merged_gate = gate_class(x).get_merged(gate_class(y))
    assert merged_gate == gate_class(z)


@pytest.mark.parametrize(
    "num_class, param_class",
    [
        (_gates.PhNum, _gates.PhParam),
        (_gates.RxNum, _gates.RxParam),
        (_gates.RyNum, _gates.RyParam),
        (_gates.RzNum, _gates.RzParam),
        (_gates.RxxNum, _gates.RxxParam),
        (_gates.RyyNum, _gates.RyyParam),
        (_gates.RzzNum, _gates.RzzParam),
        (_gates.RNum, _gates.RParam),
    ],
    ids=str,
)
def test_sanity_check_get_merged(num_class, param_class):
    # Make sure that if we explicitely instantiate the classes, merging works
    x = sympy.symbols('x')
    y = 1.12
    z = x + y

    merged_gate = param_class(x).get_merged(num_class(y))
    assert merged_gate == param_class(z)

    merged_gate = num_class(y).get_merged(param_class(x))
    assert merged_gate == param_class(z)

    merged_gate = num_class(y).get_merged(num_class(y))
    assert merged_gate == num_class(2 * y)

    merged_gate = param_class(x).get_merged(param_class(x))
    assert merged_gate == param_class(2 * x)
