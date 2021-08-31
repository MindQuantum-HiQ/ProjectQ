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

#ifndef VECTOR_KERNEL4_HPP
#define VECTOR_KERNEL4_HPP

#include "utils.hpp"

namespace details
{
    class kernel4
    {
    public:
        template <class V, class M, typename UINT, typename D>
        static inline void core(V &psi, UINT I, const D d, M const &m_tuple)
        {
            const auto &[m, mt] = m_tuple;

            const UINT d0 = d[0];
            const UINT d1 = d[1];
            const UINT d2 = d[2];
            const UINT d3 = d[3];

            intrin_t v[4];

            v[0] = load2(&psi[I]);
            v[1] = load2(&psi[I + d0]);
            v[2] = load2(&psi[I + d1]);
            v[3] = load2(&psi[I + d0 + d1]);

            intrin_t tmp[8];

            tmp[0] = add(mul(v[0], m[0], mt[0]),
                         add(mul(v[1], m[1], mt[1]), add(mul(v[2], m[2], mt[2]), mul(v[3], m[3], mt[3]))));
            tmp[1] = add(mul(v[0], m[4], mt[4]),
                         add(mul(v[1], m[5], mt[5]), add(mul(v[2], m[6], mt[6]), mul(v[3], m[7], mt[7]))));
            tmp[2] = add(mul(v[0], m[8], mt[8]),
                         add(mul(v[1], m[9], mt[9]), add(mul(v[2], m[10], mt[10]), mul(v[3], m[11], mt[11]))));
            tmp[3] = add(mul(v[0], m[12], mt[12]),
                         add(mul(v[1], m[13], mt[13]), add(mul(v[2], m[14], mt[14]), mul(v[3], m[15], mt[15]))));
            tmp[4] = add(mul(v[0], m[16], mt[16]),
                         add(mul(v[1], m[17], mt[17]), add(mul(v[2], m[18], mt[18]), mul(v[3], m[19], mt[19]))));
            tmp[5] = add(mul(v[0], m[20], mt[20]),
                         add(mul(v[1], m[21], mt[21]), add(mul(v[2], m[22], mt[22]), mul(v[3], m[23], mt[23]))));
            tmp[6] = add(mul(v[0], m[24], mt[24]),
                         add(mul(v[1], m[25], mt[25]), add(mul(v[2], m[26], mt[26]), mul(v[3], m[27], mt[27]))));
            tmp[7] = add(mul(v[0], m[28], mt[28]),
                         add(mul(v[1], m[29], mt[29]), add(mul(v[2], m[30], mt[30]), mul(v[3], m[31], mt[31]))));

            v[0] = load2(&psi[I + d2]);
            v[1] = load2(&psi[I + d0 + d2]);
            v[2] = load2(&psi[I + d1 + d2]);
            v[3] = load2(&psi[I + d0 + d1 + d2]);

            tmp[0] = add(tmp[0],
                         add(mul(v[0], m[32], mt[32]),
                             add(mul(v[1], m[33], mt[33]), add(mul(v[2], m[34], mt[34]), mul(v[3], m[35], mt[35])))));
            tmp[1] = add(tmp[1],
                         add(mul(v[0], m[36], mt[36]),
                             add(mul(v[1], m[37], mt[37]), add(mul(v[2], m[38], mt[38]), mul(v[3], m[39], mt[39])))));
            tmp[2] = add(tmp[2],
                         add(mul(v[0], m[40], mt[40]),
                             add(mul(v[1], m[41], mt[41]), add(mul(v[2], m[42], mt[42]), mul(v[3], m[43], mt[43])))));
            tmp[3] = add(tmp[3],
                         add(mul(v[0], m[44], mt[44]),
                             add(mul(v[1], m[45], mt[45]), add(mul(v[2], m[46], mt[46]), mul(v[3], m[47], mt[47])))));
            tmp[4] = add(tmp[4],
                         add(mul(v[0], m[48], mt[48]),
                             add(mul(v[1], m[49], mt[49]), add(mul(v[2], m[50], mt[50]), mul(v[3], m[51], mt[51])))));
            tmp[5] = add(tmp[5],
                         add(mul(v[0], m[52], mt[52]),
                             add(mul(v[1], m[53], mt[53]), add(mul(v[2], m[54], mt[54]), mul(v[3], m[55], mt[55])))));
            tmp[6] = add(tmp[6],
                         add(mul(v[0], m[56], mt[56]),
                             add(mul(v[1], m[57], mt[57]), add(mul(v[2], m[58], mt[58]), mul(v[3], m[59], mt[59])))));
            tmp[7] = add(tmp[7],
                         add(mul(v[0], m[60], mt[60]),
                             add(mul(v[1], m[61], mt[61]), add(mul(v[2], m[62], mt[62]), mul(v[3], m[63], mt[63])))));

            v[0] = load2(&psi[I + d3]);
            v[1] = load2(&psi[I + d0 + d3]);
            v[2] = load2(&psi[I + d1 + d3]);
            v[3] = load2(&psi[I + d0 + d1 + d3]);

            tmp[0] = add(tmp[0],
                         add(mul(v[0], m[64], mt[64]),
                             add(mul(v[1], m[65], mt[65]), add(mul(v[2], m[66], mt[66]), mul(v[3], m[67], mt[67])))));
            tmp[1] = add(tmp[1],
                         add(mul(v[0], m[68], mt[68]),
                             add(mul(v[1], m[69], mt[69]), add(mul(v[2], m[70], mt[70]), mul(v[3], m[71], mt[71])))));
            tmp[2] = add(tmp[2],
                         add(mul(v[0], m[72], mt[72]),
                             add(mul(v[1], m[73], mt[73]), add(mul(v[2], m[74], mt[74]), mul(v[3], m[75], mt[75])))));
            tmp[3] = add(tmp[3],
                         add(mul(v[0], m[76], mt[76]),
                             add(mul(v[1], m[77], mt[77]), add(mul(v[2], m[78], mt[78]), mul(v[3], m[79], mt[79])))));
            tmp[4] = add(tmp[4],
                         add(mul(v[0], m[80], mt[80]),
                             add(mul(v[1], m[81], mt[81]), add(mul(v[2], m[82], mt[82]), mul(v[3], m[83], mt[83])))));
            tmp[5] = add(tmp[5],
                         add(mul(v[0], m[84], mt[84]),
                             add(mul(v[1], m[85], mt[85]), add(mul(v[2], m[86], mt[86]), mul(v[3], m[87], mt[87])))));
            tmp[6] = add(tmp[6],
                         add(mul(v[0], m[88], mt[88]),
                             add(mul(v[1], m[89], mt[89]), add(mul(v[2], m[90], mt[90]), mul(v[3], m[91], mt[91])))));
            tmp[7] = add(tmp[7],
                         add(mul(v[0], m[92], mt[92]),
                             add(mul(v[1], m[93], mt[93]), add(mul(v[2], m[94], mt[94]), mul(v[3], m[95], mt[95])))));

            v[0] = load2(&psi[I + d2 + d3]);
            v[1] = load2(&psi[I + d0 + d2 + d3]);
            v[2] = load2(&psi[I + d1 + d2 + d3]);
            v[3] = load2(&psi[I + d0 + d1 + d2 + d3]);

            _intrin_store_high_low(reinterpret_cast<double *>(&psi[I + d0]), reinterpret_cast<double *>(&psi[I]),
                                   add(tmp[0], add(mul(v[0], m[96], mt[96]),
                                                   add(mul(v[1], m[97], mt[97]),
                                                       add(mul(v[2], m[98], mt[98]), mul(v[3], m[99], mt[99]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d1]), reinterpret_cast<double *>(&psi[I + d1]),
                add(tmp[1],
                    add(mul(v[0], m[100], mt[100]),
                        add(mul(v[1], m[101], mt[101]), add(mul(v[2], m[102], mt[102]), mul(v[3], m[103], mt[103]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d2]), reinterpret_cast<double *>(&psi[I + d2]),
                add(tmp[2],
                    add(mul(v[0], m[104], mt[104]),
                        add(mul(v[1], m[105], mt[105]), add(mul(v[2], m[106], mt[106]), mul(v[3], m[107], mt[107]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d1 + d2]), reinterpret_cast<double *>(&psi[I + d1 + d2]),
                add(tmp[3],
                    add(mul(v[0], m[108], mt[108]),
                        add(mul(v[1], m[109], mt[109]), add(mul(v[2], m[110], mt[110]), mul(v[3], m[111], mt[111]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d3]), reinterpret_cast<double *>(&psi[I + d3]),
                add(tmp[4],
                    add(mul(v[0], m[112], mt[112]),
                        add(mul(v[1], m[113], mt[113]), add(mul(v[2], m[114], mt[114]), mul(v[3], m[115], mt[115]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d1 + d3]), reinterpret_cast<double *>(&psi[I + d1 + d3]),
                add(tmp[5],
                    add(mul(v[0], m[116], mt[116]),
                        add(mul(v[1], m[117], mt[117]), add(mul(v[2], m[118], mt[118]), mul(v[3], m[119], mt[119]))))));
            _intrin_store_high_low(
                reinterpret_cast<double *>(&psi[I + d0 + d2 + d3]), reinterpret_cast<double *>(&psi[I + d2 + d3]),
                add(tmp[6],
                    add(mul(v[0], m[120], mt[120]),
                        add(mul(v[1], m[121], mt[121]), add(mul(v[2], m[122], mt[122]), mul(v[3], m[123], mt[123]))))));
            _intrin_store_high_low(reinterpret_cast<double *>(&psi[I + d0 + d1 + d2 + d3]),
                                   reinterpret_cast<double *>(&psi[I + d1 + d2 + d3]),
                                   add(tmp[7], add(mul(v[0], m[124], mt[124]),
                                                   add(mul(v[1], m[125], mt[125]),
                                                       add(mul(v[2], m[126], mt[126]), mul(v[3], m[127], mt[127]))))));
        }

        template <typename M>
        static inline auto create_m(M const &m)
        {
            constexpr auto N = 1U << 4U;
            return utils::intrin_array<128>{
                load(&at<N>(m, 0, 0), &at<N>(m, 1, 0)),     load(&at<N>(m, 0, 1), &at<N>(m, 1, 1)),
                load(&at<N>(m, 0, 2), &at<N>(m, 1, 2)),     load(&at<N>(m, 0, 3), &at<N>(m, 1, 3)),
                load(&at<N>(m, 2, 0), &at<N>(m, 3, 0)),     load(&at<N>(m, 2, 1), &at<N>(m, 3, 1)),
                load(&at<N>(m, 2, 2), &at<N>(m, 3, 2)),     load(&at<N>(m, 2, 3), &at<N>(m, 3, 3)),
                load(&at<N>(m, 4, 0), &at<N>(m, 5, 0)),     load(&at<N>(m, 4, 1), &at<N>(m, 5, 1)),
                load(&at<N>(m, 4, 2), &at<N>(m, 5, 2)),     load(&at<N>(m, 4, 3), &at<N>(m, 5, 3)),
                load(&at<N>(m, 6, 0), &at<N>(m, 7, 0)),     load(&at<N>(m, 6, 1), &at<N>(m, 7, 1)),
                load(&at<N>(m, 6, 2), &at<N>(m, 7, 2)),     load(&at<N>(m, 6, 3), &at<N>(m, 7, 3)),
                load(&at<N>(m, 8, 0), &at<N>(m, 9, 0)),     load(&at<N>(m, 8, 1), &at<N>(m, 9, 1)),
                load(&at<N>(m, 8, 2), &at<N>(m, 9, 2)),     load(&at<N>(m, 8, 3), &at<N>(m, 9, 3)),
                load(&at<N>(m, 10, 0), &at<N>(m, 11, 0)),   load(&at<N>(m, 10, 1), &at<N>(m, 11, 1)),
                load(&at<N>(m, 10, 2), &at<N>(m, 11, 2)),   load(&at<N>(m, 10, 3), &at<N>(m, 11, 3)),
                load(&at<N>(m, 12, 0), &at<N>(m, 13, 0)),   load(&at<N>(m, 12, 1), &at<N>(m, 13, 1)),
                load(&at<N>(m, 12, 2), &at<N>(m, 13, 2)),   load(&at<N>(m, 12, 3), &at<N>(m, 13, 3)),
                load(&at<N>(m, 14, 0), &at<N>(m, 15, 0)),   load(&at<N>(m, 14, 1), &at<N>(m, 15, 1)),
                load(&at<N>(m, 14, 2), &at<N>(m, 15, 2)),   load(&at<N>(m, 14, 3), &at<N>(m, 15, 3)),
                load(&at<N>(m, 0, 4), &at<N>(m, 1, 4)),     load(&at<N>(m, 0, 5), &at<N>(m, 1, 5)),
                load(&at<N>(m, 0, 6), &at<N>(m, 1, 6)),     load(&at<N>(m, 0, 7), &at<N>(m, 1, 7)),
                load(&at<N>(m, 2, 4), &at<N>(m, 3, 4)),     load(&at<N>(m, 2, 5), &at<N>(m, 3, 5)),
                load(&at<N>(m, 2, 6), &at<N>(m, 3, 6)),     load(&at<N>(m, 2, 7), &at<N>(m, 3, 7)),
                load(&at<N>(m, 4, 4), &at<N>(m, 5, 4)),     load(&at<N>(m, 4, 5), &at<N>(m, 5, 5)),
                load(&at<N>(m, 4, 6), &at<N>(m, 5, 6)),     load(&at<N>(m, 4, 7), &at<N>(m, 5, 7)),
                load(&at<N>(m, 6, 4), &at<N>(m, 7, 4)),     load(&at<N>(m, 6, 5), &at<N>(m, 7, 5)),
                load(&at<N>(m, 6, 6), &at<N>(m, 7, 6)),     load(&at<N>(m, 6, 7), &at<N>(m, 7, 7)),
                load(&at<N>(m, 8, 4), &at<N>(m, 9, 4)),     load(&at<N>(m, 8, 5), &at<N>(m, 9, 5)),
                load(&at<N>(m, 8, 6), &at<N>(m, 9, 6)),     load(&at<N>(m, 8, 7), &at<N>(m, 9, 7)),
                load(&at<N>(m, 10, 4), &at<N>(m, 11, 4)),   load(&at<N>(m, 10, 5), &at<N>(m, 11, 5)),
                load(&at<N>(m, 10, 6), &at<N>(m, 11, 6)),   load(&at<N>(m, 10, 7), &at<N>(m, 11, 7)),
                load(&at<N>(m, 12, 4), &at<N>(m, 13, 4)),   load(&at<N>(m, 12, 5), &at<N>(m, 13, 5)),
                load(&at<N>(m, 12, 6), &at<N>(m, 13, 6)),   load(&at<N>(m, 12, 7), &at<N>(m, 13, 7)),
                load(&at<N>(m, 14, 4), &at<N>(m, 15, 4)),   load(&at<N>(m, 14, 5), &at<N>(m, 15, 5)),
                load(&at<N>(m, 14, 6), &at<N>(m, 15, 6)),   load(&at<N>(m, 14, 7), &at<N>(m, 15, 7)),
                load(&at<N>(m, 0, 8), &at<N>(m, 1, 8)),     load(&at<N>(m, 0, 9), &at<N>(m, 1, 9)),
                load(&at<N>(m, 0, 10), &at<N>(m, 1, 10)),   load(&at<N>(m, 0, 11), &at<N>(m, 1, 11)),
                load(&at<N>(m, 2, 8), &at<N>(m, 3, 8)),     load(&at<N>(m, 2, 9), &at<N>(m, 3, 9)),
                load(&at<N>(m, 2, 10), &at<N>(m, 3, 10)),   load(&at<N>(m, 2, 11), &at<N>(m, 3, 11)),
                load(&at<N>(m, 4, 8), &at<N>(m, 5, 8)),     load(&at<N>(m, 4, 9), &at<N>(m, 5, 9)),
                load(&at<N>(m, 4, 10), &at<N>(m, 5, 10)),   load(&at<N>(m, 4, 11), &at<N>(m, 5, 11)),
                load(&at<N>(m, 6, 8), &at<N>(m, 7, 8)),     load(&at<N>(m, 6, 9), &at<N>(m, 7, 9)),
                load(&at<N>(m, 6, 10), &at<N>(m, 7, 10)),   load(&at<N>(m, 6, 11), &at<N>(m, 7, 11)),
                load(&at<N>(m, 8, 8), &at<N>(m, 9, 8)),     load(&at<N>(m, 8, 9), &at<N>(m, 9, 9)),
                load(&at<N>(m, 8, 10), &at<N>(m, 9, 10)),   load(&at<N>(m, 8, 11), &at<N>(m, 9, 11)),
                load(&at<N>(m, 10, 8), &at<N>(m, 11, 8)),   load(&at<N>(m, 10, 9), &at<N>(m, 11, 9)),
                load(&at<N>(m, 10, 10), &at<N>(m, 11, 10)), load(&at<N>(m, 10, 11), &at<N>(m, 11, 11)),
                load(&at<N>(m, 12, 8), &at<N>(m, 13, 8)),   load(&at<N>(m, 12, 9), &at<N>(m, 13, 9)),
                load(&at<N>(m, 12, 10), &at<N>(m, 13, 10)), load(&at<N>(m, 12, 11), &at<N>(m, 13, 11)),
                load(&at<N>(m, 14, 8), &at<N>(m, 15, 8)),   load(&at<N>(m, 14, 9), &at<N>(m, 15, 9)),
                load(&at<N>(m, 14, 10), &at<N>(m, 15, 10)), load(&at<N>(m, 14, 11), &at<N>(m, 15, 11)),
                load(&at<N>(m, 0, 12), &at<N>(m, 1, 12)),   load(&at<N>(m, 0, 13), &at<N>(m, 1, 13)),
                load(&at<N>(m, 0, 14), &at<N>(m, 1, 14)),   load(&at<N>(m, 0, 15), &at<N>(m, 1, 15)),
                load(&at<N>(m, 2, 12), &at<N>(m, 3, 12)),   load(&at<N>(m, 2, 13), &at<N>(m, 3, 13)),
                load(&at<N>(m, 2, 14), &at<N>(m, 3, 14)),   load(&at<N>(m, 2, 15), &at<N>(m, 3, 15)),
                load(&at<N>(m, 4, 12), &at<N>(m, 5, 12)),   load(&at<N>(m, 4, 13), &at<N>(m, 5, 13)),
                load(&at<N>(m, 4, 14), &at<N>(m, 5, 14)),   load(&at<N>(m, 4, 15), &at<N>(m, 5, 15)),
                load(&at<N>(m, 6, 12), &at<N>(m, 7, 12)),   load(&at<N>(m, 6, 13), &at<N>(m, 7, 13)),
                load(&at<N>(m, 6, 14), &at<N>(m, 7, 14)),   load(&at<N>(m, 6, 15), &at<N>(m, 7, 15)),
                load(&at<N>(m, 8, 12), &at<N>(m, 9, 12)),   load(&at<N>(m, 8, 13), &at<N>(m, 9, 13)),
                load(&at<N>(m, 8, 14), &at<N>(m, 9, 14)),   load(&at<N>(m, 8, 15), &at<N>(m, 9, 15)),
                load(&at<N>(m, 10, 12), &at<N>(m, 11, 12)), load(&at<N>(m, 10, 13), &at<N>(m, 11, 13)),
                load(&at<N>(m, 10, 14), &at<N>(m, 11, 14)), load(&at<N>(m, 10, 15), &at<N>(m, 11, 15)),
                load(&at<N>(m, 12, 12), &at<N>(m, 13, 12)), load(&at<N>(m, 12, 13), &at<N>(m, 13, 13)),
                load(&at<N>(m, 12, 14), &at<N>(m, 13, 14)), load(&at<N>(m, 12, 15), &at<N>(m, 13, 15)),
                load(&at<N>(m, 14, 12), &at<N>(m, 15, 12)), load(&at<N>(m, 14, 13), &at<N>(m, 15, 13)),
                load(&at<N>(m, 14, 14), &at<N>(m, 15, 14)), load(&at<N>(m, 14, 15), &at<N>(m, 15, 15))};
        }

        // bit indices id[.] are given from high to low (e.g. control first for CNOT)
        template <class V, class M, typename UINT, int CTRLMASK>
        static inline void dispatch(V &psi, M const &m, UINT ctrlmask, const unsigned *id)
        {
            kernel_dispatch<4, kernel4, CTRLMASK>(psi, m, ctrlmask, id);
        }
    };
}  // namespace details

#endif /* VECTOR_KERNEL4_HPP */
