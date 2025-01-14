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
Contain a compiler engine to calculate resource count used by a quantum circuit.

A resrouce counter compiler engine counts the number of calls for each type of gate used in a circuit, in addition to
the max. number of active qubits.
"""

from projectq.cengines import BasicEngine, LastEngineException
from projectq.meta import LogicalQubitIDTag, get_control_count
from projectq.ops import Allocate, Deallocate, FlushGate, Measure
from projectq.types import WeakQubitRef


class ResourceCounter(BasicEngine):
    """
    ResourceCounter is a compiler engine which counts the number of gates and max. number of active qubits.

    Attributes:
        gate_counts (dict): Dictionary of gate counts.  The keys are tuples of the form (cmd.gate, ctrl_cnt), where
            ctrl_cnt is the number of control qubits.
        gate_class_counts (dict): Dictionary of gate class counts.  The keys are tuples of the form
            (cmd.gate.__class__, ctrl_cnt), where ctrl_cnt is the number of control qubits.
        max_width (int): Maximal width (=max. number of active qubits at any given point).
    Properties:
        depth_of_dag (int): It is the longest path in the directed acyclic graph (DAG) of the program.
    """

    def __init__(self):
        """
        Initialize a resource counter engine.

        Sets all statistics to zero.
        """
        super().__init__()
        self.gate_counts = {}
        self.gate_class_counts = {}
        self._active_qubits = 0
        self.max_width = 0
        # key: qubit id, depth of this qubit
        self._depth_of_qubit = {}
        self._previous_max_depth = 0

    def is_available(self, cmd):
        """
        Test whether a Command is supported by a compiler engine.

        Specialized implementation of is_available: Returns True if the ResourceCounter is the last engine (since it
        can count any command).

        Args:
            cmd (Command): Command for which to check availability (all Commands can be counted).

        Returns:
            availability (bool): True, unless the next engine cannot handle the Command (if there is a next engine).
        """
        try:
            return BasicEngine.is_available(self, cmd)
        except LastEngineException:
            return True

    @property
    def depth_of_dag(self):
        """Return the depth of the DAG."""
        if self._depth_of_qubit:
            current_max = max(self._depth_of_qubit.values())
            return max(current_max, self._previous_max_depth)
        return self._previous_max_depth

    def _add_cmd(self, cmd):  # pylint: disable=too-many-branches
        """Add a gate to the count."""
        if cmd.gate == Allocate:
            self._active_qubits += 1
            self._depth_of_qubit[cmd.qubits[0][0].id] = 0
        elif cmd.gate == Deallocate:
            self._active_qubits -= 1
            depth = self._depth_of_qubit[cmd.qubits[0][0].id]
            self._previous_max_depth = max(self._previous_max_depth, depth)
            self._depth_of_qubit.pop(cmd.qubits[0][0].id)
        elif self.is_last_engine and cmd.gate == Measure:
            for qureg in cmd.qubits:
                for qubit in qureg:
                    self._depth_of_qubit[qubit.id] += 1
                    # Check if a mapper assigned a different logical id
                    logical_id_tag = None
                    for tag in cmd.tags:
                        if isinstance(tag, LogicalQubitIDTag):
                            logical_id_tag = tag
                    if logical_id_tag is not None:
                        qubit = WeakQubitRef(qubit.engine, logical_id_tag.logical_qubit_id)
                    self.main_engine.set_measurement_result(qubit, 0)
        else:
            qubit_ids = set()
            for qureg in cmd.all_qubits:
                for qubit in qureg:
                    qubit_ids.add(qubit.id)
            if len(qubit_ids) == 1:
                self._depth_of_qubit[list(qubit_ids)[0]] += 1
            else:
                max_depth = 0
                for qubit_id in qubit_ids:
                    max_depth = max(max_depth, self._depth_of_qubit[qubit_id])
                for qubit_id in qubit_ids:
                    self._depth_of_qubit[qubit_id] = max_depth + 1

        self.max_width = max(self.max_width, self._active_qubits)

        ctrl_cnt = get_control_count(cmd)
        gate_description = (cmd.gate, ctrl_cnt)
        gate_class_description = (cmd.gate.klass, ctrl_cnt)

        try:
            self.gate_counts[gate_description] += 1
        except KeyError:
            self.gate_counts[gate_description] = 1

        try:
            self.gate_class_counts[gate_class_description] += 1
        except KeyError:
            self.gate_class_counts[gate_class_description] = 1

    def __str__(self):
        """
        Return the string representation of this ResourceCounter.

        Returns:
            A summary (string) of resources used, including gates, number of calls, and max. number of qubits that
                were active at the same time.
        """
        if len(self.gate_counts) > 0:
            gate_class_list = []
            for gate_class_description, num in self.gate_class_counts.items():
                gate_class, ctrl_cnt = gate_class_description
                gate_class_list.append('{}{} : {}'.format(ctrl_cnt * "C", gate_class.__name__, num))

            gate_list = []
            for gate_description, num in self.gate_counts.items():
                gate, ctrl_cnt = gate_description
                gate_list.append('{}{} : {}'.format(ctrl_cnt * "C", gate, num))

            return ''.join(
                [
                    "Gate class counts:\n    ",
                    "\n    ".join(sorted(gate_class_list)),
                    "\n\nGate counts:\n    ",
                    "\n    ".join(sorted(gate_list)),
                    "\n\nMax. width (number of qubits) : {}.".format(self.max_width),
                ]
            )
        return "(No quantum resources used)"

    def receive(self, command_list):
        """
        Receive a list of commands.

        Receive a list of commands from the previous engine, increases the counters of the received commands, and then
        send them on to the next engine.

        Args:
            command_list (list<Command>): List of commands to receive (and count).
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._add_cmd(cmd)

            # (try to) send on
            if not self.is_last_engine:
                self.send([cmd])
