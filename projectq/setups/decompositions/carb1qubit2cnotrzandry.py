# -*- coding: utf-8 -*-
#   Copyright 2017, 2021 ProjectQ-Framework (www.projectq.ch)
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
"""
Register the decomposition of an controlled arbitary single qubit gate.

See paper "Elementary gates for quantum computing" by Adriano Barenco et al.,
arXiv:quant-ph/9503016v1. (Note: They use different gate definitions!) or
Nielsen and Chuang chapter 4.3.
"""

import cmath
import itertools
import math

import numpy

from projectq.cengines import DecompositionRule
from projectq.meta import Control, get_control_count
from projectq.ops import BasicGate, Ph, Ry, Rz, X
from projectq.setups.decompositions import arb1qubit2rzandry as arb1q

TOLERANCE = 1e-12


def _recognize_carb1qubit(cmd):
    """Recognize single controlled one qubit gates with a matrix."""
    if get_control_count(cmd) == 1:
        try:
            return cmd.gate.matrix.shape[0] == 2 and not cmd.gate.is_parametric()
        except AttributeError:
            return False
    return False


# TODO: make this work with parametric gates?
def _test_parameters(matrix, a, b, c_half):  # pylint: disable=invalid-name
    """
    Build matrix V with parameters (a, b, c/2) and compares against matrix.

    V = [[-sin(c/2) * exp(j*a), exp(j*(a-b)) * cos(c/2)],
         [exp(j*(a+b)) * cos(c/2), exp(j*a) * sin(c/2)]]

    Args:
        matrix(list): 2x2 matrix
        a: Parameter of V
        b: Parameter of V
        c_half: c/2. Parameter of V

    Returns:
        True if matrix elements of V and `matrix` are TOLERANCE close.
    """
    v_matrix = [
        [
            -math.sin(c_half) * cmath.exp(1j * a),
            cmath.exp(1j * (a - b)) * math.cos(c_half),
        ],
        [
            cmath.exp(1j * (a + b)) * math.cos(c_half),
            cmath.exp(1j * a) * math.sin(c_half),
        ],
    ]
    return numpy.allclose(v_matrix, matrix, rtol=10 * TOLERANCE, atol=TOLERANCE)


def _recognize_v(matrix):  # pylint: disable=too-many-branches
    """
    Test whether a matrix has the correct form.

    Recognize a matrix which can be written in the following form:

    V = [[-sin(c/2) * exp(j*a), exp(j*(a-b)) * cos(c/2)],
         [exp(j*(a+b)) * cos(c/2), exp(j*a) * sin(c/2)]]

    Args:
        matrix(list): 2x2 matrix
    Returns:
        False if it is not possible otherwise (a, b, c/2)
    """
    if abs(matrix[0][0]) < TOLERANCE:
        two_a = cmath.phase(matrix[0][1] * matrix[1][0]) % (2 * math.pi)
        if abs(two_a) < TOLERANCE or abs(two_a) > 2 * math.pi - TOLERANCE:
            # from 2a==0 (mod 2pi), it follows that a==0 or a==pi,
            # w.l.g. we can choose a==0 because (see U above)
            # c/2 -> c/2 + pi would have the same effect as as a==0 -> a==pi.
            a = 0  # pylint: disable=invalid-name
        else:
            a = two_a / 2.0  # pylint: disable=invalid-name
        two_b = cmath.phase(matrix[1][0]) - cmath.phase(matrix[0][1])
        possible_b = [
            (two_b / 2.0) % (2 * math.pi),
            (two_b / 2.0 + math.pi) % (2 * math.pi),
        ]
        possible_c_half = [0, math.pi]

        for b, c_half in itertools.product(possible_b, possible_c_half):  # pylint: disable=invalid-name
            if _test_parameters(matrix, a, b, c_half):
                return (a, b, c_half)
        raise RuntimeError('Case matrix[0][0]==0 should work in all cases, but did not!')  # pragma: no cover

    if abs(matrix[0][1]) < TOLERANCE:
        two_a = cmath.phase(-matrix[0][0] * matrix[1][1]) % (2 * math.pi)
        if abs(two_a) < TOLERANCE or abs(two_a) > 2 * math.pi - TOLERANCE:
            # from 2a==0 (mod 2pi), it follows that a==0 or a==pi,
            # w.l.g. we can choose a==0 because (see U above)
            # c/2 -> c/2 + pi would have the same effect as as a==0 -> a==pi.
            a = 0  # pylint: disable=invalid-name
        else:
            a = two_a / 2.0  # pylint: disable=invalid-name
        b = 0  # pylint: disable=invalid-name
        possible_c_half = [math.pi / 2.0, 3.0 / 2.0 * math.pi]

        for c_half in possible_c_half:
            if _test_parameters(matrix, a, b, c_half):
                return (a, b, c_half)
        return False

    two_a = cmath.phase(-1.0 * matrix[0][0] * matrix[1][1]) % (2 * math.pi)
    if abs(two_a) < TOLERANCE or abs(two_a) > 2 * math.pi - TOLERANCE:
        # from 2a==0 (mod 2pi), it follows that a==0 or a==pi,
        # w.l.g. we can choose a==0 because (see U above)
        # c/2 -> c/2 + pi would have the same effect as as a==0 -> a==pi.
        a = 0  # pylint: disable=invalid-name
    else:
        a = two_a / 2.0  # pylint: disable=invalid-name
    two_b = cmath.phase(matrix[1][0]) - cmath.phase(matrix[0][1])
    possible_b = [
        (two_b / 2.0) % (2 * math.pi),
        (two_b / 2.0 + math.pi) % (2 * math.pi),
    ]
    tmp = math.acos(abs(matrix[1][0]))
    possible_c_half = [
        tmp % (2 * math.pi),
        (tmp + math.pi) % (2 * math.pi),
        (-1.0 * tmp) % (2 * math.pi),
        (-1.0 * tmp + math.pi) % (2 * math.pi),
    ]
    for b, c_half in itertools.product(possible_b, possible_c_half):  # pylint: disable=invalid-name
        if _test_parameters(matrix, a, b, c_half):
            return (a, b, c_half)
    return False


def _decompose_carb1qubit(cmd):  # pylint: disable=too-many-branches
    """
    Decompose the single controlled 1 qubit gate into CNOT, Rz, Ry, C(Ph).

    See Nielsen and Chuang chapter 4.3.

    An arbitrary one qubit gate matrix can be writen as
    U = [[exp(j*(a-b/2-d/2))*cos(c/2), -exp(j*(a-b/2+d/2))*sin(c/2)],
         [exp(j*(a+b/2-d/2))*sin(c/2), exp(j*(a+b/2+d/2))*cos(c/2)]]
    where a,b,c,d are real numbers.
    Then U = exp(j*a) Rz(b) Ry(c) Rz(d).

    Then C(U) = C(exp(ja)) * A * CNOT * B * CNOT * C with
    A = Rz(b) * Ry(c/2)
    B = Ry(-c/2) * Rz(-(d+b)/2)
    C = Rz((d-b)/2)
    Note that a == 0 if U is element of SU(2). Also note that
    the controlled phase C(exp(ia)) can be implemented with single
    qubit gates.

    If the one qubit gate matrix can be writen as
    V = [[-sin(c/2) * exp(j*a), exp(j*(a-b)) * cos(c/2)],
         [exp(j*(a+b)) * cos(c/2), exp(j*a) * sin(c/2)]]
    Then C(V) = C(exp(ja))* E * CNOT * D with
    E = Rz(b)Ry(c/2)
    D = Ry(-c/2)Rz(-b)
    This improvement is important for C(Y) or C(Z)

    For a proof follow Lemma 5.5 of Barenco et al.
    """
    # pylint: disable=invalid-name

    matrix = cmd.gate.matrix.tolist()
    qb = cmd.qubits
    eng = cmd.engine

    # Case 1: Unitary matrix which can be written in the form of V:
    parameters_for_v = _recognize_v(matrix)
    if parameters_for_v:
        a, b, c_half = parameters_for_v  # pylint: disable=invalid-name
        if Rz(-b) != Rz(0):
            Rz(-b) | qb
        if Ry(-c_half) != Ry(0):
            Ry(-c_half) | qb
        with Control(eng, cmd.control_qubits):
            X | qb
        if Ry(c_half) != Ry(0):
            Ry(c_half) | qb
        if Rz(b) != Rz(0):
            Rz(b) | qb
        if a != 0:
            with Control(eng, cmd.control_qubits):
                Ph(a) | qb

    # Case 2: General matrix U:
    else:
        a, b_half, c_half, d_half = arb1q._find_parameters(matrix)  # pylint: disable=protected-access
        d = 2 * d_half
        b = 2 * b_half
        if Rz((d - b) / 2.0) != Rz(0):
            Rz((d - b) / 2.0) | qb
        with Control(eng, cmd.control_qubits):
            X | qb
        if Rz(-(d + b) / 2.0) != Rz(0):
            Rz(-(d + b) / 2.0) | qb
        if Ry(-c_half) != Ry(0):
            Ry(-c_half) | qb
        with Control(eng, cmd.control_qubits):
            X | qb
        if Ry(c_half) != Ry(0):
            Ry(c_half) | qb
        if Rz(b) != Rz(0):
            Rz(b) | qb
        if a != 0:
            with Control(eng, cmd.control_qubits):
                Ph(a) | qb


#: Decomposition rules
all_defined_decomposition_rules = [DecompositionRule(BasicGate, _decompose_carb1qubit, _recognize_carb1qubit)]
