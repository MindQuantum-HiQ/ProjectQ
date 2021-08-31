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

#ifndef VECTOR_KERNEL2_HPP
#define VECTOR_KERNEL2_HPP

#include "utils.hpp"

namespace details
{
    class kernel2
    {
    public:
        template <class V, class M, typename UINT, typename D>
        static inline void core(V &psi, UINT I, const D d, M const &m_tuple)
        {
            const auto &[m, mt] = m_tuple;

            intrin_t v[4];

            v[0] = load2(&psi[I]);
            v[1] = load2(&psi[I + d[0]]);
            v[2] = load2(&psi[I + d[1]]);
            v[3] = load2(&psi[I + d[0] + d[1]]);

            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d[0]]), reinterpret_cast<double *>(&psi[I]),
                add(mul(v[0], m[0], mt[0]),
                    add(mul(v[1], m[1], mt[1]), add(mul(v[2], m[2], mt[2]), mul(v[3], m[3], mt[3])))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d[0] + d[1]]), reinterpret_cast<double *>(&psi[I + d[1]]),
                add(mul(v[0], m[4], mt[4]),
                    add(mul(v[1], m[5], mt[5]), add(mul(v[2], m[6], mt[6]), mul(v[3], m[7], mt[7])))));
        }

        template <typename M>
        static inline auto create_m(M const &m)
        {
            constexpr auto N = 1U << 2U;
            return utils::intrin_array<8>{
                load(&at<N>(m, 0, 0), &at<N>(m, 1, 0)), load(&at<N>(m, 0, 1), &at<N>(m, 1, 1)),
                load(&at<N>(m, 0, 2), &at<N>(m, 1, 2)), load(&at<N>(m, 0, 3), &at<N>(m, 1, 3)),
                load(&at<N>(m, 2, 0), &at<N>(m, 3, 0)), load(&at<N>(m, 2, 1), &at<N>(m, 3, 1)),
                load(&at<N>(m, 2, 2), &at<N>(m, 3, 2)), load(&at<N>(m, 2, 3), &at<N>(m, 3, 3))};
        }

        // bit indices id[.] are given from high to low (e.g. control first for CNOT)
        template <class V, class M, typename UINT, int CTRLMASK>
        static inline void dispatch(V &psi, M const &m, UINT ctrlmask, const unsigned *id)
        {
            kernel_dispatch<2, kernel2, CTRLMASK>(psi, m, ctrlmask, id);
        }
    };
}  // namespace details

#endif /* VECTOR_KERNEL2_HPP */
