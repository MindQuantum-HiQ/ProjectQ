# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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

"""Contains the main engine of every compiler engine pipeline, called MainEngine."""

import operator as op
from copy import deepcopy

from pyparsing import (
    CharsNotIn,
    Empty,
    Group,
    Literal,
    OneOrMore,
    Optional,
    Or,
    Suppress,
    Word,
    ZeroOrMore,
    alphanums,
    alphas,
    cppStyleComment,
    cStyleComment,
    dblQuotedString,
    nestedExpr,
    pyparsing_common,
    removeQuotes,
)

from projectq.ops import All, Measure

from ._pyparsing_expr import eval_expr
from ._qiskit_conv import gates_conv_table
from ._utils import OpaqueGate, apply_gate

# ==============================================================================

_QISKIT_VARS = {}
_BITS_VARS = {}
_CUSTOM_GATES = {}
_OPAQUE_GATES = {}


class CommonTokens:
    """Some general tokens."""

    # pylint: disable = too-few-public-methods

    int_v = pyparsing_common.signed_integer
    float_v = pyparsing_common.fnumber
    string_v = dblQuotedString().setParseAction(removeQuotes)

    # variable names
    cname = Word(alphas + "_", alphanums + '_')

    lbra, rbra = map(Suppress, "[]")

    # variable expressions (e.g. qubit[0])
    variable_expr = Group(cname + Optional(lbra + int_v + rbra))


# ==============================================================================


class QASMVersionOp:
    """OpenQASM version."""

    def __init__(self, toks):
        """
        Initialize an QASMVersionOp oject.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        self.version = toks[0]

    def eval(self, _):
        """
        Evaluate a QASMVersionOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        # pylint: disable=unused-argument

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        return 'QASMVersionOp({})'.format(self.version)


class IncludeOp:
    """Include file operation."""

    def __init__(self, toks):
        """
        Initialize an IncludeOp object.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        self.fname = toks[0]

    def eval(self, _):
        """
        Evaluate an IncludeOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        if self.fname in 'qelib1.inc, stdlib.inc':
            pass
        else:  # pragma: nocover
            raise RuntimeError('Invalid cannot read: {}! (unsupported)'.format(self.fname))

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        return 'IncludeOp({})'.format(self.fname)


# ==============================================================================


class QubitProxy:
    """Qubit access proxy class."""

    def __init__(self, toks):
        """
        Initialize a QubitProxy object.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        if len(toks) == 2:
            self.name = str(toks[0])
            self.index = int(toks[1])
        else:
            self.name = toks[0]
            self.index = None

    def eval(self, _):
        """
        Evaluate a QubitProxy.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        if self.index is not None:
            return _QISKIT_VARS[self.name][self.index]
        return _QISKIT_VARS[self.name]

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        if self.index is not None:
            return 'Qubit({}[{}])'.format(self.name, self.index)
        return 'Qubit({})'.format(self.name)


# ==============================================================================


class VarDeclOp:
    """Variable declaration operation."""

    # pylint: disable = too-few-public-methods

    def __init__(self, type_t, nbits, name, init):
        """
        Initialize a VarDeclOp object.

        Args:
            type_t (str): Type of variable
            nbits (int): Number of bits in variable
            name (str): Name of variable
            init (str): Initialization expression for variable
        """
        self.type_t = type_t
        self.nbits = nbits
        self.name = name
        self.init = init

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        if self.init:
            return "{}({}, {}, {}) = {}".format(self.__class__.__name__, self.type_t, self.nbits, self.name, self.init)

        return "{}({}, {}, {})".format(self.__class__.__name__, self.type_t, self.nbits, self.name)


# ------------------------------------------------------------------------------


class QVarOp(VarDeclOp):
    """Quantum variable declaration operation."""

    # pylint: disable = too-few-public-methods

    def eval(self, eng):
        """
        Evaluate a QVarOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        if self.name not in _QISKIT_VARS:
            _QISKIT_VARS[self.name] = eng.allocate_qureg(self.nbits)
        else:  # pragma: nocover
            raise RuntimeError('Variable exist already: {}'.format(self.name))


# ------------------------------------------------------------------------------


class CVarOp(VarDeclOp):
    """Classical variable declaration operation."""

    # pylint: disable = too-few-public-methods

    def eval(self, _):
        """
        Evaluate a CVarOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        # NB: here we are cheating a bit, since we are ignoring the number of
        # bits, except for classical registers...
        if self.name not in _BITS_VARS:
            init = 0
            if self.init:  # pragma: nocover
                init = parse_expr(self.init)

            # The followings are OpenQASM 3.0
            if self.type_t in ('const', 'float', 'fixed', 'angle'):  # pragma: nocover
                _BITS_VARS[self.name] = float(init)
            elif self.type_t in ('int', 'uint'):  # pragma: nocover
                _BITS_VARS[self.name] = int(init)
            elif self.type_t == 'bool':  # pragma: nocover
                _BITS_VARS[self.name] = bool(init)
            else:
                # bit, creg
                if self.init is not None:
                    raise RuntimeError('Type of {} variable does not support initialization'.format(self.name))
                _BITS_VARS[self.name] = [False] * self.nbits
        else:  # pragma: nocover
            raise RuntimeError('Variable exist already: {}'.format(self.name))


# ==============================================================================


class GateDefOp:
    """Operation representing a gate definition."""

    def __init__(self, toks):
        """
        Initialize a GateDefOp object.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        self.name = toks[1]
        self.params = [t[0] for t in toks[2]]
        self.qparams = list(toks[3])
        self.body = list(toks[4])
        if not self.body:
            self.body = []

    def eval(self, _):
        """
        Evaluate a GateDefOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        _CUSTOM_GATES[self.name] = (self.params, self.qparams, self.body)

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        return "GateDefOp({}, {}, {})\n\t{}".format(self.name, self.params, self.qparams, self.body)


# ==============================================================================


class MeasureOp:
    """Measurement operations (OpenQASM 2.0 & 3.0)."""

    def __init__(self, toks):
        """
        Initialize a MeasureOp object.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        if toks[1] == 'measure':  # pragma: nocover
            # OpenQASM 3.0
            self.qubits = QubitProxy(toks[2])
            self.bits = tuple(toks[0])
        elif toks[0] == 'measure':
            # OpenQASM 2.0
            self.qubits = QubitProxy(toks[1])
            self.bits = tuple(toks[2])
        else:  # pragma: nocover
            raise RuntimeError('Unable to normalize measurement operation!')

    def eval(self, eng):
        """
        Evaluate a MeasureOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        # pylint: disable = pointless-statement, expression-not-assigned
        # pylint: disable = global-statement

        global _BITS_VARS

        qubits = self.qubits.eval(eng)
        if not isinstance(qubits, list):
            Measure | qubits
        else:
            All(Measure) | qubits
        eng.flush()

        if not isinstance(qubits, list):
            if len(self.bits) == 1:
                _BITS_VARS[self.bits[0]][0] = bool(qubits)
            else:
                _BITS_VARS[self.bits[0]][self.bits[1]] = bool(qubits)
        else:
            bits = _BITS_VARS[self.bits[0]]
            for idx, qubit in enumerate(qubits):
                bits[idx] = bool(qubit)

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        return 'MeasureOp({}, {})'.format(self.qubits, self.bits)


# ------------------------------------------------------------------------------


class OpaqueDefOp:
    """Opaque gate definition operation."""

    def __init__(self, toks):
        """
        Initialize an OpaqueDefOp object.

        Args:
            name (str): Name/type of gat
            params (list,tuple): Parameter for the gate (may be empty)
            qubits (list): List of target qubits
        """
        self.name = toks[1]
        self.params = toks[2]

    def eval(self, _):
        """
        Evaluate a OpaqueDefOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        _OPAQUE_GATES[self.name] = OpaqueGate(self.name, self.params)

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        if self.params:
            return 'OpaqueOp({}, {})'.format(self.name, self.params)
        return 'OpaqueOp({})'.format(self.name)


# ------------------------------------------------------------------------------


class GateOp:
    """Gate applied to qubits operation."""

    def __init__(self, s, loc, toks):
        """
        Initialize a GateOp object.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        self.name = toks[0]
        if len(toks) == 2:
            self.params = []
            self.qubits = [QubitProxy(qubit) for qubit in toks[1]]
        else:
            param_str = s[loc : s.find(';', loc)]  # noqa: E203
            self.params = param_str[param_str.find('(') + 1 : param_str.rfind(')')].split(',')  # noqa: E203
            self.qubits = [QubitProxy(qubit) for qubit in toks[2]]

    def eval(self, eng):  # pylint: disable=too-many-branches
        """
        Evaluate a GateOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        if self.name in gates_conv_table:
            gate = gates_conv_table[self.name](*[parse_expr(p) for p in self.params])

            qubits = []
            for qureg in [qubit.eval(eng) for qubit in self.qubits]:
                try:
                    qubits.extend(qureg)
                except TypeError:
                    qubits.append(qureg)

            apply_gate(gate, qubits)
        elif self.name in _OPAQUE_GATES:
            qubits = []
            for qureg in [qubit.eval(eng) for qubit in self.qubits]:
                try:
                    qubits.extend(qureg)
                except TypeError:
                    qubits.append(qureg)

            apply_gate(_OPAQUE_GATES[self.name], qubits)
        elif self.name in _CUSTOM_GATES:
            gate_params, gate_qparams, gate_body = _CUSTOM_GATES[self.name]

            if self.params:
                if len(self.params) != len(gate_params):
                    raise RuntimeError('The number of parameters passed to the gate {} is wrong'.format(self.name))

            params_map = {p_param: p_var for p_var, p_param in zip(self.params, gate_params)}
            qparams_map = {q_param: q_var for q_var, q_param in zip(self.qubits, gate_qparams)}

            # NB: this is a hack...
            #     Will probably not work for multiple expansions of variables...
            # pylint: disable = global-statement
            global _BITS_VARS
            bits_vars_bak = deepcopy(_BITS_VARS)
            _BITS_VARS.update(params_map)

            for gate in gate_body:
                # Map gate parameters and quantum parameters to real variables
                gate.qubits = [qparams_map[q.name] for q in gate.qubits]
                gate.eval(eng)
            _BITS_VARS = bits_vars_bak
        else:  # pragma: nocover
            if self.params:
                gate_str = '{}({}) | {}'.format(self.name, self.params, self.qubits)
            else:
                gate_str = '{} | {}'.format(self.name, self.qubits)
            raise RuntimeError('Unknown gate: {}'.format(gate_str))

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        return 'GateOp({}, {}, {})'.format(self.name, self.params, self.qubits)


# ==============================================================================


class AssignOp:  # pragma: nocover
    """Variable assignment operation (OpenQASM 3.0 only)."""

    def __init__(self, toks):
        """
        Initialize an AssignOp object.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        self.var = toks[0]
        self.value = toks[1][0]

    def eval(self, _):
        """
        Evaluate an AssignOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        if self.var in _BITS_VARS:
            # Assigning to creg or bit is not supported yet...
            if isinstance(_BITS_VARS[self.var], list):
                raise RuntimeError('Assignment operations on classical registers not yet supported!')
            value = parse_expr(self.value)
            _BITS_VARS[self.var] = value
        else:
            raise RuntimeError('The variable {} is not defined!'.format(self.var))
        return 0

    def __repr__(self):
        """Mainly for debugging purposes."""
        return 'AssignOp({},{})'.format(self.var, self.value)


# ==============================================================================


def _parse_if_conditional(if_str):
    # pylint: disable = invalid-name
    start = if_str.find('(') + 1

    level = 1
    for idx, ch in enumerate(if_str[start:]):
        if ch == '(':  # pragma: nocover
            # NB: only relevant for OpenQASM 3.0
            level += 1
        elif ch == ')':
            level -= 1
        if level == 0:
            return if_str[start : start + idx]  # noqa: E203
    raise RuntimeError('Unbalanced parantheses in {}'.format(if_str))  # pragma: nocover


class IfOp:
    """Operation representing a conditional expression (if-expr)."""

    greater = Literal('>').addParseAction(lambda: op.gt)
    greater_equal = Literal('>=').addParseAction(lambda: op.ge)
    less = Literal('<').addParseAction(lambda: op.lt)
    less_equal = Literal('<=').addParseAction(lambda: op.le)
    equal = Literal('==').addParseAction(lambda: op.eq)
    not_equal = Literal('!=').addParseAction(lambda: op.ne)

    logical_bin_op = Or([greater, greater_equal, less, less_equal, equal, not_equal])

    cond_expr = CommonTokens.variable_expr.copy() + logical_bin_op + CharsNotIn('()')

    def __init__(self, if_str, loc, toks):
        """
        Initialize an IfOp object.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        # pylint: disable=unused-argument

        cond = _parse_if_conditional(if_str[loc:])
        res = IfOp.cond_expr.parseString(cond, parseAll=True)
        self.binary_op = res[1]
        self.comp_expr = res[2]
        self.body = toks[2:]

        if len(res[0]) == 1:
            self.bit = res[0][0]
        else:  # pragma: nocover
            # OpenQASM >= 3.0 only
            name, index = res[0]
            self.bit = (name, index)

    def eval(self, eng):
        """
        Evaluate an IfOp.

        Args:
            eng (projectq.BasicEngine): ProjectQ MainEngine to use
        """
        if isinstance(self.bit, tuple):  # pragma: nocover
            # OpenQASM >= 3.0 only
            bit = _BITS_VARS[self.bit[0]][self.bit[1]]
        else:
            bit_val = _BITS_VARS[self.bit]
            if isinstance(bit_val, list) and len(bit_val) > 1:
                bit = 0
                for bit_el in reversed(bit_val):
                    bit = (bit << 1) | bit_el
            else:
                bit = bit_val[0]

        if self.binary_op(bit, parse_expr(self.comp_expr)):
            for gate in self.body:
                gate.eval(eng)

    def __repr__(self):  # pragma: nocover
        """Mainly for debugging purposes."""
        return "IfExpr({} {} {}) {{ {} }}".format(self.bit, self.binary_op, self.comp_expr, self.body)


# ==============================================================================


def create_var_decl(toks):
    """
    Create either a classical or a quantum variable operation.

    Args:
        toks (pyparsing.Tokens): Pyparsing tokens
    """
    type_t = toks[0]

    names = []
    nbits = 1
    body = None

    if len(toks) == 3:  # pragma: nocover
        # OpenQASM >= 3.0 only
        # qubit[NN] var, var, var;
        # fixed[7, 25] num;
        names = toks[2]
        nbits = toks[1]
        var_list = []

        def _get_name(name):
            return name

        def _get_nbits(_):
            return nbits

    elif len(toks) == 2:
        # qubit qa, qb[2], qc[3];
        names = toks[1]

        def _get_name(name):
            return name[0]

        def _get_nbits(name):
            if len(name) == 1:  # pragma: nocover
                # OpenQASM >= 3.0 only
                return 1
            return name[1]

    else:  # pragma: nocover
        # OpenQASM >= 3.0 only
        # const myvar = 1234;
        names = [toks[2]]
        nbits = toks[1]
        body = toks[3][0]

        def _get_name(name):
            return name

        def _get_nbits(_):
            return nbits

    var_list = []
    for name in names:
        if type_t in ('const', 'creg', 'bit', 'uint', 'int', 'fixed', 'float', 'angle', 'bool'):
            var_list.append(CVarOp(type_t, _get_nbits(name), _get_name(name), body))
        elif body is None:
            var_list.append(QVarOp(type_t, _get_nbits(name), _get_name(name), body))
        else:  # pragma: nocover
            raise RuntimeError('Initializer for quantum variable is unsupported!')

    return var_list


def parse_expr(expr_str):
    """
    Parse a (mathematical) expression.

    Args:
        expr_str (str): Expression to evaluate
    """
    return eval_expr(expr_str, _BITS_VARS)


# ==============================================================================


class QiskitParser:
    """Qiskit parser class."""

    def __init__(self):
        """Initialize a QiskitParser object."""
        # pylint: disable = too-many-locals
        # ----------------------------------------------------------------------
        # Punctuation marks

        lpar, rpar, lbra, rbra, lbrace, rbrace = map(Suppress, "()[]{}")
        equal_sign, comma, end = map(Suppress, "=,;")

        # ----------------------------------------------------------------------
        # Quantum and classical types

        qubit_t = Literal("qubit") ^ Literal("qreg")
        bit_t = Literal("bit") ^ Literal("creg")
        bool_t = Literal("bool")
        const_t = Literal("const")
        int_t = Literal("int")
        uint_t = Literal("uint")
        angle_t = Literal("angle")
        fixed_t = Literal("fixed")
        float_t = Literal("float")

        # ----------------------------------------------------------------------
        # Other core types

        cname = CommonTokens.cname.copy()
        float_v = CommonTokens.float_v.copy()
        int_v = CommonTokens.int_v.copy()
        string_v = CommonTokens.string_v.copy()

        # ----------------------------------------------------------------------
        # Variable type matching

        # Only match an exact type
        var_type = Or([qubit_t, bit_t, bool_t, const_t, int_t, uint_t, angle_t, float_t])

        # Match a type or an array of type (e.g. int vs int[10])
        type_t = (var_type + Optional(lbra + int_v + rbra, default=1)) | (
            fixed_t + Group(lbra + int_v + comma + int_v + rbra)
        )

        # ----------------------------------------------------------------------
        # (mathematical) expressions

        expr = CharsNotIn(',;')
        variable_expr = CommonTokens.variable_expr

        # ----------------------------------------------------------------------
        # Variable declarations

        # e.g. qubit[10] qr, qs / int[5] i, j
        variable_decl_const_bits = type_t + Group(cname + ZeroOrMore(comma + cname))

        # e.g. qubit qr[10], qs[2] / int i[5], j[10]
        variable_decl_var_bits = var_type + Group(variable_expr + ZeroOrMore(comma + variable_expr))

        # e.g. int[10] i = 5;
        variable_decl_assign = type_t + cname + equal_sign + Group(expr)

        # Putting it all together
        variable_decl_statement = Or(
            [variable_decl_const_bits, variable_decl_var_bits, variable_decl_assign]
        ).addParseAction(create_var_decl)

        # ----------------------------------------------------------------------
        # Gate operations

        gate_op_no_param = cname + Group(variable_expr + ZeroOrMore(comma + variable_expr))
        gate_op_w_param = (
            cname + Group(nestedExpr(ignoreExpr=comma)) + Group(variable_expr + ZeroOrMore(comma + variable_expr))
        )

        # ----------------------------------
        # Measure gate operations

        measure_op_qasm2 = Literal("measure") + variable_expr + Suppress("->") + variable_expr
        measure_op_qasm3 = variable_expr + equal_sign + Literal("measure") + variable_expr

        measure_op = (measure_op_qasm2 ^ measure_op_qasm3).addParseAction(MeasureOp)

        # Putting it all together
        gate_op = Or([gate_op_no_param, gate_op_w_param, measure_op]).addParseAction(GateOp)

        # ----------------------------------------------------------------------
        # If expressions

        if_expr_qasm2 = Literal("if") + nestedExpr(ignoreExpr=comma) + gate_op + end

        # NB: not exactly 100% OpenQASM 3.0 conformant...
        if_expr_qasm3 = (
            Literal("if") + nestedExpr(ignoreExpr=comma) + (lbrace + OneOrMore(Group(gate_op + end)) + rbrace)
        )
        if_expr = (if_expr_qasm2 ^ if_expr_qasm3).addParseAction(IfOp)

        assign_op = (cname + equal_sign + Group(expr)).addParseAction(AssignOp)

        # ----------------------------------------------------------------------

        # NB: this is not restrictive enough and may parse some invalid code
        #     such as:
        # gate g a
        # {
        #         U(0,0,0) a[0];  // <- indexing of a is forbidden
        # }

        param_decl_qasm2 = cname
        param_decl_qasm3 = type_t + Suppress(":") + cname

        param_decl = Group(param_decl_qasm2 ^ param_decl_qasm3)

        qargs_list = Group(cname + ZeroOrMore(comma + cname))

        gate_def_no_args = ZeroOrMore(lpar + rpar) + Group(Empty()) + qargs_list
        gate_def_w_args = lpar + Group(param_decl + ZeroOrMore(comma + param_decl)) + rpar + qargs_list
        gate_def_expr = (
            Literal("gate")
            + cname
            + (gate_def_no_args ^ gate_def_w_args)
            + lbrace
            + Group(ZeroOrMore(gate_op + end))
            + rbrace
        ).addParseAction(GateDefOp)

        # ----------------------------------
        # Opaque gate declarations operations

        opaque_def_expr = (Literal("opaque") + cname + (gate_def_no_args ^ gate_def_w_args) + end).addParseAction(
            OpaqueDefOp
        )

        # ----------------------------------------------------------------------

        header = Suppress("OPENQASM") + (int_v ^ float_v).addParseAction(QASMVersionOp) + end

        include = Suppress("include") + string_v.addParseAction(IncludeOp) + end

        statement = (
            (measure_op + end)
            | if_expr
            | (gate_def_expr)
            | opaque_def_expr
            | (variable_decl_statement + end)
            | (assign_op + end)
            | (gate_op + end)
        )

        self.parser = header + ZeroOrMore(include) + ZeroOrMore(statement)
        self.parser.ignore(cppStyleComment)
        self.parser.ignore(cStyleComment)

    def parse_str(self, qasm_str):
        """
        Parse a QASM string.

        Args:
            qasm_str (str): QASM string
        """
        return self.parser.parseString(qasm_str, parseAll=True)

    def parse_file(self, fname):
        """
        Parse a QASM file.

        Args:
            fname (str): Filename
        """
        return self.parser.parseFile(fname, parseAll=True)


def _reset():
    """Reset internal variables."""
    # pylint: disable = invalid-name, global-statement
    global _QISKIT_VARS, _BITS_VARS, _CUSTOM_GATES, _OPAQUE_GATES

    _QISKIT_VARS = {}
    _BITS_VARS = {}
    _CUSTOM_GATES = {}
    _OPAQUE_GATES = {}


# ==============================================================================

parser = QiskitParser()

# ------------------------------------------------------------------------------


def read_qasm_str(eng, qasm_str):
    """
    Read an OpenQASM (2.0, 3.0 is experimental) string and convert it to ProjectQ commands.

    This version of the function uses pyparsing in order to parse the *.qasm file.

    Args:
        eng (MainEngine): MainEngine to use for creating qubits and commands.
        filename (string): Path to *.qasm file

    Note:
        At this time, we support most of OpenQASM 2.0 and some of 3.0,
        although the latter is still experimental.
    """
    _reset()
    for operation in parser.parse_str(qasm_str).asList():
        operation.eval(eng)
    return _QISKIT_VARS, _BITS_VARS


# ------------------------------------------------------------------------------


def read_qasm_file(eng, filename):
    """
    Read an OpenQASM (2.0, 3.0 is experimental) and convert it to ProjectQ Commands.

    This version of the function uses pyparsing in order to parse the *.qasm
    file.

    Args:
        eng (MainEngine): MainEngine to use for creating qubits and commands.
        filename (string): Path to *.qasm file

    Note:
        At this time, we support most of OpenQASM 2.0 and some of 3.0, although the latter is still experimental.

        Also note that we do not try to enforce 100% conformity to the OpenQASM standard while parsing QASM code. The
        parser may allow some syntax that are actually banned by the standard.
    """
    _reset()
    for operation in parser.parse_file(filename).asList():
        operation.eval(eng)
    return _QISKIT_VARS, _BITS_VARS


# ==============================================================================
