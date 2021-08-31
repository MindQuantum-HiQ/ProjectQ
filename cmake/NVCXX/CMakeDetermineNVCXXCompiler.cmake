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

# Parse include information from some compiler output
#
# parse_include_info(<compiler_output> <directory-variable> <log-variable>) cmake-lint: disable=R0912,R0915
#
# cmake-lint: disable=R0912,R0915
function(parse_include_info text dir_var log_var)
  # clear variables we append to (avoids possible pollution from parent scopes)
  set(implicit_dirs_tmp)
  set(log "")

  # go through each line of output...
  string(REGEX REPLACE "\r*\n" ";" output_lines "${text}")
  foreach(line IN LISTS output_lines)
    set(cmd)
    set(include_regex "[^\n]*cpp1[^\n]*")
    if("${line}" MATCHES "${include_regex}")
      separate_arguments(args NATIVE_COMMAND "${line}")
      list(GET args 0 cmd)
    else()
      # check to see if the link line is comma-separated instead of space separated
      string(REGEX REPLACE "," " " line "${line}")
      if("${line}" MATCHES "${include_regex}")
        separate_arguments(args NATIVE_COMMAND "${line}")
        list(GET args 0 cmd)
      endif()
    endif()
    set(is_msvc 0)
    if("${cmd}" MATCHES "${include_regex}")
      string(APPEND log "  include line: [${line}]\n")
      string(REGEX REPLACE ";-(I|isystem|-sys_include);" ";-\\1" args "${args}")
      set(skip_value_of "")
      foreach(arg IN LISTS args)
        if(skip_value_of)
          string(APPEND log "    arg [${arg}] ==> skip value of ${skip_value_of}\n")
          set(skip_value_of "")
        elseif("${arg}" MATCHES "^--sys_include(.:)?[/\\]")
          # Unix include path.
          string(REGEX REPLACE "^--sys_include" "" dir "${arg}")
          list(APPEND implicit_dirs_tmp ${dir})
          string(APPEND log "    arg [${arg}] ==> dir [${dir}]\n")
        elseif("${arg}" MATCHES "^-(I|isystem)(.:)?[/\\]")
          # Unix include path.
          string(REGEX REPLACE "^-(I|isystem)" "" dir "${arg}")
          list(APPEND implicit_dirs_tmp ${dir})
          string(APPEND log "    arg [${arg}] ==> dir [${dir}]\n")
        elseif("${arg}" MATCHES "^[-/](INCLUDE|include):(.+)")
          # MSVC search path.
          set(dir "${CMAKE_MATCH_2}")
          list(APPEND implicit_dirs_tmp ${dir})
          string(APPEND log "    arg [${arg}] ==> dir [${dir}]\n")
        elseif("${arg}" STREQUAL "cl.exe")
          string(APPEND log "    arg [${arg}] ==> recognize MSVC cl\n")
          set(is_msvc 1)
        else()
          string(APPEND log "    arg [${arg}] ==> ignore\n")
        endif()
      endforeach()
    else()
      string(APPEND log "  ignore line: [${line}]\n")
    endif()
  endforeach()

  # Cleanup list of library and framework directories.
  set(implicit_dirs "")
  foreach(dir IN LISTS implicit_dirs_tmp)
    get_filename_component(dir "${dir}" ABSOLUTE)
    string(FIND "${dir}" "${CMAKE_FILES_DIRECTORY}/" pos)
    if(NOT pos LESS 0)
      set(msg ", skipping non-system directory")
    else()
      set(msg "")
      list(APPEND implicit_dirs "${dir}")
    endif()
    string(APPEND log "  collapse include dir [${d}] ==> [${dir}]${msg}\n")
  endforeach()
  list(REMOVE_DUPLICATES implicit_dirs)

  # Return results.
  set(${dir_var}
      "${implicit_dirs}"
      PARENT_SCOPE)
  set(${log_var}
      "${log}"
      PARENT_SCOPE)
endfunction()

# ==============================================================================

message(CHECK_START "Detecting NVCXX compiler info")

# Compute the directory in which to run the test.
set(CMAKE_NVCXX_COMPILER_ID_DIR ${CMAKE_PLATFORM_INFO_DIR}/CompilerIdNVCXX)

# # Create a clean working directory.
file(REMOVE_RECURSE ${CMAKE_NVCXX_COMPILER_ID_DIR})
file(MAKE_DIRECTORY ${CMAKE_NVCXX_COMPILER_ID_DIR})
file(MAKE_DIRECTORY ${CMAKE_NVCXX_COMPILER_ID_DIR}/tmp)

# ==============================================================================

include(${CMAKE_ROOT}/Modules/CMakeDetermineCompiler.cmake)
include(${CMAKE_ROOT}/Modules/CMakeParseImplicitLinkInfo.cmake)
include(nvhpc_helpers)

# cmake-lint: disable=C0103,E1120

if(NOT
   (("${CMAKE_GENERATOR}" MATCHES "Make")
    OR ("${CMAKE_GENERATOR}" MATCHES "Ninja")
    OR ("${CMAKE_GENERATOR}" MATCHES "Visual Studio (1|[9][0-9])")))
  message(CHECK_FAIL "failed")
  message(FATAL_ERROR "NVCXX language not currently supported by \"${CMAKE_GENERATOR}\" generator")
endif()

if(${CMAKE_GENERATOR} MATCHES "Visual Studio")
  if(DEFINED ENV{NVCXX} OR DEFINED CMAKE_NVCXX_HOST_COMPILER)
    message(WARNING "Visual Studio does not support specifying NVCXX or CMAKE_NVCXX_HOST_COMPILER. \
Using the C++ compiler provided by Visual Studio.")
  endif()
else()
  if(NOT CMAKE_NVCXX_COMPILER)
    set(CMAKE_NVCXX_COMPILER_INIT NOTFOUND)

    # prefer the environment variable NVCXX
    if(NOT $ENV{NVCXX} STREQUAL "")
      get_filename_component(CMAKE_NVCXX_COMPILER_INIT $ENV{NVCXX} PROGRAM PROGRAM_ARGS CMAKE_NVCXX_FLAGS_ENV_INIT)
      if(CMAKE_NVCXX_FLAGS_ENV_INIT)
        set(CMAKE_NVCXX_COMPILER_ARG1
            "${CMAKE_NVCXX_FLAGS_ENV_INIT}"
            CACHE STRING "Arguments to CXX compiler")
      endif()
      if(NOT EXISTS ${CMAKE_NVCXX_COMPILER_INIT})
        message(CHECK_FAIL "failed")
        message(
          FATAL_ERROR
            "Could not find compiler set in environment variable NVCXX:\n$ENV{NVCXX}.\n${CMAKE_NVCXX_COMPILER_INIT}")
      endif()
    endif()

    # finally list compilers to try
    if(NOT CMAKE_NVCXX_COMPILER_INIT)
      set(CMAKE_NVCXX_COMPILER_LIST nvc++)
    endif()

    set(_CMAKE_NVCXX_COMPILER_PATHS "$ENV{NVCXX_PATH}/bin")
    _cmake_find_compiler(NVCXX)
    unset(_CMAKE_NVCXX_COMPILER_PATHS)
  else()
    _cmake_find_compiler_path(NVCXX)
  endif()

  mark_as_advanced(CMAKE_NVCXX_COMPILER)
endif()

if(NOT "$ENV{NVCXXARCHS}" STREQUAL "")
  set(CMAKE_NVCXX_ARCHITECTURES
      "$ENV{NVCXXARCHS}"
      CACHE STRING "NVCXX architectures")
endif()

# Build a small source file to identify the compiler.
if(NOT CMAKE_NVCXX_COMPILER_ID_RUN)
  set(CMAKE_NVCXX_COMPILER_ID_RUN 1)

  execute_process(
    COMMAND ${CMAKE_NVCXX_COMPILER} --version
    OUTPUT_VARIABLE _compiler_version
    RESULT_VARIABLE _compiler_version_result)

  # Display the final identification result.
  if(_compiler_version_result EQUAL 0)
    if(_compiler_version MATCHES
       "nvc\\+\\+( *[0-9]+\\.[0-9]+-[0-9]+) *[a-zA-Z]+ *[0-9]+-bit target on ([a-zA-Z0-9\\-]+ *[a-zA-Z]+)")
      string(REPLACE "-" "." _version ${CMAKE_MATCH_1})
      set(_archid " ${CMAKE_MATCH_2}")
    else()
      set(_version)
      set(_archid)
    endif()

    message(STATUS "The NVCXX compiler identification is " "NVHPC-nvc++${_version}")
    unset(_archid)
    unset(_version)
    unset(_variant)
  else()
    message(STATUS "The NVCXX compiler identification is unknown")
  endif()

  if(${CMAKE_GENERATOR} MATCHES "Visual Studio")
    # TODO: Fix once available on Windows
    get_filename_component(CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT "${CMAKE_NVCXX_COMPILER}" DIRECTORY)
    get_filename_component(CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT "${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}" DIRECTORY)
    get_filename_component(CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT "${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}" DIRECTORY)
    set(CMAKE_NVCXX_COMPILER_LIBRARY_ROOT "${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}")
  else()
    # cmake-lint: disable=C0103
    set(_NVCXX_NVCC_EXECUTABLE "${CMAKE_NVCXX_COMPILER}")

    include(CheckNVCXXCompilerFlag)
    set(_nvcxx_test_extra_flags)

    define_property(
      GLOBAL
      PROPERTY _nvcxx_try_compile_extra_flags
      BRIEF_DOCS "Extra compiler flags for NVCXX try_compile() statements to speed up compilation"
      FULL_DOCS "Extra compiler flags for NVCXX try_compile() statements to speed up compilation")

    if(_CMAKE_NVCXX_USE_FAST_SEARCH)
      if(NVCXX_FAST_SEARCH_FLAGS)
        set(_nvcxx_test_extra_flags ${NVCXX_FAST_SEARCH_FLAGS})
      else()
        set(_nvcxx_test_extra_flags -stdpar -cuda -gpu=cc60) # NB: cc60 is the earliest compatible with -stdpar
      endif()
    else()
      # Find single compute capability flag (for faster compilation later on)
      set(_found_compute_cc FALSE)
      foreach(cc 60 70 80 86) # NB: -stdpar compatible since cc60
        nvcxx_check_compiler_flag(-gpu=cc${cc} nvcxx_compiler_has_compute_${cc})
        if(nvcxx_compiler_has_compute_${cc})
          set(_found_compute_cc TRUE)
          set(CMAKE_REQUIRED_FLAGS -gpu=cc${cc})
          list(APPEND _nvcxx_test_extra_flags -gpu=cc${cc})
          break()
        endif()
      endforeach()

      # Find compiler flag to enable CUDA
      set(_found_cuda_flag FALSE)
      foreach(_flag stdpar cuda)
        nvcxx_check_compiler_flag(-${_flag} nvcxx_compiler_has_${_flag})
        if(nvcxx_compiler_has_${_flag})
          set(_found_cuda_flag TRUE)
          list(APPEND _nvcxx_test_extra_flags -${_flag})
          break()
        endif()
      endforeach()

      if(NOT _found_cuda_flag)
        message(CHECK_FAIL "failed")
        message(FATAL_ERROR "Test compilation with CUDA flag failed")
      endif()
    endif()

    set(_env_flags $ENV{NVCXXFLAGS})
    separate_arguments(_env_flags)
    list(APPEND _nvcxx_test_extra_flags ${_env_flags})
    nvhpc_sanitize_cc(_nvcxx_test_extra_flags LIST ${_nvcxx_test_extra_flags})
    set_property(GLOBAL PROPERTY _nvcxx_try_compile_extra_flags ${_nvcxx_test_extra_flags})

    file(WRITE ${CMAKE_NVCXX_COMPILER_ID_DIR}/CMakeNVCXXCompilerId.cpp "int main() {return 0;}")

    execute_process(
      COMMAND ${_NVCXX_NVCC_EXECUTABLE} ${_nvcxx_test_extra_flags} -dM CMakeNVCXXCompilerId.cpp
      WORKING_DIRECTORY ${CMAKE_NVCXX_COMPILER_ID_DIR}
      OUTPUT_VARIABLE _nvcxx_info_output
      ERROR_VARIABLE _nvcxx_info_output
      RESULT_VARIABLE _nvcxx_info_result)

    if(_nvcxx_info_result EQUAL 0)
      if(_nvcxx_info_output MATCHES "#define __NVCOMPILER_MAJOR__ *([0-9]+)")
        set(CMAKE_NVCXX_COMPILER_VERSION_MAJOR ${CMAKE_MATCH_1})
      endif()
      if(_nvcxx_info_output MATCHES "#define __NVCOMPILER_MINOR__ *([0-9]+)")
        set(CMAKE_NVCXX_COMPILER_VERSION_MINOR ${CMAKE_MATCH_1})
      endif()
      if(_nvcxx_info_output MATCHES "#define __NVCOMPILER_PATCHLEVEL__ *([0-9]+)")
        set(_patch ${CMAKE_MATCH_1})
      endif()

      if(DEFINED CMAKE_NVCXX_COMPILER_VERSION_MAJOR
         AND DEFINED CMAKE_NVCXX_COMPILER_VERSION_MINOR
         AND DEFINED _patch)
        set(CMAKE_NVCXX_COMPILER_VERSION
            ${CMAKE_NVCXX_COMPILER_VERSION_MAJOR}.${CMAKE_NVCXX_COMPILER_VERSION_MINOR}.${_patch})
      endif()
      if(_nvcxx_info_output MATCHES "#define __CUDACC_VER_MAJOR__ *([0-9]+)")
        set(CUDAToolkit_VERSION_MAJOR ${CMAKE_MATCH_1})
      endif()
      if(_nvcxx_info_output MATCHES "#define __CUDACC_VER_MINOR__ *([0-9]+)")
        set(CUDAToolkit_VERSION_MINOR ${CMAKE_MATCH_1})
      endif()
      if(_nvcxx_info_output MATCHES "#define __CUDACC_VER_BUILD__ *([0-9]+)")
        set(CUDAToolkit_VERSION_PATCH ${CMAKE_MATCH_1})
      endif()

      if(DEFINED CUDAToolkit_VERSION_MAJOR
         AND DEFINED CUDAToolkit_VERSION_MINOR
         AND DEFINED CUDAToolkit_VERSION_PATCH)
        set(CUDAToolkit_VERSION ${CUDAToolkit_VERSION_MAJOR}.${CUDAToolkit_VERSION_MINOR}.${CUDAToolkit_VERSION_PATCH})
      endif()

      if(_nvcxx_info_output MATCHES "#define __BYTE_ORDER__ *([a-zA-Z_]+)")
        if(CMAKE_MATCH_1 STREQUAL "__ORDER_LITTLE_ENDIAN__")
          set(CMAKE_NVCXX_BYTE_ORDER "LITTLE_ENDIAN")
        elseif(CMAKE_MATCH_1 STREQUAL "__ORDER_BIG_ENDIAN__")
          set(CMAKE_NVCXX_BYTE_ORDER "BIG_ENDIAN")
        else()
          set(CMAKE_NVCXX_BYTE_ORDER)
        endif()
      endif()

      if(_nvcxx_info_output MATCHES "#define __SIZEOF_POINTER__ *([0-9]+)")
        set(CMAKE_NVCXX_SIZEOF_DATA_PTR ${CMAKE_MATCH_1})
      endif()

      if(_nvcxx_info_output MATCHES "#define __cplusplus *([0-9]+)L")
        if(${CMAKE_MATCH_1} GREATER 202002)
          set(CMAKE_NVCXX_STANDARD_COMPUTED_DEFAULT 23)
        elseif(${CMAKE_MATCH_1} GREATER 201703)
          set(CMAKE_NVCXX_STANDARD_COMPUTED_DEFAULT 17)
        elseif(${CMAKE_MATCH_1} GREATER 201402)
          set(CMAKE_NVCXX_STANDARD_COMPUTED_DEFAULT 14)
        elseif(${CMAKE_MATCH_1} GREATER 201103)
          set(CMAKE_NVCXX_STANDARD_COMPUTED_DEFAULT 11)
        else()
          set(CMAKE_NVCXX_STANDARD_COMPUTED_DEFAULT 98)
        endif()
      endif()

      file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeOutput.log
           "Parsed NVCXX nvc++ compiler defines from:\n${_nvcxx_info_output}\n\n")
    endif()

    execute_process(
      COMMAND ${_NVCXX_NVCC_EXECUTABLE} ${_nvcxx_test_extra_flags} -v CMakeNVCXXCompilerId.cpp
      WORKING_DIRECTORY ${CMAKE_NVCXX_COMPILER_ID_DIR}
      OUTPUT_VARIABLE CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT
      ERROR_VARIABLE CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT
      RESULT_VARIABLE CMAKE_NVCXX_COMPILER_ID_RESULT)

    if(CMAKE_NVCXX_COMPILER_ID_RESULT EQUAL 0)
      file(
        APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeOutput.log
        "Compiling NVCXX nvc++ test program to extract implicit include and link information succeeded.\n"
        "Command line:\n"
        "${_NVCXX_NVCC_EXECUTABLE} ${_nvcxx_test_extra_flags} -v \
${CMAKE_NVCXX_COMPILER_ID_DIR}/CMakeNVCXXCompilerId.cpp\n\n"
        "Compilation output:\n${CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT}\n\n")
    else()
      file(
        APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeError.log
        "Compiling NVCXX nvc++ test program to extract implicit include and link information failed."
        "\nCommand line:\n"
        "${_NVCXX_NVCC_EXECUTABLE} ${_nvcxx_test_extra_flags} -v \
${CMAKE_NVCXX_COMPILER_ID_DIR}/CMakeNVCXXCompilerId.cpp\n\n"
        "Compilation output:\n${CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT}\n\n")
    endif()

    if(CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT MATCHES "PGI_CURR_CUDA_HOME=([^\r\n]*)")
      get_filename_component(CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT "${CMAKE_MATCH_1}" ABSOLUTE)
    else()
      if(CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT MATCHES "NVCOMPILER=([^\r\n]*)")
        set(_nvhpc_root "${CMAKE_MATCH_1}")
      else()
        get_filename_component(_nvhpc_root "${_NVCXX_NVCC_EXECUTABLE}" DIRECTORY)
        get_filename_component(_nvhpc_root "${_nvhpc_root}" DIRECTORY)
        get_filename_component(_nvhpc_root "${_nvhpc_root}" DIRECTORY)
      endif()
      set(CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT
          ${_nvhpc_root}/cuda/${CUDAToolkit_VERSION_MAJOR}.${CUDAToolkit_VERSION_MINOR})
    endif()

    set(CMAKE_NVCXX_DEVICE_LINKER "${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}/bin/nvlink${CMAKE_EXECUTABLE_SUFFIX}")
    set(CMAKE_NVCXX_FATBINARY "${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}/bin/fatbinary${CMAKE_EXECUTABLE_SUFFIX}")

    # In a non-scattered installation the following are equivalent to CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT. We first check
    # for a non-scattered installation to prefer it over a scattered installation.

    # CMAKE_NVCXX_COMPILER_LIBRARY_ROOT contains the device library.
    if(EXISTS "${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}/nvvm/libdevice")
      set(CMAKE_NVCXX_COMPILER_LIBRARY_ROOT "${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}")
    else()
      message(CHECK_FAIL "failed")
      message(FATAL_ERROR "Couldn't find NVCXX library root.")
    endif()

    set(CMAKE_NVCXX_COMPILER_TOOLKIT_LIBRARY_ROOT "${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}")
  endif()

  set(CMAKE_NVCXX_COMPILER_ID_FLAGS_ALWAYS "-v")
endif()

if(${CMAKE_GENERATOR} MATCHES "Visual Studio")
  # TODO: check this!
  # ~~~
  # set(CMAKE_NVCXX_HOST_LINK_LAUNCHER "${CMAKE_LINKER}")
  # set(CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES "")
  # set(CMAKE_NVCXX_HOST_IMPLICIT_LINK_DIRECTORIES "")
  # set(CMAKE_NVCXX_HOST_IMPLICIT_LINK_FRAMEWORK_DIRECTORIES "")

  # # We do not currently detect CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES but we do need to detect #
  # CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT from the compiler by looking at which cudart library exists in the implicit link
  # # libraries passed to the host linker. if(CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT MATCHES "link\\.exe
  # [^\n]*cudart_static\\.lib") set(CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT "STATIC")
  # elseif(CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT MATCHES "link\\.exe [^\n]*cudart\\.lib")
  # set(CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT "SHARED") else() set(CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT "NONE") endif()
  # set(_SET_CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT "set(CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT
  # \"${CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT}\")")
  # ~~~
else()
  set(_nvcxx_log "")
  string(REPLACE "\r" "" _nvcxx_output_orig "${CMAKE_NVCXX_COMPILER_PRODUCED_OUTPUT}")

  set(_nvcxx_link_line "")
  # Remove variable exports
  string(REGEX REPLACE "^ *Export *[^\n]*\n" "" _nvcxx_output "${_nvcxx_output_orig}")
  # Encode [] characters that break list expansion.
  string(REPLACE "[" "{==={" _nvcxx_output "${_nvcxx_output}")
  string(REPLACE "]" "}===}" _nvcxx_output "${_nvcxx_output}")
  # Split lines.
  string(REGEX REPLACE "\n+(#\\\$ )?" ";" _nvcxx_output "${_nvcxx_output}")
  # Get rid of all empty lines (except 1)
  list(REMOVE_DUPLICATES _nvcxx_output)
  foreach(line IN LISTS _nvcxx_output)
    set(_nvcxx_output_line "${line}")
    string(REPLACE "{==={" "[" _nvcxx_output_line "${_nvcxx_output_line}")
    string(REPLACE "}===}" "]" _nvcxx_output_line "${_nvcxx_output_line}")
    string(APPEND _nvcxx_log "  considering line: [${_nvcxx_output_line}]\n")
    if(_nvcxx_output_line MATCHES "^.*bin/ld[^\n]*" AND NOT _nvcxx_output_line MATCHES ".*warning[^\n]*")
      set(_nvcxx_link_line "${_nvcxx_output_line}")
      string(APPEND _nvcxx_log "    extracted link line: [${_nvcxx_link_line}]\n")
    elseif(_nvcxx_output_line MATCHES "^.*cpp1[^\n]*")
      set(_nvcxx_include_line "${_nvcxx_output_line}")
      string(APPEND _nvcxx_log "    extracted include line: [${_nvcxx_link_line}]\n")
    else()
      string(APPEND _nvcxx_log "    ignoring line\n")
    endif()
  endforeach()

  if(_nvcxx_link_line)
    if("x${CMAKE_NVCXX_SIMULATE_ID}" STREQUAL "xMSVC")
      # TODO: Check this!
      set(CMAKE_NVCXX_HOST_LINK_LAUNCHER "${CMAKE_LINKER}")
    else()
      # extract the compiler that is being used for linking
      separate_arguments(_nvcxx_link_line_args UNIX_COMMAND "${_nvcxx_link_line}")
      list(GET _nvcxx_link_line_args 0 _nvcxx_host_link_launcher)
      if(IS_ABSOLUTE "${_nvcxx_host_link_launcher}")
        string(APPEND _nvcxx_log "  extracted link launcher absolute path: [${_nvcxx_host_link_launcher}]\n")
        set(CMAKE_NVCXX_HOST_LINK_LAUNCHER "${_nvcxx_host_link_launcher}")
      else()
        string(APPEND _nvcxx_log "  extracted link launcher name: [${_nvcxx_host_link_launcher}]\n")
        find_program(
          _nvcxx_find_host_link_launcher
          NAMES ${_nvcxx_host_link_launcher}
          PATHS ${_nvcxx_path}
          NO_DEFAULT_PATH)
        find_program(_nvcxx_find_host_link_launcher NAMES ${_nvcxx_host_link_launcher})
        if(_nvcxx_find_host_link_launcher)
          string(APPEND _nvcxx_log "  found link launcher absolute path: [${_nvcxx_find_host_link_launcher}]\n")
          set(CMAKE_NVCXX_HOST_LINK_LAUNCHER "${_nvcxx_find_host_link_launcher}")
        else()
          string(APPEND _nvcxx_log "  could not find link launcher absolute path\n")
          set(CMAKE_NVCXX_HOST_LINK_LAUNCHER "${_nvcxx_host_link_launcher}")
        endif()
        unset(_nvcxx_find_host_link_launcher CACHE)
      endif()
    endif()

    cmake_parse_implicit_link_info(
      "${_nvcxx_link_line}" CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES CMAKE_NVCXX_HOST_IMPLICIT_LINK_DIRECTORIES
      CMAKE_NVCXX_HOST_IMPLICIT_LINK_FRAMEWORK_DIRECTORIES log "${CMAKE_NVCXX_IMPLICIT_OBJECT_REGEX}")

    # ~~~
    # NB: for now disable this and let NVCXX handle the implicit libraries...
    set(CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES ${CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES})
    set(CMAKE_NVCXX_IMPLICIT_LINK_DIRECTORIES ${CMAKE_NVCXX_HOST_IMPLICIT_LINK_DIRECTORIES})
    set(CMAKE_NVCXX_IMPLICIT_LINK_FRAMEWORK_DIRECTORIES ${CMAKE_NVCXX_HOST_IMPLICIT_LINK_FRAMEWORK_DIRECTORIES})

    # Detect CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT from the compiler by looking at which cudart library exists in the
    # implicit link libraries passed to the host linker. This is required when a project sets the cuda runtime library
    # as part of the initial flags.
    if(";${CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES};" MATCHES [[;cudart_static(\.lib)?;]])
      set(CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT "STATIC")
    elseif(";${CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES};" MATCHES [[;cudart(\.lib)?;]])
      set(CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT "SHARED")
    else()
      set(CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT "NONE")
    endif()
    # cmake-lint: disable=C0103
    set(_SET_CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT
        "set(CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT \"${CMAKE_NVCXX_RUNTIME_LIBRARY_DEFAULT}\")")

    file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeOutput.log
         "Parsed NVCXX nvc++ implicit link information from above output:\n${_nvcxx_log}\n${log}\n\n")
  else()
    message(CHECK_FAIL "failed")
    file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeError.log
         "Failed to parse NVCXX nvc++ implicit link information:\n${_nvcxx_log}\n\n")
    message(FATAL_ERROR "Failed to extract nvcxx implicit link line.")
  endif()
endif()

# CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES is detected above as the list of libraries that the NVCXX compiler implicitly
# passes to the host linker. CMake invokes the host linker directly and so needs to pass these libraries. We filter out
# those that should not be passed unconditionally both here and from CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES in
# CMakeTestNVCXXCompiler.
set(CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES_EXCLUDE
    # The NVCXX runtime libraries are controlled by CMAKE_NVCXX_RUNTIME_LIBRARY.
    cudart
    cudart.lib
    cudart_static
    cudart_static.lib
    cudadevrt
    cudadevrt.lib
    # Dependencies of the NVCXX static runtime library on Linux hosts.
    rt
    pthread
    dl)
list(REMOVE_ITEM CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES ${CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES_EXCLUDE})
# cmake-lint: disable=C0103
set(_SET_CMAKE_NVCXX_COMPILER_SYSROOT "")

# NB: for now disable this and let NVCXX handle the implicit libraries...
set(CMAKE_NVCXX_IMPLICIT_LINK_DIRECTORIES)
set(CMAKE_NVCXX_IMPLICIT_LINK_LIBRARIES)
set(CMAKE_NVCXX_HOST_IMPLICIT_LINK_DIRECTORIES)
set(CMAKE_NVCXX_HOST_IMPLICIT_LINK_LIBRARIES)

# ------------------------------------------------------------------------------

parse_include_info("${_nvcxx_include_line}" CMAKE_NVCXX_IMPLICIT_INCLUDE_DIRECTORIES log)
file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeOutput.log
     "Parsed NVCXX nvc++ implicit include information from above output:\n${_nvcc_log}\n${log}\n\n")

set(CMAKE_NVCXX_TOOLKIT_INCLUDE_DIRECTORIES)
foreach(_dir ${CMAKE_NVCXX_IMPLICIT_INCLUDE_DIRECTORIES})
  if(_dir MATCHES "^${CMAKE_NVCXX_COMPILER_TOOLKIT_ROOT}")
    get_filename_component(_tmp ${_dir} ABSOLUTE)
    list(APPEND CMAKE_NVCXX_TOOLKIT_INCLUDE_DIRECTORIES ${_tmp})
  endif()
endforeach(_dir)

list(REMOVE_ITEM CMAKE_NVCXX_IMPLICIT_INCLUDE_DIRECTORIES ${CMAKE_NVCXX_TOOLKIT_INCLUDE_DIRECTORIES})

set(CMAKE_NVCXX_COMPILER_ENV_VAR NVCXX)
set(CMAKE_NVCXX_COMPILE_FEATURES cuda_std_03;cuda_std_11;cuda_std_14;cuda_std_17)
set(CMAKE_NVCXX03_COMPILE_FEATURES cuda_std_03)
set(CMAKE_NVCXX11_COMPILE_FEATURES cuda_std_11)
set(CMAKE_NVCXX14_COMPILE_FEATURES cuda_std_14)
set(CMAKE_NVCXX17_COMPILE_FEATURES cuda_std_17)
set(CMAKE_NVCXX20_COMPILE_FEATURES cuda_std_20)
set(CMAKE_NVCXX23_COMPILE_FEATURES cuda_std_23)

# ==============================================================================
# Configure variables set in this file for fast reload later on

configure_file(${CMAKE_CURRENT_LIST_DIR}/CMakeNVCXXCompiler.cmake.in
               ${CMAKE_PLATFORM_INFO_DIR}/CMakeNVCXXCompiler.cmake @ONLY)

message(CHECK_PASS "done")
