# -*- coding: utf-8 -*-
#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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

"""Register a decomposition rule for a unitary QubitOperator to one qubit gates."""

import cmath
from numbers import Number

import sympy

from projectq.cengines import DecompositionRule
from projectq.meta import Control, get_control_count
from projectq.ops import Ph, QubitOperator, X, Y, Z


def _phase(coefficient):
    if isinstance(coefficient, Number):
        return cmath.phase(coefficient)
    return sympy.arg(coefficient)


def _recognize_qubitop(cmd):
    """For efficiency only use this if at most 1 control qubit."""
    return get_control_count(cmd) <= 1


def _decompose_qubitop(cmd):
    if len(cmd.qubits) != 1:
        raise ValueError('QubitOperator decomposition can only accept a single quantum register')
    qureg = cmd.qubits[0]
    eng = cmd.engine
    qubit_op = cmd.gate
    with Control(eng, cmd.control_qubits):
        ((term, coefficient),) = qubit_op.terms.items()
        Ph(_phase(coefficient)) | qureg[0]
        for index, action in term:
            if action == "X":
                X | qureg[index]
            elif action == "Y":
                Y | qureg[index]
            elif action == "Z":
                Z | qureg[index]


#: Decomposition rules
all_defined_decomposition_rules = [DecompositionRule(QubitOperator, _decompose_qubitop, _recognize_qubitop)]
