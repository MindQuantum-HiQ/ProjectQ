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

#include "simbackends.hpp"

#include "debug_info.hpp"
#include "instrset.hpp"

#include <string>
#ifdef HIQ_WITH_CUDA
#    include <cuda_runtime_api.h>
#endif

// Read SIM backend from the environment variable.
backends::SimBackend backends::SimBackendGetEnv()
{
    const char* cenv = getenv("SIM_BACKEND");  // NOLINT(concurrency-mt-unsafe)
    if (cenv == nullptr) {
        return SimBackend::Auto;
    }

    const std::string env = cenv;
    if (env == "AUTO") {
        return SimBackend::Auto;
    }
    if (env == "SCALAR_SERIAL") {
        return SimBackend::ScalarSerial;
    }
    if (env == "SCALAR_THREADED") {
        return SimBackend::ScalarThreaded;
    }
    if (env == "VECTOR_SERIAL") {
        return SimBackend::VectorSerial;
    }
    if (env == "VECTOR_THREADED") {
        return SimBackend::VectorThreaded;
    }
    if (env == "OFFLOAD_NVIDIA") {
        return SimBackend::OffloadNVIDIA;
    }
    if (env == "OFFLOAD_INTEL") {
        return SimBackend::OffloadIntel;
    }

    return SimBackend::Unknown;
}

// Automatically select the most suitable SIM backend for the current machine.
backends::SimBackend backends::SimBackendGetAuto()
{
    // If NVIDIA GPU is available, select SimBackend::OffloadNVIDIA
    // TODO(dmitry) Make the selection to actually depend on the problem size (need to propagate it here).
    if (SimBackendIsAvailable(SimBackend::OffloadNVIDIA)) {
        return SimBackend::OffloadNVIDIA;
    }

    // If AVX2 is available, select SimBackend::VectorThreaded
    if (SimBackendIsAvailable(SimBackend::VectorThreaded)) {
        return SimBackend::VectorThreaded;
    }

    // If no any better option, select SimBackend::ScalarThreaded
    return SimBackend::ScalarThreaded;
}

// Check whether the SIM backend is actually supported by the current version.
bool backends::SimBackendIsSupported(SimBackend backend)
{
    switch (backend) {
        case SimBackend::ScalarSerial:
        case SimBackend::ScalarThreaded:
            return true;
        case SimBackend::VectorSerial:
        case SimBackend::VectorThreaded:
            return isSupported(agner::InstrSet::AVX2);
        case SimBackend::OffloadNVIDIA:
#ifdef HIQ_WITH_CUDA
            return true;
#endif
        case SimBackend::OffloadIntel:
        case SimBackend::Auto:
        case SimBackend::Unknown:
        default:
            return false;
    }

    return false;
}

// Check whether the SIM backend is available to the current process.
bool backends::SimBackendIsAvailable(SimBackend backend)
{
    if (backend == SimBackend::OffloadNVIDIA) {
        int ngpus = 0;
#ifdef HIQ_WITH_CUDA
        // NOTE A user may want to make a GPU ariticially invisiable to us
        // by leveraging CUDA_VISIBLE_DEVICES env.
        cudaGetDeviceCount(&ngpus);
#endif
        return (ngpus > 0);
    }

    return SimBackendIsSupported(backend);
}

// Acquire the Python module for the given backend
pybind11::module_ backends::SimBackendAcquire(SimBackend backend)  // NOLINT(misc-no-recursion)
{
    std::string backendName;
    switch (backend) {
        case SimBackend::Auto:
            return SimBackendAcquire(SimBackendGetAuto());
        case SimBackend::ScalarSerial:
            backendName = "_cppsim_scalar_serial";
            break;
        case SimBackend::ScalarThreaded:
            backendName = "_cppsim_scalar_threaded";
            break;
        case SimBackend::VectorSerial:
            backendName = "_cppsim_vector_serial";
            break;
        case SimBackend::VectorThreaded:
            backendName = "_cppsim_vector_threaded";
            break;
        case SimBackend::OffloadNVIDIA:
#ifdef HIQ_WITH_CUDA
            backendName = "_cppsim_offload_nvidia";
#else
            throw pybind11::value_error("Python module was not compiled with CUDA support enabled!");
#endif
            break;
        case SimBackend::OffloadIntel:
            throw pybind11::value_error("Python module was not compiled with DPC++ support enabled!");

        case SimBackend::Unknown:
        default:
            throw pybind11::value_error("Could not acquire an unsupported _sim backend");
    }

    debug::printf("Using '%s' backend\n", backendName.c_str());

    // Import backend as a python module (to avoid platform-specific dlopen() stuff)
    try {
        return pybind11::module_::import(backendName.c_str());
    }
    catch (pybind11::error_already_set& ex) {
        if (!ex.matches(PyExc_ImportError)) {
            throw;
        }
        backendName = "projectq.backends._sim." + backendName;
        debug::printf("Using '%s' backend\n", backendName.c_str());
        return pybind11::module_::import(backendName.c_str());
    }
}
