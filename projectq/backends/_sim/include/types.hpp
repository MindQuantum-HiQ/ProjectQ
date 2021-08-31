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

#ifndef TYPES_HPP
#define TYPES_HPP

#include "aligned_allocator.hpp"
#include "fusion.hpp"

#include <complex>
#include <cstddef>
#include <vector>

namespace types
{
    static constexpr auto alignment = 512;
    using calc_type = double;
    using complex_type = std::complex<calc_type>;
    using StateVector = std::vector<complex_type, aligned_allocator<complex_type, alignment>>;

    using V = StateVector;
    using M = fusion::Fusion::Matrix;
    using UINT = std::size_t;
}  // namespace types

#endif  // TYPES_HPP
