// x86 instruction set detection
// Based on Agner Fog's C++ vector class library:
// http://www.agner.org/optimize/vectorclass.zip
// (c) Copyright 2012-2021 Agner Fog.
// Apache License version 2.0 or later.

#include "instrset.hpp"

#if defined(__aarch64__)

InstrSet agner::InstrSetDetect()
{
    return InstrSet::Unknown;
}

bool agner::isSupported(InstrSet)
{
    return true;
}

#else

#    include <x86intrin.h>

#    include <array>
#    include <cstdint>

// Define interface to cpuid instruction.
// input:  eax = functionnumber, ecx = 0
// output: eax = output[0], ebx = output[1], ecx = output[2], edx = output[3]
static inline void cpuid(std::array<uint32_t, 4>& output, int functionnumber)
{
    uint32_t a(0);
    uint32_t b(0);
    uint32_t c(0);
    uint32_t d(0);
    __asm("cpuid" : "=a"(a), "=b"(b), "=c"(c), "=d"(d) : "a"(functionnumber), "c"(0) :);  // NOLINT(hicpp-no-assembler)
    output[0] = a;
    output[1] = b;
    output[2] = c;
    output[3] = d;
}

static constexpr auto CPUID_FEATURE = 7U;
static constexpr auto CPUID_AAVX512_FEATURE = uint32_t(0xD);
static constexpr auto AVX512_FEATURE = uint32_t(0x60);
static constexpr auto AVX512BW_FEATURE = uint32_t(0x40020000);

// Define interface to xgetbv instruction
static inline uint64_t xgetbv(int ctr)
{
    uint64_t a(0);
    uint64_t d(0);
    __asm("xgetbv" : "=a"(a), "=d"(d) : "c"(ctr) :);  // NOLINT(hicpp-no-assembler)
    // NOLINTNEXTLINE(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
    return a | (d << 32U);
}

auto agner::InstrSetDetect() -> InstrSet
{
    static InstrSet iset = InstrSet::Unknown;

    if (iset != InstrSet::Unknown) {
        return iset;
    }

    iset = InstrSet::I80386;                      // default value
    std::array<uint32_t, 4> abcd = {0, 0, 0, 0};  // cpuid results
    cpuid(abcd, 0);                               // call cpuid function 0
    if (abcd[0] == 0U) {
        return iset;  // no further cpuid function supported
    }
    cpuid(abcd, 1);  // call cpuid function 1 for feature flags
    if ((abcd[3] & (1U << 0U)) == 0U) {
        return iset;  // no floating point
    }
    if ((abcd[3] & (1U << 23U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no MMX
        return iset;
    }
    if ((abcd[3] & (1U << 15U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no conditional move
        return iset;
    }
    if ((abcd[3] & (1U << 24U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no FXSAVE
        return iset;
    }
    if ((abcd[3] & (1U << 25U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no SSE
        return iset;
    }

    // 1: SSE supported
    iset = InstrSet::SSE;
    if ((abcd[3] & (1U << 26U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no SSE2
        return iset;
    }

    // 2: SSE2 supported
    iset = InstrSet::SSE2;
    if ((abcd[2] & (1U << 0U)) == 0U) {
        // no SSE3
        return iset;
    }

    // 3: SSE3 supported
    iset = InstrSet::SSE3;
    if ((abcd[2] & (1U << 9U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no SSSE3
        return iset;
    }

    // 4: SSSE3 supported
    iset = InstrSet::SSSE3;
    if ((abcd[2] & (1U << 19U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no SSE4.1
        return iset;
    }

    // 5: SSE4.1 supported
    iset = InstrSet::SSE41;
    if ((abcd[2] & (1U << 23U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no POPCNT
        return iset;
    }
    if ((abcd[2] & (1U << 20U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no SSE4.2
        return iset;
    }

    // 6: SSE4.2 supported
    iset = InstrSet::SSE42;
    if ((abcd[2] & (1U << 27U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no OSXSAVE
        return iset;
    }
    if ((xgetbv(0) & 6U) != 6U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // AVX not enabled in O.S.
        return iset;
    }
    if ((abcd[2] & (1U << 28U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        return iset;                      // no AVX
    }

    // 7: AVX supported
    iset = InstrSet::AVX;
    // call cpuid leaf 7 for feature flags
    cpuid(abcd, 7U);                     // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
    if ((abcd[1] & (1U << 5U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no AVX2
        return iset;
    }

    // 8: AVX2 supported
    iset = InstrSet::AVX2;
    if ((abcd[1] & (1U << 16U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no AVX512
        return iset;
    }
    // call cpuid leaf 0xD for feature flags
    cpuid(abcd, CPUID_AAVX512_FEATURE);
    if ((abcd[0] & AVX512_FEATURE) != AVX512_FEATURE) {
        // no AVX512
        return iset;
    }

    // 9: AVX512F supported
    iset = InstrSet::AVX512F;
    // call cpuid 7 leaf for feature flags
    cpuid(abcd, CPUID_FEATURE);
    if ((abcd[1] & (1U << 31U)) == 0U) {  // NOLINT(cppcoreguidelines-avoid-magic-numbers,readability-magic-numbers)
        // no AVX512VL
        return iset;
    }

    // 10: AVX512VL supported
    iset = InstrSet::AVX512VL;
    if ((abcd[1] & AVX512BW_FEATURE) != AVX512BW_FEATURE) {
        // no AVX512BW, AVX512DQ
        return iset;
    }

    // 11: AVX512BW, AVX512DQ supported
    iset = InstrSet::AVX512BW_DQ;

    return iset;
}

bool agner::isSupported(InstrSet iset)
{
    if (iset == InstrSet::Unknown) {
        return false;
    }

    InstrSet isetMax = InstrSetDetect();
    return (iset <= isetMax);
}
#endif  // __aarch64__
