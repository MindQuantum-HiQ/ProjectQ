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

from . import cunitary2rzry as cu2rzry


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
    assert not cu2rzry._recognize_UCtrl(saving_backend.received_commands[3])
    assert cu2rzry._recognize_UCtrl(saving_backend.received_commands[4])


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

        rule_set = DecompositionRuleSet(modules=[cu2rzry])
        test_dummy_eng = DummyEngine(save_commands=True)
        test_eng = MainEngine(
            backend=Simulator(),
            engine_list=[AutoReplacer(rule_set), InstructionFilter(rx_decomp_gates), test_dummy_eng],
        )

        correct_qb = correct_eng.allocate_qubit()
        correct_ctrl = correct_eng.allocate_qubit()
        with Control(correct_eng, correct_ctrl):
            U(alpha, beta, gamma, delta) | correct_qb
        correct_eng.flush()

        test_qb = test_eng.allocate_qubit()
        test_ctrl = test_eng.allocate_qubit()
        with Control(test_eng, test_ctrl):
            U(alpha, beta, gamma, delta) | test_qb
        test_eng.flush()

        assert correct_dummy_eng.received_commands[2].gate == U(alpha, beta, gamma, delta)
        assert test_dummy_eng.received_commands[2].gate != U(alpha, beta, gamma, delta)

        for fstate in ['00', '01', '10', '11']:
            test = test_eng.backend.get_amplitude(fstate, test_qb + test_ctrl)
            correct = correct_eng.backend.get_amplitude(fstate, correct_qb + correct_ctrl)
            assert correct == pytest.approx(test, rel=1e-12, abs=1e-12)

            test_map, test_wf = test_eng.backend.cheat()
            correct_map, correct_wf = correct_eng.backend.cheat()

            # Make sure the qubits are in the same order in the wavefunction
            assert test_map == correct_map
            assert correct_wf == pytest.approx(test_wf, rel=1e-12, abs=1e-12)

        Measure | test_ctrl
        Measure | test_qb
        Measure | correct_ctrl
        Measure | correct_qb
