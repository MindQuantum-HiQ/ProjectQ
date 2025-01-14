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

"""
The ProjectQ interface to a C++-based simulator.

The C++ simulator has to be built first. If the C++ simulator is not exported to python, a (slow) python
implementation is used as an alternative.
"""

# pylint: disable=no-name-in-module

import math
import random

from projectq.cengines import BasicEngine
from projectq.meta import LogicalQubitIDTag, get_control_count, has_negative_control
from projectq.ops import (
    Allocate,
    BasicMathGate,
    Deallocate,
    FlushGate,
    Measure,
    TimeEvolution,
)
from projectq.types import WeakQubitRef

FALLBACK_TO_PYSIM = False
try:
    from ._cppsim import SimBackend  # pylint: disable=unused-import
    from ._cppsim import Simulator as SimulatorBackend
except ImportError:  # pragma: no cover
    from ._pysim import Simulator as SimulatorBackend

    SimBackend = None
    FALLBACK_TO_PYSIM = True


class Simulator(BasicEngine):
    """
    Simulator is a compiler engine which simulates a quantum computer using C++-based kernels.

    OpenMP is enabled and the number of threads can be controlled using the OMP_NUM_THREADS environment variable, i.e.

    .. code-block:: bash

        export OMP_NUM_THREADS=4 # use 4 threads
        export OMP_PROC_BIND=spread # bind threads to processors by spreading
    """

    def __init__(self, gate_fusion=False, rnd_seed=None):
        """
        Construct the C++/Python-simulator object and initialize it with a random seed.

        Args:
            gate_fusion (bool): If True, gates are cached and only executed once a certain gate-size has been reached
                (only has an effect for the c++ simulator).
            rnd_seed (int): Random seed (uses random.randint(0, 4294967295) by default).

        Example of gate_fusion: Instead of applying a Hadamard gate to 5 qubits, the simulator calculates the
        kronecker product of the 1-qubit gate matrices and then applies one 5-qubit gate. This increases operational
        intensity and keeps the simulator from having to iterate through the state vector multiple times. Depending on
        the system (and, especially, number of threads), this may or may not be beneficial.

        Note:
            If the C++ Simulator extension was not built or cannot be found, the Simulator defaults to a Python
            implementation of the kernels.  While this is much slower, it is still good enough to run basic quantum
            algorithms.

            If you need to run large simulations, check out the tutorial in the docs which gives futher hints on how
            to build the C++ extension.
        """
        if rnd_seed is None:
            rnd_seed = random.randint(0, 4294967295)
        super().__init__()
        self._simulator = SimulatorBackend(rnd_seed)
        self._gate_fusion = gate_fusion

    def is_available(self, cmd):
        """
        Test whether a Command is supported by a compiler engine.

        Specialized implementation of is_available: The simulator can deal with all arbitrarily-controlled gates which
        provide a gate-matrix (via gate.matrix) and acts on 5 or less qubits (not counting the control qubits).

        Args:
            cmd (Command): Command for which to check availability (single- qubit gate, arbitrary controls)

        Returns:
            True if it can be simulated and False otherwise.
        """
        if has_negative_control(cmd):
            return False

        if (
            cmd.gate == Measure
            or cmd.gate == Allocate
            or cmd.gate == Deallocate
            or isinstance(cmd.gate, (BasicMathGate, TimeEvolution))
        ):
            return True

        if cmd.gate.is_parametric():
            return False

        try:
            # Allow up to 5-qubit gates
            return cmd.gate.matrix.shape[0] <= 2 ** 5
        except AttributeError:
            return False

    def _convert_logical_to_mapped_qureg(self, qureg):
        """
        Convert a qureg from logical to mapped qubits if there is a mapper.

        Args:
            qureg (list[Qubit],Qureg): Logical quantum bits
        """
        mapper = self.main_engine.mapper
        if mapper is not None:
            mapped_qureg = []
            for qubit in qureg:
                if qubit.id not in mapper.current_mapping:
                    raise RuntimeError("Unknown qubit id. Please make sure you have called eng.flush().")
                new_qubit = WeakQubitRef(qubit.engine, mapper.current_mapping[qubit.id])
                mapped_qureg.append(new_qubit)
            return mapped_qureg
        return qureg

    def get_expectation_value(self, qubit_operator, qureg):
        """
        Return the expectation value of a qubit operator.

        Get the expectation value of qubit_operator w.r.t. the current wave
        function represented by the supplied quantum register.

        Args:
            qubit_operator (projectq.ops.QubitOperator): Operator to measure.
            qureg (list[Qubit],Qureg): Quantum bits to measure.

        Returns:
            Expectation value

        Note:
            Make sure all previous commands (especially allocations) have passed through the compilation chain (call
            main_engine.flush() to make sure).

        Note:
            If there is a mapper present in the compiler, this function automatically converts from logical qubits to
            mapped qubits for the qureg argument.

        Raises:
            Exception: If `qubit_operator` acts on more qubits than present in the `qureg` argument.
        """
        qureg = self._convert_logical_to_mapped_qureg(qureg)
        num_qubits = len(qureg)
        for term, _ in qubit_operator.terms.items():
            if not term == () and term[-1][0] >= num_qubits:
                raise Exception("qubit_operator acts on more qubits than contained in the qureg.")
        operator = [(list(term), coeff) for (term, coeff) in qubit_operator.terms.items()]
        return self._simulator.get_expectation_value(operator, [qb.id for qb in qureg])

    def apply_qubit_operator(self, qubit_operator, qureg):
        """
        Apply a (possibly non-unitary) qubit_operator to the current wave function represented by a quantum register.

        Args:
            qubit_operator (projectq.ops.QubitOperator): Operator to apply.
            qureg (list[Qubit],Qureg): Quantum bits to which to apply the operator.

        Raises:
            Exception: If `qubit_operator` acts on more qubits than present in
                the `qureg` argument.

        Warning:
            This function allows applying non-unitary gates and it will not re-normalize the wave function! It is for
            numerical experiments only and should not be used for other purposes.

        Note:
            Make sure all previous commands (especially allocations) have passed through the compilation chain (call
            main_engine.flush() to make sure).

        Note:
            If there is a mapper present in the compiler, this function automatically converts from logical qubits to
            mapped qubits for the qureg argument.
        """
        qureg = self._convert_logical_to_mapped_qureg(qureg)
        num_qubits = len(qureg)
        for term, _ in qubit_operator.terms.items():
            if not term == () and term[-1][0] >= num_qubits:
                raise Exception("qubit_operator acts on more qubits than contained in the qureg.")
        operator = [(list(term), coeff) for (term, coeff) in qubit_operator.terms.items()]
        return self._simulator.apply_qubit_operator(operator, [qb.id for qb in qureg])

    def get_probability(self, bit_string, qureg):
        """
        Return the probability of the outcome `bit_string` when measuring the quantum register `qureg`.

        Args:
            bit_string (list[bool|int]|string[0|1]): Measurement outcome.
            qureg (Qureg|list[Qubit]): Quantum register.

        Returns:
            Probability of measuring the provided bit string.

        Note:
            Make sure all previous commands (especially allocations) have passed through the compilation chain (call
            main_engine.flush() to make sure).

        Note:
            If there is a mapper present in the compiler, this function automatically converts from logical qubits to
            mapped qubits for the qureg argument.
        """
        qureg = self._convert_logical_to_mapped_qureg(qureg)
        bit_string = [bool(int(b)) for b in bit_string]
        return self._simulator.get_probability(bit_string, [qb.id for qb in qureg])

    def get_amplitude(self, bit_string, qureg):
        """
        Return the probability amplitude of the supplied `bit_string`.

        The ordering is given by the quantum register `qureg`, which must
        contain all allocated qubits.

        Args:
            bit_string (list[bool|int]|string[0|1]): Computational basis state
            qureg (Qureg|list[Qubit]): Quantum register determining the ordering. Must contain all allocated qubits.

        Returns:
            Probability amplitude of the provided bit string.

        Note:
            Make sure all previous commands (especially allocations) have passed through the compilation chain (call
            main_engine.flush() to make sure).

        Note:
            If there is a mapper present in the compiler, this function automatically converts from logical qubits to
            mapped qubits for the qureg argument.
        """
        qureg = self._convert_logical_to_mapped_qureg(qureg)
        bit_string = [bool(int(b)) for b in bit_string]
        return self._simulator.get_amplitude(bit_string, [qb.id for qb in qureg])

    def set_wavefunction(self, wavefunction, qureg):
        """
        Set the wavefunction and the qubit ordering of the simulator.

        The simulator will adopt the ordering of qureg (instead of reordering
        the wavefunction).

        Args:
            wavefunction (list[complex]): Array of complex amplitudes
                describing the wavefunction (must be normalized).
            qureg (Qureg|list[Qubit]): Quantum register determining the
                ordering. Must contain all allocated qubits.

        Note:
            Make sure all previous commands (especially allocations) have
            passed through the compilation chain (call main_engine.flush() to
            make sure).

        Note:
            If there is a mapper present in the compiler, this function
            automatically converts from logical qubits to mapped qubits for
            the qureg argument.
        """
        qureg = self._convert_logical_to_mapped_qureg(qureg)
        self._simulator.set_wavefunction(wavefunction, [qb.id for qb in qureg])

    def collapse_wavefunction(self, qureg, values):
        """
        Collapse a quantum register onto a classical basis state.

        Args:
            qureg (Qureg|list[Qubit]): Qubits to collapse.
            values (list[bool|int]|string[0|1]): Measurement outcome for each
                                                 of the qubits in `qureg`.

        Raises:
            RuntimeError: If an outcome has probability (approximately) 0 or
                if unknown qubits are provided (see note).

        Note:
            Make sure all previous commands have passed through the
            compilation chain (call main_engine.flush() to make sure).

        Note:
            If there is a mapper present in the compiler, this function
            automatically converts from logical qubits to mapped qubits for
            the qureg argument.
        """
        qureg = self._convert_logical_to_mapped_qureg(qureg)
        return self._simulator.collapse_wavefunction([qb.id for qb in qureg], [bool(int(v)) for v in values])

    def cheat(self):
        """
        Access the ordering of the qubits and the state vector directly.

        This is a cheat function which enables, e.g., more efficient
        evaluation of expectation values and debugging.

        Returns:
            A tuple where the first entry is a dictionary mapping qubit
            indices to bit-locations and the second entry is the corresponding
            state vector.

        Note:
            Make sure all previous commands have passed through the
            compilation chain (call main_engine.flush() to make sure).

        Note:
            If there is a mapper present in the compiler, this function
            DOES NOT automatically convert from logical qubits to mapped
            qubits.
        """
        return self._simulator.cheat()

    def select_backend(self, backend_type):
        """
        Select a particular type of simulator backend. Only applicable to the C++ simulator.

        Args:
            backend_type (SimBackend): enum value describing the backend type
                Currently the following values are valid:
                  - ScalarSerial (no vector instructions, non-threaded)
                  - ScalarThreaded (no vector instructions, threaded)
                  - VectorSerial (with vector instructions, non-threaded)
                  - VectorThreaded (with vector instruction, threaded)
                  - OffloadNvidia (computations on a GPU using CUDA)
                  - Auto (choose best available option)

                Note that not all backend may be available on your machine.
        """
        self._simulator.select_backend(backend_type)

    def _handle(self, cmd):  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
        """
        Handle all commands.

        i.e., call the member functions of the C++- simulator object corresponding to measurement, allocation/
        deallocation, and (controlled) single-qubit gate.

        Args:
            cmd (Command): Command to handle.

        Raises:
            Exception: If a non-single-qubit gate needs to be processed (which should never happen due to
                is_available).
        """
        if cmd.gate == Measure:
            if get_control_count(cmd) != 0:
                raise ValueError('Cannot have control qubits with a measurement gate!')
            ids = [qb.id for qr in cmd.qubits for qb in qr]
            out = self._simulator.measure_qubits(ids)
            i = 0
            for qureg in cmd.qubits:
                for qb in qureg:
                    # Check if a mapper assigned a different logical id
                    logical_id_tag = None
                    for tag in cmd.tags:
                        if isinstance(tag, LogicalQubitIDTag):
                            logical_id_tag = tag
                    if logical_id_tag is not None:
                        qb = WeakQubitRef(qb.engine, logical_id_tag.logical_qubit_id)
                    self.main_engine.set_measurement_result(qb, out[i])
                    i += 1
        elif cmd.gate == Allocate:
            qubit_id = cmd.qubits[0][0].id
            self._simulator.allocate_qubit(qubit_id)
        elif cmd.gate == Deallocate:
            qubit_id = cmd.qubits[0][0].id
            self._simulator.deallocate_qubit(qubit_id)
        elif isinstance(cmd.gate, BasicMathGate):
            # improve performance by using C++ code for some commomn gates
            from projectq.libs.math import (  # pylint: disable=import-outside-toplevel
                AddConstant,
                AddConstantModN,
                MultiplyByConstantModN,
            )

            qubitids = []
            for qureg in cmd.qubits:
                qubitids.append([])
                for qb in qureg:
                    qubitids[-1].append(qb.id)
            if FALLBACK_TO_PYSIM:
                math_fun = cmd.gate.get_math_function(cmd.qubits)
                self._simulator.emulate_math(math_fun, qubitids, [qb.id for qb in cmd.control_qubits])
            else:
                # Individual code for different standard gates to make it
                # faster!
                if isinstance(cmd.gate, AddConstant):
                    self._simulator.emulate_math_addConstant(cmd.gate.a, qubitids, [qb.id for qb in cmd.control_qubits])
                elif isinstance(cmd.gate, AddConstantModN):
                    self._simulator.emulate_math_addConstantModN(
                        cmd.gate.a,
                        cmd.gate.N,
                        qubitids,
                        [qb.id for qb in cmd.control_qubits],
                    )
                elif isinstance(cmd.gate, MultiplyByConstantModN):
                    self._simulator.emulate_math_multiplyByConstantModN(
                        cmd.gate.a,
                        cmd.gate.N,
                        qubitids,
                        [qb.id for qb in cmd.control_qubits],
                    )
                else:
                    math_fun = cmd.gate.get_math_function(cmd.qubits)
                    self._simulator.emulate_math(math_fun, qubitids, [qb.id for qb in cmd.control_qubits])
        elif isinstance(cmd.gate, TimeEvolution):
            op = [(list(term), coeff) for (term, coeff) in cmd.gate.hamiltonian.terms.items()]
            time = cmd.gate.time
            qubitids = [qb.id for qb in cmd.qubits[0]]
            ctrlids = [qb.id for qb in cmd.control_qubits]
            self._simulator.emulate_time_evolution(op, time, qubitids, ctrlids)
        elif len(cmd.gate.matrix) <= 2 ** 5:
            matrix = cmd.gate.matrix
            ids = [qb.id for qureg in cmd.qubits for qb in qureg]
            if not 2 ** len(ids) == len(cmd.gate.matrix):
                raise Exception(
                    "Simulator: Error applying {} gate: "
                    "{}-qubit gate applied to {} qubits.".format(
                        str(cmd.gate), int(math.log(len(cmd.gate.matrix), 2)), len(ids)
                    )
                )
            self._simulator.apply_controlled_gate(
                [item for sublist in matrix.tolist() for item in sublist], ids, [qb.id for qb in cmd.control_qubits]
            )

            if not self._gate_fusion:
                self._simulator.run()
        else:
            raise Exception(
                "This simulator only supports controlled k-qubit"
                " gates with k < 6!\nPlease add an auto-replacer"
                " engine to your list of compiler engines."
            )

    def receive(self, command_list):
        """
        Receive a list of commands.

        Receive a list of commands from the previous engine and handle them (simulate them classically) prior to
        sending them on to the next engine.

        Args:
            command_list (list<Command>): List of commands to execute on the simulator.
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._handle(cmd)
            else:
                self._simulator.run()  # flush gate --> run all saved gates
            if not self.is_last_engine:
                self.send([cmd])
