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

#ifndef GMEM_H
#define GMEM_H

#ifdef HIQ_WITH_CUDA

#    include <driver_types.h>

#    include <cstddef>

class GlobalMemory
{
    // If not cudaSuccess, indicates that the GlobalMemory::* functions are not usable at all.
    // (checked by every function call in the beginning).
    cudaError_t fatalError;

    int ngpus;
    size_t szgmem;

    char *gmem, *ptr;

    bool init();

public:
    bool isAvailable();

    // Allocate global memory from the preallocated buffer.
    void* alloc(size_t size);

    // Reset free memory pointer to the beginning of preallocated buffer.
    void free();

    // Check whether the specified memory address belongs to GPU memory allocation.
    bool isAllocatedOnGPU(const void* ptr);

    cudaError_t set(void* dst, const int val, size_t size);

    cudaError_t copy(void* dst, const void* src, size_t size);

    cudaError_t getLastError();

    GlobalMemory();

    ~GlobalMemory();

    GlobalMemory(const GlobalMemory&) = delete;
    GlobalMemory(GlobalMemory&&) = delete;
    GlobalMemory& operator=(const GlobalMemory&) = delete;
    GlobalMemory& operator=(GlobalMemory&&) = delete;
};

GlobalMemory* get_memory_on_gpu(int device);
void release_memory_on_gpu(int device);

#endif  // HIQ_WITH_CUDA
#endif  // CUDA_GPU_H
