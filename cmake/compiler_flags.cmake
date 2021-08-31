# ==============================================================================
#
# Copyright 2020 <Huawei Technologies Co., Ltd>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# ==============================================================================

# C++ standard flags
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.18)
  set(CMAKE_CUDA_STANDARD 17)
  set(CMAKE_CUDA_STANDARD_REQUIRED ON)
else()
  # NB: this might be buggy due to the order in which CMake passes arguments to CUDA... You might want to try using
  # target_compile_options() or set_source_file_properties()
  add_compile_options("$<$<COMPILE_LANGUAGE:CUDA>:-std=c++17>")
endif()
set(CMAKE_CUDA_RUNTIME_LIBRARY SHARED)
set(CUDA_SEPARABLE_COMPILATION ON)

# Ideally this would work... but since these are just initializers for target properties and we cannot add those default
# properties without changing the CMake source code, we have to resort to manually setting the flag below...
set(CMAKE_NVCXX_STANDARD 17)
set(CMAKE_NVCXX_STANDARD_REQUIRED ON)
add_compile_options("$<$<COMPILE_LANGUAGE:NVCXX>:-std=c++17>")

set(CMAKE_NVCXX_RUNTIME_LIBRARY SHARED)
set(NVCXX_SEPARABLE_COMPILATION ON)

# Ideally this would work... but since these are just initializers for target properties and we cannot add those default
# properties without changing the CMake source code, we have to resort to manually setting the flag below...
set(CMAKE_DPCXX_STANDARD 17)
set(CMAKE_DPCXX_STANDARD_REQUIRED ON)
add_compile_options("$<$<COMPILE_LANGUAGE:DPCXX>:-std=c++17>")

# CUDA related flags nvc++-Error-Unknown switch: -flto
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION OFF)

# Always generate position independent code
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)

# RPATH settings... Funadamentally, we do not want to use RPATH but RUNPATH. In order to achieve this, we use a
# combination of these CMake options, some target properties (namely INSTALL_RPATH; see *_set_rpath macros in
# macros.cmake) and some linker flags (see linker_flags.cmake)
#
# All of this should achieve the desired effect on all platforms and compilers

set(CMAKE_BUILD_SKIP_RPATH TRUE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH FALSE)

# CMake usually does not add -I/usr/local/include to any compiler commands. This can lead to some issues on Mac OS when
# using the -isysroot option so we allow for explicit -I/usr/local/include on the command line.
if(APPLE)
  list(REMOVE_ITEM CMAKE_C_IMPLICIT_INCLUDE_DIRECTORIES /usr/local/include)
  list(REMOVE_ITEM CMAKE_CXX_IMPLICIT_INCLUDE_DIRECTORIES /usr/local/include)
  list(REMOVE_ITEM CMAKE_C_IMPLICIT_LINK_DIRECTORIES /usr/local/lib)
  list(REMOVE_ITEM CMAKE_CXX_IMPLICIT_LINK_DIRECTORIES /usr/local/lib)
endif()

# ------------------------------------------------------------------------------

test_compile_option(
  _compile_flags
  LANGS CXX DPCXX
  FLAGS "-fms-extensions" "-fno-plt" "-fno-semantic-interposition" "-fwrapv"
  AUTO_ADD_CO)

test_compile_option(
  _disable_warnings
  LANGS CXX DPCXX
  FLAGS "-Wno-unknown-pragmas" "-Wno-gnu-anonymous-struct" "-Wno-nested-anon-types"
  AUTO_ADD_CO)

test_compile_option(
  _compile_flags_release
  LANGS CXX DPCXX
  FLAGS "-ffast-math /fp:fast -fast" "-O3 /Ox"
  AUTO_ADD_CO
  GENEX "$<AND:$<OR:$<CONFIG:RELEASE>,$<CONFIG:RELWITHDEBINFO>>,$<COMPILE_LANGUAGE:@lang@>>")

# --------------------------------------

test_compile_option(
  _dpcpp_flags
  LANGS DPCXX
  FLAGS "-fsycl"
  AUTO_ADD_CO)

# --------------------------------------

if(ENABLE_PROFILING)
  test_compile_option(
    _profiling_flags
    LANGS CXX DPCXX
    FLAGS "-pg -prof-gen /Qprof-gen" "-fprofile-instr-generate"
    AUTO_ADD_CO)
endif()

# --------------------------------------

if(ENABLE_STACK_PROTECTION)
  test_compile_option(
    _stack_protection
    LANGS CXX DPCXX
    FLAGS "-fstack-protector-all"
    AUTO_ADD_CO)
endif()

# --------------------------------------

if(USE_NATIVE_INTRINSICS OR USE_INTRINSICS)
  define_property(
    TARGET
    PROPERTY SUPPORTS_SIMD
    INHERITED
    BRIEF_DOCS "If set, indicates that the target supports SIMD instructions"
    FULL_DOCS "If set, indicates that the target supports SIMD instructions")
endif()

if(USE_NATIVE_INTRINSICS)
  # Add -march=native regardless of Debug/Release
  test_compile_option(
    _archnative_flag
    LANGS CXX DPCXX
    FLAGS "-march=native -xHost /QxHost /arch:AVX512 /arch:AVX2 /arch:AVX")

  if(NOT _archnative_flag_CXX)
    message(FATAL_ERROR "Unable to find compiler flag for CXX compiler intrinsics")
  endif()
  # TODO: failure if DPCXX fails as well?
elseif(USE_INTRINSICS)
  if(X86_64)
    test_compile_option(
      _intrin_flag
      LANGS CXX DPCXX
      FLAGS "-mavx2 -xCORE-AVX2 /QxCORE-AVX2 /arch:AVX2")
  elseif(AARCH64)
    test_compile_option(
      _intrin_flag
      LANGS CXX DPCXX
      FLAGS "-march=armv8.5-a -march=armv8.4-a -march=armv8.3-a -march=armv8.2-a")
  endif()
endif()

add_compile_options(
  "$<$<AND:$<AND:$<COMPILE_LANGUAGE:CXX>,$<BOOL:${USE_NATIVE_INTRINSICS}>,$<BOOL:$<TARGET_PROPERTY:SUPPORTS_SIMD>>>>:\
${_archnative_flag_CXX}>"
  "$<$<AND:$<AND:$<COMPILE_LANGUAGE:CXX>,$<AND:$<NOT:$<BOOL:${USE_NATIVE_INTRINSICS}>>,$<BOOL:${USE_INTRINSICS}>>,\
    $<BOOL:$<TARGET_PROPERTY:SUPPORTS_SIMD>>>>:${_intrin_flag_CXX}>")

# ------------------------------------------------------------------------------

if(NOT VERSION_INFO)
  execute_process(
    COMMAND ${Python_EXECUTABLE} setup.py --version
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE _version_info
    OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
  set(VERSION_INFO "\"${_version_info}\"")
endif()

add_compile_definitions(
  "$<$<BOOL:${USE_OPENMP}>:USE_OPENMP>" "$<$<BOOL:${USE_PARALLEL_STL}>:USE_PARALLEL_STL>"
  "$<$<BOOL:${VERSION_INFO}>:VERSION_INFO=${VERSION_INFO}>"
  "$<$<OR:$<CONFIG:RELEASE>,$<CONFIG:RELWITHDEBINFO>>:_FORTIFY_SOURCE=2>")

# ==============================================================================
# Platform specific flags

if(WIN32)
  add_compile_definitions(_USE_MATH_DEFINES _CRT_SECURE_NO_WARNINGS WIN32_LEAN_AND_MEAN)
endif()
