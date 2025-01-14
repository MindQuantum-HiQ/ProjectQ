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
"""
Registers a decomposition for the Entangle gate.

Applies a Hadamard gate to the first qubit and then, conditioned on this first
qubit, CNOT gates to all others.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import Control
from projectq.ops import All, Entangle, H, X


def _decompose_entangle(cmd):
    """Decompose the entangle gate."""
    qureg = cmd.qubits[0]
    eng = cmd.engine

    with Control(eng, cmd.control_qubits):
        H | qureg[0]
        with Control(eng, qureg[0]):
            All(X) | qureg[1:]


#: Decomposition rules
all_defined_decomposition_rules = [DecompositionRule(Entangle, _decompose_entangle)]
