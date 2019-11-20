#   Copyright 2019 ProjectQ-Framework (www.projectq.ch)
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
"""Tests for projectq.cengines._openqasm.py."""

# This is required under Mac OS X when using virtual environments
import platform
if platform.system() == 'Darwin':
    import matplotlib
    matplotlib.use('Qt5Agg')

import pytest
from qiskit import QuantumCircuit

import re
from projectq.cengines import MainEngine, DummyEngine
from projectq.meta import Control
from projectq.ops import (X, NOT, Y, Z, T, Tdag, S, Sdag, H, Ph, R, Rx, Ry, Rz,
                          Swap, Allocate, Deallocate, Measure, Barrier,
                          Entangle, Command)
from ._openqasm import OpenQASMEngine

# ==============================================================================


def test_openqasm_init():
    qc_list = []

    def _process(circuit):
        qc_list.append(circuit)

    eng = OpenQASMEngine(_process)
    assert eng._process_func is _process
    assert not eng._qreg_dict
    assert not eng._creg_dict
    assert eng._reg_index == 0
    assert not eng._available_indices


@pytest.mark.parametrize("qubit_id_redux", [False, True])
def test_openqasm_allocate_deallocate(qubit_id_redux):
    qc_list = []

    def _process(circuit):
        qc_list.append(circuit)

    backend = OpenQASMEngine(_process, qubit_id_mapping_redux=qubit_id_redux)
    assert backend._qubit_id_mapping_redux == qubit_id_redux

    eng = MainEngine(backend)
    qubit = eng.allocate_qubit()
    eng.flush()

    assert len(backend._qreg_dict) == 1
    assert len(backend._creg_dict) == 1
    assert backend._reg_index == 1
    assert not backend._available_indices
    assert len(qc_list) == 1
    qasm = qc_list[0].qasm()
    assert re.search(r'qreg\s+q0\[1\]', qasm)
    assert re.search(r'creg\s+c0\[1\]', qasm)

    qureg = eng.allocate_qureg(5)
    eng.flush()

    assert len(backend._qreg_dict) == 6
    assert len(backend._creg_dict) == 6
    assert backend._reg_index == 6
    assert not backend._available_indices
    assert len(qc_list) == 2
    qasm = qc_list[1].qasm()
    for i in range(1, 6):
        assert re.search(r'qreg\s+q{}\[1\]'.format(i), qasm)
        assert re.search(r'creg\s+c{}\[1\]'.format(i), qasm)

    del qubit
    eng.flush()
    if qubit_id_redux:
        assert len(backend._qreg_dict) == 5
        assert len(backend._creg_dict) == 5
        assert backend._reg_index == 6
        assert backend._available_indices == [0]
    else:
        assert len(backend._qreg_dict) == 6
        assert len(backend._creg_dict) == 6
        assert backend._reg_index == 6
        assert not backend._available_indices

    qubit = eng.allocate_qubit()
    eng.flush()

    if qubit_id_redux:
        assert len(backend._qreg_dict) == 6
        assert len(backend._creg_dict) == 6
        assert backend._reg_index == 6
        assert not backend._available_indices
    else:
        assert len(backend._qreg_dict) == 7
        assert len(backend._creg_dict) == 7
        assert backend._reg_index == 7
        assert not backend._available_indices


@pytest.mark.parametrize("gate, is_available",
                         [(X, True), (Y, True), (Z, True), (T, True),
                          (Tdag, True), (S, True), (Sdag, True),
                          (Allocate, True), (Deallocate, True),
                          (Measure, True), (NOT, True), (Rx(0.5), True),
                          (Ry(0.5), True), (Rz(0.5), True), (R(0.5), True),
                          (Ph(0.5), True), (Barrier, True), (Entangle, False)])
def test_openqasm_is_available(gate, is_available):
    qc_list = []

    def _process(circuit):
        qc_list.append(circuit)

    eng = MainEngine(backend=DummyEngine(),
                     engine_list=[OpenQASMEngine(_process)])
    qubit1 = eng.allocate_qubit()
    cmd = Command(eng, gate, (qubit1, ))
    eng.is_available(cmd) == is_available

    eng = MainEngine(backend=OpenQASMEngine(_process),
                     engine_list=[])
    qubit1 = eng.allocate_qubit()
    cmd = Command(eng, gate, (qubit1, ))
    eng.is_available(cmd) == is_available


@pytest.mark.parametrize("gate, is_available", [(H, True), (X, True),
                                                (NOT, True), (Y, True),
                                                (Z, True), (Rz(0.5), True),
                                                (R(0.5), True),
                                                (Rx(0.5), False),
                                                (Ry(0.5), False)])
def test_openqasm_is_available_1control(gate, is_available):
    main_circuit = QuantumCircuit()

    def _process(circuit):
        main_circuit.extend(circuit)

    eng = MainEngine(backend=DummyEngine(),
                     engine_list=[OpenQASMEngine(_process)])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    cmd = Command(eng, gate, (qubit1, ), controls=qureg)
    assert eng.is_available(cmd) == is_available

    eng = MainEngine(backend=OpenQASMEngine(_process),
                     engine_list=[])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    cmd = Command(eng, gate, (qubit1, ), controls=qureg)
    assert eng.is_available(cmd) == is_available


@pytest.mark.parametrize("gate, is_available", [(X, True), (NOT, True),
                                                (Y, False), (Z, False),
                                                (Rz(0.5), False),
                                                (R(0.5), False),
                                                (Rx(0.5), False),
                                                (Ry(0.5), False)])
def test_openqasm_is_available_2control(gate, is_available):
    main_circuit = QuantumCircuit()

    def _process(circuit):
        main_circuit.extend(circuit)

    eng = MainEngine(backend=DummyEngine(),
                     engine_list=[OpenQASMEngine(_process)])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(2)
    cmd = Command(eng, gate, (qubit1, ), controls=qureg)
    assert eng.is_available(cmd) == is_available

    eng = MainEngine(backend=OpenQASMEngine(_process), engine_list=[])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(2)
    cmd = Command(eng, gate, (qubit1, ), controls=qureg)
    assert eng.is_available(cmd) == is_available


def test_openqasm_test_qasm_single_qubit_gates():
    main_circuit = QuantumCircuit()

    def _process(circuit):
        main_circuit.extend(circuit)

    backend = OpenQASMEngine(_process)
    eng = MainEngine(backend=backend, engine_list=[])
    qubit = eng.allocate_qubit()

    H | qubit
    S | qubit
    T | qubit
    Sdag | qubit
    Tdag | qubit
    X | qubit
    Y | qubit
    Z | qubit
    R(0.5) | qubit
    Rx(0.5) | qubit
    Ry(0.5) | qubit
    Rz(0.5) | qubit
    Ph(0.5) | qubit
    NOT | qubit
    Measure | qubit
    eng.flush()

    qasm = [l for l in main_circuit.qasm().split('\n')[2:] if l]
    assert qasm == [
        'qreg q0[1];', 'creg c0[1];', 'h q0[0];', 's q0[0];', 't q0[0];',
        'sdg q0[0];', 'tdg q0[0];', 'x q0[0];', 'y q0[0];', 'z q0[0];',
        'u1(0.500000000000000) q0[0];', 'rx(0.500000000000000) q0[0];',
        'ry(0.500000000000000) q0[0];', 'rz(0.500000000000000) q0[0];',
        'u1(-0.250000000000000) q0[0];', 'x q0[0];', 'measure q0[0] -> c0[0];'
    ]


def test_openqasm_test_qasm_single_qubit_gates_control():
    main_circuit = QuantumCircuit()

    def _process(circuit):
        main_circuit.extend(circuit)

    backend = OpenQASMEngine(_process)
    eng = MainEngine(backend=backend, engine_list=[])
    qubit = eng.allocate_qubit()
    ctrl = eng.allocate_qubit()

    with Control(eng, ctrl):
        H | qubit
        X | qubit
        Y | qubit
        Z | qubit
        NOT | qubit
        R(0.5) | qubit
        Rz(0.5) | qubit
        Ph(0.5) | qubit
    eng.flush()

    qasm = [l for l in main_circuit.qasm().split('\n')[2:] if l]
    print(qasm)
    assert qasm == [
        'qreg q0[1];', 'qreg q1[1];', 'creg c0[1];', 'creg c1[1];',
        'ch q1[0],q0[0];', 'cx q1[0],q0[0];', 'cy q1[0],q0[0];',
        'cz q1[0],q0[0];', 'cx q1[0],q0[0];',
        'cu1(0.500000000000000) q1[0],q0[0];',
        'crz(0.500000000000000) q1[0],q0[0];',
        'cu1(-0.250000000000000) q1[0],q0[0];'
    ]
