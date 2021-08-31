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

#include "debug_info.hpp"
#include "gmem.h"
#include "nvidia/check.h"

#include <cuda.h>

#include <dlfcn.h>

#include <cstdio>
#include <fstream>
#include <iterator>
#include <map>
#include <string>
#include <vector>

__device__ double2 m_const[32 * 32];  // kernel5 (1 << N) * (1 << N)

extern "C" void* load_m_const(const void* data, size_t size)
{
    if (size > sizeof(m_const)) {
        fprintf(stderr, "load_m_const() size (%zu) does not fit the constant memory buffer (%zu)\n", size,
                sizeof(m_const));
        exit(-1);
    }

    void* ptr(nullptr);
    CUDA_ERR_CHECK(cudaGetSymbolAddress(&ptr, m_const));
    CUDA_ERR_CHECK(cudaMemcpyToSymbol(m_const, data, size));
    return ptr;
}

#ifdef CUDA_PGI_WORKAROUND

struct fatCubinStruct
{
    int magic;    // Always 0x466243b1
    int version;  // Sequence number of the cubin
    void* fat;    // The pointer to the real cubin
    void* other;  // Some pointer related to the data segment
};

// Working around a SIGSEGV in __pgi_cuda_register_fat_binaryA
// occuring specifically when compiling a pybind11 moddule with nvc++.
// Perhaps, PGI folks forgot to cover this in their tricky __PGI_CUDA_LOC
// anchor logic. This code is not portable and should go away once
// there is a fix from NVIDIA.

extern "C" void* __pgi_cuda_register_fat_binaryA(fatCubinStruct* fatCubin, void** pgi_cuda_loc);

extern "C" void* __pgi_cuda_register_fat_binary(fatCubinStruct* fatCubin)
{
    fatCubinStruct* __PGI_CUDA_LOC = (fatCubinStruct*) dlsym(nullptr, "__PGI_CUDA_LOC");
    __pgi_cuda_register_fat_binaryA(fatCubin, (void**) __PGI_CUDA_LOC);

    return __PGI_CUDA_LOC->other;
}

// Further working around cudaInvalidDeviceFunction error during cudaLaunch in PGI nvc++,
// when the code in compiled as a shared library.

#    define EXPECT(var, value)                                                                                         \
        expect(var, value,                                                                                             \
               (const char*) "The supported version of __cudaRegisterFunction() expects \"" #var                       \
                             "\" value to be equal to " #value "\n")

template <typename T, typename TVal>
inline void expect(const T& var, const TVal value, const char* msg)
{
    if (var != value) {
        fprintf(stderr, "%s", msg);
        exit(-1);
    }
}

CUmodule module = nullptr;

std::map<void*, std::pair<std::string, CUfunction>>* deviceFuns_ = nullptr;

// Override the internal CUDA kernels registration hook, in order to make our own index of
// the available CUDA kernels. Later on, we use this index to perform our own kernel launch
// sequence, which replaces PGI's runtime library issues.
extern "C" void __cudaRegisterFunction(void** fatCubinHandle_, const char* hostFun, char* deviceFun,
                                       const char* deviceName, int thread_limit, uint3* tid, uint3* bid, dim3* bDim,
                                       dim3* gDim, int* wSize)
{
    EXPECT(thread_limit, -1);
    EXPECT(tid, nullptr);
    EXPECT(bid, nullptr);
    EXPECT(bDim, nullptr);
    EXPECT(gDim, nullptr);
    EXPECT(wSize, nullptr);

    CUresult err;

    if (!module) {
        // Like cuInit(), but more appropriate.
        cudaSetDevice(0);

        CUdevice dev;
        err = cuCtxGetDevice(&dev);
        if (err != CUDA_SUCCESS) {
            fprintf(stderr, "Cannot get device from context, error = %d\n", err);
            exit(-1);
        }

        CUcontext ctx;
        err = cuDevicePrimaryCtxRetain(&ctx, dev);
        if (err != CUDA_SUCCESS) {
            fprintf(stderr, "Cannot retain device primary context, error = %d\n", err);
            exit(-1);
        }

        fatCubinStruct* fatCubinHandle = reinterpret_cast<fatCubinStruct*>(*fatCubinHandle_);
        char* fatbin = reinterpret_cast<char*>(fatCubinHandle->fat);
        unsigned char magic[] = {0x50, 0xed, 0x55, 0xba, 0x01, 0x00, 0x10, 0x00};
        if (memcmp(fatbin, magic, sizeof(magic))) {
            fprintf(stderr, "Could not match fatbin magic header\n");
            exit(-1);
        }

        std::vector<char> log(65536);

        // Set jit target from context (which we got by setting the device).
        CUjit_option options[] = {CU_JIT_TARGET /*CU_JIT_TARGET_FROM_CUCONTEXT*/, CU_JIT_ERROR_LOG_BUFFER,
                                  CU_JIT_ERROR_LOG_BUFFER_SIZE_BYTES};
        void* values[] = {(void*) CU_TARGET_COMPUTE_70 /*NULL*/, &log[0], (void*) log.size()};

        // Load the located CUDA fatbinary image into a "module" prepared for execution.
        // This call may also choose to JIT-compile the PTX assembly, if provided within a fatbinary.
        err = cuModuleLoadDataEx(&module, &fatbin[0], sizeof(options) / sizeof(options[0]), options, values);
        if (err != CUDA_SUCCESS) {
            fprintf(stderr, "Could not load CUDA module, error = %d, log = \"%s\"\n", (int) err, &log[0]);
            exit(-1);
        }
    }

    if (!deviceFuns_) {
        // Deferred map creation, to make sure we are not overrunning its C++ static
        // constructor, as __cudaRegisterFunction() calls may happen quite early at the startup.
        deviceFuns_ = new std::map<void*, std::pair<std::string, CUfunction>>();
    }

    // Cache the function pointer-name mapping.
    auto& deviceFuns = *deviceFuns_;
    deviceFuns[(void*) hostFun].first = deviceName;
}

#    undef EXPECT

extern "C" cudaError_t __cudaPopCallConfiguration(dim3* gridDim, dim3* blockDim, size_t* sharedMem, void*);

extern "C" int __pgiLaunchKernelFromStub(void* hostFun, void** argv, int argc)
{
    // Extract the functions pointer-name mapping.
    auto& deviceFuns = *deviceFuns_;
    auto& deviceName = deviceFuns.at(hostFun).first;
    if (deviceName == "") {
        fprintf(stderr, "Could not launch unknown CUDA function %p\n", hostFun);
        exit(-1);
    }

    CUresult err;

    // Lookup for a previously cached function.
    CUfunction& func = deviceFuns[(void*) hostFun].second;
    if (!func) {
        // Load function from module.
        err = cuModuleGetFunction(&func, module, deviceName.c_str());
        if (err != CUDA_SUCCESS) {
            fprintf(stderr, "Could not get CUDA kernel %s, error = %d\n", deviceName.c_str(), (int) err);
            exit(-1);
        }
    }

    // Extract the latest <<<...>>> kernel launch compute grid configuration,
    // which we will use to launch the kernel manually with CUDA Driver API.
    dim3 gridDim, blockDim;
    size_t sharedMem;
    cudaStream_t stream;
    __cudaPopCallConfiguration(&gridDim, &blockDim, &sharedMem, &stream);

    // Launch the kernel with CUDA Driver API.
    debug::printf("GPU kernel <(%d, %d, %d), (%d, %d, %d)>\n", (int) gridDim.x, (int) gridDim.y, (int) gridDim.z,
                  (int) blockDim.x, (int) blockDim.y, (int) blockDim.z);
    err = cuLaunchKernel(func, gridDim.x, gridDim.y, gridDim.z, blockDim.x, blockDim.y, blockDim.z, sharedMem, stream,
                         argv, NULL);
    if (err != CUDA_SUCCESS) {
        fprintf(stderr, "Could not launch CUDA kernel %s, error = %d\n", deviceName.c_str(), (int) err);
        exit(-1);
    }

    // We do not synchronize (wait) for the kernel to finish here, as it
    // should be provided by the caller. PGI, please manage at least this
    // simple task!

    return err;
}
#endif  // CUDA_PGI_WORKAROUND
