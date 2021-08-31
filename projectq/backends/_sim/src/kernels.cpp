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

#include "cintrin.hpp"
#include "debug_info.hpp"
#include "dispatch.hpp"
#include "kernel1.hpp"
#include "kernel2.hpp"
#include "kernel3.hpp"
#include "kernel4.hpp"
#include "kernel5.hpp"
#include "types.hpp"

#include <pybind11/pybind11.h>

#include <array>
#include <functional>

template <class V, class M, typename UINT>
using Kernel = std::function<void(V&, M const&, UINT, const unsigned*)>;

template <class V, class M, typename UINT>
static const std::array<std::array<Kernel<V, M, UINT>, 2>, 5> kernels{
    {{{details::kernel1::dispatch<V, M, UINT, 0>, details::kernel1::dispatch<V, M, UINT, 1>}},
     {{details::kernel2::dispatch<V, M, UINT, 0>, details::kernel2::dispatch<V, M, UINT, 1>}},
     {{details::kernel3::dispatch<V, M, UINT, 0>, details::kernel3::dispatch<V, M, UINT, 1>}},
     {{details::kernel4::dispatch<V, M, UINT, 0>, details::kernel4::dispatch<V, M, UINT, 1>}},
     {{details::kernel5::dispatch<V, M, UINT, 0>, details::kernel5::dispatch<V, M, UINT, 1>}}}};

using types::M;
using types::UINT;
using types::V;

extern "C" void kernel(V& psi, M const& m, UINT ctrlmask, fusion::Fusion::IndexVector const& ids, unsigned nids)
{
    debug::printf("kernel%d\n", static_cast<int>(nids));

    // NOLINTNEXTLINE
    kernels<V, M, UINT>[nids - 1][ctrlmask == 0 ? 0 : 1](psi, m, ctrlmask, &ids[0]);
}

// NOLINTNEXTLINE
PYBIND11_MODULE(MODULE_NAME, m)
{
    m.doc() = "C++ simulator backend specialization for ProjectQ";
    m.def("kernel", []() { return reinterpret_cast<void*>(&kernel); });  // NOLINT
}
