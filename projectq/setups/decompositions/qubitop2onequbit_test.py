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

import cmath

import pytest
import sympy

import projectq.setups.decompositions.qubitop2onequbit as qubitop2onequbit
from projectq import MainEngine
from projectq.backends import ParametricGateBackend, Simulator
from projectq.cengines import (
    AutoReplacer,
    DecompositionRuleSet,
    DummyEngine,
    InstructionFilter,
)
from projectq.meta import Control
from projectq.ops import All, Command, Measure, Ph, QubitOperator, X, Y, Z
from projectq.types import WeakQubitRef


def test_recognize():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    ctrl_qureg = eng.allocate_qureg(2)
    qureg = eng.allocate_qureg(2)
    with Control(eng, ctrl_qureg):
        QubitOperator("X0 Y1") | qureg
    with Control(eng, ctrl_qureg[0]):
        QubitOperator("X0 Y1") | qureg
    eng.flush()
    cmd0 = saving_backend.received_commands[4]
    cmd1 = saving_backend.received_commands[5]
    assert not qubitop2onequbit._recognize_qubitop(cmd0)
    assert qubitop2onequbit._recognize_qubitop(cmd1)

    x, y = sympy.symbols('x y')
    with Control(eng, ctrl_qureg):
        QubitOperator("X0 Y1", x) | qureg
    with Control(eng, ctrl_qureg[0]):
        QubitOperator("X0 Y1", y) | qureg
    eng.flush()

    cmd0 = saving_backend.received_commands[7]
    cmd1 = saving_backend.received_commands[8]
    assert not qubitop2onequbit._recognize_qubitop(cmd0)
    assert qubitop2onequbit._recognize_qubitop(cmd1)


def test_invalid_decomposition():
    qb0 = WeakQubitRef(None, idx=0)
    qb1 = WeakQubitRef(None, idx=0)
    with pytest.raises(ValueError):
        qubitop2onequbit._decompose_qubitop(Command(None, QubitOperator('X1 X2'), qubits=([qb0], [qb1])))


def _decomp_gates(eng, cmd):
    if isinstance(cmd.gate, QubitOperator):
        return False
    return True


def default_setup(num_qubits, test_backend):
    random_initial_state = [0.2 + 0.1 * x * cmath.exp(0.1j + 0.2j * x) for x in range(2 ** (num_qubits + 1))]
    rule_set = DecompositionRuleSet(modules=[qubitop2onequbit])
    test_eng = MainEngine(
        backend=test_backend, verbose=True, engine_list=[AutoReplacer(rule_set), InstructionFilter(_decomp_gates)]
    )

    test_qureg = test_eng.allocate_qureg(num_qubits)
    test_ctrl_qb = test_eng.allocate_qubit()
    test_eng.flush()

    correct_eng = MainEngine(backend=Simulator())
    correct_qureg = correct_eng.allocate_qureg(num_qubits)
    correct_ctrl_qb = correct_eng.allocate_qubit()
    correct_eng.flush()
    correct_eng.backend.set_wavefunction(random_initial_state, correct_qureg + correct_ctrl_qb)
    return (random_initial_state, test_eng, correct_eng, test_qureg, correct_qureg, test_ctrl_qb, correct_ctrl_qb)


@pytest.fixture
def num_qubits():
    return 4


# ==============================================================================


def test_qubitop2singlequbit(num_qubits):
    (
        random_initial_state,
        test_eng,
        correct_eng,
        test_qureg,
        correct_qureg,
        test_ctrl_qb,
        correct_ctrl_qb,
    ) = default_setup(num_qubits, Simulator())

    test_eng.backend.set_wavefunction(random_initial_state, test_qureg + test_ctrl_qb)

    qubit_op_0 = QubitOperator("X0 Y1 Z3", -1.0j)
    qubit_op_1 = QubitOperator("Z0 Y1 X3", cmath.exp(0.6j))

    qubit_op_0 | test_qureg
    with Control(test_eng, test_ctrl_qb):
        qubit_op_1 | test_qureg
    test_eng.flush()

    correct_eng.backend.apply_qubit_operator(qubit_op_0, correct_qureg)
    with Control(correct_eng, correct_ctrl_qb):
        Ph(0.6) | correct_qureg[0]
        Z | correct_qureg[0]
        Y | correct_qureg[1]
        X | correct_qureg[3]
    correct_eng.flush()

    for fstate in range(2 ** (num_qubits + 1)):
        binary_state = format(fstate, '0' + str(num_qubits + 1) + 'b')
        test = test_eng.backend.get_amplitude(binary_state, test_qureg + test_ctrl_qb)
        correct = correct_eng.backend.get_amplitude(binary_state, correct_qureg + correct_ctrl_qb)
        assert correct == pytest.approx(test, rel=1e-10, abs=1e-10)

    All(Measure) | correct_qureg + correct_ctrl_qb
    All(Measure) | test_qureg + test_ctrl_qb
    correct_eng.flush()
    test_eng.flush()


def test_qubitop2singlequbit_param(num_qubits):
    (
        random_initial_state,
        test_eng,
        correct_eng,
        test_qureg,
        correct_qureg,
        test_ctrl_qb,
        correct_ctrl_qb,
    ) = default_setup(num_qubits, ParametricGateBackend())

    sim_eng = MainEngine(backend=Simulator(), engine_list=[])
    sim_qureg = test_eng.backend.send_to(sim_eng)
    sim_eng.backend.set_wavefunction(random_initial_state, sim_qureg)

    # Make sure that the order in which the qubits are allocated is the same!
    assert correct_eng.backend.cheat()[0] == sim_eng.backend.cheat()[0]

    x, y = sympy.symbols("x y")
    subs = {x: -1.0j, y: cmath.exp(0.6j)}

    op_0_terms = "X0 Y1 Z3"
    op_1_terms = "Z0 Y1 X3"

    qubit_op_0 = QubitOperator(op_0_terms, x)
    qubit_op_1 = QubitOperator(op_1_terms, y)

    qubit_op_0_ref = QubitOperator(op_0_terms, subs[x])

    qubit_op_0 | test_qureg
    with Control(test_eng, test_ctrl_qb):
        qubit_op_1 | test_qureg
    test_eng.flush()

    test_eng.backend.send_to(sim_eng, subs)

    correct_eng.backend.apply_qubit_operator(qubit_op_0_ref, correct_qureg)
    with Control(correct_eng, correct_ctrl_qb):
        Ph(cmath.phase(subs[y])) | correct_qureg[0]
        Z | correct_qureg[0]
        Y | correct_qureg[1]
        X | correct_qureg[3]
    correct_eng.flush()

    for fstate in range(2 ** (num_qubits + 1)):
        binary_state = format(fstate, '0' + str(num_qubits + 1) + 'b')
        test = sim_eng.backend.get_amplitude(binary_state, sim_qureg)
        correct = correct_eng.backend.get_amplitude(binary_state, correct_qureg + correct_ctrl_qb)
        assert correct == pytest.approx(test, rel=1e-10, abs=1e-10)

    All(Measure) | correct_qureg + correct_ctrl_qb
    All(Measure) | test_qureg + test_ctrl_qb
    correct_eng.flush()
    test_eng.flush()
    test_eng.backend.send_to(sim_eng)
