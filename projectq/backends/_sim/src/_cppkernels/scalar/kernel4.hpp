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

#ifndef SCALAR_KERNEL4_HPP
#define SCALAR_KERNEL4_HPP

namespace details
{
    class kernel4
    {
    public:
        template <class V, class M, typename UINT, typename D>
        static inline void core(V &psi, UINT I, const D d, M const &m)
        {
            const UINT d0 = d[0];
            const UINT d1 = d[1];
            const UINT d2 = d[2];
            const UINT d3 = d[3];

            std::complex<double> v[4];
            v[0] = psi[I];
            v[1] = psi[I + d0];
            v[2] = psi[I + d1];
            v[3] = psi[I + d0 + d1];

            std::complex<double> tmp[16];

            tmp[0] = add(mul(v[0], m[0][0]), add(mul(v[1], m[0][1]), add(mul(v[2], m[0][2]), mul(v[3], m[0][3]))));
            tmp[1] = add(mul(v[0], m[1][0]), add(mul(v[1], m[1][1]), add(mul(v[2], m[1][2]), mul(v[3], m[1][3]))));
            tmp[2] = add(mul(v[0], m[2][0]), add(mul(v[1], m[2][1]), add(mul(v[2], m[2][2]), mul(v[3], m[2][3]))));
            tmp[3] = add(mul(v[0], m[3][0]), add(mul(v[1], m[3][1]), add(mul(v[2], m[3][2]), mul(v[3], m[3][3]))));
            tmp[4] = add(mul(v[0], m[4][0]), add(mul(v[1], m[4][1]), add(mul(v[2], m[4][2]), mul(v[3], m[4][3]))));
            tmp[5] = add(mul(v[0], m[5][0]), add(mul(v[1], m[5][1]), add(mul(v[2], m[5][2]), mul(v[3], m[5][3]))));
            tmp[6] = add(mul(v[0], m[6][0]), add(mul(v[1], m[6][1]), add(mul(v[2], m[6][2]), mul(v[3], m[6][3]))));
            tmp[7] = add(mul(v[0], m[7][0]), add(mul(v[1], m[7][1]), add(mul(v[2], m[7][2]), mul(v[3], m[7][3]))));
            tmp[8] = add(mul(v[0], m[8][0]), add(mul(v[1], m[8][1]), add(mul(v[2], m[8][2]), mul(v[3], m[8][3]))));
            tmp[9] = add(mul(v[0], m[9][0]), add(mul(v[1], m[9][1]), add(mul(v[2], m[9][2]), mul(v[3], m[9][3]))));
            tmp[10] = add(mul(v[0], m[10][0]), add(mul(v[1], m[10][1]), add(mul(v[2], m[10][2]), mul(v[3], m[10][3]))));
            tmp[11] = add(mul(v[0], m[11][0]), add(mul(v[1], m[11][1]), add(mul(v[2], m[11][2]), mul(v[3], m[11][3]))));
            tmp[12] = add(mul(v[0], m[12][0]), add(mul(v[1], m[12][1]), add(mul(v[2], m[12][2]), mul(v[3], m[12][3]))));
            tmp[13] = add(mul(v[0], m[13][0]), add(mul(v[1], m[13][1]), add(mul(v[2], m[13][2]), mul(v[3], m[13][3]))));
            tmp[14] = add(mul(v[0], m[14][0]), add(mul(v[1], m[14][1]), add(mul(v[2], m[14][2]), mul(v[3], m[14][3]))));
            tmp[15] = add(mul(v[0], m[15][0]), add(mul(v[1], m[15][1]), add(mul(v[2], m[15][2]), mul(v[3], m[15][3]))));

            v[0] = psi[I + d2];
            v[1] = psi[I + d0 + d2];
            v[2] = psi[I + d1 + d2];
            v[3] = psi[I + d0 + d1 + d2];

            tmp[0] = add(tmp[0],
                         add(mul(v[0], m[0][4]), add(mul(v[1], m[0][5]), add(mul(v[2], m[0][6]), mul(v[3], m[0][7])))));
            tmp[1] = add(tmp[1],
                         add(mul(v[0], m[1][4]), add(mul(v[1], m[1][5]), add(mul(v[2], m[1][6]), mul(v[3], m[1][7])))));
            tmp[2] = add(tmp[2],
                         add(mul(v[0], m[2][4]), add(mul(v[1], m[2][5]), add(mul(v[2], m[2][6]), mul(v[3], m[2][7])))));
            tmp[3] = add(tmp[3],
                         add(mul(v[0], m[3][4]), add(mul(v[1], m[3][5]), add(mul(v[2], m[3][6]), mul(v[3], m[3][7])))));
            tmp[4] = add(tmp[4],
                         add(mul(v[0], m[4][4]), add(mul(v[1], m[4][5]), add(mul(v[2], m[4][6]), mul(v[3], m[4][7])))));
            tmp[5] = add(tmp[5],
                         add(mul(v[0], m[5][4]), add(mul(v[1], m[5][5]), add(mul(v[2], m[5][6]), mul(v[3], m[5][7])))));
            tmp[6] = add(tmp[6],
                         add(mul(v[0], m[6][4]), add(mul(v[1], m[6][5]), add(mul(v[2], m[6][6]), mul(v[3], m[6][7])))));
            tmp[7] = add(tmp[7],
                         add(mul(v[0], m[7][4]), add(mul(v[1], m[7][5]), add(mul(v[2], m[7][6]), mul(v[3], m[7][7])))));
            tmp[8] = add(tmp[8],
                         add(mul(v[0], m[8][4]), add(mul(v[1], m[8][5]), add(mul(v[2], m[8][6]), mul(v[3], m[8][7])))));
            tmp[9] = add(tmp[9],
                         add(mul(v[0], m[9][4]), add(mul(v[1], m[9][5]), add(mul(v[2], m[9][6]), mul(v[3], m[9][7])))));
            tmp[10] = add(tmp[10], add(mul(v[0], m[10][4]),
                                       add(mul(v[1], m[10][5]), add(mul(v[2], m[10][6]), mul(v[3], m[10][7])))));
            tmp[11] = add(tmp[11], add(mul(v[0], m[11][4]),
                                       add(mul(v[1], m[11][5]), add(mul(v[2], m[11][6]), mul(v[3], m[11][7])))));
            tmp[12] = add(tmp[12], add(mul(v[0], m[12][4]),
                                       add(mul(v[1], m[12][5]), add(mul(v[2], m[12][6]), mul(v[3], m[12][7])))));
            tmp[13] = add(tmp[13], add(mul(v[0], m[13][4]),
                                       add(mul(v[1], m[13][5]), add(mul(v[2], m[13][6]), mul(v[3], m[13][7])))));
            tmp[14] = add(tmp[14], add(mul(v[0], m[14][4]),
                                       add(mul(v[1], m[14][5]), add(mul(v[2], m[14][6]), mul(v[3], m[14][7])))));
            tmp[15] = add(tmp[15], add(mul(v[0], m[15][4]),
                                       add(mul(v[1], m[15][5]), add(mul(v[2], m[15][6]), mul(v[3], m[15][7])))));

            v[0] = psi[I + d3];
            v[1] = psi[I + d0 + d3];
            v[2] = psi[I + d1 + d3];
            v[3] = psi[I + d0 + d1 + d3];

            tmp[0] = add(tmp[0], add(mul(v[0], m[0][8]),
                                     add(mul(v[1], m[0][9]), add(mul(v[2], m[0][10]), mul(v[3], m[0][11])))));
            tmp[1] = add(tmp[1], add(mul(v[0], m[1][8]),
                                     add(mul(v[1], m[1][9]), add(mul(v[2], m[1][10]), mul(v[3], m[1][11])))));
            tmp[2] = add(tmp[2], add(mul(v[0], m[2][8]),
                                     add(mul(v[1], m[2][9]), add(mul(v[2], m[2][10]), mul(v[3], m[2][11])))));
            tmp[3] = add(tmp[3], add(mul(v[0], m[3][8]),
                                     add(mul(v[1], m[3][9]), add(mul(v[2], m[3][10]), mul(v[3], m[3][11])))));
            tmp[4] = add(tmp[4], add(mul(v[0], m[4][8]),
                                     add(mul(v[1], m[4][9]), add(mul(v[2], m[4][10]), mul(v[3], m[4][11])))));
            tmp[5] = add(tmp[5], add(mul(v[0], m[5][8]),
                                     add(mul(v[1], m[5][9]), add(mul(v[2], m[5][10]), mul(v[3], m[5][11])))));
            tmp[6] = add(tmp[6], add(mul(v[0], m[6][8]),
                                     add(mul(v[1], m[6][9]), add(mul(v[2], m[6][10]), mul(v[3], m[6][11])))));
            tmp[7] = add(tmp[7], add(mul(v[0], m[7][8]),
                                     add(mul(v[1], m[7][9]), add(mul(v[2], m[7][10]), mul(v[3], m[7][11])))));
            tmp[8] = add(tmp[8], add(mul(v[0], m[8][8]),
                                     add(mul(v[1], m[8][9]), add(mul(v[2], m[8][10]), mul(v[3], m[8][11])))));
            tmp[9] = add(tmp[9], add(mul(v[0], m[9][8]),
                                     add(mul(v[1], m[9][9]), add(mul(v[2], m[9][10]), mul(v[3], m[9][11])))));
            tmp[10] = add(tmp[10], add(mul(v[0], m[10][8]),
                                       add(mul(v[1], m[10][9]), add(mul(v[2], m[10][10]), mul(v[3], m[10][11])))));
            tmp[11] = add(tmp[11], add(mul(v[0], m[11][8]),
                                       add(mul(v[1], m[11][9]), add(mul(v[2], m[11][10]), mul(v[3], m[11][11])))));
            tmp[12] = add(tmp[12], add(mul(v[0], m[12][8]),
                                       add(mul(v[1], m[12][9]), add(mul(v[2], m[12][10]), mul(v[3], m[12][11])))));
            tmp[13] = add(tmp[13], add(mul(v[0], m[13][8]),
                                       add(mul(v[1], m[13][9]), add(mul(v[2], m[13][10]), mul(v[3], m[13][11])))));
            tmp[14] = add(tmp[14], add(mul(v[0], m[14][8]),
                                       add(mul(v[1], m[14][9]), add(mul(v[2], m[14][10]), mul(v[3], m[14][11])))));
            tmp[15] = add(tmp[15], add(mul(v[0], m[15][8]),
                                       add(mul(v[1], m[15][9]), add(mul(v[2], m[15][10]), mul(v[3], m[15][11])))));

            v[0] = psi[I + d2 + d3];
            v[1] = psi[I + d0 + d2 + d3];
            v[2] = psi[I + d1 + d2 + d3];
            v[3] = psi[I + d0 + d1 + d2 + d3];

            psi[I] = (add(tmp[0], add(mul(v[0], m[0][12]),
                                      add(mul(v[1], m[0][13]), add(mul(v[2], m[0][14]), mul(v[3], m[0][15]))))));
            psi[I + d0] = (add(tmp[1], add(mul(v[0], m[1][12]),
                                           add(mul(v[1], m[1][13]), add(mul(v[2], m[1][14]), mul(v[3], m[1][15]))))));
            psi[I + d1] = (add(tmp[2], add(mul(v[0], m[2][12]),
                                           add(mul(v[1], m[2][13]), add(mul(v[2], m[2][14]), mul(v[3], m[2][15]))))));
            psi[I + d0 + d1] = (add(
                tmp[3],
                add(mul(v[0], m[3][12]), add(mul(v[1], m[3][13]), add(mul(v[2], m[3][14]), mul(v[3], m[3][15]))))));
            psi[I + d2] = (add(tmp[4], add(mul(v[0], m[4][12]),
                                           add(mul(v[1], m[4][13]), add(mul(v[2], m[4][14]), mul(v[3], m[4][15]))))));
            psi[I + d0 + d2] = (add(
                tmp[5],
                add(mul(v[0], m[5][12]), add(mul(v[1], m[5][13]), add(mul(v[2], m[5][14]), mul(v[3], m[5][15]))))));
            psi[I + d1 + d2] = (add(
                tmp[6],
                add(mul(v[0], m[6][12]), add(mul(v[1], m[6][13]), add(mul(v[2], m[6][14]), mul(v[3], m[6][15]))))));
            psi[I + d0 + d1 + d2] = (add(
                tmp[7],
                add(mul(v[0], m[7][12]), add(mul(v[1], m[7][13]), add(mul(v[2], m[7][14]), mul(v[3], m[7][15]))))));
            psi[I + d3] = (add(tmp[8], add(mul(v[0], m[8][12]),
                                           add(mul(v[1], m[8][13]), add(mul(v[2], m[8][14]), mul(v[3], m[8][15]))))));
            psi[I + d0 + d3] = (add(
                tmp[9],
                add(mul(v[0], m[9][12]), add(mul(v[1], m[9][13]), add(mul(v[2], m[9][14]), mul(v[3], m[9][15]))))));
            psi[I + d1 + d3] = (add(
                tmp[10],
                add(mul(v[0], m[10][12]), add(mul(v[1], m[10][13]), add(mul(v[2], m[10][14]), mul(v[3], m[10][15]))))));
            psi[I + d0 + d1 + d3] = (add(
                tmp[11],
                add(mul(v[0], m[11][12]), add(mul(v[1], m[11][13]), add(mul(v[2], m[11][14]), mul(v[3], m[11][15]))))));
            psi[I + d2 + d3] = (add(
                tmp[12],
                add(mul(v[0], m[12][12]), add(mul(v[1], m[12][13]), add(mul(v[2], m[12][14]), mul(v[3], m[12][15]))))));
            psi[I + d0 + d2 + d3] = (add(
                tmp[13],
                add(mul(v[0], m[13][12]), add(mul(v[1], m[13][13]), add(mul(v[2], m[13][14]), mul(v[3], m[13][15]))))));
            psi[I + d1 + d2 + d3] = (add(
                tmp[14],
                add(mul(v[0], m[14][12]), add(mul(v[1], m[14][13]), add(mul(v[2], m[14][14]), mul(v[3], m[14][15]))))));
            psi[I + d0 + d1 + d2 + d3] = (add(
                tmp[15],
                add(mul(v[0], m[15][12]), add(mul(v[1], m[15][13]), add(mul(v[2], m[15][14]), mul(v[3], m[15][15]))))));
        }

        // bit indices id[.] are given from high to low (e.g. control first for CNOT)
        template <class V, class M, typename UINT, int CTRLMASK>
        static inline void dispatch(V &psi, M const &m, UINT ctrlmask, const unsigned *id)
        {
            kernel_dispatch<4, kernel4, CTRLMASK>(psi, m, ctrlmask, id);
        }
    };
}  // namespace details

#endif /* SCALAR_KERNEL4_HPP */
