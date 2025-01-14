# -*- coding: utf-8 -*-
#   Copyright 2017, 2021 ProjectQ-Framework (www.projectq.ch)
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

"""Contain a compiler engine which generates TikZ Latex code describing the circuit."""

from builtins import input

from projectq.cengines import BasicEngine, LastEngineException
from projectq.meta import get_control_count
from projectq.ops import Allocate, Deallocate, FlushGate, Measure

from ._to_latex import to_latex


class CircuitItem:  # pylint: disable=too-few-public-methods
    """Item of a quantum circuit to draw."""

    def __init__(self, gate, lines, ctrl_lines):
        """
        Initialize a circuit item.

        Args:
            gate: Gate object.
            lines (list<int>): Circuit lines the gate acts on.
            ctrl_lines (list<int>): Circuit lines which control the gate.
        """
        self.gate = gate
        self.lines = lines
        self.ctrl_lines = ctrl_lines
        self.id = -1

    def __eq__(self, other):
        """Equal operator."""
        return (
            self.gate == other.gate
            and self.lines == other.lines
            and self.ctrl_lines == other.ctrl_lines
            and self.id == other.id
        )


class CircuitDrawer(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """
    CircuitDrawer is a compiler engine which generates TikZ code for drawing quantum circuits.

    The circuit can be modified by editing the settings.json file which is generated upon first execution. This
    includes adjusting the gate width, height, shadowing, line thickness, and many more options.

    After initializing the CircuitDrawer, it can also be given the mapping from qubit IDs to wire location (via the
    :meth:`set_qubit_locations` function):

    .. code-block:: python

        circuit_backend = CircuitDrawer()
        circuit_backend.set_qubit_locations({0: 1, 1: 0}) # swap lines 0 and 1
        eng = MainEngine(circuit_backend)

        ... # run quantum algorithm on this main engine

        print(circuit_backend.get_latex()) # prints LaTeX code

    To see the qubit IDs in the generated circuit, simply set the `draw_id` option in the settings.json file under
    "gates":"AllocateQubitGate" to True:

    .. code-block:: python

        "gates": {
            "AllocateQubitGate": {
                "draw_id": True,
                "height": 0.15,
                "width": 0.2,
                "pre_offset": 0.1,
                "offset": 0.1
            },
            ...

    The settings.json file has the following structure:

    .. code-block:: python

        {
            "control": { # settings for control "circle"
                    "shadow": false,
                    "size": 0.1
            },
            "gate_shadow": true, # enable/disable shadows for all gates
            "gates": {
                    "GateClassString": {
                        GATE_PROPERTIES
                    }
                    "GateClassString2": {
                        ...
            },
            "lines": { # settings for qubit lines
                    "double_classical": true, # draw double-lines for
                                              # classical bits
                    "double_lines_sep": 0.04, # gap between the two lines
                                              # for double lines
                    "init_quantum": true, # start out with quantum bits
                    "style": "very thin" # line style
            }
        }

    All gates (except for the ones requiring special treatment) support the following properties:

    .. code-block:: python

        "GateClassString": {
            "height": GATE_HEIGHT,
            "width": GATE_WIDTH
            "pre_offset": OFFSET_BEFORE_PLACEMENT,
            "offset": OFFSET_AFTER_PLACEMENT,
        },

    """

    def __init__(self, accept_input=False, default_measure=0):
        """
        Initialize a circuit drawing engine.

        The TikZ code generator uses a settings file (settings.json), which can be altered by the user. It contains
        gate widths, heights, offsets, etc.

        Args:
            accept_input (bool): If accept_input is true, the printer queries the user to input measurement results if
                the CircuitDrawer is the last engine. Otherwise, all measurements yield the result default_measure (0
                or 1).
            default_measure (bool): Default value to use as measurement results if accept_input is False and there is
                no underlying backend to register real measurement results.
        """
        super().__init__()
        self._accept_input = accept_input
        self._default_measure = default_measure
        self._qubit_lines = {}
        self._free_lines = []
        self._map = {}

        # Order in which qubit lines are drawn
        self._drawing_order = []

    def is_available(self, cmd):
        """
        Test whether a Command is supported by a compiler engine.

        Specialized implementation of is_available: Returns True if the CircuitDrawer is the last engine (since it can
        print any command).

        Args:
            cmd (Command): Command for which to check availability (all Commands can be printed).

        Returns:
            availability (bool): True, unless the next engine cannot handle the Command (if there is a next engine).
        """
        try:
            return BasicEngine.is_available(self, cmd)
        except LastEngineException:
            return True

    def set_qubit_locations(self, id_to_loc):
        """
        Set the qubit lines to use for the qubits explicitly.

        To figure out the qubit IDs, simply use the setting `draw_id` in the settings file. It is located in
        "gates":"AllocateQubitGate".  If draw_id is True, the qubit IDs are drawn in red.

        Args:
            id_to_loc (dict): Dictionary mapping qubit ids to qubit line numbers.

        Raises:
            RuntimeError: If the mapping has already begun (this function needs be called before any gates have been
                received).
        """
        if len(self._map) > 0:
            raise RuntimeError("set_qubit_locations() has to be called before applying gates!")

        for k in range(min(id_to_loc), max(id_to_loc) + 1):
            if k not in id_to_loc:
                raise RuntimeError(
                    "set_qubit_locations(): Invalid id_to_loc "
                    "mapping provided. All ids in the provided"
                    " range of qubit ids have to be mapped "
                    "somewhere."
                )
        self._map = id_to_loc

    def _print_cmd(self, cmd):
        """
        Add a command to the list of commands to be printed.

        Add the command cmd to the circuit diagram, taking care of potential measurements as specified in the __init__
        function.

        Queries the user for measurement input if a measurement command arrives if accept_input was set to
        True. Otherwise, it uses the default_measure parameter to register the measurement outcome.

        Args:
            cmd (Command): Command to add to the circuit diagram.
        """
        # pylint: disable=R0801
        if cmd.gate == Allocate:
            qubit_id = cmd.qubits[0][0].id
            if qubit_id not in self._map:
                self._map[qubit_id] = qubit_id
            self._qubit_lines[qubit_id] = []

        if cmd.gate == Deallocate:
            qubit_id = cmd.qubits[0][0].id
            self._free_lines.append(qubit_id)

        if self.is_last_engine and cmd.gate == Measure:
            if get_control_count(cmd) != 0:
                raise ValueError('Cannot have control qubits with a measurement gate!')

            for qureg in cmd.qubits:
                for qubit in qureg:
                    if self._accept_input:
                        meas_str = None
                        while meas_str not in ('0', '1', 1, 0):
                            prompt = "Input measurement result (0 or 1) for qubit {}: ".format(qubit)
                            meas_str = input(prompt)
                    else:
                        meas_str = self._default_measure
                    self.main_engine.set_measurement_result(qubit, int(meas_str))

        all_lines = [qb.id for qr in cmd.all_qubits for qb in qr]

        gate = cmd.gate
        lines = [qb.id for qr in cmd.qubits for qb in qr]
        ctrl_lines = [qb.id for qb in cmd.control_qubits]
        item = CircuitItem(gate, lines, ctrl_lines)
        for line in all_lines:
            self._qubit_lines[line].append(item)

        self._drawing_order.append(all_lines[0])

    def get_latex(self, ordered=False, draw_gates_in_parallel=True):
        """
        Return the latex document string representing the circuit.

        Simply write this string into a tex-file or, alternatively, pipe the
        output directly to, e.g., pdflatex:

        .. code-block:: bash

            python3 my_circuit.py | pdflatex

        where my_circuit.py calls this function and prints it to the terminal.

        Args:
            ordered(bool): flag if the gates should be drawn in the order they were added to the circuit
            draw_gates_in_parallel(bool): flag if parallel gates should be drawn parallel (True), or not (False)
        """
        qubit_lines = {}

        for line, qubit_line in self._qubit_lines.items():
            new_line = self._map[line]
            qubit_lines[new_line] = []

            for cmd in qubit_line:
                lines = [self._map[qb_id] for qb_id in cmd.lines]
                ctrl_lines = [self._map[qb_id] for qb_id in cmd.ctrl_lines]
                gate = cmd.gate
                new_cmd = CircuitItem(gate, lines, ctrl_lines)
                if gate == Allocate:
                    new_cmd.id = cmd.lines[0]
                qubit_lines[new_line].append(new_cmd)

        drawing_order = None
        if ordered:
            drawing_order = self._drawing_order

        return to_latex(
            qubit_lines,
            drawing_order=drawing_order,
            draw_gates_in_parallel=draw_gates_in_parallel,
        )

    def receive(self, command_list):
        """
        Receive a list of commands.

        Receive a list of commands from the previous engine, print the commands, and then send them on to the next
        engine.

        Args:
            command_list (list<Command>): List of Commands to print (and potentially send on to the next engine).
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._print_cmd(cmd)
            # (try to) send on
            if not self.is_last_engine:
                self.send([cmd])
