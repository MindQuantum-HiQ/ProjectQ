# -*- coding: utf-8 -*-
#   Copyright 2020 <Huawei Technologies Co., Ltd>
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

"""Contains a compiler engine that converts ProjectQ commands to JSON format."""

import json

from six.moves import map

from projectq.cengines import DummyEngine
from projectq.ops import (
    AllocateQubitGate,
    BasicGate,
    ClassicalInstructionGate,
    Command,
    DeallocateQubitGate,
    FlushGate,
)

# ==============================================================================


class ProjectQJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for ProjectQ commands and gates."""

    def default(self, o):
        """Define the default data serialization."""
        if isinstance(o, BasicGate):
            if isinstance(o, FlushGate):
                return 'FlushGate'
            return str(o)

        if isinstance(o, Command):
            data = {'gate': o.gate}
            if not isinstance(o.gate, FlushGate):
                data['targets'] = [qb.id for qureg in o.qubits for qb in qureg]
            if not isinstance(o.gate, ClassicalInstructionGate):
                data['controls'] = [qb.id for qb in o.control_qubits]
            return data

        return json.JSONEncoder.default(self, o)


# ==============================================================================


def calculate_circuit_depth(command_list):
    """
    Calculate the depth of a quantum circuit.

    Args:
        command_list (list): List of ProjectQ commands

    Returns:
        Depth of quantum circuit (int)
    """
    prev_max_depth = 0
    depth_of_qubit = {}

    for cmd in command_list:
        if isinstance(cmd.gate, AllocateQubitGate):
            depth_of_qubit[cmd.qubits[0][0].id] = 0
        elif isinstance(cmd.gate, DeallocateQubitGate):
            prev_max_depth = max(prev_max_depth, depth_of_qubit[cmd.qubits[0][0].id])
            depth_of_qubit.pop(cmd.qubits[0][0].id)
        elif isinstance(cmd.gate, FlushGate):
            pass
        else:
            qubit_ids = {qubit.id for qureg in cmd.all_qubits for qubit in qureg}
            if len(qubit_ids) == 1:
                depth_of_qubit[list(qubit_ids)[0]] += 1
            else:
                depth = max([depth_of_qubit[qubit_id] for qubit_id in qubit_ids])
                for qubit_id in qubit_ids:
                    depth_of_qubit[qubit_id] = depth + 1

    if not depth_of_qubit:
        return prev_max_depth
    return max(prev_max_depth, max(depth_of_qubit.values()))


# ==============================================================================


class JSONBackend(DummyEngine):
    """ProjectQ engine to convert a list of commands to JSON format."""

    _gate_map = {AllocateQubitGate: 1, DeallocateQubitGate: 2}

    @staticmethod
    def _get_gate_id(cmd):
        return JSONBackend._gate_map.get(cmd.gate.__class__, 0)

    def __init__(self):
        """Initialize a JSONBackend object."""
        DummyEngine.__init__(self, save_commands=True)

    def json(self, **kwargs):
        """
        Get a JSON representation of the commands processed by this engine as JSON string.

        Args:
            **kwargs: Arbitrary keyword arguments (see dumps() function from
                  json module)
        """
        return json.dumps(self._prepare_json_data(), cls=ProjectQJSONEncoder, **kwargs)

    def write_json(self, fp_obj, **kwargs):
        """
        Write a JSON representation of the commands processed by this engine to a JSON formatted stream.

        Args:
            fp_obj (file-like object): Stream to output JSON to
            **kwargs: Arbitrary keyword arguments (see dump() function from json module)
        """
        json.dump(self._prepare_json_data(), fp_obj, cls=ProjectQJSONEncoder, **kwargs)

    def _prepare_json_data(self):
        gate_ids = list(map(JSONBackend._get_gate_id, self.received_commands))
        print(gate_ids)
        return {
            'n_allocate': gate_ids.count(JSONBackend._gate_map[AllocateQubitGate]),
            'n_deallocate': gate_ids.count(JSONBackend._gate_map[DeallocateQubitGate]),
            'depth': calculate_circuit_depth(self.received_commands),
            'circuit': self.received_commands,
        }
