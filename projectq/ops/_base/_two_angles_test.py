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

"""Tests for projectq.ops._two_angles."""

import math

import numpy as np
import pytest

from projectq.ops._base import _basics

from . import _two_angles

# ==============================================================================


@pytest.mark.parametrize(
    "input_angle1, modulo_angle1",
    [(2.0, 2.0), (17.0, 4.4336293856408275), (-0.5 * math.pi, 1.5 * math.pi), (2 * math.pi, 0)],
)
@pytest.mark.parametrize(
    "input_angle2, modulo_angle2",
    [(2.0, 2.0), (17.0, 4.4336293856408275), (-0.5 * math.pi, 1.5 * math.pi), (2 * math.pi, 0)],
)
def test_basic_phase_gate_init(input_angle1, modulo_angle1, input_angle2, modulo_angle2):
    # Test internal representation
    gate = _two_angles.BasicPhaseGate2(input_angle1, input_angle2)
    assert gate.theta == pytest.approx(modulo_angle1)
    assert gate.phi == pytest.approx(modulo_angle2)


def test_basic_phase_gate_str():
    basic_phase_gate = _two_angles.BasicPhaseGate2(0.5, 0.7)
    assert str(basic_phase_gate) == "BasicPhaseGate2(0.5,0.7)"


def test_basic_phase_gate_to_string():
    basic_phase_gate = _two_angles.BasicPhaseGate2(0.5, 0.7)
    assert basic_phase_gate.to_string(False) == "BasicPhaseGate2(0.5,0.7)"

    basic_phase_gate = _two_angles.BasicPhaseGate2(0.5 * math.pi, 0.7 * math.pi)
    assert basic_phase_gate.to_string(True) == "BasicPhaseGate2(0.5π,0.7π)"


def test_basic_phase_tex_str():
    basic_phase_gate = _two_angles.BasicPhaseGate2(0.5, 0.7)
    assert basic_phase_gate.tex_str() == R"BasicPhaseGate2$(0.159\pi,0.223\pi)$"
    basic_rotation_gate = _two_angles.BasicPhaseGate2(2 * math.pi - 1e-13, 2 * math.pi - 1e-13)
    assert basic_rotation_gate.tex_str() == R"BasicPhaseGate2$(0.0\pi,0.0\pi)$"


@pytest.mark.parametrize('angle1, inverse_angle1', [(2.0, -2.0 + 2 * math.pi), (-0.5, 0.5), (0.0, 0)])
@pytest.mark.parametrize('angle2, inverse_angle2', [(2.0, -2.0 + 2 * math.pi), (-0.5, 0.5), (0.0, 0)])
def test_parametric_angle_get_inverse(angle1, inverse_angle1, angle2, inverse_angle2):
    gate = _two_angles.BasicPhaseGate2(angle1, angle2)
    inverse = gate.get_inverse()
    assert isinstance(inverse, _two_angles.BasicPhaseGate2)
    assert np.isclose(inverse.theta, inverse_angle1)
    assert np.isclose(inverse.phi, inverse_angle2)


def test_basic_phase_gate_get_merged():
    basic_gate = _basics.BasicGate()
    basic_phase_gate1 = _two_angles.BasicPhaseGate2(0.5, 0.7)
    basic_phase_gate2 = _two_angles.BasicPhaseGate2(1.0, 0.8)
    basic_phase_gate3 = _two_angles.BasicPhaseGate2(1.5, 1.5)
    with pytest.raises(_basics.NotMergeable):
        basic_phase_gate1.get_merged(basic_gate)
    merged_gate = basic_phase_gate1.get_merged(basic_phase_gate2)
    assert merged_gate == basic_phase_gate3


def test_basic_phase_gate_comparison_and_hash():
    basic_phase_gate1 = _two_angles.BasicPhaseGate2(0.5, 0.7)
    basic_phase_gate2 = _two_angles.BasicPhaseGate2(0.5, 0.7)
    basic_phase_gate3 = _two_angles.BasicPhaseGate2(0.5 + 2 * math.pi, 0.7 + 2 * math.pi)
    assert basic_phase_gate1 == basic_phase_gate2
    assert hash(basic_phase_gate1) == hash(basic_phase_gate2)
    assert basic_phase_gate1 == basic_phase_gate3
    assert hash(basic_phase_gate1) == hash(basic_phase_gate3)
    basic_phase_gate4 = _two_angles.BasicPhaseGate2(0.50000001, 0.70000001)
    # Test __ne__:
    assert basic_phase_gate4 != basic_phase_gate1
    # Test one gate close to 2*pi the other one close to 0
    basic_phase_gate5 = _two_angles.BasicPhaseGate2(1.0e-13, 1.0e-13)
    basic_phase_gate6 = _two_angles.BasicPhaseGate2(2 * math.pi - 1.0e-13, 2 * math.pi - 1.0e-13)
    assert basic_phase_gate5 == basic_phase_gate6
    assert basic_phase_gate6 == basic_phase_gate5
    assert hash(basic_phase_gate5) == hash(basic_phase_gate6)
    # Test different types of gates
    basic_gate = _basics.BasicGate()
    assert not basic_gate == basic_phase_gate6
    assert basic_phase_gate2 != _two_angles.BasicPhaseGate2(0.5 + math.pi, 0.7 + math.pi)
