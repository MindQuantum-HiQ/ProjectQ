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

#ifndef VECTOR_KERNEL3_HPP
#define VECTOR_KERNEL3_HPP

#include "utils.hpp"

namespace details
{
    class kernel3
    {
    public:
        template <class V, class M, typename UINT, typename D>
        static inline void core(V &psi, UINT I, const D d, M const &m_tuple)
        {
            const auto &[m, mt] = m_tuple;

            const UINT d0 = d[0];
            const UINT d1 = d[1];
            const UINT d2 = d[2];

            intrin_t v[4];

            v[0] = load2(&psi[I]);
            v[1] = load2(&psi[I + d0]);
            v[2] = load2(&psi[I + d1]);
            v[3] = load2(&psi[I + d0 + d1]);

            intrin_t tmp[4];

            tmp[0] = add(mul(v[0], m[0], mt[0]),
                         add(mul(v[1], m[1], mt[1]), add(mul(v[2], m[2], mt[2]), mul(v[3], m[3], mt[3]))));
            tmp[1] = add(mul(v[0], m[4], mt[4]),
                         add(mul(v[1], m[5], mt[5]), add(mul(v[2], m[6], mt[6]), mul(v[3], m[7], mt[7]))));
            tmp[2] = add(mul(v[0], m[8], mt[8]),
                         add(mul(v[1], m[9], mt[9]), add(mul(v[2], m[10], mt[10]), mul(v[3], m[11], mt[11]))));
            tmp[3] = add(mul(v[0], m[12], mt[12]),
                         add(mul(v[1], m[13], mt[13]), add(mul(v[2], m[14], mt[14]), mul(v[3], m[15], mt[15]))));

            v[0] = load2(&psi[I + d2]);
            v[1] = load2(&psi[I + d0 + d2]);
            v[2] = load2(&psi[I + d1 + d2]);
            v[3] = load2(&psi[I + d0 + d1 + d2]);

            _intrin_store_high_low(reinterpret_cast<double *>(&psi[I + d0]), reinterpret_cast<double *>(&psi[I]),
                                   add(tmp[0], add(mul(v[0], m[16], mt[16]),
                                                   add(mul(v[1], m[17], mt[17]),
                                                       add(mul(v[2], m[18], mt[18]), mul(v[3], m[19], mt[19]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d1]), reinterpret_cast<double *>(&psi[I + d1]),
                add(tmp[1],
                    add(mul(v[0], m[20], mt[20]),
                        add(mul(v[1], m[21], mt[21]), add(mul(v[2], m[22], mt[22]), mul(v[3], m[23], mt[23]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d2]), reinterpret_cast<double *>(&psi[I + d2]),
                add(tmp[2],
                    add(mul(v[0], m[24], mt[24]),
                        add(mul(v[1], m[25], mt[25]), add(mul(v[2], m[26], mt[26]), mul(v[3], m[27], mt[27]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d1 + d2]), reinterpret_cast<double *>(&psi[I + d1 + d2]),
                add(tmp[3],
                    add(mul(v[0], m[28], mt[28]),
                        add(mul(v[1], m[29], mt[29]), add(mul(v[2], m[30], mt[30]), mul(v[3], m[31], mt[31]))))));
        }

        template <typename M>
        static inline auto create_m(M const &m)
        {
            constexpr auto N = 1U << 3U;
            return utils::intrin_array<32>{
                load(&at<N>(m, 0, 0), &at<N>(m, 1, 0)), load(&at<N>(m, 0, 1), &at<N>(m, 1, 1)),
                load(&at<N>(m, 0, 2), &at<N>(m, 1, 2)), load(&at<N>(m, 0, 3), &at<N>(m, 1, 3)),
                load(&at<N>(m, 2, 0), &at<N>(m, 3, 0)), load(&at<N>(m, 2, 1), &at<N>(m, 3, 1)),
                load(&at<N>(m, 2, 2), &at<N>(m, 3, 2)), load(&at<N>(m, 2, 3), &at<N>(m, 3, 3)),
                load(&at<N>(m, 4, 0), &at<N>(m, 5, 0)), load(&at<N>(m, 4, 1), &at<N>(m, 5, 1)),
                load(&at<N>(m, 4, 2), &at<N>(m, 5, 2)), load(&at<N>(m, 4, 3), &at<N>(m, 5, 3)),
                load(&at<N>(m, 6, 0), &at<N>(m, 7, 0)), load(&at<N>(m, 6, 1), &at<N>(m, 7, 1)),
                load(&at<N>(m, 6, 2), &at<N>(m, 7, 2)), load(&at<N>(m, 6, 3), &at<N>(m, 7, 3)),
                load(&at<N>(m, 0, 4), &at<N>(m, 1, 4)), load(&at<N>(m, 0, 5), &at<N>(m, 1, 5)),
                load(&at<N>(m, 0, 6), &at<N>(m, 1, 6)), load(&at<N>(m, 0, 7), &at<N>(m, 1, 7)),
                load(&at<N>(m, 2, 4), &at<N>(m, 3, 4)), load(&at<N>(m, 2, 5), &at<N>(m, 3, 5)),
                load(&at<N>(m, 2, 6), &at<N>(m, 3, 6)), load(&at<N>(m, 2, 7), &at<N>(m, 3, 7)),
                load(&at<N>(m, 4, 4), &at<N>(m, 5, 4)), load(&at<N>(m, 4, 5), &at<N>(m, 5, 5)),
                load(&at<N>(m, 4, 6), &at<N>(m, 5, 6)), load(&at<N>(m, 4, 7), &at<N>(m, 5, 7)),
                load(&at<N>(m, 6, 4), &at<N>(m, 7, 4)), load(&at<N>(m, 6, 5), &at<N>(m, 7, 5)),
                load(&at<N>(m, 6, 6), &at<N>(m, 7, 6)), load(&at<N>(m, 6, 7), &at<N>(m, 7, 7))};
        }

        // bit indices id[.] are given from high to low (e.g. control first for CNOT)
        template <class V, class M, typename UINT, int CTRLMASK>
        static inline void dispatch(V &psi, M const &m, UINT ctrlmask, const unsigned *id)
        {
            kernel_dispatch<3, kernel3, CTRLMASK>(psi, m, ctrlmask, id);
        }
    };
}  // namespace details

#endif /* VECTOR_KERNEL3_HPP */
