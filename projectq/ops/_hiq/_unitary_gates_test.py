# -*- coding: utf-8 -*-
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

"""Tests for projectq.ops._unitary_gates."""

import math
from copy import deepcopy

import numpy as np
import pytest
import sympy
from sympy.core.basic import Basic as SympyBase

from projectq.ops import R, get_inverse

from .._base._gates_test import _cos, _exp, _sin, angle_idfn
from .._parametric import InvalidAngle, ParametricGate
from . import _unitary_gates as _gates


def create_matrix(alpha, beta, gamma, delta):
    if any(isinstance(angle, SympyBase) for angle in (alpha, beta, gamma, delta)):
        return sympy.exp(1j * alpha) * sympy.Matrix(
            [
                [
                    sympy.exp(-0.5j * (beta + delta)) * _cos(gamma / 2),
                    -sympy.exp(-0.5j * (beta - delta)) * _sin(gamma / 2),
                ],
                [
                    sympy.exp(0.5j * (beta - delta)) * _sin(gamma / 2),
                    sympy.exp(0.5j * (beta + delta)) * _cos(gamma / 2),
                ],
            ]
        )
    return _exp(1j * alpha) * np.array(
        [
            [
                _exp(-0.5j * (beta + delta)) * _cos(gamma / 2),
                -_exp(-0.5j * (beta - delta)) * _sin(gamma / 2),
            ],
            [
                _exp(0.5j * (beta - delta)) * _sin(gamma / 2),
                _exp(0.5j * (beta + delta)) * _cos(gamma / 2),
            ],
        ]
    )


@pytest.mark.parametrize(
    'angle',
    [
        0,
        math.pi,
        math.pi - _gates.ANGLE_TOLERANCE / 2,
        math.pi - _gates.ANGLE_TOLERANCE,
        math.pi + _gates.ANGLE_TOLERANCE / 2,
        math.pi + _gates.ANGLE_TOLERANCE,
    ],
    ids=['0', 'pi', 'pi-tol/2', 'pi-tol', 'pi+tol/2', 'pi+tol'],
)
def test_rounded_angle_tolerance(angle):
    rounded_angle = _gates._round_angle(angle, 1)
    assert rounded_angle in (0, math.pi)


@pytest.mark.parametrize(
    'alpha', [0, 2.1, 2 * math.pi, sympy.Float(0), sympy.Float(2.1), 2 * sympy.pi, sympy.Symbol('x')], ids=angle_idfn
)
@pytest.mark.parametrize(
    'beta', [0, 2.2, 2 * math.pi, sympy.Float(0), sympy.Float(2.2), 2 * sympy.pi, sympy.Symbol('y')], ids=angle_idfn
)
@pytest.mark.parametrize(
    'gamma', [0, 2.3, 2 * math.pi, sympy.Float(0), sympy.Float(2.3), 2 * sympy.pi, sympy.Symbol('z')], ids=angle_idfn
)
@pytest.mark.parametrize(
    'delta', [0, 2.4, 2 * math.pi, sympy.Float(0), sympy.Float(2.4), 2 * sympy.pi, sympy.Symbol('u')], ids=angle_idfn
)
def test_u_gates(alpha, beta, gamma, delta):
    klass = _gates.U

    NumKlass, ParamKlass = klass.__subclasses__()
    if not issubclass(ParamKlass, ParametricGate):
        ParamKlass, NumKlass = NumKlass, ParamKlass

    gate = klass(alpha, beta, gamma, delta)
    expected_matrix = create_matrix(alpha, beta, gamma, delta)

    assert gate.matrix.shape == expected_matrix.shape
    if all(not isinstance(angle, SympyBase) for angle in (alpha, beta, gamma, delta)):
        assert np.allclose(gate.matrix, expected_matrix)
        assert not gate.is_parametric()
        assert gate.__class__ is NumKlass
    else:
        gate_copy = deepcopy(gate)
        assert gate.__class__ is ParamKlass

        assert gate.matrix - expected_matrix == sympy.Matrix([[0, 0], [0, 0]])
        gate_evald = gate.evaluate({alpha: 1, beta: 2, gamma: 3, delta: 4})
        assert gate.is_parametric()
        assert gate_evald is not gate
        assert gate == gate_copy
        assert gate_evald.__class__ is NumKlass

        # Make sure they have the same dispatch class
        assert gate_evald.klass is gate.klass

        ref_angles = {'alpha': alpha, 'beta': beta, 'gamma': gamma, 'delta': delta}

        angles = {}
        for name, angle in ref_angles.items():
            try:
                angles = float(alpha), float(beta), float(gamma), float(delta)
                assert gate_evald == NumKlass(*angles)
            except TypeError:
                pass


def test_u_param_gates_invalid():
    with pytest.raises(InvalidAngle):
        _gates.U(sympy.I, 0, 0, 0)
    with pytest.raises(InvalidAngle):
        _gates.U(0, sympy.I, 0, 0)
    with pytest.raises(InvalidAngle):
        _gates.U(0, 0, sympy.I, 0)
    with pytest.raises(InvalidAngle):
        _gates.U(0, 0, 0, sympy.I)


@pytest.mark.parametrize('alpha', (sympy.Float(0), 2 * sympy.pi))
@pytest.mark.parametrize('beta', (sympy.Float(0), 4 * sympy.pi))
@pytest.mark.parametrize('gamma', (sympy.Float(0), 4 * sympy.pi))
@pytest.mark.parametrize('delta', (sympy.Float(0), 4 * sympy.pi))
def test_u_parametric_is_identity(alpha, beta, gamma, delta):
    assert _gates.U(alpha, beta, gamma, delta).is_identity()


@pytest.mark.parametrize('alpha', (0, 2 * math.pi))
@pytest.mark.parametrize('beta', (0, 4 * math.pi))
@pytest.mark.parametrize('gamma', (0, 4 * math.pi))
@pytest.mark.parametrize('delta', (0, 4 * math.pi))
def test_u_is_identity(alpha, beta, gamma, delta):
    x, y, z, u = sympy.symbols('x y z u')
    gate = _gates.U(x, y, z, u)
    assert gate.evaluate({x: alpha, y: beta, z: gamma, u: delta}).is_identity()


def test_u_get_inverse():
    gate = _gates.U(1, 2, 3, 4)
    assert np.allclose(gate.matrix @ gate.get_inverse().matrix, np.identity(2))
    assert np.allclose(gate.get_inverse().matrix @ gate.matrix, np.identity(2))

    x, y, z, u = sympy.symbols('x y z u')
    gate = _gates.U(x, y, z, u)
    assert sympy.simplify(gate.matrix * gate.get_inverse().matrix) - sympy.eye(2) == sympy.zeros(2, 2)
    assert sympy.simplify(gate.get_inverse().matrix * gate.matrix) - sympy.eye(2) == sympy.zeros(2, 2)


@pytest.mark.parametrize("lamda", [0, 0.2, 2.1, 4.1, 2 * math.pi, 4 * math.pi])
def test_u1(lamda):
    gate = _gates.U1(lamda)
    assert np.allclose(gate.matrix, R(lamda).matrix)
    assert np.allclose(np.dot(gate.matrix, get_inverse(gate).matrix), np.eye(2))


def test_u_u2_u3_str():
    gate = _gates.U(1, 2, 3, 4)
    gate_str = str(gate)
    gate_tex = gate.tex_str()

    assert gate_str == 'U(1.0,2.0,3.0,4.0)'
    assert gate_tex == 'U$_{1.0,2.0,3.0,4.0}$'
    assert hash(gate) == hash(gate_str)

    a, b, c, d = sympy.symbols('alpha beta gamma delta')
    gate = _gates.U(a, b, c, d)
    gate_str = str(gate)
    gate_tex = gate.tex_str()

    assert gate_str == 'U(alpha,beta,gamma,delta)'
    assert gate_tex == r'U$(\alpha,\beta,\gamma,\delta)$'
    assert hash(gate) == hash(gate_str)

    gate = _gates.U3(2, 3, 4)
    gate_str = str(gate)
    gate_tex = gate.tex_str()

    assert gate_str == 'U3(2.0,3.0,4.0)'
    assert gate_tex == 'U3$(2.0,3.0,4.0)$'

    gate = _gates.U3(a, b, c)
    gate_str = str(gate)
    gate_tex = gate.tex_str()

    assert gate_str == 'U3(alpha,beta,gamma)'
    assert gate_tex == r'U3$(\alpha,\beta,\gamma)$'

    gate = _gates.U2(3, 4)
    gate_str = str(gate)
    gate_tex = gate.tex_str()

    assert gate_str == 'U2(3.0,4.0)'
    assert gate_tex == 'U2$(3.0,4.0)$'

    gate = _gates.U2(a, b)
    gate_str = str(gate)
    gate_tex = gate.tex_str()

    assert gate_str == 'U2(alpha,beta)'
    assert gate_tex == r'U2$(\alpha,\beta)$'


def test_u_u2_u3_to_string():
    _gates.U(1, 2, 3, 4).to_string(symbols=True) == ''
    _gates.U3(1, 2, 3).to_string(symbols=True) == ''
    _gates.U2(1, 2).to_string(symbols=True) == ''

    a, b, c, d = sympy.symbols('alpha beta gamma delta')
    _gates.U(a, b, c, d).to_string(symbols=True) == ''
    _gates.U3(a, b, c).to_string(symbols=True) == ''
    _gates.U2(a, b).to_string(symbols=True) == ''


def test_u_equality():
    gate = _gates.U(1, 2, 3, 4)
    assert gate == _gates.U(1, 2, 3, 4)
    assert not (gate == _gates.U(0, 2, 3, 4))
    assert gate != _gates.U(0, 2, 3, 4)
    assert gate != _gates.U3(1, 2, 3)

    x, y, z, u, up, v = sympy.symbols('x y z u u v')
    gate = _gates.U(x, y, z, u)
    assert gate == _gates.U(x, y, z, up)
    assert not (gate == _gates.U(x, y, z, v))
    assert gate != _gates.U(x, y, z, v)
    assert gate != _gates.U3(x, y, z)

    gate = _gates.U3(x, y, z)
    gate == deepcopy(gate)

    gate = _gates.U2(x, y)
    gate == deepcopy(gate)
