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

#ifndef VECTOR_KERNEL1_HPP
#define VECTOR_KERNEL1_HPP

#include "utils.hpp"

namespace details
{
    class kernel1
    {
    public:
        template <class V, class M, typename UINT, typename D>
        static inline void core(V &psi, UINT I, const D d, M const &m_tuple)
        {
            const auto &[m, mt] = m_tuple;

            intrin_t v[2];

            v[0] = load2(&psi[I]);
            v[1] = load2(&psi[I + d[0]]);

            _intrin_store_high_low(reinterpret_cast<double *>(&psi[I + d[0]]), reinterpret_cast<double *>(&psi[I]),
                                   add(mul(v[0], m[0], mt[0]), mul(v[1], m[1], mt[1])));
        }

        template <typename M>
        static inline auto create_m(M const &m)
        {
            constexpr auto N = 1U << 1U;
            return utils::intrin_array<2>{load(&at<N>(m, 0, 0), &at<N>(m, 1, 0)),
                                          load(&at<N>(m, 0, 1), &at<N>(m, 1, 1))};
        }

        // bit indices id[.] are given from high to low (e.g. control first for CNOT)
        template <class V, class M, typename UINT, int CTRLMASK>
        static inline void dispatch(V &psi, M const &m, UINT ctrlmask, const unsigned *id)
        {
            kernel_dispatch<1, kernel1, CTRLMASK>(psi, m, ctrlmask, id);
        }
    };

}  // namespace details

#endif /* VECTOR_KERNEL1_HPP */
