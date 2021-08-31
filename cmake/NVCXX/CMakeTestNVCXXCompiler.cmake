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

if(CMAKE_NVCXX_COMPILER_FORCED)
  # The compiler configuration was forced by the user. Assume the user has configured all compiler information.
  set(CMAKE_NVCXX_COMPILER_WORKS TRUE)
  return()
endif()

include(CMakeTestCompilerCommon)

# Remove any cached result from an older CMake version. We now store this in CMakeNVCXXCompiler.cmake.
unset(CMAKE_NVCXX_COMPILER_WORKS CACHE)

# This file is used by EnableLanguage in cmGlobalGenerator to determine that the selected cuda compiler can actually
# compile and link the most basic of programs.   If not, a fatal error is set and cmake stops processing commands and
# will not generate any makefiles or projects.
if(NOT CMAKE_NVCXX_COMPILER_WORKS)
  if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.17)
    PrintTestCompilerStatus("NVCXX")
  endif()

  set(_srcdir ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp)
  set(_src ${_srcdir}/main.cpp)
  file(MAKE_DIRECTORY ${_srcdir})
  file(
    WRITE ${_src}
    "#ifndef __NVCOMPILER\n"
    "#     error \"This is not the nvc++ C++17 NVCXX compiler\"\n"
    "#endif\n"
    "#if __NVCOMPILER_MAJOR__  >= 21 && __NVCOMPILER_MINOR__ > 2\n"
    "#  ifndef __CUDACC_VER_MAJOR__\n"
    "#       error \"You need to compile this file with NVCXX support enabled (e.g. with -stdpar)\"\n"
    "#  endif\n"
    "#endif\n"
    "int main(){return 0;}\n")

  set(CMAKE_SOURCE_FILE main.cpp)
  set(LANG NVCXX)
  set(CMAKE_LANG_FLAGS ${CMAKE_${LANG}_FLAGS})
  set(CMAKE_LANG_STANDARD ${CMAKE_${LANG}_STANDARD})
  set(CMAKE_LANG_STANDARD_REQUIRED ${CMAKE_${LANG}_STANDARD_REQUIRED})
  set(CMAKE_LANG_EXTENSIONS ${CMAKE_${LANG}_EXTENSIONS})

  string(RANDOM _random)
  set(CMAKE_EXEC_NAME cmTC_${_random})

  include(_protect_arguments)
  _protect_arguments(CMAKE_REQUIRED_DEFINITIONS)
  string(REPLACE ";" "\n                " CMAKE_REQUIRED_DEFINITIONS "${CMAKE_REQUIRED_DEFINITIONS}")

  configure_file(${CMAKE_CURRENT_LIST_DIR}/../try_compile/CMakeLists.txt.in ${_srcdir}/CMakeLists.txt @ONLY)

  try_compile(
    CMAKE_NVCXX_COMPILER_WORKS ${CMAKE_BINARY_DIR}/CMakeTmp
    ${_srcdir} CMAKE_TRY_COMPILE
    CMAKE_FLAGS -DCMAKE_NVCXX_FLAGS_INIT:STRING=${CMAKE_NVCXX_FLAGS_INIT}
                -DCMAKE_NVCXX_LDFLAGS_INIT:STRING=${CMAKE_NVCXX_LDFLAGS_INIT}
    OUTPUT_VARIABLE __CMAKE_NVCXX_COMPILER_OUTPUT)

  # Move result from cache to normal variable.
  set(CMAKE_NVCXX_COMPILER_WORKS ${CMAKE_NVCXX_COMPILER_WORKS})
  unset(CMAKE_NVCXX_COMPILER_WORKS CACHE)
  if(NOT CMAKE_NVCXX_COMPILER_WORKS)
    if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.17)
      printtestcompilerresult(CHECK_FAIL "broken")
    endif()
    file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeError.log
         "Determining if the NVCXX compiler works failed with "
         "the following output:\n${__CMAKE_NVCXX_COMPILER_OUTPUT}\n\n")
    string(REPLACE "\n" "\n  " _output "${__CMAKE_NVCXX_COMPILER_OUTPUT}")
    message(
      FATAL_ERROR
        "The NVCXX compiler\n  \"${CMAKE_NVCXX_COMPILER}\"\n"
        "is not able to compile a simple test program.\nIt fails " "with the following output:\n  ${_output}\n\n"
        "CMake will not be able to correctly generate this project.")
  endif()
  if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.17)
    printtestcompilerresult(CHECK_PASS "works")
  endif()
  file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeOutput.log
       "Determining if the NVCXX compiler works passed with "
       "the following output:\n${__CMAKE_NVCXX_COMPILER_OUTPUT}\n\n")
endif()

# Try to identify the compiler features
include(${CMAKE_ROOT}/Modules/CMakeDetermineCompileFeatures.cmake)
cmake_determine_compile_features(NVCXX)

if("x${CMAKE_NVCXX_SIMULATE_ID}" STREQUAL "xMSVC")
  set(CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES "${CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES}")
  set(CMAKE_NVCXX_IMPLICIT_LINK_DIRECTORIES "${CMAKE_NVCXX_HOST_IMPLICIT_LINK_DIRECTORIES}")
endif()

# Filter out implicit link libraries that should not be passed unconditionally. See
# CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES_EXCLUDE in CMakeDetermineNVCXXCompiler.
list(REMOVE_ITEM CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES ${CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES_EXCLUDE})

# Remove the NVCXX Toolkit include directories from the set of implicit system include directories. This resolves the
# issue that NVCC doesn't specify these includes as SYSTEM includes when compiling device code, and sometimes they
# contain headers that generate warnings, so let users mark them as SYSTEM explicitly
if(CMAKE_NVCXX_TOOLKIT_INCLUDE_DIRECTORIES)
  list(REMOVE_ITEM CMAKE_NVCXX_IMPLICIT_INCLUDE_DIRECTORIES ${CMAKE_NVCXX_TOOLKIT_INCLUDE_DIRECTORIES})
endif()

# Re-configure to save learned information.
configure_file(${CMAKE_CURRENT_LIST_DIR}/CMakeNVCXXCompiler.cmake.in
               ${CMAKE_PLATFORM_INFO_DIR}/CMakeNVCXXCompiler.cmake @ONLY)
include(${CMAKE_PLATFORM_INFO_DIR}/CMakeNVCXXCompiler.cmake)

unset(__CMAKE_NVCXX_COMPILER_OUTPUT)
