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
""" Engine to convert ProjectQ commands to OpenQASM (using qiskit) """

from projectq.cengines import BasicEngine
from projectq.meta import get_control_count
from projectq.ops import (X, NOT, Y, Z, T, Tdag, S, Sdag, H, Ph, R, Rx, Ry, Rz,
                          Swap, Measure, Allocate, Deallocate, Barrier,
                          FlushGate)

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

# ==============================================================================


def _dummy_process(qc):
    pass


# ==============================================================================


class OpenQASMEngine(BasicEngine):
    """
    Engine to convert ProjectQ commands to OpenQASM using qiskit
    """
    def __init__(self,
                 process_func=_dummy_process,
                 qubit_id_mapping_redux=True):
        """
        Initialize the OpenQASMEngine object.

        Args:
            process_func (function): Function to be called periodically to
                process a qiskit.QuantumCircuit. This happens anytime a
                FlushGate gets processed by the engine.
                This function should accept a single argument:
                :py:class:`qiskit.QuantumCircuit`.
            qubit_id_mapping_redux (bool): If True, try to allocate new Qubit
                                           IDs to the next available qreg/creg
                                           (if any), otherwise create a new
                                           qreg/creg.
                                           If False, simply create a new
                                           qreg/creg for each new Qubit ID

        Example:
            .. code-block:: python

                from projectq.cengines import MainEngine, OpenQASMEngine

                backend = OpenQASMEngine()
                eng = MainEngine(backend=backend)
                # do something ...
                eng.flush()
                qc = backend.circuit # get the corresponding Qiskit circuit

        If you have a ProjectQ program with multiple measurements (followed by
        `eng.flush()`) the OpenQASMEngine can automatically generate a list of
        circuits:

        Example:
            .. code-block:: python

                from projectq.cengines import MainEngine, OpenQASMEngine

                qc_list = []
                def process(qc):
                    qc_list.append(qc)

                backend = OpenQASMEngine(process_func=process)
                eng = MainEngine(backend=backend)
                # do something ...
                eng.flush()
                # do something ...
                eng.flush()
                qc_list # contains a list of successive circuits
        """
        BasicEngine.__init__(self)
        self._was_flushed = False
        self._openqasm_circuit = QuantumCircuit()
        self._process_func = process_func
        self._qreg_dict = dict()
        self._creg_dict = dict()
        self._qubit_id_mapping_redux = qubit_id_mapping_redux
        self._reg_index = 0
        self._available_indices = []

    @property
    def circuit(self):
        """
        Return the last OpenQASM circuit stored by this engine

        Note:
            This is essentially the quantum circuit up to the last
            FlushGate. Assuming that no other gate was processed since then.
        """
        return self._openqasm_circuit

    def is_available(self, cmd):
        """
        Return true if the command can be executed.

        Args:
            cmd (Command): Command for which to check availability
        """
        gate = cmd.gate
        n_controls = get_control_count(cmd)

        is_available = False

        if gate in (Measure, Allocate, Deallocate, Barrier):
            is_available = True

        if n_controls == 0:
            if gate in (H, S, Sdag, T, Tdag, X, NOT, Y, Z, Swap):
                is_available = True
            if isinstance(gate, (Ph, R, Rx, Ry, Rz)):
                is_available = True
        elif n_controls == 1:
            if gate in (H, X, NOT, Y, Z):
                is_available = True
            if isinstance(gate, (
                    R,
                    Rz,
            )):
                is_available = True
        elif n_controls == 2:
            if gate in (X, NOT):
                is_available = True

        if not is_available:
            return False
        if not self.is_last_engine:
            return self.next_engine.is_available(cmd)
        else:
            return True

    def _store(self, cmd):
        """
        Temporarily store the command cmd.

        Translates the command and stores it the _openqasm_circuit attribute
        (self._openqasm_circuit)

        Args:
            cmd: Command to store
        """
        gate = cmd.gate
        n_controls = get_control_count(cmd)

        _ccontrolled_gates_func = {
            X: self._openqasm_circuit.ccx,
            NOT: self._openqasm_circuit.ccx,
        }
        _controlled_gates_func = {
            H: self._openqasm_circuit.ch,
            Ph: self._openqasm_circuit.cu1,
            R: self._openqasm_circuit.cu1,
            Rz: self._openqasm_circuit.crz,
            X: self._openqasm_circuit.cx,
            NOT: self._openqasm_circuit.cx,
            Y: self._openqasm_circuit.cy,
            Z: self._openqasm_circuit.cz,
            Swap: self._openqasm_circuit.cswap
        }
        _gates_func = {
            Barrier: self._openqasm_circuit.barrier,
            H: self._openqasm_circuit.h,
            Ph: self._openqasm_circuit.u1,
            S: self._openqasm_circuit.s,
            Sdag: self._openqasm_circuit.sdg,
            T: self._openqasm_circuit.t,
            Tdag: self._openqasm_circuit.tdg,
            R: self._openqasm_circuit.u1,
            Rx: self._openqasm_circuit.rx,
            Ry: self._openqasm_circuit.ry,
            Rz: self._openqasm_circuit.rz,
            X: self._openqasm_circuit.x,
            NOT: self._openqasm_circuit.x,
            Y: self._openqasm_circuit.y,
            Z: self._openqasm_circuit.z,
            Swap: self._openqasm_circuit.swap
        }

        if self._was_flushed:
            self._reset_after_flush()

        if gate == Allocate:
            add = True
            if self._qubit_id_mapping_redux and self._available_indices:
                add = False
                index = self._available_indices.pop()
            else:
                index = self._reg_index
                self._reg_index += 1

            qb_id = cmd.qubits[0][0].id
            self._qreg_dict[qb_id] = QuantumRegister(1, 'q{}'.format(index))
            self._creg_dict[qb_id] = ClassicalRegister(1, 'c{}'.format(index))

            if add:
                self._openqasm_circuit.add_register(self._qreg_dict[qb_id])
                self._openqasm_circuit.add_register(self._creg_dict[qb_id])

        elif gate == Deallocate:
            qb_id = cmd.qubits[0][0].id
            # self._openqasm_circuit.reset(self._qreg_dict[qb_id])

            if self._qubit_id_mapping_redux:
                self._available_indices.append(
                    int(self._qreg_dict[qb_id].name[1:]))
                del self._qreg_dict[qb_id]
                del self._creg_dict[qb_id]

        elif gate == Measure:
            assert len(cmd.qubits) == 1 and len(cmd.qubits[0]) == 1
            qb_id = cmd.qubits[0][0].id
            # self._openqasm_circuit.barrier(self._qreg_dict[qb_id])
            self._openqasm_circuit.measure(self._qreg_dict[qb_id],
                                           self._creg_dict[qb_id])

        elif n_controls == 2:
            targets = [
                self._qreg_dict[qb.id] for qureg in cmd.qubits for qb in qureg
            ]
            controls = [self._qreg_dict[qb.id] for qb in cmd.control_qubits]

            try:
                _ccontrolled_gates_func[gate](*(controls + targets))
            except KeyError:
                raise RuntimeError(
                    'Unable to perform {} gate with n=2 control qubits'.format(
                        gate))

        elif n_controls == 1:
            target_qureg = [
                self._qreg_dict[qb.id] for qureg in cmd.qubits for qb in qureg
            ]

            try:
                if isinstance(gate, Ph):
                    _controlled_gates_func[type(gate)](
                        -gate.angle / 2.,
                        self._qreg_dict[cmd.control_qubits[0].id],
                        target_qureg[0])
                elif isinstance(gate, (
                        R,
                        Rz,
                )):
                    _controlled_gates_func[type(gate)](
                        gate.angle, self._qreg_dict[cmd.control_qubits[0].id],
                        target_qureg[0])
                else:
                    _controlled_gates_func[gate](
                        self._qreg_dict[cmd.control_qubits[0].id],
                        *target_qureg)
            except KeyError as e:
                raise RuntimeError(
                    'Unable to perform {} gate with n=1 control qubits'.format(
                        gate))
        else:
            target_qureg = [
                self._qreg_dict[qb.id] for qureg in cmd.qubits for qb in qureg
            ]
            if isinstance(gate, Ph):
                _gates_func[type(gate)](-gate.angle / 2., target_qureg[0])
            elif isinstance(gate, (R, Rx, Ry, Rz)):
                _gates_func[type(gate)](gate.angle, target_qureg[0])
            else:
                _gates_func[gate](*target_qureg)

    def _reset_after_flush(self):
        """
        Reset the internal quantum circuit after a FlushGate
        """
        self._was_flushed = False
        regs = []
        regs.extend(self._openqasm_circuit.qregs)
        regs.extend(self._openqasm_circuit.cregs)

        self._openqasm_circuit = QuantumCircuit()
        for reg in regs:
            self._openqasm_circuit.add_register(reg)

    def _run(self):
        """
        Run the circuit.
        """
        self._was_flushed = True
        self._process_func(self._openqasm_circuit)

    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until
        completion.

        Args:
            command_list: List of commands to execute
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._store(cmd)
            else:
                self._run()

        if not self.is_last_engine:
            self.send(command_list)
