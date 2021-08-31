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

"Tests for projectq.setups.decompositions.unitary2rzry.py"

import pytest

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (
    AutoReplacer,
    DecompositionRuleSet,
    DummyEngine,
    InstructionFilter,
)
from projectq.meta import Control
from projectq.ops import Measure, U

from . import unitary2rzry as u2rzry


def test_recognize_correct_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qubit = eng.allocate_qubit()
    eng.flush()
    U(1, 2, 3, 4) | qubit
    with Control(eng, ctrl_qubit):
        U(2, 3, 4, 5) | qubit
    eng.flush(deallocate_qubits=True)
    assert u2rzry._recognize_UNoCtrl(saving_backend.received_commands[3])
    assert not u2rzry._recognize_UNoCtrl(saving_backend.received_commands[4])


def rx_decomp_gates(eng, cmd):
    g = cmd.gate
    if isinstance(g, U):
        return False
    else:
        return True


@pytest.mark.parametrize("alpha", [0, 2.2])
@pytest.mark.parametrize("beta", [0, 2.3])
@pytest.mark.parametrize("gamma", [0, 2.4])
@pytest.mark.parametrize("delta", [0, 2.5])
def test_decomposition(alpha, beta, gamma, delta):
    for basis_state in ([1, 0], [0, 1]):
        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(), engine_list=[correct_dummy_eng])

        rule_set = DecompositionRuleSet(modules=[u2rzry])
        test_dummy_eng = DummyEngine(save_commands=True)
        test_eng = MainEngine(
            backend=Simulator(),
            engine_list=[AutoReplacer(rule_set), InstructionFilter(rx_decomp_gates), test_dummy_eng],
        )

        correct_qb = correct_eng.allocate_qubit()
        U(alpha, beta, gamma, delta) | correct_qb
        correct_eng.flush()

        test_qb = test_eng.allocate_qubit()
        U(alpha, beta, gamma, delta) | test_qb
        test_eng.flush()

        assert correct_dummy_eng.received_commands[1].gate == U(alpha, beta, gamma, delta)
        assert test_dummy_eng.received_commands[1].gate != U(alpha, beta, gamma, delta)

        for fstate in ['0', '1']:
            test = test_eng.backend.get_amplitude(fstate, test_qb)
            correct = correct_eng.backend.get_amplitude(fstate, correct_qb)
            assert correct == pytest.approx(test, rel=1e-12, abs=1e-12)

        Measure | test_qb
        Measure | correct_qb
