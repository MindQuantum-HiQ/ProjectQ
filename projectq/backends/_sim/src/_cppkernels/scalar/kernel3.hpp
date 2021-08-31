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

#ifndef SCALAR_KERNEL3_HPP
#define SCALAR_KERNEL3_HPP

namespace details
{
    class kernel3
    {
    public:
        template <class V, class M, typename UINT, typename D>
        static inline void core(V &psi, UINT I, const D d, M const &m)
        {
            const UINT d0 = d[0];
            const UINT d1 = d[1];
            const UINT d2 = d[2];

            std::complex<double> v[4];
            v[0] = psi[I];
            v[1] = psi[I + d0];
            v[2] = psi[I + d1];
            v[3] = psi[I + d0 + d1];

            std::complex<double> tmp[8];

            tmp[0] = add(mul(v[0], m[0][0]), add(mul(v[1], m[0][1]), add(mul(v[2], m[0][2]), mul(v[3], m[0][3]))));
            tmp[1] = add(mul(v[0], m[1][0]), add(mul(v[1], m[1][1]), add(mul(v[2], m[1][2]), mul(v[3], m[1][3]))));
            tmp[2] = add(mul(v[0], m[2][0]), add(mul(v[1], m[2][1]), add(mul(v[2], m[2][2]), mul(v[3], m[2][3]))));
            tmp[3] = add(mul(v[0], m[3][0]), add(mul(v[1], m[3][1]), add(mul(v[2], m[3][2]), mul(v[3], m[3][3]))));
            tmp[4] = add(mul(v[0], m[4][0]), add(mul(v[1], m[4][1]), add(mul(v[2], m[4][2]), mul(v[3], m[4][3]))));
            tmp[5] = add(mul(v[0], m[5][0]), add(mul(v[1], m[5][1]), add(mul(v[2], m[5][2]), mul(v[3], m[5][3]))));
            tmp[6] = add(mul(v[0], m[6][0]), add(mul(v[1], m[6][1]), add(mul(v[2], m[6][2]), mul(v[3], m[6][3]))));
            tmp[7] = add(mul(v[0], m[7][0]), add(mul(v[1], m[7][1]), add(mul(v[2], m[7][2]), mul(v[3], m[7][3]))));

            v[0] = psi[I + d2];
            v[1] = psi[I + d0 + d2];
            v[2] = psi[I + d1 + d2];
            v[3] = psi[I + d0 + d1 + d2];

            psi[I] = (add(
                tmp[0], add(mul(v[0], m[0][4]), add(mul(v[1], m[0][5]), add(mul(v[2], m[0][6]), mul(v[3], m[0][7]))))));
            psi[I + d0] = (add(
                tmp[1], add(mul(v[0], m[1][4]), add(mul(v[1], m[1][5]), add(mul(v[2], m[1][6]), mul(v[3], m[1][7]))))));
            psi[I + d1] = (add(
                tmp[2], add(mul(v[0], m[2][4]), add(mul(v[1], m[2][5]), add(mul(v[2], m[2][6]), mul(v[3], m[2][7]))))));
            psi[I + d0 + d1] = (add(
                tmp[3], add(mul(v[0], m[3][4]), add(mul(v[1], m[3][5]), add(mul(v[2], m[3][6]), mul(v[3], m[3][7]))))));
            psi[I + d2] = (add(
                tmp[4], add(mul(v[0], m[4][4]), add(mul(v[1], m[4][5]), add(mul(v[2], m[4][6]), mul(v[3], m[4][7]))))));
            psi[I + d0 + d2] = (add(
                tmp[5], add(mul(v[0], m[5][4]), add(mul(v[1], m[5][5]), add(mul(v[2], m[5][6]), mul(v[3], m[5][7]))))));
            psi[I + d1 + d2] = (add(
                tmp[6], add(mul(v[0], m[6][4]), add(mul(v[1], m[6][5]), add(mul(v[2], m[6][6]), mul(v[3], m[6][7]))))));
            psi[I + d0 + d1 + d2] = (add(
                tmp[7], add(mul(v[0], m[7][4]), add(mul(v[1], m[7][5]), add(mul(v[2], m[7][6]), mul(v[3], m[7][7]))))));
        }

        // bit indices id[.] are given from high to low (e.g. control first for CNOT)
        template <class V, class M, typename UINT, int CTRLMASK>
        static inline void dispatch(V &psi, M const &m, UINT ctrlmask, const unsigned *id)
        {
            kernel_dispatch<3, kernel3, CTRLMASK>(psi, m, ctrlmask, id);
        }
    };
}  // namespace details

#endif /* SCALAR_KERNEL3_HPP */
