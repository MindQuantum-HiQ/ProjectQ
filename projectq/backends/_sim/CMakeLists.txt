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

# ~~~
# Add a C++ Python extension
#
# add_aux_python_library(<target>
#                        [OUTPUT <output_dir>]
#                        [KERNELS <kernel_include_dir>]
#                        [DEFINES <compiler_define> [<compiler_define> ...]]
#                        [LIBS <library> [<library> ...]]
#                        [INCLUDES <include_dir> [<include_dir> ...]]
# ~~~
macro(add_aux_python_library target)
  cmake_parse_arguments(${target} "" "OUTPUT;KERNELS" "DEFINES;LIBS;INCLUDES" ${ARGN})

  python_add_library(${target} MODULE ${${target}_UNPARSED_ARGUMENTS})

  target_include_directories(
    ${target}
    PRIVATE ${${target}_INCLUDES} ${CMAKE_CURRENT_SOURCE_DIR}/include ${CMAKE_CURRENT_SOURCE_DIR}/src/_cppkernels
            ${CMAKE_CURRENT_SOURCE_DIR}/src/_cppkernels/${${target}_KERNELS})

  target_compile_definitions(${target} PRIVATE ${${target}_DEFINES} MODULE_NAME=${target})

  target_link_libraries(${target} PRIVATE pybind11::module ${${target}_LIBS})

  python_install_set_rpath(${target} ".")

  if(NOT ${target}_OUTPUT)
    set_output_directory_auto(${target} "projectq/backends/_sim")
  else()
    set_output_directory_auto(${target} ${${target}_OUTPUT})
  endif()
endmacro()

# ==============================================================================

set(EXT_NAME _cppsim)

# ==============================================================================

# Scalar instructions, single-threaded
add_aux_python_library(${EXT_NAME}_scalar_serial src/kernels.cpp KERNELS scalar DEFINES NOINTRIN)

# Scalar instructions, multi-threaded
add_aux_python_library(
  ${EXT_NAME}_scalar_threaded
  src/kernels.cpp
  KERNELS
  scalar
  DEFINES
  NOINTRIN
  ENABLE_MULTITHREADING
  LIBS
  ${PARALLEL_LIBS})

# ------------------------------------------------------------------------------

# Vector instructions, single-threaded
add_aux_python_library(${EXT_NAME}_vector_serial src/kernels.cpp KERNELS vector DEFINES INTRIN)

# Vector instructions, multi-threaded
add_aux_python_library(
  ${EXT_NAME}_vector_threaded
  src/kernels.cpp
  KERNELS
  vector
  DEFINES
  ENABLE_MULTITHREADING
  INTRIN
  LIBS
  ${PARALLEL_LIBS})

set_target_properties(${EXT_NAME}_vector_serial ${EXT_NAME}_vector_threaded PROPERTIES SUPPORTS_SIMD TRUE)

# ------------------------------------------------------------------------------
# Offload to NVIDIA GPU
if(ENABLE_CUDA)
  add_aux_python_library(
    ${EXT_NAME}_offload_nvidia
    src/_cppkernels/nvidia/kernels.cpp
    src/_cppkernels/nvidia/kernels.cu
    src/_cppkernels/nvidia/gmem.cu
    KERNELS
    scalar
    DEFINES
    HIQ_WITH_CUDA)

  if(CMAKE_NVCXX_COMPILER_VERSION VERSION_LESS 21.5 OR NOT CUDA_STATIC)
    # NB: if NVHPC < 21.5 and static, there is nothing we can do...
    message(STATUS "Using CUDA-PGI workaround")
    target_compile_definitions(${EXT_NAME}_offload_nvidia PRIVATE CUDA_PGI_WORKAROUND)
    target_link_libraries(${EXT_NAME}_offload_nvidia PUBLIC CUDA::cuda_driver)
  endif()

  include(target_cuda_architectures)
  target_cuda_architectures(${EXT_NAME}_offload_nvidia PUBLIC LANG NVCXX ${CMAKE_CUDA_ARCHITECTURES})
  set_source_files_properties(src/_cppkernels/nvidia/kernels.cpp PROPERTIES LANGUAGE NVCXX)
else()
  set(_tmp ${_CPPSIM_OFFLOAD_NVIDIA_OUTPUT_DIR}) # Silence CMake warning
  message(STATUS "Not compiling the NVIDIA GPU backend, because nvc++ executable is not found in the $PATH "
                 "or NVHPC could not be properly configured by CMake\n"
                 "(NVIDIA HPC SDK could be downloaded from https://developer.nvidia.com/hpc-sdk)")
endif()

# TODO: Offload to Intel GPU
if(ENABLE_DPCXX)
  # Example
  # ~~~
  # set(_src ${CMAKE_CURRENT_BINARY_DIR}/src/kernels_dpcpp.cpp)
  # configure_file(${CMAKE_CURRENT_LIST_DIR}/src/kernels.cpp ${_src} COPYONLY)
  # add_aux_python_library(
  #   ${EXT_NAME}_offload_intel
  #   ${_src}
  #   KERNELS
  #   scalar
  #   DEFINES
  #   ENABLE_MULTITHREADING
  #   LIBS
  #   ${PARALLEL_LIBS})
  # set_source_files_properties(${_src} PROPERTIES LANGUAGE DPCXX)
  # ~~~
endif()

# ------------------------------------------------------------------------------

python_add_library(${EXT_NAME} MODULE src/${EXT_NAME}.cpp src/simulator.cpp src/simbackends.cpp src/instrset.cpp)
target_link_libraries(${EXT_NAME} PRIVATE pybind11::module)
target_include_directories(${EXT_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
                                               ${CMAKE_CURRENT_SOURCE_DIR}/src/_cppkernels)
set_output_directory_auto(${EXT_NAME} "projectq/backends/_sim")
if(ENABLE_CUDA)
  target_link_libraries(${EXT_NAME} PUBLIC $<IF:$<BOOL:${CUDA_STATIC}>,CUDA::cudart_static,CUDA::cudart>)
  target_compile_definitions(${EXT_NAME} PRIVATE HIQ_WITH_CUDA)
endif()

# ==============================================================================
