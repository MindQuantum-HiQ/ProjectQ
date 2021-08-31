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

"""Tests for projectq.ops._parametric_base."""

from copy import deepcopy
from itertools import chain

import numpy as np
import pytest
import sympy

from projectq.cengines import DummyEngine, MainEngine
from projectq.ops import (
    CNOT,
    All,
    Allocate,
    BasicGate,
    Command,
    Deallocate,
    FlushGate,
    H,
    Measure,
    Rx,
    Rxx,
    X,
)
from projectq.types import WeakQubitRef

from ._parametric_backend import DestinationEngineGateUnsupported, ParametricGateBackend

# ==============================================================================


def foo(self):
    return 'WeakQubitRef_{}[{}]'.format(id(self), self.id)


Command.__repr__ = Command.__str__
WeakQubitRef.__repr__ = foo


class MyGate(BasicGate):
    def __str__(self):
        return "MyGate"


# ==============================================================================


def test_param_backend_is_last():
    engine = ParametricGateBackend()

    qubit = WeakQubitRef(engine=None, idx=0)
    cmd = Command(engine=None, gate=Allocate, qubits=([qubit],))

    with pytest.raises(RuntimeError):
        engine.receive([cmd])


def test_param_backend_is_available():
    engine = ParametricGateBackend()
    qb = WeakQubitRef(engine=None, idx=0)

    assert engine.is_available(Command(engine=None, gate=X, qubits=([qb],)))
    assert engine.is_available(Command(engine=None, gate=MyGate(), qubits=([qb],)))


def test_param_backend_receive():
    engine = ParametricGateBackend()
    engine.is_last_engine = True
    assert engine._min_allocated_id is None
    assert engine._max_allocated_id is None

    qubit00 = WeakQubitRef(engine=None, idx=0)
    qubit01 = WeakQubitRef(engine=None, idx=1)
    qubit10 = WeakQubitRef(engine=None, idx=10)

    cmd00 = Command(engine=None, gate=Allocate, qubits=([qubit00],))
    cmd01 = Command(engine=None, gate=Allocate, qubits=([qubit01],))
    cmd10 = Command(engine=None, gate=Allocate, qubits=([qubit10],))

    engine.receive([cmd00])
    assert len(engine._received_commands) == 1
    assert engine._received_commands[0] is cmd00
    assert engine._min_allocated_id == 0
    assert engine._max_allocated_id == 0

    engine.receive([cmd01])
    assert len(engine._received_commands) == 2
    assert engine._received_commands[0] is cmd00
    assert engine._received_commands[1] is cmd01
    assert engine._min_allocated_id == 0
    assert engine._max_allocated_id == 1

    engine.receive([cmd10])
    assert len(engine._received_commands) == 3
    assert engine._received_commands[0] is cmd00
    assert engine._received_commands[1] is cmd01
    assert engine._received_commands[2] is cmd10
    assert engine._min_allocated_id == 0
    assert engine._max_allocated_id == 10

    engine = ParametricGateBackend()
    engine.is_last_engine = True

    engine.receive([cmd10])
    assert len(engine._received_commands) == 1
    assert engine._received_commands[0] is cmd10
    assert engine._min_allocated_id == 10
    assert engine._max_allocated_id == 10

    engine.receive([cmd01])
    assert len(engine._received_commands) == 2
    assert engine._received_commands[0] is cmd10
    assert engine._received_commands[1] is cmd01
    assert engine._min_allocated_id == 1
    assert engine._max_allocated_id == 10


def test_param_send_to_lone_engine():
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True

    engine = ParametricGateBackend()
    engine.is_last_engine = True

    qubit0 = WeakQubitRef(engine=None, idx=0)
    qubit1 = WeakQubitRef(engine=None, idx=10)

    cmd0 = Command(engine=None, gate=Allocate, qubits=([qubit0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qubit1],))
    cmd2 = Command(engine=None, gate=X, qubits=([qubit1],))

    engine.receive([cmd0, cmd1, cmd2])
    engine.send_to(backend)

    assert len(backend.received_commands) == 3
    assert backend.received_commands[0].gate == Allocate
    assert backend.received_commands[0].qubits[0][0].id == qubit0.id
    assert backend.received_commands[1].gate == Allocate
    assert backend.received_commands[1].qubits[0][0].id == qubit1.id
    assert backend.received_commands[2].gate == X
    assert backend.received_commands[2].qubits[0][0].id == qubit1.id


def test_param_send_to_self_noop():
    engine = ParametricGateBackend()
    engine.is_last_engine = True

    qubit0 = WeakQubitRef(engine=None, idx=0)
    qubit1 = WeakQubitRef(engine=None, idx=10)

    cmd0 = Command(engine=None, gate=Allocate, qubits=([qubit0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qubit1],))
    cmd2 = Command(engine=None, gate=X, qubits=([qubit1],))

    engine.receive([cmd0, cmd1, cmd2])

    received_commands = deepcopy(engine._received_commands)
    engine.send_to(engine)
    # Make sure that commands were not added a second time
    assert len(received_commands) == len(engine._received_commands)


def test_param_send_to_other_engine():
    main_eng = MainEngine(backend=DummyEngine(save_commands=True), engine_list=[])
    backend = main_eng.backend
    assert main_eng._qubit_idx == 0

    engine = ParametricGateBackend()
    engine.is_last_engine = True

    qubit0 = WeakQubitRef(engine=None, idx=0)
    qubit1 = WeakQubitRef(engine=None, idx=10)

    cmd0 = Command(engine=None, gate=Allocate, qubits=([qubit0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qubit1],))
    cmd2 = Command(engine=None, gate=X, qubits=([qubit1],))

    engine.receive([cmd0, cmd1, cmd2])
    engine.send_to(backend)
    main_eng.flush()

    assert len(backend.received_commands) == 4
    assert backend.received_commands[0].gate == Allocate
    assert backend.received_commands[0].qubits[0][0].id == qubit0.id
    assert backend.received_commands[1].gate == Allocate
    assert backend.received_commands[1].qubits[0][0].id == qubit1.id
    assert backend.received_commands[2].gate == X
    assert backend.received_commands[2].qubits[0][0].id == qubit1.id
    assert isinstance(backend.received_commands[3].gate, FlushGate)

    assert main_eng._qubit_idx == 11
    assert len(main_eng.active_qubits) == 2
    assert WeakQubitRef(main_eng, 0) in main_eng.active_qubits
    assert WeakQubitRef(main_eng, 10) in main_eng.active_qubits


def test_param_send_to_self_error():
    eng = MainEngine(backend=ParametricGateBackend(), engine_list=[])
    qureg = eng.allocate_qureg(2)
    X | qureg[1]

    with pytest.raises(RuntimeError):
        eng.backend.send_to(eng)


def test_param_send_to_main_engine_error_no_alloc():
    other = DummyEngine()
    eng = MainEngine(backend=ParametricGateBackend(), engine_list=[])

    qubit = WeakQubitRef(engine=None, idx=0)
    cmd = Command(engine=None, gate=X, qubits=([qubit],))

    eng.backend.receive([cmd])
    with pytest.raises(RuntimeError):
        eng.backend.send_to(other)


def test_param_send_to_main_engine_error_new_alloc():
    eng = MainEngine(backend=ParametricGateBackend(), engine_list=[])
    other = MainEngine(backend=DummyEngine(), engine_list=[])

    qubit = eng.allocate_qubit()
    H | qubit

    other_qubit0 = other.allocate_qubit()
    eng.backend.send_to(other)  # OK: allocate qubit before sending commands

    other_qubit1 = other.allocate_qubit()
    with pytest.raises(RuntimeError):
        eng.backend.send_to(other)

    Measure | other_qubit0
    Measure | other_qubit1


def test_param_send_to_other_main_engine():
    eng = MainEngine(backend=ParametricGateBackend(), engine_list=[])
    other = MainEngine(backend=DummyEngine(save_commands=True), engine_list=[])
    assert other._qubit_idx == 0

    qureg = eng.allocate_qureg(2)
    H | qureg[0]
    CNOT | (qureg[0], qureg[1])
    assert eng._qubit_idx == 2
    del qureg
    eng.flush()

    eng.backend.send_to(other)
    assert other._qubit_idx == 2
    assert len(other.backend.received_commands) == 7
    assert other.backend.received_commands[0].gate == Allocate
    assert other.backend.received_commands[0].qubits[0][0].id == 0
    assert other.backend.received_commands[1].gate == Allocate
    assert other.backend.received_commands[1].qubits[0][0].id == 1
    assert other.backend.received_commands[2].gate == H
    assert other.backend.received_commands[2].qubits[0][0].id == 0
    assert other.backend.received_commands[3].gate == X
    assert other.backend.received_commands[3].qubits[0][0].id == 1
    assert other.backend.received_commands[3].control_qubits[0].id == 0
    assert other.backend.received_commands[4].gate == Deallocate
    assert other.backend.received_commands[4].qubits[0][0].id == 1
    assert other.backend.received_commands[5].gate == Deallocate
    assert other.backend.received_commands[5].qubits[0][0].id == 0
    assert isinstance(other.backend.received_commands[6].gate, FlushGate)


def test_param_send_to_other_main_engine2():
    backend = ParametricGateBackend()
    eng = MainEngine(backend=backend, engine_list=[])
    other_backend = DummyEngine(save_commands=True)
    other = MainEngine(backend=other_backend, engine_list=[])

    dummy_qubits = other.allocate_qureg(10)  # noqa: F841
    other.flush()
    assert other._qubit_idx == 10

    qureg = eng.allocate_qureg(2)
    H | qureg[0]
    CNOT | (qureg[0], qureg[1])
    eng.flush()
    assert eng._qubit_idx == 2

    # ==================================

    def get_ids(cmd_list):
        return list(chain.from_iterable([qubit.id for qureg in cmd.all_qubits for qubit in qureg] for cmd in cmd_list))

    # ==================================

    assert len(eng.backend._received_commands) == 5
    assert [cmd.gate for cmd in backend._received_commands] == [Allocate] * 2 + [H, X, FlushGate()]
    assert get_ids(backend._received_commands) == [0, 1, 0, 0, 1, -1]

    assert len(other.backend.received_commands) == 11
    assert [cmd.gate for cmd in other_backend.received_commands] == [Allocate] * 10 + [FlushGate()]
    assert get_ids(other_backend.received_commands) == list(range(10)) + [-1]

    # ----------------------------------

    eng.backend.send_to(other)
    other.flush()
    assert other._qubit_idx == 12

    assert len(eng.backend._received_commands) == 5
    assert [cmd.gate for cmd in backend._received_commands] == [Allocate] * 2 + [H, X, FlushGate()]
    assert get_ids(backend._received_commands) == [0, 1, 0, 0, 1, -1]

    assert len(other.backend.received_commands) == 11 + 5 + 1
    assert [cmd.gate for cmd in other_backend.received_commands] == [Allocate] * 10 + [FlushGate()] + [Allocate] * 2 + [
        H,
        X,
        FlushGate(),
    ] + [FlushGate()]
    print(other_backend.received_commands)
    assert get_ids(other_backend.received_commands) == list(range(10)) + [-1] + [10, 11, 10, 10, 11, -1, -1]

    # ----------------------------------

    eng.__del__()
    assert len(backend._received_commands) == 5 + 3
    assert [cmd.gate for cmd in backend._received_commands[-3:]] == [Deallocate, Deallocate, FlushGate()]
    assert len(other_backend.received_commands) == 17

    other.__del__()
    assert len(backend._received_commands) == 5 + 3
    assert len(other_backend.received_commands) == 17 + 10 + 2 + 1
    assert [cmd.gate for cmd in other_backend.received_commands[-13:]] == [Deallocate] * 12 + [FlushGate()]


def test_param_send_to_separate_alloc_and_dealloc():
    num_qubits = 10
    test_eng = MainEngine(backend=ParametricGateBackend(), engine_list=[])
    test_qureg = test_eng.allocate_qureg(num_qubits)
    test_eng.flush()

    sim_eng = MainEngine(engine_list=[])
    qureg = test_eng.backend.send_to(sim_eng)

    assert len(qureg) == num_qubits
    assert [qb.id for qb in qureg] == list(range(num_qubits))

    del test_qureg
    test_eng.flush()
    qureg = test_eng.backend.send_to(sim_eng)
    assert qureg == []


def test_param_send_to_allocation_order():
    # Minimum number of qubits to guarantee failure (at least for the error
    # that lead to the creation of this test)
    num_qubits = 9

    correct_eng = MainEngine(engine_list=[])
    correct_qureg = correct_eng.allocate_qureg(num_qubits)
    correct_eng.flush()

    test_eng = MainEngine(backend=ParametricGateBackend(), engine_list=[])
    test_qureg = test_eng.allocate_qureg(num_qubits)
    test_eng.flush()

    sim_eng = MainEngine(engine_list=[])
    sim_qureg = test_eng.backend.send_to(sim_eng)

    # Make sure that the order in which the qubits are allocated is the same!
    # NB: qubit_id_shift == 0 in this case so direct comparison is possible
    assert [qb.id for qb in correct_qureg] == [qb.id for qb in sim_qureg]
    assert [qb.id for qb in test_qureg] == [qb.id for qb in sim_qureg]


def test_param_send_to_with_parametric_gates(monkeypatch):
    def is_available(self, cmd):
        if not self.is_last_engine:
            return self.next_engine.is_available(cmd)
        return True

    monkeypatch.setattr(DummyEngine, 'is_available', is_available)

    backend = ParametricGateBackend()
    eng = MainEngine(backend=backend, engine_list=[])
    trace_eng = DummyEngine(save_commands=True)
    other = MainEngine(engine_list=[trace_eng])

    x, y = sympy.symbols('x y')

    qureg = eng.allocate_qureg(2)
    Rx(x) | qureg[0]
    Rxx(y) | (qureg[0], qureg[1])
    eng.flush()

    other_qureg = other.allocate_qureg(2)
    All(X) | other_qureg
    other.flush()

    assert len(backend._received_commands) == 5
    assert len(trace_eng.received_commands) == 5

    with pytest.raises(DestinationEngineGateUnsupported):
        backend.send_to(other)
        other.flush()

    assert len(backend._received_commands) == 5
    assert len(trace_eng.received_commands) == 5

    backend.send_to(other, subs={x: 1, y: np.pi})
    other.flush()

    assert len(backend._received_commands) == 5
    assert len(trace_eng.received_commands) == 5 + 5 + 1

    All(Measure) | qureg
    All(Measure) | other_qureg

    # NB: the qubits that `other` received from `eng` were not measured and
    # are not easily accessible...
    other.receive(
        [
            Command(
                other,
                gate=Measure,
                qubits=([WeakQubitRef(other, idx=2)],),
            ),
            Command(
                other,
                gate=Measure,
                qubits=([WeakQubitRef(other, idx=3)],),
            ),
        ]
    )


def test_param_clear():
    eng = MainEngine(backend=ParametricGateBackend(), engine_list=[])
    other_backend = DummyEngine(save_commands=True)
    other = MainEngine(backend=other_backend, engine_list=[])

    dummy_qubits = other.allocate_qureg(10)  # noqa: F841
    other.flush()
    assert other._qubit_idx == 10

    qureg = eng.allocate_qureg(2)
    H | qureg[0]
    CNOT | (qureg[0], qureg[1])
    eng.flush()
    assert eng._qubit_idx == 2

    # ==================================

    assert len(eng.backend._received_commands) == 5
    assert eng.backend._min_allocated_id == 0
    assert eng.backend._max_allocated_id == 1
    assert other not in eng.backend._last_sent_gate_idx
    assert other not in eng.backend._main_engine_qubit_idx

    # ----------------------------------

    eng.backend.send_to(other)

    # ----------------------------------

    assert len(eng.backend._received_commands) == 5
    assert eng.backend._min_allocated_id == 0
    assert eng.backend._max_allocated_id == 1
    assert eng.backend._last_sent_gate_idx[other] == 5
    assert eng.backend._main_engine_qubit_idx[other] == 12

    # ----------------------------------

    eng.backend.clear()

    # ----------------------------------

    assert not eng.backend._received_commands
    assert eng.backend._min_allocated_id is None
    assert eng.backend._max_allocated_id is None
    assert not eng.backend._last_sent_gate_idx
    assert not eng.backend._main_engine_qubit_idx
