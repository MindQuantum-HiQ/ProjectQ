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

#ifndef DISPATCH_HPP
#define DISPATCH_HPP

#include "debug_info.hpp"
#include "for_each.hpp"
#include "kernel_counter.hpp"
#include "to_array.hpp"

#include <climits>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <iostream>
#include <tuple>
#include <type_traits>

#if defined(HIQ_WITH_CUDA)
#    include "nvidia/check.h"
#    include "nvidia/gmem.h"

extern "C" void* load_m_const(const void* data, size_t size);
#endif  // HIQ_WITH_CUDA

namespace details
{
#ifdef HIQ_WITH_CUDA
    GlobalMemory* global(nullptr);
#endif  // HIQ_WITH_CUDA

    template <unsigned int N, typename M>
    inline const auto& toArray(M const& m)
    {
        return *reinterpret_cast<const std::array<std::array<std::complex<double>, 1UL << N>, 1UL << N>*>(&m[0]);
    }

    template <int N, typename UINT>
    inline auto& toArray1d(UINT* d)
    {
        return *reinterpret_cast<const std::array<UINT, N>*>(d);
    }

}  // namespace details

namespace traits
{
    template <typename T>
    struct is_tuple : public std::false_type  // NOLINT
    {};

    template <typename... args_t>
    struct is_tuple<std::tuple<args_t...>> : public std::true_type
    {};

    template <typename T>
    inline constexpr auto is_tuple_v = is_tuple<std::remove_cv_t<std::remove_reference_t<T>>>::value;

    template <typename T>
    struct m_traits
    {
        template <int N>
        static inline const auto& convert(const T& m)
        {
            return details::toArray<N>(m);
        }
    };

    template <typename M, typename MT>
    struct m_traits<std::tuple<M, MT>>
    {
        template <int N>
        static inline const auto& convert(const std::tuple<M, MT>& m)
        {
            return m;
        }
    };

    template <int N, typename M>
    inline const auto& get_m(M const& m)
    {
        return m_traits<M>::template convert<N>(m);
    }
}  // namespace traits

template <int N, typename K, int CTRLMASK, typename UINT, typename BITMASK, class V, class M, typename D, typename BM,
          typename BO>
inline void kernel_body(const BITMASK& ii, const BM bitMask, const BO bitOffset, V psi, M const& m_,
                        const UINT ctrlmask, const D d, const D ds)
{
    const auto& m = traits::get_m<N>(m_);

    // TODO(damien): Can further use SIMD here
    UINT i = (ii & bitMask[N]) >> bitOffset[N];
    for (int jj = 0; jj < N; jj++) {
        i += ((ii & bitMask[jj]) >> bitOffset[jj]) * ds[jj];
    }

    if constexpr (CTRLMASK == 0) {  // NOLINT: old version of clang-tidy do not handle this well...
        K::core(psi, i, d, m);
    }
    else {
        if ((i & ctrlmask) == ctrlmask) {
            K::core(psi, i, d, m);
        }
    }
}

template <typename BITMASK, typename BITMASK_DIFF, int N, typename K, int CTRLMASK, class V, class M, typename UINT>
inline void kernel_loop(const BITMASK& maskBitSize, const std::array<unsigned, N + 1>& bitSize, V& psi_, M const& m_,
                        const UINT ctrlmask, const std::array<UINT, N>& d, const std::array<UINT, N>& ds)
{
    const BITMASK upperBound = (CHAR_BIT * sizeof(BITMASK) == maskBitSize) ? ~BITMASK(0U)
                                                                           : (BITMASK(1U) << maskBitSize) - 1U;

    // Generate bitmasks for multiindex parts.
    std::array<BITMASK, N + 1> bitMask;
    for (int jj = 0; jj < N + 1; jj++) {
        bitMask[jj] = BITMASK((1 << bitSize[jj]) - 1);  // NOLINT
    }

    // Shift bitmasks to position them one after another.
    // Generate bitmasks shifts (prefix sum of bitmasks sizes)
    std::array<BITMASK, N + 1> bitOffset;
    bitOffset[0] = 0U;
    for (int jj = 1; jj < N + 1; jj++) {
        bitOffset[jj] = bitSize[jj - 1] + bitOffset[jj - 1];  // NOLINT
        bitMask[jj] <<= bitOffset[jj];
    }

#if defined(HIQ_WITH_CUDA)
    std::complex<double>* psi = reinterpret_cast<std::complex<double>*>(
        details::global->alloc(sizeof(psi[0]) * psi_.size()));
    details::global->copy(psi, psi_.data(), sizeof(psi[0]) * psi_.size());
    const std::complex<double>* m = reinterpret_cast<const std::complex<double>*>(
        load_m_const(&m_[0], (1 << N) * (1 << N) * sizeof(m[0])));
#else
    std::complex<double>* psi = &psi_[0];
#    ifdef INTRIN
    const auto tmp_ = K::create_m(m_);
    const auto m = std::make_tuple(tmp_, utils::make_hermitian_array(tmp_));
#    else
    const std::complex<double>* m = &m_[0];
#    endif  // INTRIN
#endif      // HIQ_WITH_CUDA

    details::kernel_counter<BITMASK, BITMASK_DIFF, 0> ii(upperBound);

    parallel::for_each(ii, [bitMask, bitOffset, psi, m, ctrlmask, d, ds](BITMASK ii) {
        kernel_body<N, K, CTRLMASK, UINT>(ii, bitMask, bitOffset, psi, m, ctrlmask, d, ds);
    });

#if defined(HIQ_WITH_CUDA)
    // Copy back psi
    details::global->copy(psi_.data(), psi, sizeof(psi[0]) * psi_.size());
    details::global->free();
#endif  // HIQ_WITH_CUDA

    // Run the last iteration separately to avoid a possible index type overflow.
    if constexpr (traits::is_tuple_v<decltype(m)>) {
        kernel_body<N, K, CTRLMASK, UINT>(upperBound, bitMask, bitOffset, &psi_[0], m, ctrlmask, d, ds);
    }
    else {
        kernel_body<N, K, CTRLMASK, UINT>(upperBound, bitMask, bitOffset, &psi_[0], m_, ctrlmask, d, ds);
    }
}

template <typename T>
constexpr auto BITSIZE(T v)
{
    if (v) {
        return static_cast<unsigned>(CHAR_BIT) * sizeof(int) - __builtin_clz(v);
    }
    return 0UL;
}

template <typename T, typename U>
constexpr auto ROUNDUP(T v, U to)
{
    return ((v) + (to) -1U) & -(to);  // NOLINT(hicpp-signed-bitwise)
}

template <int N, typename K, int CTRLMASK, class V, class M, typename UINT>
inline void kernel_dispatch(V& psi, M const& m, UINT ctrlmask, const unsigned* id)
{
#ifdef HIQ_WITH_CUDA
    int device(0);
    cudaGetDevice(&device);
    details::global = get_memory_on_gpu(device);
#endif  // HIQ_WITH_CUDA

    std::array<UINT, N> d;
    std::array<UINT, N> ds;
    for (int i = 0; i < N; i++) {
        d[i] = UINT(1) << id[i];  // NOLINT
        ds[i] = d[i] * 2U;
    }
    std::sort(begin(ds), end(ds), std::greater<UINT>());
    std::array<UINT, N + 1> de;
    de[0] = psi.size() / ds[0];
    for (int i = 1; i < N; i++) {
        de[i] = ds[i - 1] / 2U / ds[i];
    }
    de[N] = ds[N - 1] / 2U;

    // Calculate the total size of bitmask.
    size_t maskBitSize = 0;
    std::array<unsigned, N + 1> bitSize;
    for (int i = 0; i < N + 1; i++) {
        bitSize[i] = BITSIZE(de[i] - 1);
        maskBitSize += bitSize[i];
        debug::printf("%zu bit size = %zu\n", static_cast<size_t>(de[i] - 1U), static_cast<size_t>(bitSize[i]));
    }
    size_t maskByteSize = ROUNDUP(maskBitSize, CHAR_BIT) / static_cast<size_t>(CHAR_BIT);

    debug::printf("Required bitmask size = %zu bits (%zu bytes)\n", maskBitSize, maskByteSize);

    // Select the loop index type, based on the required bit population
    switch (maskByteSize) {
        case 0:
        case 1:
            kernel_loop<uint8_t, int16_t, N, K, CTRLMASK>(maskBitSize, bitSize, psi, m, ctrlmask, d, ds);
            break;
        case 2:
            kernel_loop<uint16_t, int32_t, N, K, CTRLMASK>(maskBitSize, bitSize, psi, m, ctrlmask, d, ds);
            break;
        case 3:
        case 4:
            kernel_loop<uint32_t, int64_t, N, K, CTRLMASK>(maskBitSize, bitSize, psi, m, ctrlmask, d, ds);
            break;
        case 5:  // NOLINT
        case 6:  // NOLINT
        case 7:  // NOLINT
        case 8:  // NOLINT
        default:
            std::cerr << "The bitmask size of > 4 bytes is not supported\n";
            exit(-1);  // NOLINT
    }

#ifdef HIQ_WITH_CUDA
    details::global = nullptr;
#endif  // HIQ_WITH_CUDA
}

#undef BITSIZE
#undef ROUNDUP

#endif  // DISPATCH_HPP
