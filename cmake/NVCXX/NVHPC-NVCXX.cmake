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
# cmake-lint: disable=C0103

include(Compiler/CMakeCommonCompilerMacros)

# TODO: Check that `False` is ok here since the compiler is doing everything
set(CMAKE_NVCXX_COMPILER_HAS_DEVICE_LINK_PHASE FALSE)
set(CMAKE_NVCXX_VERBOSE_FLAG "-v")
set(CMAKE_NVCXX_VERBOSE_COMPILE_FLAG "-v")

set(_CMAKE_COMPILE_AS_NVCXX_FLAG "-x cu")
# ~~~
# set(_CMAKE_NVCXX_PTX_FLAG "")
# set(_CMAKE_NVCXX_DEVICE_CODE "")
# ~~~

# ~~~
# NB: cannot use this as of now, since it seems that -MD implies -E (ie. preprocess only)
# NB2: this requires cmake >= 3.20
# set(CMAKE_DEPFILE_FLAGS_NVCXX "-MD=<DEP_FILE> -MT <DEP_TARGET>")
# set(CMAKE_NVCXX_DEPFILE_FORMAT gcc)
# if((NOT DEFINED CMAKE_DEPENDS_USE_COMPILER OR CMAKE_DEPENDS_USE_COMPILER)
#     AND CMAKE_GENERATOR MATCHES "Makefiles|WMake")
#   set(CMAKE_NVCXX_DEPENDS_USE_COMPILER TRUE)
# endif()
set(CMAKE_NVCXX_DEPENDS_USE_COMPILER FALSE)
# ~~~

set(CMAKE_NVCXX_COMPILE_OPTIONS_PIE -fPIE)
set(CMAKE_NVCXX_COMPILE_OPTIONS_PIC -fPIC)
set(CMAKE_NVCXX_COMPILE_OPTIONS_VISIBILITY -fvisibility=)
set(CMAKE_DPCXX_COMPILE_OPTIONS_VISIBILITY_INLINES_HIDDEN "-fvisibility-inlines-hidden")
set(CMAKE_SHARED_LIBRARY_NVCXX_FLAGS -fPIC)

string(APPEND CMAKE_NVCXX_FLAGS_INIT " ")
string(APPEND CMAKE_NVCXX_FLAGS_DEBUG_INIT " -g -O0")
string(APPEND CMAKE_NVCXX_FLAGS_MINSIZEREL_INIT " -O2 -s")
string(APPEND CMAKE_NVCXX_FLAGS_RELEASE_INIT " -fast -O3 -DNDEBUG")
string(APPEND CMAKE_NVCXX_FLAGS_RELWITHDEBINFO_INIT " -O2 -gopt -DNDEBUG")

if(CMAKE_HOST_WIN32)
  string(APPEND CMAKE_NVCXX_FLAGS_INIT " -Bdynamic")
endif()

set(CMAKE_SHARED_LIBRARY_CREATE_NVCXX_FLAGS -shared)
set(CMAKE_INCLUDE_SYSTEM_FLAG_NVCXX -isystem=)

set(CMAKE_NVCXX_LINKER_WRAPPER_FLAG "-Xlinker" " ")
set(CMAKE_NVCXX_LINKER_WRAPPER_FLAG_SEP)

set(CMAKE_NVCXX_RUNTIME_LIBRARY_LINK_OPTIONS_STATIC "cudadevrt;cudart_static")
set(CMAKE_NVCXX_RUNTIME_LIBRARY_LINK_OPTIONS_SHARED "cudadevrt;cudart")
set(CMAKE_NVCXX_RUNTIME_LIBRARY_LINK_OPTIONS_MODULE "cudadevrt;cudart")
set(CMAKE_NVCXX_RUNTIME_LIBRARY_LINK_OPTIONS_NONE "")

if(UNIX AND NOT (CMAKE_SYSTEM_NAME STREQUAL "QNX"))
  list(APPEND CMAKE_NVCXX_RUNTIME_LIBRARY_LINK_OPTIONS_STATIC "rt" "pthread" "dl")
endif()

set(CMAKE_NVCXX03_STANDARD_COMPILE_OPTION "")
set(CMAKE_NVCXX03_EXTENSION_COMPILE_OPTION "")
set(CMAKE_NVCXX11_STANDARD_COMPILE_OPTION "-std=c++11")
set(CMAKE_NVCXX11_EXTENSION_COMPILE_OPTION "-std=c++11 --gnu_extensions")
set(CMAKE_NVCXX14_STANDARD_COMPILE_OPTION "-std=c++14")
set(CMAKE_NVCXX14_EXTENSION_COMPILE_OPTION "-std=c++14 --gnu_extensions")
set(CMAKE_NVCXX17_STANDARD_COMPILE_OPTION "-std=c++17")
set(CMAKE_NVCXX17_EXTENSION_COMPILE_OPTION "-std=c++17 --gnu_extensions")
set(CMAKE_NVCXX20_STANDARD_COMPILE_OPTION "-std=c++20")
set(CMAKE_NVCXX20_EXTENSION_COMPILE_OPTION "-std=c++20 --gnu_extensions")

set(_CMAKE_NVCXX_IPO_SUPPORTED_BY_CMAKE YES)
if(NOT CMAKE_SYSTEM_PROCESSOR STREQUAL ppc64le AND (NOT CMAKE_HOST_WIN32))
  set(_CMAKE_NVCXX_IPO_MAY_BE_SUPPORTED_BY_COMPILER YES)
  set(CMAKE_NVCXX_COMPILE_OPTIONS_IPO "-Mipa=fast,inline")
else()
  set(_CMAKE_NVCXX_IPO_MAY_BE_SUPPORTED_BY_COMPILER NO)
endif()

__compiler_check_default_language_standard(NVCXX 20 17)
