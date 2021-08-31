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

#ifndef INSTRSET_HPP
#define INSTRSET_HPP

#include <cstdint>
#include <limits>

namespace agner
{
    enum class InstrSet : uint8_t
    {
        I80386 = 0,        // 80386 instruction set
        SSE = 1,           // or above = SSE (XMM) supported by CPU (not testing for O.S. support)
        SSE2 = 2,          // or above = SSE2
        SSE3 = 3,          // or above = SSE3
        SSSE3 = 4,         // or above = Supplementary SSE3 (SSSE3)
        SSE41 = 5,         // or above = SSE4.1
        SSE42 = 6,         // or above = SSE4.2
        AVX = 7,           // or above = AVX supported by CPU and operating system
        AVX2 = 8,          // or above = AVX2
        AVX512F = 9,       // or above = AVX512F
        AVX512VL = 10,     // or above = AVX512VL
        AVX512BW_DQ = 11,  // or above = AVX512BW, AVX512DQ

        Unknown = std::numeric_limits<uint8_t>::max(),
    };

    InstrSet InstrSetDetect();

    bool isSupported(InstrSet iset);

}  // namespace agner

#endif  // INSTRSET_HPP
