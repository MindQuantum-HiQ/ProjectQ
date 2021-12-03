# ==============================================================================
#
# Copyright 2020 <Huawei Technologies Co., Ltd>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ==============================================================================

include(CMakeDependentOption)

# ==============================================================================
# Python related options

if(APPLE)
  option(PYTHON_VIRTUALENV_COMPAT "(Mac OS X) Make CMake search for Python Framework *after* any available\
  unix-style package. Can be useful in case of virtual environments." ON)
else()
  option(PYTHON_VIRTUALENV_COMPAT "(Mac OS X) Make CMake search for Python Framework *after* any available\
  unix-style package. Can be useful in case of virtual environments." OFF)
endif()

option(IS_PYTHON_BUILD "Is CMake called from setup.py? (e.g. python3 setup.py install?)" OFF)
option(IN_PLACE_BUILD "Are we building in-place for testing?" OFF)

# ==============================================================================
# CUDA related options

option(CUDA_ALLOW_UNSUPPORTED_COMPILER "Allow the use of an unsupported compiler version" OFF)
option(ENABLE_CUDA "Enable building of CUDA libraries" ON)
option(NVCXX_FAST_SEARCH "Use a fast algorithm to test for the validity of nvc++ (set to OFF if detection fails)" ON)
option(CUDA_STATIC "Use static version of Nvidia CUDA libraries during linking (also applies to nvc++)" ON)

option(ENABLE_DPCXX "Enable building of DPC++ libraries" OFF)

# ==============================================================================
# Compilation options

# cmake-lint: disable=C0103
set(_USE_OPENMP ON)
if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC"
   OR "x${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU"
   OR "x${CMAKE_CXX_COMPILER_ID}" STREQUAL "Intel"
   OR "x${CMAKE_CXX_COMPILER_ID}" STREQUAL "IntelLLVM")
  set(_USE_OPENMP OFF)
endif()
option(USE_OPENMP "Use OpenMP instead parallel STL" ${_USE_OPENMP})

set(_USE_PARALLEL_STL OFF)
if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC"
   OR "x${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU"
   OR "x${CMAKE_CXX_COMPILER_ID}" STREQUAL "Intel"
   OR "x${CMAKE_CXX_COMPILER_ID}" STREQUAL "IntelLLVM")
  set(_USE_PARALLEL_STL ON)
endif()
option(USE_PARALLEL_STL "Use parallel STL algorithms (GCC, Intel, IntelLLVM and MSVC only for now)"
       ${_USE_PARALLEL_STL})

# ------------------------------------------------------------------------------

option(USE_INTRINSICS "Enable/disable the use of compiler intrinsics" ON)
option(USE_NATIVE_INTRINSICS "Use -march=native (or equivalent compiler flag)" ON)

# ------------------------------------------------------------------------------

option(ENABLE_PROFILING "Enable compilation with profiling flags." OFF)
option(ENABLE_STACK_PROTECTION "Enable the use of -fstack-protector during compilation" ON)

# ==============================================================================
# Linking options

option(ENABLE_RUNPATH "Prefer RUNPATH over RPATH when linking" OFF)

option(LINKER_DTAGS "Use --enable-new-dtags or --disable-new-dtags during linking" ON)
option(LINKER_NOEXECSTACK "Use -z,noexecstack during linking" ON)
option(LINKER_RELRO "Use -z,relro during linking for certain targets" ON)
option(LINKER_RPATH "Enable the use of RPATH/RUNPATH related flags during linking" OFF)
option(LINKER_STRIP_ALL "Use --strip-all during linking" ON)

# ==============================================================================
# Other CMake related options

option(BUILD_TESTING "Build the test suite?" OFF)

# NB: most if not all of our libraries have the type explicitly specified.
option(BUILD_SHARED_LIBS "Build shared libs" OFF)

option(USE_VERBOSE_MAKEFILE "Use verbose Makefiles" ON)

# ==============================================================================
# ==============================================================================
# Python related options

if(PYTHON_VIRTUALENV_COMPAT)
  set(CMAKE_FIND_FRAMEWORK LAST)
endif()

# ------------------------------------------------------------------------------

if(IS_PYTHON_BUILD AND IN_PLACE_BUILD)
  message(FATAL_ERROR "Cannot specify both IS_PYTHON_BUILD=ON and IN_PLACE_BUILD=ON!")
endif()

# ==============================================================================
# CUDA related options

include(CheckLanguage)

list(PREPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR}/DPCXX)

if(ENABLE_DPCXX)
  check_language(DPCXX)
  if(CMAKE_DPCXX_COMPILER)
    enable_language(DPCXX)
  else()
    message(STATUS "Disabling DPCXX due to inexistant DPCXX compiler or error during compiler setup")
    set(ENABLE_DPCXX
        OFF
        CACHE INTERNAL "Enable building of DPC++ libraries")
  endif()
endif()

# ------------------------------------------------------------------------------

list(PREPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR}/NVCXX)

if(CUDA_ALLOW_UNSUPPORTED_COMPILER)
  set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -allow-unsupported-compiler")
endif()

if(CUDA_STATIC)
  set(CMAKE_CUDA_RUNTIME_LIBRARY Static) # NB: CMake 3.17
else()
  unset(CMAKE_CUDA_RUNTIME_LIBRARY)
endif()

if(ENABLE_CUDA)
  if(NOT CMAKE_CUDA_ARCHITECTURES AND "$ENV{CUDAARCHS}" STREQUAL "")
    # PASCAL 60 VOLTA 70
    set(CMAKE_CUDA_ARCHITECTURES 60 70)

    # NB: CUDAARCHS requires CMake 3.20
    message(STATUS "Neither of CMAKE_CUDA_ARCHITECTURES (CMake variable) or CUDAARCHS (env. variable; CMake 3.20+) "
                   "have been defined. Defaulting to ${CMAKE_CUDA_ARCHITECTURES}")
  elseif(NOT "$ENV{CUDAARCHS}" STREQUAL "")
    message(STATUS "CUDAARCHS environment variable present: $ENV{CUDAARCHS}")
  endif()

  set(CMAKE_NVCXX_FLAGS_INIT "-stdpar -cuda")
  set(CMAKE_NVCXX_LDFLAGS_INIT "-stdpar -cuda")
  set(_CMAKE_NVCXX_USE_FAST_SEARCH ${NVCXX_FAST_SEARCH})

  check_language(NVCXX)

  if(CMAKE_NVCXX_COMPILER)
    find_package(CUDAToolkit REQUIRED)
  endif()

  if(CMAKE_NVCXX_COMPILER AND CUDAToolkit_FOUND)
    enable_language(NVCXX)
    enable_language(CUDA)
  else()
    message(STATUS "Disabling CUDA due to inexistant CUDA compiler/toolkit or error during compiler setup")
    set(ENABLE_CUDA
        OFF
        CACHE INTERNAL "Enable building of CUDA libraries")
  endif()
endif()

# ==============================================================================
# Compilation options

if($ENV{NIX_ENFORCE_NO_NATIVE})
  message(STATUS "Detecting nix build with NIX_ENFORCE_NO_NATIVE=1")
  message(STATUS "-> disabling -march=native in favor of intrinsics")
  set(USE_NATIVE_INTRINSICS OFF)
  set(USE_INTRINSICS ON)
endif()

if(USE_NATIVE_INTRINSICS AND USE_INTRINSICS)
  message(STATUS "Favouring native intrinsics over normal intrinsics")
  set(USE_INTRINSICS
      OFF
      CACHE BOOL "Enable/disable the use of compiler intrinsics")
endif()

# ==============================================================================
# Other CMake related options

if(USE_VERBOSE_MAKEFILE)
  set(CMAKE_VERBOSE_MAKEFILE ON)
endif()

# ==============================================================================
