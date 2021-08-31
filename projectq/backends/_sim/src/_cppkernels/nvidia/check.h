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

#ifndef NVIDIA_CHECK_H
#define NVIDIA_CHECK_H

#ifdef HIQ_WITH_CUDA
#    include <cuda_runtime_api.h>
#    include <driver_types.h>

#    include <cstdio>

// NOLINTNEXTLINE(cppcoreguidelines-macro-usage)
#    define CUDA_ERR_CHECK(x)                                                                                          \
        do {                                                                                                           \
            cudaError_t err = x;                                                                                       \
            if (err != cudaSuccess) {                                                                                  \
                std::fprintf(stderr, "CUDA error %d \"%s\" at %s:%d\n", static_cast<int>(err),                         \
                             cudaGetErrorString(err), __FILE__, __LINE__);                                             \
                exit(-1);                                                                                              \
            }                                                                                                          \
        } while (0)

#endif  // HIQ_WITH_CUDA
#endif  // NVIDIA_CHECK_H
