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

"""Tests for projectq.ops._parametric_base."""

import math
from numbers import Number

import numpy as np
import pytest
import sympy
from sympy.parsing.sympy_parser import parse_expr

from .._base import _basics
from . import _parametric_base as _param

# ==============================================================================


def idfn(val):
    if isinstance(val, _basics.BasicGate):
        return str(val)


# ------------------------------------------------------------------------------


class MyGateReal(_param.ParametricGateReal):
    def __init__(self, alpha, beta):
        super().__init__(alpha=alpha, beta=beta)

    def __str__(self):
        return 'MyGate({}, {})'.format(self.alpha, self.beta)


class MyGateCmplx(_param.ParametricGateCmplx):
    def __init__(self, alpha, beta):
        super().__init__(alpha=alpha, beta=beta)

    def __str__(self):
        return 'MyGateCmplx({}, {})'.format(self.alpha, self.beta)


class MyAngleGate(_basics.DispatchGateClass):
    def __new__(cls, angle):
        if angle is not None:
            if isinstance(angle, Number):
                return super().__new__(MyAngleNum)
            return super().__new__(MyAngleParam)
        return super().__new__(cls)


class MyAngleNum(MyAngleGate, _basics.BasicAngleGate):
    _mod_pi = 1


class MyAngleParam(MyAngleGate, _param.ParametricAngleGate):
    _mod_pi = 1


class MyRotationGate(_basics.DispatchGateClass):
    def __new__(self, angle):
        if isinstance(angle, Number):
            return super().__new__(NumMyRotationGate)
        return super().__new__(ParamMyRotationGate)


class NumMyRotationGate(MyRotationGate, _basics.BasicRotationGate):
    _mod_pi = 4


class ParamMyRotationGate(MyRotationGate, _param.ParametricRotationGate):
    _mod_pi = 4


# ==============================================================================


def test_parametric_str_not_implemented():
    with pytest.raises(NotImplementedError):
        str(_param.ParametricGate(a=1))


def test_parametric_is_parametric():
    a, b = sympy.symbols('alpha beta')
    assert _param.ParametricGate(a=a, b=b).is_parametric()
    assert _param.ParametricGate(a=a, b=10).is_parametric()
    assert _param.ParametricGate(a=10, b=b).is_parametric()
    assert not _param.ParametricGate(a=int(1), b=1.5).is_parametric()


def test_parametric_real_evaluate():
    a, b = sympy.symbols('alpha beta')
    gate = MyGateReal(a, b)
    assert gate.is_parametric()
    partial = gate.evaluate({a: int(1)})
    assert isinstance(partial.alpha, float)
    assert gate.is_parametric()

    new_gate = partial.evaluate({b: 2})
    assert not new_gate.is_parametric()
    assert isinstance(new_gate.alpha, float)
    assert isinstance(new_gate.beta, float)


def test_parametric_cmplx_evaluate():
    a, b = sympy.symbols('alpha beta')
    gate = MyGateCmplx(a, b)
    assert gate.is_parametric()
    partial = gate.evaluate({a: 1})
    assert gate.is_parametric()
    assert isinstance(partial.alpha, complex)

    new_gate = partial.evaluate({b: 2})
    assert not new_gate.is_parametric()
    assert isinstance(new_gate.alpha, complex)
    assert isinstance(new_gate.beta, complex)
    assert new_gate.alpha == 1
    assert new_gate.beta == 2


def test_parametric_angle_invalid():
    _param.ParametricAngleGate(sympy.Float(1.1234))
    with pytest.raises(_param.InvalidAngle):
        _param.ParametricAngleGate(sympy.I)
    _param.ParametricAngleGate(abs(sympy.I))


def test_parametric_angle_hash():
    x, y = sympy.symbols('x x')

    gate1 = _param.ParametricAngleGate(x)
    gate2 = _param.ParametricAngleGate(y)
    assert gate1 == gate2
    assert hash(gate1) == hash(gate2)

    x, y = sympy.symbols('x y')
    gate1 = _param.ParametricAngleGate(x)
    gate2 = _param.ParametricAngleGate(y)
    assert gate1 != gate2
    assert hash(gate1) != hash(gate2)


def test_parametric_angle_str_conversions():
    x = sympy.symbols('x')
    gate = _param.ParametricAngleGate(x)

    assert str(gate) == 'ParametricAngleGate(x)'
    assert gate.to_string() == 'ParametricAngleGate(x)'
    assert gate.tex_str() == 'ParametricAngleGate$(x)$'


def test_parametric_angle_evaluate():
    x, y = sympy.symbols('x y')
    gate = MyAngleGate(x)
    assert gate.is_parametric()
    partial_eval = gate.evaluate({y: 1})
    assert partial_eval.is_parametric()
    assert gate.__class__ == partial_eval.__class__

    complete_eval = gate.evaluate({x: 4 * math.pi})
    assert not complete_eval.is_parametric()
    assert gate.__class__ != complete_eval.__class__
    assert complete_eval.is_identity()
    assert complete_eval.angle == 0

    complete_eval = gate.evaluate({x: 4 * math.pi + 1})
    assert not complete_eval.is_parametric()
    assert gate.__class__ != complete_eval.__class__
    assert complete_eval.angle == 1


def test_parametric_angle_is_parametric():
    x = sympy.symbols('x')
    assert _param.ParametricAngleGate(x).is_parametric()
    assert _param.ParametricAngleGate(1).is_parametric()
    assert _param.ParametricAngleGate(1.0).is_parametric()


@pytest.mark.parametrize(
    'angle, inverse_angle', [(parse_expr('x'), parse_expr('-x')), (parse_expr('x+2'), parse_expr('-x-2'))]
)
def test_parametric_angle_get_inverse(angle, inverse_angle):
    gate = _param.ParametricAngleGate(angle)
    inverse = gate.get_inverse()
    assert isinstance(inverse, _param.ParametricAngleGate)
    assert inverse.angle == inverse_angle


def test_parametric_angle_equality():
    x, y = sympy.symbols('x y')
    gate = _param.ParametricAngleGate(x)
    assert not (gate == _basics.BasicGate())
    assert gate == _param.ParametricAngleGate(x)
    assert gate == _param.ParametricAngleGate(sympy.Symbol('x'))
    assert not (gate == _param.ParametricAngleGate(y))

    assert gate != _basics.BasicGate()
    assert gate != _param.ParametricAngleGate(y)


@pytest.mark.parametrize(
    'klass, ntime_pi, expected',
    [
        (_param.ParametricRotationGate, 0, True),
        (_param.ParametricRotationGate, 1, False),
        (_param.ParametricRotationGate, 2, False),
        (_param.ParametricRotationGate, 4, True),
        (_param.ParametricRotationGate, 8, True),
        (_param.ParametricPhaseGate, 0, True),
        (_param.ParametricPhaseGate, 1, False),
        (_param.ParametricPhaseGate, 2, True),
        (_param.ParametricPhaseGate, 4, True),
    ],
    ids=idfn,
)
def test_parametric_angle_is_identity(klass, ntime_pi, expected):
    assert klass(ntime_pi * sympy.pi).is_identity() == expected
    assert klass(ntime_pi * np.pi).is_identity() == expected
    assert klass(ntime_pi * math.pi).is_identity() == expected


def test_parametric_rotation_gate_get_merged():
    x, y = sympy.symbols('x y')
    z = x + y
    basic_gate = _basics.BasicGate()
    param_rotation_gate1 = _param.ParametricRotationGate(x)
    param_rotation_gate2 = _param.ParametricRotationGate(y)
    param_rotation_gate3 = _param.ParametricRotationGate(z)
    with pytest.raises(_basics.NotMergeable):
        param_rotation_gate1.get_merged(basic_gate)
    merged_gate = param_rotation_gate1.get_merged(param_rotation_gate2)
    assert merged_gate == param_rotation_gate3


def test_mixed_parametric_rotation_gate_mixed_get_merged():
    x = sympy.symbols('x')
    y = 1.12
    z = x + y

    param_rotation_gate1 = _param.ParametricRotationGate(x)
    basic_rotation_gate2 = _basics.BasicRotationGate(y)

    # This does not work (contrary to the example below) because there is no
    # dispatch class (MyRotationGate in the example above) in order to make
    # the link between the numeric and parametric gate classes.
    with pytest.raises(_basics.NotMergeable):
        param_rotation_gate1.get_merged(basic_rotation_gate2)

    param_rotation_gate1 = MyRotationGate(x)
    basic_rotation_gate2 = MyRotationGate(y)
    param_rotation_gate3 = MyRotationGate(z)

    merged_gate = param_rotation_gate1.get_merged(basic_rotation_gate2)
    assert merged_gate == param_rotation_gate3
