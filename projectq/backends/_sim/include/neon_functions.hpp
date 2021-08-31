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

#ifndef NEON_FUNCTIONS_HPP
#define NEON_FUNCTIONS_HPP

#ifdef __aarch64__
#    include <arm_neon.h>

inline float64x2x2_t vdupq_n_f64_x2(double a)
{
    auto tmp = vmov_n_f64(a);
    return {vcombine_f64(tmp, tmp), vcombine_f64(tmp, tmp)};
}

inline void vst1q_f64_x2(float64_t* hi, float64_t* lo, float64x2x2_t a)
{
    vst1q_f64(hi, a.val[0]);
    vst1q_f64(lo, a.val[1]);
}

inline float64x2x2_t vhsubq_f64_x2(float64x2x2_t a, float64x2x2_t b)
{
    return {vcombine_f64(vsub_f64(vget_low_f64(a.val[0]), vget_high_f64(a.val[0])),
                         vsub_f64(vget_low_f64(b.val[0]), vget_high_f64(b.val[0]))),
            vcombine_f64(vsub_f64(vget_low_f64(a.val[1]), vget_high_f64(a.val[1])),
                         vsub_f64(vget_low_f64(b.val[1]), vget_high_f64(b.val[1])))};
}

template <uint8_t imm8>
float64x2x2_t vpermq_f64_x2(float64x2x2_t a)
{
    float64x2x2_t res;
    if constexpr (imm8 & 1U && (imm8 >> 1U) & 1U) {
        res.val[0] = vcombine_f64(vget_high_f64(a.val[0]), vget_high_f64(a.val[0]));
    }
    else if constexpr ((imm8 >> 1U) & 1U) {
        res.val[0] = vcombine_f64(vget_low_f64(a.val[0]), vget_high_f64(a.val[0]));
    }
    else if constexpr (imm8 & 1U) {
        res.val[0] = vcombine_f64(vget_high_f64(a.val[0]), vget_low_f64(a.val[0]));
    }
    else {
        res.val[0] = vcombine_f64(vget_low_f64(a.val[0]), vget_low_f64(a.val[0]));
    }

    if constexpr ((imm8 >> 2U) & 1U && (imm8 >> 3U) & 1U) {
        res.val[1] = vcombine_f64(vget_high_f64(a.val[1]), vget_high_f64(a.val[1]));
    }
    else if constexpr ((imm8 >> 3U) & 1U) {
        res.val[1] = vcombine_f64(vget_low_f64(a.val[1]), vget_high_f64(a.val[1]));
    }
    else if constexpr ((imm8 >> 2U) & 1U) {
        res.val[1] = vcombine_f64(vget_high_f64(a.val[1]), vget_low_f64(a.val[1]));
    }
    else {
        res.val[1] = vcombine_f64(vget_low_f64(a.val[1]), vget_low_f64(a.val[1]));
    }

    return res;
}

inline float64x2x2_t vmulq_f64_x2(float64x2x2_t a, float64x2x2_t b)
{
    return {vmulq_f64(a.val[0], b.val[0]), vmulq_f64(a.val[1], b.val[1])};
}

#endif  // __aarch64__
#endif  /* NEON_FUNCTIONS_HPP */
