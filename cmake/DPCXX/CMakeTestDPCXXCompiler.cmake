if(CMAKE_DPCXX_COMPILER_FORCED)
  # The compiler configuration was forced by the user. Assume the user has configured all compiler information.
  set(CMAKE_DPCXX_COMPILER_WORKS TRUE)
  return()
endif()

include(CMakeTestCompilerCommon)

# work around enforced code signing and / or missing executable target type
set(__CMAKE_SAVED_TRY_COMPILE_TARGET_TYPE ${CMAKE_TRY_COMPILE_TARGET_TYPE})
if(_CMAKE_FEATURE_DETECTION_TARGET_TYPE)
  set(CMAKE_TRY_COMPILE_TARGET_TYPE ${_CMAKE_FEATURE_DETECTION_TARGET_TYPE})
endif()

# Remove any cached result from an older CMake version. We now store this in CMakeDPCXXCompiler.cmake.
unset(CMAKE_DPCXX_COMPILER_WORKS CACHE)

# Try to identify the ABI and configure it into CMakeDPCXXCompiler.cmake
include(${CMAKE_ROOT}/Modules/CMakeDetermineCompilerABI.cmake)

cmake_determine_compiler_abi(DPCXX ${CMAKE_CURRENT_LIST_DIR}/CMakeDPCXXCompilerABI.cpp)
if(CMAKE_DPCXX_ABI_COMPILED)
  # The compiler worked so skip dedicated test below.
  set(CMAKE_DPCXX_COMPILER_WORKS TRUE)
  message(STATUS "Check for working DPCXX compiler: ${CMAKE_DPCXX_COMPILER} - skipped")
endif()

# This file is used by EnableLanguage in cmGlobalGenerator to determine that the selected C++ compiler can actually
# compile and link the most basic of programs.   If not, a fatal error is set and cmake stops processing commands and
# will not generate any makefiles or projects.
if(NOT CMAKE_DPCXX_COMPILER_WORKS)
  PrintTestCompilerStatus("DPCXX")
  __testcompiler_settrycompiletargettype()
  file(WRITE ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp/testDPCXXCompiler.cxx
       "#ifndef __cplusplus\n" "# error \"The CMAKE_DPCXX_COMPILER is set to a C compiler\"\n" "#endif\n"
       "int main(){return 0;}\n")
  try_compile(
    CMAKE_DPCXX_COMPILER_WORKS ${CMAKE_BINARY_DIR}
    ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp/testDPCXXCompiler.cxx
    OUTPUT_VARIABLE __CMAKE_DPCXX_COMPILER_OUTPUT)
  # Move result from cache to normal variable.
  set(CMAKE_DPCXX_COMPILER_WORKS ${CMAKE_DPCXX_COMPILER_WORKS})
  unset(CMAKE_DPCXX_COMPILER_WORKS CACHE)
  __testcompiler_restoretrycompiletargettype()
  if(NOT CMAKE_DPCXX_COMPILER_WORKS)
    printtestcompilerresult(CHECK_FAIL "broken")
    file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeError.log
         "Determining if the DPCXX compiler works failed with "
         "the following output:\n${__CMAKE_DPCXX_COMPILER_OUTPUT}\n\n")
    string(REPLACE "\n" "\n  " _output "${__CMAKE_DPCXX_COMPILER_OUTPUT}")
    message(
      FATAL_ERROR
        "The C++ compiler\n  \"${CMAKE_DPCXX_COMPILER}\"\n" "is not able to compile a simple test program.\nIt fails "
        "with the following output:\n  ${_output}\n\n" "CMake will not be able to correctly generate this project.")
  endif()
  printtestcompilerresult(CHECK_PASS "works")
  file(APPEND ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeOutput.log
       "Determining if the DPCXX compiler works passed with "
       "the following output:\n${__CMAKE_DPCXX_COMPILER_OUTPUT}\n\n")
endif()

# NB: this currently does not work...

# Try to identify the compiler features
# ~~~
# include(${CMAKE_ROOT}/Modules/CMakeDetermineCompileFeatures.cmake)
# cmake_determine_compile_features(DPCXX)
# ~~~

# Re-configure to save learned information.
configure_file(${CMAKE_CURRENT_LIST_DIR}/CMakeDPCXXCompiler.cmake.in
               ${CMAKE_PLATFORM_INFO_DIR}/CMakeDPCXXCompiler.cmake @ONLY)
include(${CMAKE_PLATFORM_INFO_DIR}/CMakeDPCXXCompiler.cmake)

if(CMAKE_DPCXX_SIZEOF_DATA_PTR)
  foreach(file ${CMAKE_DPCXX_ABI_FILES})
    include(${file})
  endforeach()
  unset(CMAKE_DPCXX_ABI_FILES)
endif()

set(CMAKE_TRY_COMPILE_TARGET_TYPE ${__CMAKE_SAVED_TRY_COMPILE_TARGET_TYPE})
unset(__CMAKE_SAVED_TRY_COMPILE_TARGET_TYPE)
unset(__CMAKE_DPCXX_COMPILER_OUTPUT)
