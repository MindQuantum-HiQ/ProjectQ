//   Copyright 2021 <Huawei Technologies Co., Ltd>
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.

#ifndef SIMBACKENDS_HPP
#define SIMBACKENDS_HPP

#include <pybind11/pybind11.h>

#include <cstdlib>

namespace backends
{
    // SIM backends
    enum class SimBackend
    {
        Unknown = -1,    // Unknown or unsupported backend
        Auto = 0,        // Best choice for the current system
        ScalarSerial,    // Scalar instructions, single-threaded
        ScalarThreaded,  // Scalar instructions, multi-threaded
        VectorSerial,    // Vector instructions, single-threaded
        VectorThreaded,  // Vector instructions, multi-threaded
        OffloadNVIDIA,   // Offload to NVIDIA GPU
        OffloadIntel,    // Offload to Intel GPU
    };

    // Read SIM backend from the environment variable.
    SimBackend SimBackendGetEnv();

    // Automatically select the most suitable SIM backend for the current machine.
    SimBackend SimBackendGetAuto();

    // Check whether the SIM backend is actually supported by the current version.
    bool SimBackendIsSupported(SimBackend backend);

    // Check whether the SIM backend is available to the current process.
    bool SimBackendIsAvailable(SimBackend backend);

    // Acquire the Python module for the given backend
    pybind11::module_ SimBackendAcquire(SimBackend backend);
}  // namespace backends

#endif /* SIMBACKENDS_HPP */
