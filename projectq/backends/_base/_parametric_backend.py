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

"""
Contains a backend that can handle parametric (symbolic) gates.

Contains a compiler engine which stores all the commands it receives in an
internal storage, effectively storing the result of a compilation run. The
user can then send the list of saved commands onto some other engine or
backend at a later time. In this second step, the user may also specify the
value of parameters for some parametric gates (if any).
"""

# pylint: disable=no-name-in-module

from projectq.cengines import BasicEngine
from projectq.ops import AllocateQubitGate, Command, DeallocateQubitGate, FlushGate
from projectq.types import WeakQubitRef


def _noop(arg):  # pylint: disable=unused-argument
    """Define a no-op function."""


class DestinationEngineGateUnsupported(Exception):
    """Exception raised when sending to another compiler engine and some commands are not supported by it."""


class ParametricGateBackend(BasicEngine):
    """
    ParametricGateBackend used in conjunction with parametric gates.

    The ParametricGateBackend stores all commands in an internal storage, typically *without* passing them onto the
    next engine.

    The user can later send the commands to another compiler engine by calling the provided methods (ie. preferrably
    send_to() to allow for some symbolic substitutions)
    """

    def __init__(self):
        """Initialize a PartialCompilationEngine."""
        BasicEngine.__init__(self)
        self._received_commands = []
        self._last_sent_gate_idx = {}
        self._main_engine_qubit_idx = {}
        self._min_allocated_id = None
        self._max_allocated_id = None

    def clear(self):
        """Clear the state of the backend (saved commands, internal state, etc.)."""
        self._received_commands.clear()
        self._last_sent_gate_idx = {}
        self._main_engine_qubit_idx = {}
        self._min_allocated_id = None
        self._max_allocated_id = None

    def is_available(self, cmd):
        """
        Test whether a Command is supported by a compiler engine.

        This backend accepts all commands.

        Args:
            cmd (Command): Command for which to check availability.

        Returns:
            True
        """
        # Accept all commands
        return True

    def receive(self, command_list):
        """Forward all commands to the next engine."""
        self._received_commands.extend(command_list)
        if not self.is_last_engine:
            raise RuntimeError('ParametricGateBackend must be the last engine!')
        # Recalculate the minimum/maximum allocated qubit ID
        # (required for when we eventually send the commands to some other
        # engine)

        qubit_ids = [cmd.qubits[0][0].id for cmd in command_list if isinstance(cmd.gate, AllocateQubitGate)]

        if qubit_ids:
            min_id = min(qubit_ids)
            if self._min_allocated_id is None:
                self._min_allocated_id = min_id
            else:
                self._min_allocated_id = min(self._min_allocated_id, min_id)

            max_id = max(qubit_ids)
            if self._max_allocated_id is None:
                self._max_allocated_id = max_id
            else:
                self._max_allocated_id = max(self._max_allocated_id, max_id)

    def send_to(self, engine, subs=None):  # pylint: disable=too-many-branches
        """
        Send the commands stored in an instance of ParametricGateBackend to some other engine.

        The commands are passed onto the next engine, with parametric gates evaluated according to the substitutions
        passed in as argument, by calling the .receive() method of the receiving engine.

        Args:
            engine (BasicEngine): Some ProjectQ compiler engine.  This may be another MainEngine instance or directly
                some ProjectQ backend or other compiler engine.
            subs (dict): Symbol substitutions to perform.

        Returns:
            A list of all the qubits that were allocated and will still be alive after sending the commands (ie. if a
            qubit is allocated and then de-allocated then it will not be returned).

            This can be useful in order to apply some additional gates to those qubits *after* having sent the
            commands to some other compiler engine.

            .. code-block:: python

                from projectq import MainEngine
                from projectq.backends import ParametricGateBackend

                eng = MainEngine(backend=ParametricGateBackend())
                qubit = eng.allocate_qubit()
                qureg = eng.allocate_qureg(10)
                eng.flush()

                other = MainEngine(engine_list=[])  # No compilation, only
                                                    # simulation
                other_qureg = eng.backend.send_to(other)
                # NB: other_qureg has size 11 (1 + 10)!

                All(X) | other_qureg[1:]  # Apply some X gates on the qubits
                                          # allocated by the `other`
                                          # MainEngine, leaving the ones from
                                          # the `eng` MainEngine untouched.

        Note:
            It is possible to make multiple calls to `send_to` with the same `ParametricGateBackend` and target
            engine. In that case, the backend will only send the commands it has received since the last call to
            `send_to`.

        See also:
            :py:meth:`ParametricGate.evaluate`
        """
        # pylint: disable=protected-access

        if self == engine:
            return []

        if None in (self._min_allocated_id, self._max_allocated_id) and self._received_commands:
            raise RuntimeError(
                'It appears there was no qubit allocation, so how come you have commands acting on qubits?'
            )

        qubit_id_shift = 0

        parent = engine
        add_qubits = _noop
        remove_qubits = _noop

        if engine.main_engine is not None:
            parent = engine.main_engine
            add_qubits = engine.main_engine.active_qubits.add
            remove_qubits = engine.main_engine.active_qubits.discard

            if engine.main_engine is self.main_engine:
                raise RuntimeError('Cannot send these commands to an engine with the same MainEngine!')

            # If there is a MainEngine on the other side, we might need to
            # adjust qubit IDs in order to avoid ID collisions.
            qubit_id_shift = 0
            if engine.main_engine in self._main_engine_qubit_idx:
                # At the moment, we do not support sending commands to a main engine if that main engine has allocated
                # new qubits since the last time we sent commands to it.
                if self._main_engine_qubit_idx[engine.main_engine] != engine.main_engine._qubit_idx:
                    raise RuntimeError(
                        'MainEngine receiving the commands has allocated some qubits since the last time we sent to '
                        'it. Aborting.'
                    )
            elif engine.main_engine._qubit_idx > self._min_allocated_id:
                qubit_id_shift = engine.main_engine._qubit_idx - self._min_allocated_id

        start_idx = self._last_sent_gate_idx.setdefault(parent, 0)
        allocated_qubits = []

        command_list = []
        for cmd in self._received_commands[start_idx:]:
            if isinstance(cmd.gate, FlushGate):
                command_list.append(Command(parent, gate=FlushGate(), qubits=([WeakQubitRef(parent, -1)],)))

            else:
                if subs is not None and cmd.gate.is_parametric():
                    gate = cmd.gate.evaluate(subs=subs)
                else:
                    gate = cmd.gate

                targets = tuple(
                    [WeakQubitRef(parent, qubit.id + qubit_id_shift) for qubit in qureg] for qureg in cmd.qubits
                )

                new_cmd = Command(
                    parent,
                    gate,
                    targets,
                    [WeakQubitRef(parent, qubit.id + qubit_id_shift) for qubit in cmd.control_qubits],
                    cmd.tags,
                )

                if isinstance(new_cmd.gate, AllocateQubitGate):
                    allocated_qubits.append(new_cmd.qubits[0][0])
                    add_qubits(new_cmd.qubits[0][0])
                elif isinstance(new_cmd.gate, DeallocateQubitGate):
                    if new_cmd.qubits[0][0] in allocated_qubits:
                        allocated_qubits.remove(new_cmd.qubits[0][0])
                    remove_qubits(new_cmd.qubits[0][0])

                print(parent)
                if not parent.is_available(new_cmd):
                    raise DestinationEngineGateUnsupported(
                        'Command not supported by destination engine: {}'.format(new_cmd)
                    )

                command_list.append(new_cmd)

        if engine.main_engine is not None:
            # Set qubit ID in main engine so that subsequent qubit allocations
            # do not create collisions with our qubits
            engine.main_engine._qubit_idx = self._max_allocated_id + qubit_id_shift + 1
            self._main_engine_qubit_idx[engine.main_engine] = engine.main_engine._qubit_idx

        self._last_sent_gate_idx[parent] += len(command_list)
        engine.receive(command_list)
        return allocated_qubits
