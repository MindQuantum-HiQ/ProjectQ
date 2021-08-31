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

include_guard(GLOBAL)
include(CMakeCheckCompilerFlagCommonPatterns)

cmake_policy(PUSH)
cmake_policy(SET CMP0054 NEW) # if() quoted variables not dereferenced
cmake_policy(SET CMP0057 NEW) # if() supports IN_LIST

# cmake-lint: disable=R0912,R0915

# Check whether the compiler supports a given compilation flag
function(nvcxx_check_compiler_flag _flag _var)
  set(_lang DPCXX)
  set(_source "__host__ int main() { return 0; }")
  set(_lang_fail_regex FAIL_REGEX "nvc\\+\\+-Error-Unknown switch: .*")
  set(_lang_textual "DPCXX")
  set(_lang_ext "cu")

  # Normalize locale during test compilation.
  set(_locale_vars LC_ALL LC_MESSAGES LANG)
  foreach(var IN LISTS _locale_vars)
    set(_locale_vars_saved_${var} "$ENV{${var}}")
    set(ENV{${var}} C)
  endforeach()

  check_compiler_flag_common_patterns(_common_patterns)

  # ------------------------------------------------------------------------------

  set(_FAIL_REGEX)
  set(_SRC_EXT ${_lang_ext})
  set(_key)

  if(NOT DEFINED "${_var}")
    foreach(arg ${_lang_fail_regex} ${_common_patterns})
      if("${arg}" MATCHES "^(FAIL_REGEX|SRC_EXT)$")
        set(_key "${arg}")
      elseif(_key STREQUAL "FAIL_REGEX")
        list(APPEND _FAIL_REGEX "${arg}")
      elseif(_key STREQUAL "SRC_EXT")
        set(_SRC_EXT "${arg}")
        set(_key "")
      else()
        message(FATAL_ERROR "Unknown argument:\n  ${arg}\n")
      endif()
    endforeach()

    if(NOT CMAKE_REQUIRED_QUIET)
      message(CHECK_START "Performing Test ${_var}")
    endif()

    file(WRITE "${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp/src.${_SRC_EXT}" "${_source}\n")

    execute_process(
      COMMAND ${_DPCXX_NVCC_EXECUTABLE} -c -D${_var} ${_flag} ${CMAKE_REQUIRED_FLAGS}
              ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp/src.${_SRC_EXT}
      OUTPUT_VARIABLE OUTPUT
      ERROR_VARIABLE OUTPUT
      RESULT_VARIABLE RESULT)

    if(RESULT EQUAL 0)
      set(${_var} 1)
    else()
      set(${_var} 0)
    endif()

    foreach(_regex ${_FAIL_REGEX})
      if("${OUTPUT}" MATCHES "${_regex}")
        set(${_var} 0)
      endif()
    endforeach()

    if(${_var})
      set(${_var}
          1
          CACHE INTERNAL "Test ${_var}")
      if(NOT CMAKE_REQUIRED_QUIET)
        message(CHECK_PASS "Success")
      endif()
      file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeOutput.log
           "Performing ${_lang_textual} SOURCE FILE Test ${_var} succeeded with the following output:\n" "${OUTPUT}\n"
           "Source file was:\n${_source}\n")
    else()
      if(NOT CMAKE_REQUIRED_QUIET)
        message(CHECK_FAIL "Failed")
      endif()
      set(${_var}
          ""
          CACHE INTERNAL "Test ${_var}")
      file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeError.log
           "Performing ${_lang_textual} SOURCE FILE Test ${_var} failed with the following output:\n" "${OUTPUT}\n"
           "Source file was:\n${_source}\n")
    endif()
  endif()

  # ------------------------------------------------------------------------------

  foreach(var IN LISTS _locale_vars)
    set(ENV{${var}} ${_locale_vars_saved_${var}})
  endforeach()
  set(${_var}
      "${${_var}}"
      PARENT_SCOPE)
endfunction()

cmake_policy(POP)
