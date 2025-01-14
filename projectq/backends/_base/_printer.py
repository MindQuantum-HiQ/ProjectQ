# -*- coding: utf-8 -*-
#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
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

"""Contains a compiler engine which prints commands to stdout prior to sending them on to the next engines."""

import sys
from builtins import input

from projectq.cengines import BasicEngine, LastEngineException
from projectq.meta import LogicalQubitIDTag, get_control_count
from projectq.ops import FlushGate, Measure
from projectq.types import WeakQubitRef


class CommandPrinter(BasicEngine):
    """
    Compiler engine that prints command to the standard output.

    CommandPrinter is a compiler engine which prints commands to stdout prior to sending them on to the next compiler
    engine.
    """

    def __init__(self, accept_input=True, default_measure=False, in_place=False):
        """
        Initialize a CommandPrinter.

        Args:
            accept_input (bool): If accept_input is true, the printer queries the user to input measurement results if
                the CommandPrinter is the last engine. Otherwise, all measurements yield default_measure.
            default_measure (bool): Default measurement result (if accept_input is False).
            in_place (bool): If in_place is true, all output is written on the same line of the terminal.
        """
        super().__init__()
        self._accept_input = accept_input
        self._default_measure = default_measure
        self._in_place = in_place

    def is_available(self, cmd):
        """
        Test whether a Command is supported by a compiler engine.

        Specialized implementation of is_available: Returns True if the CommandPrinter is the last engine (since it
        can print any command).

        Args:
            cmd (Command): Command of which to check availability (all Commands can be printed).
        Returns:
            availability (bool): True, unless the next engine cannot handle the Command (if there is a next engine).
        """
        try:
            return BasicEngine.is_available(self, cmd)
        except LastEngineException:
            return True

    def _print_cmd(self, cmd):
        """
        Print a command.

        Print a command or, if the command is a measurement instruction and the CommandPrinter is the last engine in
        the engine pipeline: Query the user for the measurement result (if accept_input = True) / Set the result to 0
        (if it's False).

        Args:
            cmd (Command): Command to print.
        """
        if self.is_last_engine and cmd.gate == Measure:
            if get_control_count(cmd) != 0:
                raise ValueError('Cannot have control qubits with a measurement gate!')

            print(cmd)
            for qureg in cmd.qubits:
                for qubit in qureg:
                    if self._accept_input:
                        meas_str = None
                        while meas_str not in ('0', '1', 1, 0):
                            prompt = "Input measurement result (0 or 1) for qubit {}: ".format(qubit)
                            meas_str = input(prompt)
                    else:
                        meas_str = self._default_measure
                    meas = int(meas_str)
                    # Check there was a mapper and redirect result
                    logical_id_tag = None
                    for tag in cmd.tags:
                        if isinstance(tag, LogicalQubitIDTag):
                            logical_id_tag = tag
                    if logical_id_tag is not None:
                        qubit = WeakQubitRef(qubit.engine, logical_id_tag.logical_qubit_id)
                    self.main_engine.set_measurement_result(qubit, meas)
        else:
            if self._in_place:  # pragma: no cover
                sys.stdout.write("\0\r\t\x1b[K" + str(cmd) + "\r")
            else:
                print(cmd)

    def receive(self, command_list):
        """
        Receive a list of commands.

        Receive a list of commands from the previous engine, print the
        commands, and then send them on to the next engine.

        Args:
            command_list (list<Command>): List of Commands to print (and
                potentially send on to the next engine).
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._print_cmd(cmd)
            # (try to) send on
            if not self.is_last_engine:
                self.send([cmd])
