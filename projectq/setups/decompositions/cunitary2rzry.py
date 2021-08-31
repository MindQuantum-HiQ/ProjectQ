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

"""Registers a decomposition for general unitary gates."""

from projectq.cengines import DecompositionRule
from projectq.meta import get_control_count
from projectq.ops import CNOT, R, Ry, Rz, U


def _decompose_UCtrl(cmd):  # pylint: disable=invalid-name # noqa: N802
    """Decompose a general controlled unitary to Ry, Rz and CNOT gates."""
    tgt = cmd.qubits[0][0]
    ctrl = cmd.control_qubits[0]
    alpha = cmd.gate.alpha
    beta = cmd.gate.beta
    gamma = cmd.gate.gamma
    delta = cmd.gate.delta

    # C
    Rz(delta / 2 - beta / 2) | tgt
    CNOT | (ctrl, tgt)
    # B
    Rz(-beta / 2 - delta / 2) | tgt
    Ry(-gamma / 2) | tgt
    CNOT | (ctrl, tgt)
    # A
    Ry(gamma / 2) | tgt
    Rz(beta) | tgt
    R(alpha) | tgt


def _recognize_UCtrl(cmd):  # pylint: disable=invalid-name # noqa: N802
    """Decompose the gate only if the command represents a single qubit gate (if it is not part of a control gate)."""
    return get_control_count(cmd) == 1


#: Decomposition rules
all_defined_decomposition_rules = [DecompositionRule(U, _decompose_UCtrl, _recognize_UCtrl)]
