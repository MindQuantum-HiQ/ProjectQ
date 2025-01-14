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

"""Register a decomposition to achieve a SqrtSwap gate."""

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, Control, Uncompute
from projectq.ops import CNOT, SqrtSwap, SqrtX


def _decompose_sqrtswap(cmd):
    """Decompose (controlled) swap gates."""
    if len(cmd.qubits) != 2:
        raise ValueError('SqrtSwap gate requires two quantum registers')
    if not (len(cmd.qubits[0]) == 1 and len(cmd.qubits[1]) == 1):
        raise ValueError('SqrtSwap gate requires must act on only 2 qubits')
    ctrl = cmd.control_qubits
    qubit0 = cmd.qubits[0][0]
    qubit1 = cmd.qubits[1][0]
    eng = cmd.engine

    with Control(eng, ctrl):
        with Compute(eng):
            CNOT | (qubit0, qubit1)
        with Control(eng, qubit1):
            SqrtX | qubit0
        Uncompute(eng)


#: Decomposition rules
all_defined_decomposition_rules = [DecompositionRule(SqrtSwap, _decompose_sqrtswap)]
