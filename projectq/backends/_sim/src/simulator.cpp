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

#include "simulator.hpp"

#include "simbackends.hpp"

Simulator::Simulator(unsigned seed)
    : N_(0)
    , vec_(1, 0.)
    , fusion_qubits_min_(4)
    , fusion_qubits_max_(max_qubit_num_)
    , rnd_eng_(seed)
    , backend_type_(backends::SimBackend::Unknown)
    , backend_kernel_(nullptr)
{
    vec_[0] = 1.;  // all-zero initial state
    std::uniform_real_distribution<double> dist(0., 1.);
    rng_ = [this, dist]() mutable { return dist(rnd_eng_); };

    select_backend(backends::SimBackendGetEnv());
}

void Simulator::select_backend(backends::SimBackend backend)
{
    pybind11::module_ module = backends::SimBackendAcquire(backend);
    backend_kernel_ = reinterpret_cast<backend_kernel_t*>(pybind11::cast<void*>(module.attr("kernel")()));
    backend_type_ = backend;
}

void Simulator::run()
{
    if (fused_gates_.size() < 1UL) {
        return;
    }

    fusion::Fusion::Matrix m;
    fusion::Fusion::IndexVector ids;
    fusion::Fusion::IndexVector ctrls;

    fused_gates_.perform_fusion(m, ids, ctrls);

    if (ids.size() > max_qubit_num_) {
        throw std::invalid_argument("Gates with more than 5 qubits are not supported!");
    }

    for (auto& id: ids) {
        id = map_[id];
    }

    // Pad with zeros.
    unsigned nids = ids.size();
    ids.resize(max_qubit_num_);

    auto ctrlmask = get_control_mask(ctrls);

    backend_kernel_(vec_, m, ctrlmask, ids, nids);

    fused_gates_ = fusion::Fusion();
}

Simulator::StateVector Simulator::tmpBuff1_;  // NOLINT(cppcoreguidelines-avoid-non-const-global-variables)
Simulator::StateVector Simulator::tmpBuff2_;  // NOLINT(cppcoreguidelines-avoid-non-const-global-variables)
