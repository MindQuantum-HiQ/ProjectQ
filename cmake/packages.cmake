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
# OpenMP

set(PARALLEL_LIBS)
if(USE_OPENMP)
  if(APPLE)
    find_program(BREW_CMD brew PATHS /usr/local/bin)
    if(BREW_CMD)
      # Homebrew installs libomp in ${LLVM_PREFIX}/lib and the headers in /usr/local/include
      execute_process(COMMAND ${BREW_CMD} --prefix llvm OUTPUT_VARIABLE LLVM_PREFIX)
      string(STRIP ${LLVM_PREFIX} LLVM_PREFIX)
      list(APPEND CMAKE_LIBRARY_PATH ${LLVM_PREFIX}/lib)
    else()
      # MacPorts install libomp in /opt/local/lib/libomp and the headers in /opt/local/include/libomp
      find_library(
        LIBOMP_LIB omp gomp libomp
        HINTS /opt/local/lib
        PATH_SUFFIXES libomp
        NO_DEFAULT_PATH
      )
      fin_path(
        LIBOMP_INC
        omp.h
        HINTS
        /opt/local/include
        PATH_SUFFIXES
        libomp
        NO_DEFAULT_PATH
      )
      if(LIBOMP_LIB AND LIBOMP_INC)
        get_filename_component(LIBOMP_DIR ${LIBOMP_LIB} DIRECTORY)
        list(APPEND CMAKE_LIBRARY_PATH ${LIBOMP_DIR})
        list(APPEND CMAKE_INCLUDE_PATH ${LIBOMP_INC})
      endif()
    endif()
  endif()

  # ----------------------------------------------------------------------------

  if(APPLE)
    list(PREPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR}/Modules)
  endif()
  find_package(OpenMP)
  if(OpenMP_FOUND)
    list(APPEND PARALLEL_LIBS OpenMP::OpenMP_CXX)
  endif()
endif()

if(USE_PARALLEL_STL)
  find_package(TBB REQUIRED tbb)
  target_compile_options(TBB::tbb INTERFACE "$<$<COMPILE_LANGUAGE:DPCXX>:-tbb>")
  list(APPEND PARALLEL_LIBS TBB::tbb)
endif()

# ==============================================================================

if(ENABLE_CUDA)
  if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.17)
    find_package(CUDAToolkit REQUIRED)
  else()
    find_package(CUDA REQUIRED)
    if(NOT CUDA_cuda_driver_LIBRARY)
      set(CUDA_cuda_driver_LIBRARY ${CUDA_CUDA_LIBRARY})
    endif()

    if(CUDA_cuda_driver_LIBRARY)
      add_library(CUDA::cuda_driver IMPORTED INTERFACE)
      target_include_directories(CUDA::cuda_driver SYSTEM INTERFACE "${CUDA_INCLUDE_DIRS}")
      target_link_libraries(CUDA::cuda_driver INTERFACE "${CUDA_cuda_driver_LIBRARY}")
    endif()
  endif()
endif()

# ==============================================================================

find_package(
  Python 3.5.0
  COMPONENTS Interpreter Development.Module
  REQUIRED
)

if(CMAKE_VERSION VERSION_LESS 3.17)
  message(CHECK_START "Looking for python SOABI")

  execute_process(
    COMMAND "${Python_EXECUTABLE}" "-c"
    "from sysconfig import get_config_var; print (get_config_var ('EXT_SUFFIX') or s.get_config_var ('SO')) "
    RESULT_VARIABLE _soabi_success
    OUTPUT_VARIABLE _python_so_extension
    ERROR_VARIABLE _soabi_error_value
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )

  if(NOT _soabi_success MATCHES 0)
    message(CHECK_FAIL "failed")
    message(FATAL_ERROR "Failed to extract Python SOABI extension:\n${_soabi_error_value} ")
  else()
    message(CHECK_PASS "done")
  endif()
endif()

# ------------------------------------------------------------------------------

include(${CMAKE_CURRENT_LIST_DIR}/pybind11.cmake)

# ==============================================================================
# For Huawei internal security assessment

if(BINSCOPE)
  get_filename_component(_binscope_path ${BINSCOPE} DIRECTORY)
  get_filename_component(_binscope_name ${BINSCOPE} NAME)
endif()

find_program(
  binscope_exec
  NAMES binscope ${_binscope_name}
  HINTS ${_binscope_path}
)
include(${CMAKE_CURRENT_LIST_DIR}/binscope.cmake)

# ==============================================================================
