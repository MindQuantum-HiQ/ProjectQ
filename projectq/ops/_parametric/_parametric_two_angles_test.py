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

"""Tests for projectq.ops._parametric_two_angles."""

import math
from numbers import Number

import numpy as np
import pytest
import sympy
from sympy.parsing.sympy_parser import parse_expr

from .._base import _basics, _two_angles
from . import _parametric_two_angles as _param

# ==============================================================================


def idfn(val):
    if isinstance(val, _basics.BasicGate):
        return str(val)


class MyPhaseGate2(_basics.DispatchGateClass):
    def __new__(self, theta, phi):
        if isinstance(theta, Number) and isinstance(phi, Number):
            return super().__new__(NumMyRotationGate)
        return super().__new__(ParamMyRotationGate)


class NumMyRotationGate(MyPhaseGate2, _two_angles.BasicPhaseGate2):
    _mod_pi_theta = 2
    _mod_pi_phi = 2


class ParamMyRotationGate(MyPhaseGate2, _param.ParametricPhaseGate2):
    _mod_pi_theta = 2
    _mod_pi_phi = 2


# ==============================================================================


@pytest.mark.parametrize(
    'theta, phi, is_valid',
    [
        (0, 1, True),
        (sympy.Float(1.234), 1, True),
        (1, sympy.Float(1.234), True),
        (1j, 1, False),
        (1, 1j, False),
        (sympy.I, 1, False),
        (0, sympy.I, False),
        (1, abs(sympy.I), True),
    ],
)
def test_parametric_angle_invalid(theta, phi, is_valid):
    if is_valid:
        _param.ParametricAngleGate2(theta, phi)
    else:
        with pytest.raises(_param.InvalidAngle):
            _param.ParametricAngleGate2(theta, phi)


def test_parametric_angle_hash():
    x1, x2, y1, y2 = sympy.symbols('x x y y')

    gate1 = _param.ParametricAngleGate2(x1, y1)
    gate2 = _param.ParametricAngleGate2(x2, y2)
    assert gate1 == gate2
    assert hash(gate1) == hash(gate2)

    x1, x2, y1, y2 = sympy.symbols('x y x y')
    gate1 = _param.ParametricAngleGate2(x1, y1)
    gate2 = _param.ParametricAngleGate2(x2, y2)
    assert gate1 != gate2
    assert hash(gate1) != hash(gate2)


def test_parametric_angle_str_conversions():
    x, y = sympy.symbols('x y')
    gate = _param.ParametricAngleGate2(x, y)

    assert str(gate) == 'ParametricAngleGate2(x,y)'
    assert gate.to_string() == 'ParametricAngleGate2(x,y)'
    assert gate.tex_str() == 'ParametricAngleGate2$(x,y)$'


def test_parametric_angle_is_parametric():
    x, y = sympy.symbols('x y')
    assert _param.ParametricAngleGate2(x, y).is_parametric()
    assert _param.ParametricAngleGate2(1, 2).is_parametric()
    assert _param.ParametricAngleGate2(1.0, 2.0).is_parametric()


@pytest.mark.parametrize(
    'angle1, inverse_angle1', [(parse_expr('x'), parse_expr('-x')), (parse_expr('x+2'), parse_expr('-x-2'))]
)
@pytest.mark.parametrize(
    'angle2, inverse_angle2', [(parse_expr('x'), parse_expr('-x')), (parse_expr('x+2'), parse_expr('-x-2'))]
)
def test_parametric_angle_get_inverse(angle1, inverse_angle1, angle2, inverse_angle2):
    gate = _param.ParametricPhaseGate2(angle1, angle2)
    inverse = gate.get_inverse()
    assert isinstance(inverse, _param.ParametricPhaseGate2)
    assert inverse.theta == inverse_angle1
    assert inverse.phi == inverse_angle2


def test_parametric_angle_equality():
    x1, y1, x2, y2 = sympy.symbols('x y z t')
    gate = _param.ParametricPhaseGate2(x1, y1)
    assert not (gate == _basics.BasicGate())
    assert gate == _param.ParametricPhaseGate2(x1, y1)
    assert gate == _param.ParametricPhaseGate2(sympy.Symbol('x'), sympy.Symbol('y'))
    assert not (gate == _param.ParametricPhaseGate2(x2, y2))

    assert gate != _basics.BasicGate()
    assert gate != _param.ParametricPhaseGate2(x2, y2)


@pytest.mark.parametrize(
    'ntime_pi1, expected1',
    [
        (0, True),
        (1, False),
        (2, True),
        (4, True),
    ],
    ids=idfn,
)
@pytest.mark.parametrize(
    'ntime_pi2, expected2',
    [
        (0, True),
        (1, False),
        (2, True),
        (4, True),
    ],
    ids=idfn,
)
def test_parametric_angle_is_identity(ntime_pi1, expected1, ntime_pi2, expected2):
    klass = _param.ParametricPhaseGate2
    expected = expected1 and expected2
    assert klass(ntime_pi1 * sympy.pi, ntime_pi2 * sympy.pi).is_identity() == expected

    assert klass(ntime_pi1 * np.pi, ntime_pi2 * np.pi).is_identity() == expected
    assert klass(ntime_pi1 * math.pi, ntime_pi2 * math.pi).is_identity() == expected


def test_parametric_rotation_gate_get_merged():
    x1, y1, x2, y2 = sympy.symbols('x y z t')
    z1 = x1 + x2
    z2 = y1 + y2
    basic_gate = _basics.BasicGate()
    param_rotation_gate1 = _param.ParametricPhaseGate2(x1, y1)
    param_rotation_gate2 = _param.ParametricPhaseGate2(x2, y2)
    param_rotation_gate3 = _param.ParametricPhaseGate2(z1, z2)
    with pytest.raises(_basics.NotMergeable):
        param_rotation_gate1.get_merged(basic_gate)
    merged_gate = param_rotation_gate1.get_merged(param_rotation_gate2)
    assert merged_gate == param_rotation_gate3


def test_mixed_parametric_rotation_gate_mixed_get_merged():
    x1, y1 = sympy.symbols('x y')
    x2, y2 = 1.12, 2.23

    z1 = x1 + x2
    z2 = y1 + y2

    param_rotation_gate1 = _param.ParametricPhaseGate2(x1, y1)
    basic_rotation_gate2 = _two_angles.BasicPhaseGate2(x2, y2)

    # This does not work (contrary to the example below) because there is no
    # dispatch class (MyRotationGate in the example below) in order to make
    # the link between the numeric and parametric gate classes.
    with pytest.raises(_basics.NotMergeable):
        param_rotation_gate1.get_merged(basic_rotation_gate2)

    param_rotation_gate1 = MyPhaseGate2(x1, y1)
    basic_rotation_gate2 = MyPhaseGate2(x2, y2)
    param_rotation_gate3 = MyPhaseGate2(z1, z2)

    merged_gate = param_rotation_gate1.get_merged(basic_rotation_gate2)
    assert merged_gate == param_rotation_gate3
