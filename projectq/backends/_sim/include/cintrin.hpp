// Copyright 2017 ProjectQ-Framework (www.projectq.ch)
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

#ifndef CINTRIN_HPP_
#define CINTRIN_HPP_

#if defined(NOINTRIN) || !defined(INTRIN)

template <class T>
inline T add(const T a, const T b)
{
    return a + b;
}

template <class T>
inline T mul(const T a, const T b)
{
    return a * b;
}

#else
#    include <complex>
#    include <utility>

#    if defined(__AVX2__)
#        include <immintrin.h>

namespace details
{
    using intrin_t = __m256d;
}  // namespace details

#        ifndef _mm256_set_m128d
#            define _mm256_set_m128d(hi, lo) _mm256_insertf128_pd(_mm256_castpd128_pd256(lo), (hi), 0x1)
#        endif
#        ifndef _mm256_storeu2_m128d
#            define _mm256_storeu2_m128d(hiaddr, loaddr, a)                                                            \
                do {                                                                                                   \
                    __m256d _a = (a);                                                                                  \
                    _mm_storeu_pd((loaddr), _mm256_castpd256_pd128(_a));                                               \
                    _mm_storeu_pd((hiaddr), _mm256_extractf128_pd(_a, 0x1));                                           \
                } while (0)
#        endif
#        ifndef _mm256_loadu2_m128d
#            define _mm256_loadu2_m128d(hiaddr, loaddr) _mm256_set_m128d(_mm_loadu_pd(hiaddr), _mm_loadu_pd(loaddr))
#        endif

#        define _intrin_store_high_low(hiaddr, loaddr, a) _mm256_storeu2_m128d(hiaddr, loaddr, a)

#    elif defined(__aarch64__)
#        include "neon_functions.hpp"

#        include <arm_neon.h>

namespace details
{
    using intrin_t = float64x2x2_t;
}  // namespace details

#        define _intrin_store_high_low(hiaddr, loaddr, a) vst1q_f64_x2(hiaddr, loaddr, a)
#    else
#        error Unsupported compiler intrinsics
#    endif  // __AVX2__

// =============================================================================

namespace details
{
    template <class T>
    class cintrin;

    template <>
    class cintrin<double>
    {
    public:
        using calc_t = double;
        using ret_t = cintrin<calc_t>;

        cintrin() = default;

        template <class U>
        explicit cintrin(U const* p)
            :
#    ifdef __AVX2__
            v_(_mm256_load_pd(static_cast<calc_t const*>(p)))
#    else   /* defined(__aarch64__) */
            v_(vld1q_f64_x2(static_cast<calc_t const*>(p)))
#    endif  // __AVX2__
        {}

        template <class U>
        cintrin(U const* p1, U const* p2)
            :
#    ifdef __AVX2__
            v_(_mm256_loadu2_m128d(static_cast<calc_t const*>(p2), static_cast<calc_t const*>(p1)))
#    else   /* defined(__aarch64__) */
            v_({vld1q_f64(static_cast<const calc_t*>(p2)), vld1q_f64(static_cast<const calc_t*>(p1))})
#    endif  // __AVX2__
        {}

        template <class U>
        cintrin(U const* p, bool /* broadcast */)
#    ifdef __aarch64__
            : v_({vld1q_f64(static_cast<const calc_t*>(p)), vld1q_f64(static_cast<const calc_t*>(p))})
#    endif  // __aarch64__
        {
#    ifdef __AVX2__
            const auto tmp = _mm_load_pd(static_cast<calc_t const*>(p));
            v_ = _mm256_broadcast_pd(&tmp);
#    endif  // __AVX2__
        }

        explicit cintrin(calc_t const& s1)
            :
#    ifdef __AVX2__
            v_(_mm256_set1_pd(s1))
#    else   /* defined(__aarch64__) */
            v_(vdupq_n_f64_x2(s1))
#    endif  // __AVX2__
        {}

        explicit cintrin(intrin_t const& v) : v_(v)
        {}

        std::complex<calc_t> operator[](unsigned i)
        {
            calc_t v[4];
#    ifdef __AVX2__
            _mm256_store_pd(v, v_);
#    else   /* defined(__aarch64__) */
            vst1q_f64_x2(v, v_);
#    endif  // __AVX2__
            return {v[i * 2UL], v[i * 2UL + 1UL]};
        }

        template <class U>
        void store(U* p) const
        {
#    ifdef __AVX2__
            _mm256_store_pd((calc_t*) p, v_);
#    else   /* defined(__aarch64__) */
            vst1q_f64_x2((calc_t*) p, v_);
#    endif  // __AVX2__
        }

        template <class U>
        void store(U* p1, U* p2) const
        {
#    ifdef __AVX2__
            _mm256_storeu2_m128d(static_cast<calc_t*>(p2), static_cast<calc_t*>(p1), v_);
#    else   /* defined(__aarch64__) */
            vst1q_f64((calc_t*) p2, v_.val[0]);
            vst1q_f64((calc_t*) p1, v_.val[1]);
#    endif  // __AVX2__
        }
        intrin_t v_;
    };

    // =============================================================================

    inline intrin_t mul(intrin_t const& c1, intrin_t const& c2, intrin_t const& c2tm)
    {
#    ifdef __AVX2__
        auto ac_bd = _mm256_mul_pd(c1, c2);
        auto multbmadmc = _mm256_mul_pd(c1, c2tm);
        return _mm256_hsub_pd(ac_bd, multbmadmc);
#    else   /* defined(__aarch64__) */
        auto ac_bd = vmulq_f64_x2(c1, c2);
        auto multbmadmc = vmulq_f64_x2(c1, c2tm);
        return vhsubq_f64_x2(ac_bd, multbmadmc);
#    endif  // __AVX2__
    }
    inline intrin_t add(intrin_t const& c1, intrin_t const& c2)
    {
#    ifdef __AVX2__
        return _mm256_add_pd(c1, c2);
#    else   /* defined(__aarch64__) */
        return {vaddq_f64(c1.val[0], c2.val[0]), vaddq_f64(c1.val[1], c2.val[1])};
#    endif  // __AVX2__
    }

    inline cintrin<double> mul(cintrin<double> const& c1, cintrin<double> const& c2, cintrin<double> const& c2tm)
    {
#    ifdef __AVX2__
        auto ac_bd = _mm256_mul_pd(c1.v_, c2.v_);
        auto multbmadmc = _mm256_mul_pd(c1.v_, c2tm.v_);
        return cintrin<double>(_mm256_hsub_pd(ac_bd, multbmadmc));
#    else   /* defined(__aarch64__) */
        const auto ac_bd = vmulq_f64_x2(c1.v_, c2.v_);
        const auto multbmadmc = vmulq_f64_x2(c1.v_, c2tm.v_);
        return cintrin<double>(vhsubq_f64_x2(ac_bd, multbmadmc));
#    endif  // __AVX2__
    }
    inline cintrin<double> operator*(cintrin<double> const& c1, cintrin<double> const& c2)
    {
#    ifdef __AVX2__
        intrin_t neg = _mm256_setr_pd(1.0, -1.0, 1.0, -1.0);
        auto badc = _mm256_permute_pd(c2.v_, 5);
        auto bmadmc = _mm256_mul_pd(badc, neg);
        return cintrin<double>(mul(c1.v_, c2.v_, bmadmc));
#    else   /* defined(__aarch64__) */
        intrin_t neg = {1., -1., 1., -1.};
        const auto badc = vpermq_f64_x2<5>(c2.v_);
        const auto bmadmc = vmulq_f64_x2(badc, neg);
        return mul(c1, c2, cintrin<double>(bmadmc));
#    endif  // __AVX2__
    }
    inline cintrin<double> operator+(cintrin<double> const& c1, cintrin<double> const& c2)
    {
#    ifdef __AVX2__
        return cintrin<double>(_mm256_add_pd(c1.v_, c2.v_));
#    else   /* defined(__aarch64__) */
        intrin_t tmp = {vaddq_f64(c1.v_.val[0], c2.v_.val[0]), vaddq_f64(c1.v_.val[1], c2.v_.val[1])};
        return cintrin<double>(tmp);
#    endif  // __AVX2__
    }
    inline cintrin<double> operator*(cintrin<double> const& c1, double const& d)
    {
#    ifdef __AVX2__
        auto d_d = _mm256_set1_pd(d);
        return cintrin<double>(_mm256_mul_pd(c1.v_, d_d));
#    else   /* defined(__aarch64__) */
        const auto d_d = vdupq_n_f64_x2(d);
        return vmulq_f64_x2(c1.v_, d_d);
#    endif  // __AVX2__
    }
    inline cintrin<double> operator*(double const& d, cintrin<double> const& c1)
    {
        return c1 * d;
    }

    template <class U>
    inline intrin_t load2(U* p)
    {
#    ifdef __AVX2__
        const auto tmp = _mm_load_pd((double const*) p);
        return _mm256_broadcast_pd(&tmp);
#    else   /* defined(__aarch64__) */
        const auto tmp = vld1q_f64(static_cast<const calc_t*>(p));
        return {tmp, tmp};
#    endif  // __AVX2__
    }
    template <class U>
    inline intrin_t load(U const* p1, U const* p2)
    {
#    ifdef __AVX2__
        return _mm256_loadu2_m128d(reinterpret_cast<double const*>(p2), reinterpret_cast<double const*>(p1));
#    else   /* defined(__aarch64__) */
        return {vld1q_f64(reinterpret_cast<const calc_t*>(p2)), vld1q_f64(reinterpret_cast<const calc_t*>(p1))};
#    endif  // __AVX2__
    }

}  // namespace details

#endif  // NOINTRIN || !INTRIN
#endif  // CINTRIN_HPP_
