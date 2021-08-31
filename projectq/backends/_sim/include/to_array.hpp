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

#ifndef TO_ARRAY_HPP
#define TO_ARRAY_HPP

#include <array>
#include <cstddef>
#include <type_traits>
#include <utility>

#ifdef INTRIN
#    if defined(__AVX2__)
#        include <immintrin.h>
#    elif defined(__aarch64__)
#        include "neon_functions.hpp"

#        include <arm_neon.h>
#    endif  // __AVX2__
#endif      // INTRIN

namespace utils
{
#if __cplusplus > 201703L
    template <class T, std::size_t N>
    constexpr auto to_array(T (&a)[N])
    {
        return std::to_array(a);
    }
#else
    namespace detail
    {
        template <class T, std::size_t N, std::size_t... I>
        inline constexpr std::array<std::remove_cv_t<T>, N> to_array_impl(T (&a)[N],  // NOLINT
                                                                          std::index_sequence<I...> /*unused*/)
        {
            return {{a[I]...}};
        }

    }  // namespace detail

    template <class T, std::size_t N>
    constexpr auto to_array(T (&a)[N])  // NOLINT
    {
        return detail::to_array_impl(a, std::make_index_sequence<N>{});
    }
#endif

    template <typename T, typename... args_t>
    auto make_array(args_t&&... args)
    {
        return std::array<T, sizeof...(args)>{std::forward<args_t>(args)...};
    }

    template <typename T, typename... args_t>
    auto make_matrix(args_t&&... args)
    {
        // Make sure that we have 2^n elements
        static_assert(!(sizeof...(args) & (sizeof...(args) - 1UL)));
        return make_array<T>(std::forward<args_t>(args)...);
    }

#ifdef INTRIN
#    if defined(__AVX2__)
    using intrin_t = __m256d;
    static constexpr intrin_t neg = {1., -1., 1., -1.};

    inline auto intrin_permute_5(intrin_t a)
    {
        return _mm256_permute_pd(a, 5);
    }

    inline auto intrin_mul_pd(intrin_t a, intrin_t b)
    {
        return _mm256_mul_pd(a, b);
    }
#    elif defined(__aarch64__)
    using intrin_t = float64x2x2_t;
    static constexpr float64x2x2_t neg = {1.0, -1.0, 1.0, -1.0};

    inline auto intrin_permute_5(intrin_t a)
    {
        return vpermq_f64_x2<5>(a);
    }

    inline auto intrin_mul_pd(intrin_t a, intrin_t b)
    {
        return vmulq_f64_x2(a, b);
    }
#    endif  // __AVX2__

    // Very minimalistic std::array-like class to store intrinsics values and avoid -Wignored-attributes warnings
    // from GCC
    template <std::size_t N>
    struct intrin_array
    {
        using value_type = intrin_t;
        using pointer = value_type*;
        using const_pointer = const value_type*;
        using reference = value_type&;
        using const_reference = const value_type&;
        using iterator = value_type*;
        using const_iterator = const value_type*;
        using size_type = std::size_t;
        using difference_type = std::ptrdiff_t;
        // No reverse_iterator because std::reverse_iterator takes a template argument...

        // No explicit construct/copy/destroy for aggregate types

        constexpr reference operator[](size_type n) noexcept
        {
            return data_[n];
        }

        constexpr const_reference operator[](size_type n) const noexcept
        {
            return data_[n];
        }

        intrin_t data_[N];
    };

    template <std::size_t N, std::size_t... indices>
    auto make_hermitian_array_impl(const intrin_array<N>& m, std::index_sequence<indices...>)
    {
        return intrin_array<N>{intrin_mul_pd(intrin_permute_5(m[indices]), neg)...};
    }

    template <std::size_t N>
    auto make_hermitian_array(const intrin_array<N>& m)
    {
        return make_hermitian_array_impl(m, std::make_index_sequence<N>{});
    }
#endif  // INTRIN
}  // namespace utils
#endif /* TO_ARRAY_HPP */
