# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

include_guard(GLOBAL)

cmake_policy(PUSH)
cmake_policy(SET CMP0054 NEW) # if() quoted variables not dereferenced
cmake_policy(SET CMP0057 NEW) # if() supports IN_LIST

include(_protect_arguments)

# Helper function to check if given source compiles and links into an executable.
#
# check_source_compiles_local(<lang> <source_code> <resultVar>)
function(cmake_check_source_compiles_local _lang _source _var)
  # cmake-lint: disable=R0912,R0915
  if(NOT DEFINED "${_var}")
    if(_lang STREQUAL "C")
      set(_lang_textual "C")
      set(_lang_ext "c")
    elseif(_lang STREQUAL "CXX")
      set(_lang_textual "C++")
      set(_lang_ext "cxx")
    elseif(_lang STREQUAL "CUDA")
      set(_lang_textual "CUDA")
      set(_lang_ext "cu")
    elseif(_lang STREQUAL "NVCXX")
      set(_lang_textual "NVCXX")
      set(_lang_ext "cpp")
      get_property(_flags GLOBAL PROPERTY _nvcxx_try_compile_extra_flags)
      if(_flags)
        string(APPEND CMAKE_REQUIRED_FLAGS " ${_flags}")
        list(APPEND CMAKE_REQUIRED_LINK_OPTIONS ${_flags})
      endif()
      set(CMAKE_EXTRA_CONTENT "set(CMAKE_NVCXX_FLAGS_INIT \"${CMAKE_NVCXX_FLAGS_INIT} -v\")\n
set(CMAKE_NVCXX_LDFLAGS_INIT \"${CMAKE_NVCXX_LDFLAGS_INIT} -v\")")
    elseif(_lang STREQUAL "Fortran")
      set(_lang_textual "Fortran")
      set(_lang_ext "F90")
    elseif(_lang STREQUAL "ISPC")
      set(_lang_textual "ISPC")
      set(_lang_ext "ispc")
    elseif(_lang STREQUAL "OBJC")
      set(_lang_textual "Objective-C")
      set(_lang_ext "m")
    elseif(_lang STREQUAL "OBJCXX")
      set(_lang_textual "Objective-C++")
      set(_lang_ext "mm")
    elseif(_lang STREQUAL "DPCXX")
      set(_lang_textual "DPC++")
      set(_lang_ext "cxx")
    else()
      message(SEND_ERROR "check_source_compiles: ${_lang}: unknown language.")
      return()
    endif()

    get_property(_supported_languages GLOBAL PROPERTY ENABLED_LANGUAGES)
    if(NOT _lang IN_LIST _supported_languages)
      message(SEND_ERROR "check_source_compiles: ${_lang}: needs to be enabled before use.")
      return()
    endif()

    set(_fail_regex)
    set(_src_ext)
    set(_key)
    foreach(arg ${ARGN})
      if("${arg}" MATCHES "^(FAIL_REGEX|SRC_EXT)$")
        set(_key "${arg}")
      elseif(_key STREQUAL "FAIL_REGEX")
        list(APPEND _fail_regex "${arg}")
      elseif(_key STREQUAL "SRC_EXT")
        set(_src_ext "${arg}")
        set(_key "")
      else()
        message(FATAL_ERROR "Unknown argument:\n  ${arg}\n")
      endif()
    endforeach()

    if(NOT _src_ext)
      set(_src_ext ${_lang_ext})
    endif()

    if(CMAKE_REQUIRED_LINK_OPTIONS)
      set(CHECK_${_lang}_SOURCE_COMPILES_ADD_LINK_OPTIONS LINK_OPTIONS ${CMAKE_REQUIRED_LINK_OPTIONS})
    else()
      set(CHECK_${_lang}_SOURCE_COMPILES_ADD_LINK_OPTIONS)
    endif()
    if(CMAKE_REQUIRED_LIBRARIES)
      set(CHECK_${_lang}_SOURCE_COMPILES_ADD_LIBRARIES LINK_LIBRARIES ${CMAKE_REQUIRED_LIBRARIES})
    else()
      set(CHECK_${_lang}_SOURCE_COMPILES_ADD_LIBRARIES)
    endif()
    if(CMAKE_REQUIRED_INCLUDES)
      set(CHECK_${_lang}_SOURCE_COMPILES_ADD_INCLUDES "-DINCLUDE_DIRECTORIES:STRING=${CMAKE_REQUIRED_INCLUDES}")
    else()
      set(CHECK_${_lang}_SOURCE_COMPILES_ADD_INCLUDES)
    endif()

    if(NOT CMAKE_REQUIRED_QUIET)
      message(CHECK_START "Performing Test ${_var}")
    endif()

    set(_srcdir ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp)
    set(_src ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp/src.${_src_ext})
    file(MAKE_DIRECTORY ${_srcdir})
    file(WRITE "${_src}" "${_source}\n")

    set(_cleanup_required FALSE)
    if(_lang STREQUAL "NVCXX" OR _lang STREQUAL "DPCXX")
      set(_cleanup_required TRUE)

      set(CMAKE_SOURCE_FILE src.${_src_ext})
      set(LANG ${_lang})
      set(CMAKE_LANG_FLAGS ${CMAKE_${LANG}_FLAGS})
      set(CMAKE_LANG_STANDARD ${CMAKE_${_lang}_STANDARD})
      set(CMAKE_LANG_STANDARD_REQUIRED ${CMAKE_${_lang}_STANDARD_REQUIRED})
      set(CMAKE_LANG_EXTENSIONS ${CMAKE_${_lang}_EXTENSIONS})
      list(INSERT CMAKE_REQUIRED_DEFINITIONS 0 -D${_var})

      string(RANDOM _random)
      set(CMAKE_EXEC_NAME cmTC_${_random})

      _protect_arguments(CMAKE_REQUIRED_DEFINITIONS)
      string(REPLACE ";" "\n                " CMAKE_REQUIRED_DEFINITIONS "${CMAKE_REQUIRED_DEFINITIONS}")

      configure_file(${CMAKE_CURRENT_LIST_DIR}/try_compile/CMakeLists.txt.in ${_srcdir}/CMakeLists.txt @ONLY)
      try_compile(
        ${_var} ${CMAKE_BINARY_DIR}/CMakeTmp
        ${_srcdir} CMAKE_TRY_COMPILE
        CMAKE_FLAGS -DCOMPILE_DEFINITIONS:STRING=${CMAKE_REQUIRED_FLAGS}
                    "${CHECK_${_lang}_SOURCE_COMPILES_ADD_INCLUDES}"
        OUTPUT_VARIABLE OUTPUT)
    else()
      try_compile(
        ${_var} ${CMAKE_BINARY_DIR}
        ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp/src.${_src_ext}
        COMPILE_DEFINITIONS -D${_var} ${CMAKE_REQUIRED_DEFINITIONS} ${CHECK_${_lang}_SOURCE_COMPILES_ADD_LINK_OPTIONS}
                            ${CHECK_${_lang}_SOURCE_COMPILES_ADD_LIBRARIES}
        CMAKE_FLAGS -DCOMPILE_DEFINITIONS:STRING=${CMAKE_REQUIRED_FLAGS}
                    "${CHECK_${_lang}_SOURCE_COMPILES_ADD_INCLUDES}"
        OUTPUT_VARIABLE OUTPUT)
    endif()

    foreach(_regex ${_fail_regex})
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

    if(_cleanup_required)
      file(REMOVE_RECURSE ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp)
    endif()
  endif()
endfunction()

cmake_policy(POP)

# Check if given source compiles and links into an executable.
#
# check_source_compiles_local(<lang> <code> <resultVar> [FAIL_REGEX <regex1> [<regex2>...]] [SRC_EXT <extension>])
#
# Same functionality as the builtin CMake check_source_compiles with additional support for NVCXX and DPCXX custom
# languages
function(check_source_compiles _lang _source _var)
  cmake_check_source_compiles_local(${_lang} "${_source}" ${_var} ${ARGN})
endfunction()
