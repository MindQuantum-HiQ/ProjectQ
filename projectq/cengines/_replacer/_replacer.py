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
Definitions of a few compiler engines that handle command filtering and replacement.

Contains an AutoReplacer compiler engine which uses engine.is_available to determine whether a command can be
executed. If not, it uses the loaded setup (e.g., default) to find an appropriate decomposition.

The InstructionFilter can be used to further specify which gates to replace/keep.
"""

from projectq.cengines import BasicEngine, CommandModifier, ForwarderEngine
from projectq.ops import FlushGate, get_inverse


class NoGateDecompositionError(Exception):
    """Exception raised when no gate decomposition rule can be found."""


class InstructionFilter(BasicEngine):
    """
    A compiler engine that implements a user-defined is_available() method.

    The InstructionFilter is a compiler engine which changes the behavior of is_available according to a filter
    function. All commands are passed to this function, which then returns whether this command can be executed (True)
    or needs replacement (False).
    """

    def __init__(self, filterfun):
        """
        Initialize an InstructionFilter object.

        Initializer: The provided filterfun returns True for all commands which do not need replacement and False for
        commands that do.

        Args:
            filterfun (function): Filter function which returns True for available commands, and False
                otherwise. filterfun will be called as filterfun(self, cmd).
        """
        super().__init__()
        self._filterfun = filterfun

    def is_available(self, cmd):
        """
        Test whether a Command is supported by a compiler engine.

        Specialized implementation of BasicBackend.is_available: Forwards this call to the filter function given to
        the constructor.

        Args:
            cmd (Command): Command for which to check availability.
        """
        return self._filterfun(self, cmd)

    def receive(self, command_list):
        """
        Receive a list of commands.

        This implementation simply forwards all commands to the next engine.

        Args:
            command_list (list<Command>): List of commands to receive.
        """
        self.next_engine.receive(command_list)


class AutoReplacer(BasicEngine):  # pylint: disable=too-few-public-methods
    """
    A compiler engine to automatically replace certain commands.

    The AutoReplacer is a compiler engine which uses engine.is_available in order to determine which commands need to
    be replaced/decomposed/compiled further. The loaded setup is used to find decomposition rules appropriate for each
    command (e.g., setups.default).
    """

    def __init__(
        self,
        decomposition_rule_se,
        decomposition_chooser=lambda cmd, decomposition_list: decomposition_list[0],
    ):
        """
        Initialize an AutoReplacer.

        Args:
            decomposition_chooser (function): A function which, given the
                Command to decompose and a list of potential Decomposition
                objects, determines (and then returns) the 'best'
                decomposition.

        The default decomposition chooser simply returns the first list
        element, i.e., calling

        .. code-block:: python

            repl = AutoReplacer()

        Amounts to

        .. code-block:: python

            def decomposition_chooser(cmd, decomp_list):
                return decomp_list[0]
            repl = AutoReplacer(decomposition_chooser)
        """
        super().__init__()
        self._decomp_chooser = decomposition_chooser
        self.decomposition_rule_set = decomposition_rule_se

    def _process_command(self, cmd):  # pylint: disable=too-many-locals,too-many-branches
        """
        Process a command.

        Check whether a command cmd can be handled by further engines and, if not, replace it using the decomposition
        rules loaded with the setup (e.g., setups.default).

        Args:
            cmd (Command): Command to process.

        Raises:
            Exception if no replacement is available in the loaded setup.
        """
        if self.is_available(cmd):  # pylint: disable=too-many-nested-blocks
            self.send([cmd])
        else:
            # First check for a decomposition rules of the gate class, then
            # the gate class of the inverse gate. If nothing is found, do the
            # same for the first parent class, etc.
            gate_mro = type(cmd.gate).mro()[:-1]
            # If gate does not have an inverse it's parent classes are
            # DaggeredGate, BasicGate, object. Hence don't check the last two
            inverse_mro = type(get_inverse(cmd.gate)).mro()[:-2]
            rules = self.decomposition_rule_set.decompositions

            # If the decomposition rule to remove negatively controlled qubits is present in the list of potential
            # decompositions, we process it immediately, before any other decompositions.
            controlstate_rule = [
                rule for rule in rules.get('BasicGate', []) if rule.decompose.__name__ == '_decompose_controlstate'
            ]
            if controlstate_rule and controlstate_rule[0].check(cmd):
                chosen_decomp = controlstate_rule[0]
            else:
                # check for decomposition rules
                decomp_list = []
                potential_decomps = []

                for level in range(max(len(gate_mro), len(inverse_mro))):
                    # Check for forward rules
                    if level < len(gate_mro):
                        class_name = gate_mro[level].__name__
                        try:
                            potential_decomps = rules[class_name]
                        except KeyError:
                            pass
                        # throw out the ones which don't recognize the command
                        for decomp in potential_decomps:
                            if decomp.check(cmd):
                                decomp_list.append(decomp)
                        if len(decomp_list) != 0:
                            break
                    # Check for rules implementing the inverse gate
                    # and run them in reverse
                    if level < len(inverse_mro):
                        inv_class_name = inverse_mro[level].__name__
                        try:
                            potential_decomps += [d.get_inverse_decomposition() for d in rules[inv_class_name]]
                        except KeyError:
                            pass
                        # throw out the ones which don't recognize the command
                        for decomp in potential_decomps:
                            if decomp.check(cmd):
                                decomp_list.append(decomp)
                        if len(decomp_list) != 0:
                            break

                if len(decomp_list) == 0:
                    raise NoGateDecompositionError("\nNo replacement found for " + str(cmd) + "!")

                # Basic sort of rules based on their priority
                decomp_list.sort(key=lambda rule: rule.priority, reverse=True)

                # use decomposition chooser to determine the best decomposition
                chosen_decomp = self._decomp_chooser(cmd, decomp_list)

            # the decomposed command must have the same tags
            # (plus the ones it gets from meta-statements inside the
            # decomposition rule).
            # --> use a CommandModifier with a ForwarderEngine to achieve this.
            old_tags = cmd.tags[:]

            def cmd_mod_fun(cmd):  # Adds the tags
                cmd.tags = old_tags[:] + cmd.tags
                cmd.engine = self.main_engine
                return cmd

            # the CommandModifier calls cmd_mod_fun for each command
            # --> commands get the right tags.
            cmod_eng = CommandModifier(cmd_mod_fun)
            cmod_eng.next_engine = self  # send modified commands back here
            cmod_eng.main_engine = self.main_engine
            # forward everything to cmod_eng using the ForwarderEngine
            # which behaves just like MainEngine
            # (--> meta functions still work)
            forwarder_eng = ForwarderEngine(cmod_eng)
            cmd.engine = forwarder_eng  # send gates directly to forwarder
            # (and not to main engine, which would screw up the ordering).

            chosen_decomp.decompose(cmd)  # run the decomposition

    def receive(self, command_list):
        """
        Receive a list of commands.

        Receive a list of commands from the previous compiler engine and, if necessary, replace/decompose the gates
        according to the decomposition rules in the loaded setup.

        Args:
            command_list (list<Command>): List of commands to handle.
        """
        for cmd in command_list:
            if not isinstance(cmd.gate, FlushGate):
                self._process_command(cmd)
            else:
                self.send([cmd])
