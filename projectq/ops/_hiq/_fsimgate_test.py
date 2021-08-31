# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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
"""Tests for projectq.ops.fsimgate."""

import math
from copy import deepcopy
from numbers import Number

import numpy as np
import pytest
import sympy
from sympy.core.basic import Basic as SympyBase

from .._base._gates_test import _cos, _exp, _sin, angle_idfn
from .._parametric import ParametricGate
from ._fsimgate import fSim

# ==============================================================================


def create_matrix2(angle1, angle2, matrix_gen):
    if isinstance(angle1, SympyBase) or isinstance(angle2, SympyBase):
        return sympy.Matrix(matrix_gen(angle1, angle2))
    return np.array(matrix_gen(angle1, angle2))


# ==============================================================================


@pytest.mark.parametrize(
    "klass, matrix_gen",
    [
        (
            fSim,
            lambda theta, phi: [
                [1, 0, 0, 0],
                [0, _cos(theta), -1j * _sin(theta), 0],
                [0, -1j * _sin(theta), _cos(theta), 0],
                [0, 0, 0, _exp(-1j * phi)],
            ],
        )
    ],
)
@pytest.mark.parametrize(
    "theta",
    [0, 1.2, 2 * math.pi, 4 * math.pi, sympy.Float(0), sympy.Float(2.1), 2 * sympy.pi, 4 * sympy.pi, sympy.Symbol('x')],
    ids=angle_idfn,
)
@pytest.mark.parametrize(
    "phi",
    [0, 1.2, 2 * math.pi, 4 * math.pi, sympy.Float(0), sympy.Float(2.1), 2 * sympy.pi, 4 * sympy.pi, sympy.Symbol('y')],
    ids=angle_idfn,
)
def test_rotation_gates(klass, matrix_gen, theta, phi):
    NumKlass, ParamKlass = klass.__subclasses__()
    if not issubclass(ParamKlass, ParametricGate):
        ParamKlass, NumKlass = NumKlass, ParamKlass

    gate = klass(theta, phi)
    expected_matrix = create_matrix2(theta, phi, matrix_gen)

    assert gate.matrix.shape == expected_matrix.shape
    if not isinstance(theta, SympyBase) and not isinstance(phi, SympyBase):
        assert np.allclose(gate.matrix, expected_matrix)
        assert gate.__class__ is NumKlass
    else:
        gate_copy = deepcopy(gate)
        assert gate.__class__ is ParamKlass
        assert gate.matrix == expected_matrix

        if isinstance(theta, SympyBase) and isinstance(phi, SympyBase):
            # Upon evaluation, Sympy Float and Integer will be automatically cast
            # to float and int, so we need to take that into account

            is_theta_num = isinstance(theta, Number) or theta.is_number
            is_phi_num = isinstance(phi, Number) or phi.is_number

            assert gate.__class__ is ParamKlass

            if is_theta_num or is_phi_num:
                if is_theta_num:
                    gate_evald = gate.evaluate({phi: 2.1})
                else:
                    gate_evald = gate.evaluate({theta: 1})

                assert gate_evald.__class__ is NumKlass
                assert gate_evald is not gate
                assert gate == gate_copy

                # Make sure they have the same dispatch class
                assert gate_evald.klass is gate.klass
            else:
                gate_evald = gate.evaluate({theta: 1})
                assert gate_evald.__class__ is ParamKlass
                gate_evaldd = gate_evald.evaluate({phi: 2.1})
                assert gate_evaldd is not gate
                assert gate == gate_copy

                # Make sure they have the same dispatch class
                assert gate_evald.klass is gate.klass
                assert gate_evaldd.klass is gate.klass

                # Only test equality if angle is a symbol and not a sympy
                # integer/floating point
                assert gate_evaldd == NumKlass(1, 2.1)

                assert gate.evaluate({theta: 0, phi: 0}).is_identity()
                assert gate.evaluate({theta: 4 * math.pi, phi: 0}).is_identity()
                assert gate.evaluate({theta: 0, phi: 4 * math.pi}).is_identity()
                assert gate.evaluate({theta: 4 * math.pi, phi: 4 * math.pi}).is_identity()
        else:
            if isinstance(theta, SympyBase):
                gate_evald = gate.evaluate({theta: 1})
            else:
                gate_evald = gate.evaluate({phi: 2.1})
            assert gate_evald is not gate
            assert gate == gate_copy
            assert gate_evald.__class__ is NumKlass

            # Make sure they have the same dispatch class
            assert gate_evald.klass is gate.klass
