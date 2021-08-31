# ==============================================================================
#
# Copyright 2021 <Huawei Technologies Co., Ltd>
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

include(Compiler/IntelLLVM)
__compiler_intel_llvm(DPCXX)

if("x${CMAKE_DPCXX_COMPILER_FRONTEND_VARIANT}" STREQUAL "xMSVC")
  set(CMAKE_DPCXX_COMPILE_OPTIONS_EXPLICIT_LANGUAGE -TP)
  set(CMAKE_DPCXX_CLANG_TIDY_DRIVER_MODE "cl")
  if((NOT DEFINED CMAKE_DEPENDS_USE_COMPILER OR CMAKE_DEPENDS_USE_COMPILER)
     AND CMAKE_GENERATOR MATCHES "Makefiles|WMake"
     AND CMAKE_DEPFILE_FLAGS_DPCXX)
    set(CMAKE_DPCXX_DEPENDS_USE_COMPILER TRUE)
  endif()
else()
  set(CMAKE_DPCXX_COMPILE_OPTIONS_EXPLICIT_LANGUAGE -x c++)
  if((NOT DEFINED CMAKE_DEPENDS_USE_COMPILER OR CMAKE_DEPENDS_USE_COMPILER)
     AND CMAKE_GENERATOR MATCHES "Makefiles|WMake"
     AND CMAKE_DEPFILE_FLAGS_DPCXX)
    # dependencies are computed by the compiler itself
    set(CMAKE_DPCXX_DEPFILE_FORMAT gcc)
    set(CMAKE_DPCXX_DEPENDS_USE_COMPILER TRUE)
  endif()

  set(CMAKE_DPCXX_COMPILE_OPTIONS_VISIBILITY_INLINES_HIDDEN "-fvisibility-inlines-hidden")

  string(APPEND CMAKE_DPCXX_FLAGS_MINSIZEREL_INIT " -DNDEBUG")
  string(APPEND CMAKE_DPCXX_FLAGS_RELEASE_INIT " -DNDEBUG")
  string(APPEND CMAKE_DPCXX_FLAGS_RELWITHDEBINFO_INIT " -DNDEBUG")
endif()

set(CMAKE_DPCXX98_STANDARD__HAS_FULL_SUPPORT ON)
set(CMAKE_DPCXX11_STANDARD__HAS_FULL_SUPPORT ON)
set(CMAKE_DPCXX14_STANDARD__HAS_FULL_SUPPORT ON)

if(NOT "x${CMAKE_DPCXX_SIMULATE_ID}" STREQUAL "xMSVC")
  set(CMAKE_DPCXX98_STANDARD_COMPILE_OPTION "-std=c++98")
  set(CMAKE_DPCXX98_EXTENSION_COMPILE_OPTION "-std=gnu++98")

  set(CMAKE_DPCXX11_STANDARD_COMPILE_OPTION "-std=c++11")
  set(CMAKE_DPCXX11_EXTENSION_COMPILE_OPTION "-std=gnu++11")

  set(CMAKE_DPCXX14_STANDARD_COMPILE_OPTION "-std=c++14")
  set(CMAKE_DPCXX14_EXTENSION_COMPILE_OPTION "-std=gnu++14")

  set(CMAKE_DPCXX17_STANDARD_COMPILE_OPTION "-std=c++17")
  set(CMAKE_DPCXX17_EXTENSION_COMPILE_OPTION "-std=gnu++17")

  set(CMAKE_DPCXX20_STANDARD_COMPILE_OPTION "-std=c++20")
  set(CMAKE_DPCXX20_EXTENSION_COMPILE_OPTION "-std=gnu++20")
else()
  set(CMAKE_DPCXX98_STANDARD_COMPILE_OPTION "")
  set(CMAKE_DPCXX98_EXTENSION_COMPILE_OPTION "")

  set(CMAKE_DPCXX11_STANDARD_COMPILE_OPTION "-Qstd=c++11")
  set(CMAKE_DPCXX11_EXTENSION_COMPILE_OPTION "-Qstd=c++11")

  set(CMAKE_DPCXX14_STANDARD_COMPILE_OPTION "-Qstd=c++14")
  set(CMAKE_DPCXX14_EXTENSION_COMPILE_OPTION "-Qstd=c++14")

  set(CMAKE_DPCXX17_STANDARD_COMPILE_OPTION "-Qstd=c++17")
  set(CMAKE_DPCXX17_EXTENSION_COMPILE_OPTION "-Qstd=c++17")

  set(CMAKE_DPCXX20_STANDARD_COMPILE_OPTION "-Qstd=c++20")
  set(CMAKE_DPCXX20_EXTENSION_COMPILE_OPTION "-Qstd=c++20")
endif()

if(NOT "x${CMAKE_CXX_SIMULATE_ID}" STREQUAL "xMSVC")
  __compiler_check_default_language_standard(CXX 2020 14)
else()
  set(CMAKE_CXX_STANDARD_DEFAULT "")
endif()
