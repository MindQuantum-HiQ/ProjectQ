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

"""Contains tests for the JSONBackend compiler engine."""

import json

import pytest
from six import StringIO

from projectq.cengines import MainEngine
from projectq.ops import CNOT, Allocate, Command, FlushGate, H
from projectq.types import WeakQubitRef

from ._json_converter import JSONBackend, ProjectQJSONEncoder, calculate_circuit_depth

# ==============================================================================


def test_json_encoder():
    class A(object):
        pass

    qubit = WeakQubitRef(engine=None, idx=0)

    cmd = Command(engine=None, gate=H, qubits=([qubit],))
    data = json.loads(json.dumps(cmd, cls=ProjectQJSONEncoder))
    assert data == {'gate': 'H', 'targets': [0], 'controls': []}

    cmd = Command(engine=None, gate=Allocate, qubits=([qubit],))
    data = json.loads(json.dumps(cmd, cls=ProjectQJSONEncoder))
    assert data == {'gate': 'Allocate', 'targets': [0]}

    qubit1 = WeakQubitRef(engine=None, idx=-1)
    cmd = Command(engine=None, gate=FlushGate(), qubits=([qubit1],))
    data = json.loads(json.dumps(cmd, cls=ProjectQJSONEncoder))
    assert data == {'gate': 'FlushGate'}

    with pytest.raises(TypeError):
        json.dumps(A(), cls=ProjectQJSONEncoder)


# ==============================================================================


def test_calculate_circuit_depth():
    eng = MainEngine(backend=JSONBackend(), engine_list=[])

    assert calculate_circuit_depth(eng.backend.received_commands) == 0

    qubit1 = eng.allocate_qubit()

    assert calculate_circuit_depth(eng.backend.received_commands) == 0

    for idx in range(10):
        H | qubit1
        eng.flush()

        assert calculate_circuit_depth(eng.backend.received_commands) == idx + 1

    del qubit1
    eng.flush()
    assert calculate_circuit_depth(eng.backend.received_commands) == 10

    qubit2 = eng.allocate_qubit()
    for _ in range(5):
        H | qubit2
        eng.flush()
    assert calculate_circuit_depth(eng.backend.received_commands) == 10

    qubit3 = eng.allocate_qubit()
    for _ in range(10):
        H | qubit3
    CNOT | (qubit2, qubit3)
    eng.flush()
    assert calculate_circuit_depth(eng.backend.received_commands) == 11

    eng.flush(deallocate_qubits=True)


# ==============================================================================


def test_json_backend():
    eng = MainEngine(backend=JSONBackend(), engine_list=[])
    qubit = eng.allocate_qubit()

    data = json.loads(eng.backend.json(sort_keys=True))
    assert data['n_allocate'] == 1
    assert data['n_deallocate'] == 0
    assert data['depth'] == 0
    assert data['circuit'] == [
        {
            'gate': 'Allocate',
            'targets': [0],
        }
    ]

    H | qubit
    data = json.loads(eng.backend.json(sort_keys=True))
    assert data['n_allocate'] == 1
    assert data['n_deallocate'] == 0
    assert data['depth'] == 1
    assert data['circuit'] == [
        {
            'gate': 'Allocate',
            'targets': [0],
        },
        {'gate': 'H', 'targets': [0], 'controls': []},
    ]

    other = eng.allocate_qubit()
    CNOT | (qubit, other)
    eng.flush()
    data = json.loads(eng.backend.json(sort_keys=True))

    ref_dict = {
        'n_allocate': 2,
        'n_deallocate': 0,
        'depth': 2,
        'circuit': [
            {
                'gate': 'Allocate',
                'targets': [0],
            },
            {'gate': 'H', 'targets': [0], 'controls': []},
            {
                'gate': 'Allocate',
                'targets': [1],
            },
            {'gate': 'X', 'targets': [1], 'controls': [0]},
            {
                'gate': 'FlushGate',
            },
        ],
    }

    assert data == ref_dict

    # ----------------------------------

    stream = StringIO()

    eng.backend.write_json(stream, sort_keys=True)

    data = json.loads(stream.getvalue())
    assert data == ref_dict

    eng.flush(deallocate_qubits=True)
