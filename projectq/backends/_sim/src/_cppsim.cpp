// Copyright 2017 ProjectQ-Framework (www.projectq.ch)
// Copyright 2021 <Huawei Technologies Co., Ltd>
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "simulator.hpp"
#include "types.hpp"

#include <pybind11/cast.h>
#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>

#include <complex>
#include <vector>

namespace py = pybind11;

using QuRegs = std::vector<std::vector<unsigned>>;

template <class QR>
void emulate_math_wrapper(Simulator& sim, py::function const& pyfunc, QR const& qr, std::vector<unsigned> const& ctrls)
{
    auto f = [&](std::vector<int>& x) {
        pybind11::gil_scoped_acquire acquire;
        x = pyfunc(x).cast<std::vector<int>>();
    };
    pybind11::gil_scoped_release release;
    sim.emulate_math(f, qr, ctrls);
}

// NOLINTNEXTLINE
PYBIND11_MODULE(_cppsim, m)
{
    m.doc() = "C++ simulator backend for ProjectQ";

    py::class_<Simulator>(m, "Simulator")
        .def(py::init<unsigned>())
        .def("allocate_qubit", &Simulator::allocate_qubit)
        .def("deallocate_qubit", &Simulator::deallocate_qubit)
        .def("get_classical_value", &Simulator::get_classical_value)
        .def("is_classical", &Simulator::is_classical)
        .def("measure_qubits", &Simulator::measure_qubits_return)
        .def("apply_controlled_gate", &Simulator::apply_controlled_gate<types::M>)
        .def("emulate_math", &emulate_math_wrapper<QuRegs>)
        .def("emulate_math_addConstant", &Simulator::emulate_math_addConstant<QuRegs>)
        .def("emulate_math_addConstantModN", &Simulator::emulate_math_addConstantModN<QuRegs>)
        .def("emulate_math_multiplyByConstantModN", &Simulator::emulate_math_multiplyByConstantModN<QuRegs>)
        .def("get_expectation_value", &Simulator::get_expectation_value)
        .def("apply_qubit_operator", &Simulator::apply_qubit_operator)
        .def("emulate_time_evolution", &Simulator::emulate_time_evolution)
        .def("get_probability", &Simulator::get_probability)
        .def("get_amplitude", &Simulator::get_amplitude)
        .def("set_wavefunction", &Simulator::set_wavefunction)
        .def("collapse_wavefunction", &Simulator::collapse_wavefunction)
        .def("run", &Simulator::run)
        .def("cheat", &Simulator::cheat)
        .def("select_backend", &Simulator::select_backend);

    py::enum_<backends::SimBackend>(m, "SimBackend")
        .value("Unknown", backends::SimBackend::Unknown)
        .value("Auto", backends::SimBackend::Auto)
        .value("ScalarSerial", backends::SimBackend::ScalarSerial)
        .value("ScalarThreaded", backends::SimBackend::ScalarThreaded)
        .value("VectorSerial", backends::SimBackend::VectorSerial)
        .value("VectorThreaded", backends::SimBackend::VectorThreaded)
        .value("OffloadNVIDIA", backends::SimBackend::OffloadNVIDIA)
        .value("OffloadIntel", backends::SimBackend::OffloadIntel);
}
