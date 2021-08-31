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

#include "check.h"
#include "gmem.h"

#include <cstdio>
#include <map>
#include <memory>

using namespace std;

bool GlobalMemory::init()
{
    if (fatalError != cudaSuccess) {
        return false;
    }

    return true;
}

bool GlobalMemory::isAvailable()
{
    if (!init()) {
        return false;
    }

    return (ngpus > 0);
}

void* GlobalMemory::alloc(size_t size)
{
#define MALLOC_ALIGNMENT 256

    if (!init()) {
        return NULL;
    }

    if (!gmem) {
        return NULL;
    }

    if (ptr + size + MALLOC_ALIGNMENT > gmem + szgmem) {
        return NULL;
    }

    void* result = ptr;
    ptr += size;

    ptrdiff_t alignment = (ptrdiff_t) ptr % MALLOC_ALIGNMENT;
    if (alignment) {
        ptr += MALLOC_ALIGNMENT - alignment;
    }

    return result;
}

// Reset free memory pointer to the beginning of preallocated buffer.
void GlobalMemory::free()
{
    if (!init()) {
        return;
    }

    ptr = gmem;
}

// Check whether the specified memory address belongs to GPU memory allocation.
bool GlobalMemory::isAllocatedOnGPU(const void* ptr)
{
    if (!init()) {
        return false;
    }

    if (!gmem) {
        return false;
    }

    if ((ptr >= gmem) && (ptr <= gmem + szgmem)) {
        return true;
    }

    return false;
}

cudaError_t GlobalMemory::set(void* dst, const int val, size_t size)
{
    if (!init()) {
        return {cudaErrorNoDevice};
    }

    cudaError_t cudaError;
    CUDA_ERR_CHECK(cudaError = cudaMemset(dst, val, size));
    if (cudaError != cudaSuccess) {
        fatalError = cudaError;
        return {fatalError};
    }

    return {cudaError};
}

cudaError_t GlobalMemory::copy(void* dst, const void* src, size_t size)
{
    if (!init()) {
        return {cudaErrorNoDevice};
    }

    cudaMemcpyKind kind = cudaMemcpyDeviceToHost;
    if (isAllocatedOnGPU(dst) && isAllocatedOnGPU(src)) {
        kind = cudaMemcpyDeviceToDevice;
    }
    else if (!isAllocatedOnGPU(dst) && !isAllocatedOnGPU(src)) {
        kind = cudaMemcpyHostToHost;
    }
    else if (isAllocatedOnGPU(dst) && !isAllocatedOnGPU(src)) {
        kind = cudaMemcpyHostToDevice;
    }

    cudaError_t cudaError;
    CUDA_ERR_CHECK(cudaError = cudaMemcpy(dst, src, size, kind));
    if (cudaError != cudaSuccess) {
        fatalError = cudaError;
        return {fatalError};
    }

    return {cudaError};
}

cudaError_t GlobalMemory::getLastError()
{
    // If GPU is not initialized, then there is either no
    // device or fatal error during initialization.
    if (!init()) {
        return {fatalError};
    }

    return {cudaGetLastError()};
}

GlobalMemory::GlobalMemory() : fatalError(cudaSuccess), ngpus(0), gmem(NULL), ptr(NULL)
{
    cudaError_t cudaError;

#define CUDA_RETURN_ON_ERR(x)                                                                                          \
    do {                                                                                                               \
        CUDA_ERR_CHECK(x);                                                                                             \
        if (cudaError != cudaSuccess) {                                                                                \
            fatalError = cudaError;                                                                                    \
            return;                                                                                                    \
        }                                                                                                              \
    } while (0)

    CUDA_ERR_CHECK(cudaError = cudaGetDeviceCount(&ngpus));
    if ((cudaError != cudaSuccess) && (cudaError != cudaErrorNoDevice)) {
        fatalError = cudaError;
        return;
    }

    if (!ngpus) {
        return;
    }

    // Preallocate 85% of GPU memory to save on costly allocations/deallocations.
    size_t available, total;
    CUDA_RETURN_ON_ERR(cudaError = cudaMemGetInfo(&available, &total));

    szgmem = (size_t) (0.85 * available);

    CUDA_RETURN_ON_ERR(cudaError = cudaMalloc(&gmem, szgmem));

    ptr = gmem;

#undef CUDA_RETURN_ON_ERR
}

GlobalMemory::~GlobalMemory()
{
    cudaFree(gmem);
}

// ==============================================================================

static std::map<int, std::unique_ptr<GlobalMemory>> global_memory_;

GlobalMemory* get_memory_on_gpu(int device)
{
    if (auto it = global_memory_.find(device); it != std::end(global_memory_)) {
        return it->second.get();
    }
    else {
        auto [it_new, _] = global_memory_.emplace(device, std::make_unique<GlobalMemory>());
        return it_new->second.get();
    }
}

void release_memory_on_gpu(int device)
{
    global_memory_.erase(device);
}
