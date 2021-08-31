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

# ==============================================================================

message(CHECK_START "Detecting DPCXX compiler info")

include(CMakeDetermineCompiler)

# Load system-specific compiler preferences for this language.
include(Platform/${CMAKE_SYSTEM_NAME}-Determine-DPCXX OPTIONAL)
include(Platform/${CMAKE_SYSTEM_NAME}-DPCXX OPTIONAL)
if(NOT CMAKE_DPCXX_COMPILER_NAMES)
  set(CMAKE_DPCXX_COMPILER_NAMES dpcpp)
endif()

if(${CMAKE_GENERATOR} MATCHES "Visual Studio")

elseif("${CMAKE_GENERATOR}" MATCHES "Green Hills MULTI")

elseif("${CMAKE_GENERATOR}" MATCHES "Xcode")
  set(CMAKE_DPCXX_COMPILER_XCODE_TYPE sourcecode.cpp.cpp)
  _cmake_find_compiler_path(DPCXX)
else()
  if(NOT CMAKE_DPCXX_COMPILER)
    set(CMAKE_DPCXX_COMPILER_INIT NOTFOUND)

    # prefer the environment variable DPCXX
    if(NOT $ENV{DPCXX} STREQUAL "")
      get_filename_component(CMAKE_DPCXX_COMPILER_INIT $ENV{DPCXX} PROGRAM PROGRAM_ARGS CMAKE_DPCXX_FLAGS_ENV_INIT)
      if(CMAKE_DPCXX_FLAGS_ENV_INIT)
        set(CMAKE_DPCXX_COMPILER_ARG1
            "${CMAKE_DPCXX_FLAGS_ENV_INIT}"
            CACHE STRING "Arguments to DPCXX compiler")
      endif()
      if(NOT EXISTS ${CMAKE_DPCXX_COMPILER_INIT})
        message(
          FATAL_ERROR
            "Could not find compiler set in environment variable DPCXX:\n$ENV{DPCXX}.\n${CMAKE_DPCXX_COMPILER_INIT}")
      endif()
    endif()

    # next prefer the generator specified compiler
    if(CMAKE_GENERATOR_DPCXX)
      if(NOT CMAKE_DPCXX_COMPILER_INIT)
        set(CMAKE_DPCXX_COMPILER_INIT ${CMAKE_GENERATOR_DPCXX})
      endif()
    endif()

    # finally list compilers to try
    if(NOT CMAKE_DPCXX_COMPILER_INIT)
      set(CMAKE_DPCXX_COMPILER_LIST dpcpp)
    endif()

    _cmake_find_compiler(DPCXX)
  else()
    _cmake_find_compiler_path(DPCXX)
  endif()
  mark_as_advanced(CMAKE_DPCXX_COMPILER)

  # Each entry in this list is a set of extra flags to try adding to the compile line to see if it helps produce a valid
  # identification file.
  set(CMAKE_DPCXX_COMPILER_ID_TEST_FLAGS_FIRST)
  set(CMAKE_DPCXX_COMPILER_ID_TEST_FLAGS
      # Try compiling to an object file only.
      "-c"
      # IAR does not detect language automatically
      "--c++"
      "--ec++"
      # ARMClang need target options
      "--target=arm-arm-none-eabi -mcpu=cortex-m3")
endif()

if(CMAKE_DPCXX_COMPILER_TARGET)
  set(CMAKE_DPCXX_COMPILER_ID_TEST_FLAGS_FIRST "-c --target=${CMAKE_DPCXX_COMPILER_TARGET}")
endif()

# Build a small source file to identify the compiler.
if(NOT CMAKE_DPCXX_COMPILER_ID_RUN)
  set(CMAKE_DPCXX_COMPILER_ID_RUN 1)

  # Try to identify the compiler.
  set(CMAKE_DPCXX_COMPILER_ID)
  set(CMAKE_DPCXX_PLATFORM_ID)
  file(READ ${CMAKE_ROOT}/Modules/CMakePlatformId.h.in CMAKE_DPCXX_COMPILER_ID_PLATFORM_CONTENT)

  # The IAR compiler produces weird output. See https://gitlab.kitware.com/cmake/cmake/-/issues/10176#note_153591
  list(APPEND CMAKE_DPCXX_COMPILER_ID_VENDORS IAR)
  set(CMAKE_DPCXX_COMPILER_ID_VENDOR_FLAGS_IAR)
  set(CMAKE_DPCXX_COMPILER_ID_VENDOR_REGEX_IAR "IAR .+ Compiler")

  # Match the link line from xcodebuild output of the form Ld ... ... /path/to/cc ...CompilerIdDPCXX/... to extract the
  # compiler front-end for the language.
  set(CMAKE_DPCXX_COMPILER_ID_TOOL_MATCH_REGEX
      "\nLd[^\n]*(\n[ \t]+[^\n]*)*\n[ \t]+([^ \t\r\n]+)[^\r\n]*-o[^\r\n]*CompilerIdDPCXX/(\\./)?\
(CompilerIdDPCXX.(framework|xctest|build/[^ \t\r\n]+)/)?CompilerIdDPCXX[ \t\n\\\"]")
  set(CMAKE_DPCXX_COMPILER_ID_TOOL_MATCH_INDEX 2)

  include(${CMAKE_ROOT}/Modules/CMakeDetermineCompilerId.cmake)
  cmake_determine_compiler_id(DPCXX DPCXXFLAGS CMakeDPCXXCompilerId.cpp)

  _cmake_find_compiler_sysroot(DPCXX)

  # Set old compiler and platform id variables.
  if(CMAKE_DPCXX_COMPILER_ID STREQUAL "GNU")
    set(CMAKE_COMPILER_IS_GNUDPCXX 1)
  endif()
  if(CMAKE_DPCXX_PLATFORM_ID MATCHES "MinGW")
    set(CMAKE_COMPILER_IS_MINGW 1)
  elseif(CMAKE_DPCXX_PLATFORM_ID MATCHES "Cygwin")
    set(CMAKE_COMPILER_IS_CYGWIN 1)
  endif()
else()
  if(NOT DEFINED CMAKE_DPCXX_COMPILER_FRONTEND_VARIANT)
    # Some toolchain files set our internal CMAKE_DPCXX_COMPILER_ID_RUN variable but are not aware of
    # CMAKE_DPCXX_COMPILER_FRONTEND_VARIANT. They pre-date our support for the GNU-like variant targeting the MSVC ABI
    # so we do not consider that here.
    if(CMAKE_DPCXX_COMPILER_ID STREQUAL "Clang" OR "x${CMAKE_DPCXX_COMPILER_ID}" STREQUAL "xIntelLLVM")
      if("x${CMAKE_DPCXX_SIMULATE_ID}" STREQUAL "xMSVC")
        set(CMAKE_DPCXX_COMPILER_FRONTEND_VARIANT "MSVC")
      else()
        set(CMAKE_DPCXX_COMPILER_FRONTEND_VARIANT "GNU")
      endif()
    else()
      set(CMAKE_DPCXX_COMPILER_FRONTEND_VARIANT "")
    endif()
  endif()
endif()

if(NOT _CMAKE_TOOLCHAIN_LOCATION)
  get_filename_component(_CMAKE_TOOLCHAIN_LOCATION "${CMAKE_DPCXX_COMPILER}" PATH)
endif()

# if we have a g++ cross compiler, they have usually some prefix, like e.g. powerpc-linux-g++, arm-elf-g++ or
# i586-mingw32msvc-g++ , optionally with a 3-component version number at the end (e.g. arm-eabi-gcc-4.5.2). The other
# tools of the toolchain usually have the same prefix NAME_WE cannot be used since then this test will fail for names
# like "arm-unknown-nto-qnx6.3.0-gcc.exe", where BASENAME would be "arm-unknown-nto-qnx6" instead of the correct
# "arm-unknown-nto-qnx6.3.0-"

if(NOT _CMAKE_TOOLCHAIN_PREFIX)

  if("${CMAKE_DPCXX_COMPILER_ID}" MATCHES "GNU|Clang|QCC")
    get_filename_component(COMPILER_BASENAME "${CMAKE_DPCXX_COMPILER}" NAME)
    if(COMPILER_BASENAME MATCHES "^(.+-)?(clang\\+\\+|[gc]\\+\\+|clang-cl)(-[0-9]+(\\.[0-9]+)*)?(-[^.]+)?(\\.exe)?$")
      set(_CMAKE_TOOLCHAIN_PREFIX ${CMAKE_MATCH_1})
      set(_CMAKE_TOOLCHAIN_SUFFIX ${CMAKE_MATCH_3})
      set(_CMAKE_COMPILER_SUFFIX ${CMAKE_MATCH_5})
    elseif("${CMAKE_DPCXX_COMPILER_ID}" MATCHES "Clang")
      if(CMAKE_DPCXX_COMPILER_TARGET)
        set(_CMAKE_TOOLCHAIN_PREFIX ${CMAKE_DPCXX_COMPILER_TARGET}-)
      endif()
    elseif(COMPILER_BASENAME MATCHES "QCC(\\.exe)?$")
      if(CMAKE_DPCXX_COMPILER_TARGET MATCHES "gcc_nto([a-z0-9]+_[0-9]+|[^_le]+)(le)")
        set(_CMAKE_TOOLCHAIN_PREFIX nto${CMAKE_MATCH_1}-)
      endif()
    endif()

    # if "llvm-" is part of the prefix, remove it, since llvm doesn't have its own binutils but uses the regular ar,
    # objcopy, etc. (instead of llvm-objcopy etc.)
    if("${_CMAKE_TOOLCHAIN_PREFIX}" MATCHES "(.+-)?llvm-$")
      set(_CMAKE_TOOLCHAIN_PREFIX ${CMAKE_MATCH_1})
    endif()
  elseif("${CMAKE_DPCXX_COMPILER_ID}" MATCHES "TI")
    # TI compilers are named e.g. cl6x, cl470 or armcl.exe
    get_filename_component(COMPILER_BASENAME "${CMAKE_DPCXX_COMPILER}" NAME)
    if(COMPILER_BASENAME MATCHES "^(.+)?cl([^.]+)?(\\.exe)?$")
      set(_CMAKE_TOOLCHAIN_PREFIX "${CMAKE_MATCH_1}")
      set(_CMAKE_TOOLCHAIN_SUFFIX "${CMAKE_MATCH_2}")
    endif()

  endif()

endif()

set(_CMAKE_PROCESSING_LANGUAGE "DPCXX")
include(CMakeFindBinUtils)
include(Compiler/${CMAKE_DPCXX_COMPILER_ID}-FindBinUtils OPTIONAL)
unset(_CMAKE_PROCESSING_LANGUAGE)

if(CMAKE_DPCXX_COMPILER_SYSROOT)
  string(CONCAT _SET_CMAKE_DPCXX_COMPILER_SYSROOT
                "set(CMAKE_DPCXX_COMPILER_SYSROOT \"${CMAKE_DPCXX_COMPILER_SYSROOT}\")\n"
                "set(CMAKE_COMPILER_SYSROOT \"${CMAKE_DPCXX_COMPILER_SYSROOT}\")")
else()
  set(_SET_CMAKE_DPCXX_COMPILER_SYSROOT "")
endif()

if(CMAKE_DPCXX_COMPILER_ARCHITECTURE_ID)
  set(_SET_CMAKE_DPCXX_COMPILER_ARCHITECTURE_ID
      "set(CMAKE_DPCXX_COMPILER_ARCHITECTURE_ID ${CMAKE_DPCXX_COMPILER_ARCHITECTURE_ID})")
else()
  set(_SET_CMAKE_DPCXX_COMPILER_ARCHITECTURE_ID "")
endif()

if(MSVC_DPCXX_ARCHITECTURE_ID)
  set(SET_MSVC_DPCXX_ARCHITECTURE_ID "set(MSVC_DPCXX_ARCHITECTURE_ID ${MSVC_DPCXX_ARCHITECTURE_ID})")
endif()

if(CMAKE_DPCXX_XCODE_ARCHS)
  set(SET_CMAKE_XCODE_ARCHS "set(CMAKE_XCODE_ARCHS \"${CMAKE_DPCXX_XCODE_ARCHS}\")")
endif()

# ==============================================================================

set(CMAKE_DPCXX_RANLIB ${CMAKE_RANLIB})
set(CMAKE_DPCXX_LINKER ${CMAKE_DPCXX_COMPILER})

set(CMAKE_DPCXX_COMPILE_FEATURES cxx_std_03;cxx_std_11;cxx_std_14;cxx_std_17)
set(CMAKE_DPCXX03_COMPILE_FEATURES cxx_std_03)
set(CMAKE_DPCXX11_COMPILE_FEATURES cxx_std_11)
set(CMAKE_DPCXX14_COMPILE_FEATURES cxx_std_14)
set(CMAKE_DPCXX17_COMPILE_FEATURES cxx_std_17)
set(CMAKE_DPCXX20_COMPILE_FEATURES cxx_std_20)
set(CMAKE_DPCXX23_COMPILE_FEATURES cxx_std_23)

# ==============================================================================

# configure all variables set in this file
configure_file(${CMAKE_CURRENT_LIST_DIR}/CMakeDPCXXCompiler.cmake.in
               ${CMAKE_PLATFORM_INFO_DIR}/CMakeDPCXXCompiler.cmake @ONLY)

set(CMAKE_DPCXX_COMPILER_ENV_VAR "DPCXX")
