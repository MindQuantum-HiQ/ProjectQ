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
# Largely inspired by the FindBoost.cmake module:
#
# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.
# ==============================================================================

# cmake-lint: disable=C0103,C0111,C0307

#[=======================================================================[.rst:
FindTBB
---------

Find TBB include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(TBB
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if TBB is not found
    [COMPONENTS <libs>...] # TBB libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "TBB
CMake" build.  For the latter case skip to the :ref:`TBB CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``TBB_FOUND``
  True if headers and requested libraries were found.

``TBB_INCLUDE_DIRS``
  TBB include directories.

``TBB_LIBRARY_DIRS``
  Link directories for TBB libraries.

``TBB_LIBRARIES``
  TBB component libraries to be linked.

``TBB_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``TBB_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``TBB_VERSION``
  TBB version number in ``X.Y`` format.

``TBB_VERSION_MAJOR``
  TBB major version number (``X`` in ``X.Y``).

``TBB_VERSION_MINOR``
  TBB minor version number (``Y`` in ``X.Y``).

``TBB_INTERFACE_VERSION``
  TBB engineering-focused interface version

``TBB_INTERFACE_VERSION_MAJOR``
  TBB engineering-focused interface major version

``TBB_BINARY_VERSION`` or ``TBB_COMPATIBLE_INTERFACE_VERSION`` (legacy)
  TBB binary compatibility version

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``TBB_INCLUDE_DIR``
  Directory containing TBB headers.

``TBB_LIBRARY_DIR_RELEASE``
  Directory containing release TBB libraries.

``TBB_LIBRARY_DIR_DEBUG``
  Directory containing debug TBB libraries.

``TBB_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``TBB_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``TBB_ROOT``, ``TBBROOT``
  Preferred installation prefix.

``TBB_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``TBB_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``TBB_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``TBB``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the TBB header files using the above hint variables (excluding ``TBB_LIBRARYDIR``) and
saves the result in ``TBB_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``TBB_INCLUDEDIR``), "lib" directories near ``TBB_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``TBB_LIBRARY_DIR_DEBUG`` and ``TBB_LIBRARY_DIR_RELEASE`` and
individual library locations in ``TBB_<COMPONENT>_LIBRARY_DEBUG`` and ``TBB_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``TBB::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

Implicit dependencies such as ``TBB::tbbmalloc`` requiring ``TBB::tbb`` will be automatically detected and satisfied,
even if tbb is not specified when using :command:`find_package` and if ``TBB::tbb`` is not added to
:command:`target_link_libraries`.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(TBB)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

TBB libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``TBB_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``TBB_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  TBB_FIND_RELEASE_ONLY is ``ON``).

``TBB_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``TBB_DEBUG``
  Set to ``ON`` to enable debug output from ``FindTBB``.  Please enable this before filing any bug report.

``TBB_LIBRARY_DIR``
  Default value for ``TBB_LIBRARY_DIR_RELEASE`` and ``TBB_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find TBB headers only:

.. code-block:: cmake

  find_package(TBB 2020.03)
  if(TBB_FOUND)
    include_directories(${TBB_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC TBB::tbb)
  endif()

Find TBB libraries and use imported targets:

.. code-block:: cmake

  find_package(TBB 2020.03 REQUIRED COMPONENTS tbbmalloc tbbmalloc_proxy)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC TBB::tbbmalloc TBB::tbbmalloc_proxy)

Find TBB headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(TBB_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(TBB_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(TBB 2020.03 COMPONENTS TBB::tbbmalloc TBB::tbbmalloc_proxy)
  if(TBB_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC TBB::tbbmalloc TBB::tbbmalloc_proxy)
  endif()

.. _`TBB CMake`:

TBB CMake
^^^^^^^^^^^

If TBB was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``TBBConfig.cmake`` and stores the result in ``CACHE``
entry ``TBB_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the TBB CMake package configuration for details on what it provides.

Set ``TBB_NO_TBB_CMAKE`` to ``ON``, to disable the search for tbb-cmake.

#]=======================================================================]

# The FPHSA helper provides standard way of reporting final search results to the user including the version and
# component checks.
include(FindPackageHandleStandardArgs)

# Save project's policies
cmake_policy(PUSH)
cmake_policy(SET CMP0057 NEW) # if IN_LIST
cmake_policy(SET CMP0102 NEW) # if mark_as_advanced(non_cache_var)

# ==============================================================================
# FindTBB general variables
set(_TBB_TARGET_DEFINITIONS "$<$<OR:$<CONFIG:Debug>,$<CONFIG:RelWithDebInfo>>:TBB_USE_DEBUG=1>"
                            "__TBB_NO_IMPLICIT_LINKAGE=1")

# ==============================================================================
# FindTBB functions & macros
#

#
# Print debug text if TBB_DEBUG is set. Call example: _TBB_DEBUG_PRINT("${CMAKE_CURRENT_LIST_FILE}"
# "${CMAKE_CURRENT_LIST_LINE}" "debug message")
#
function(_tbb_debug_print file line text)
  if(TBB_DEBUG)
    message(STATUS "[ ${file}:${line} ] ${text}")
  endif()
endfunction()

#
# _TBB_DEBUG_PRINT_VAR(file line variable_name [ENVIRONMENT] [SOURCE "short explanation of origin of var value"])
#
# ENVIRONMENT - look up environment variable instead of CMake variable
#
# Print variable name and its value if TBB_DEBUG is set. Call example: _TBB_DEBUG_PRINT_VAR("${CMAKE_CURRENT_LIST_FILE}"
# "${CMAKE_CURRENT_LIST_LINE}" TBB_ROOT)
#
function(_tbb_debug_print_var file line name)
  if(TBB_DEBUG)
    cmake_parse_arguments(_args "ENVIRONMENT" "SOURCE" "" ${ARGN})

    unset(source)
    if(_args_SOURCE)
      set(source " (${_args_SOURCE})")
    endif()

    if(_args_ENVIRONMENT)
      if(DEFINED ENV{${name}})
        set(value "\"$ENV{${name}}\"")
      else()
        set(value "<unset>")
      endif()
      set(_name "ENV{${name}}")
    else()
      if(DEFINED "${name}")
        set(value "\"${${name}}\"")
      else()
        set(value "<unset>")
      endif()
      set(_name "${name}")
    endif()

    _tbb_debug_print("${file}" "${line}" "${_name} = ${value}${source}")
  endif()
endfunction()

# ######################################################################################################################
#
# Check the existence of the libraries.
#
# ######################################################################################################################
# This macro was taken directly from the FindQt4.cmake file that is included with the CMake distribution. This is NOT my
# work. All work was done by the original authors of the FindQt4.cmake file. Only minor modifications were made to
# remove references to Qt and make this file more generally applicable And ELSE/ENDIF pairs were removed for
# readability.
# ######################################################################################################################

macro(_tbb_adjust_lib_vars basename)
  if(TBB_INCLUDE_DIR)
    if(TBB_${basename}_LIBRARY_DEBUG AND TBB_${basename}_LIBRARY_RELEASE)
      # if the generator is multi-config or if CMAKE_BUILD_TYPE is set for single-config generators, set optimized and
      # debug libraries
      get_property(_isMultiConfig GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
      if(_isMultiConfig OR CMAKE_BUILD_TYPE)
        set(TBB_${basename}_LIBRARY optimized ${TBB_${basename}_LIBRARY_RELEASE} debug ${TBB_${basename}_LIBRARY_DEBUG})
      else()
        # For single-config generators where CMAKE_BUILD_TYPE has no value, just use the release libraries
        set(TBB_${basename}_LIBRARY ${TBB_${basename}_LIBRARY_RELEASE})
      endif()
      # FIXME: This probably should be set for both cases
      set(TBB_${basename}_LIBRARIES optimized ${TBB_${basename}_LIBRARY_RELEASE} debug ${TBB_${basename}_LIBRARY_DEBUG})
    endif()

    # if only the release version was found, set the debug variable also to the release version
    if(TBB_${basename}_LIBRARY_RELEASE AND NOT TBB_${basename}_LIBRARY_DEBUG)
      set(TBB_${basename}_LIBRARY_DEBUG ${TBB_${basename}_LIBRARY_RELEASE})
      set(TBB_${basename}_LIBRARY ${TBB_${basename}_LIBRARY_RELEASE})
      set(TBB_${basename}_LIBRARIES ${TBB_${basename}_LIBRARY_RELEASE})
    endif()

    # if only the debug version was found, set the release variable also to the debug version
    if(TBB_${basename}_LIBRARY_DEBUG AND NOT TBB_${basename}_LIBRARY_RELEASE)
      set(TBB_${basename}_LIBRARY_RELEASE ${TBB_${basename}_LIBRARY_DEBUG})
      set(TBB_${basename}_LIBRARY ${TBB_${basename}_LIBRARY_DEBUG})
      set(TBB_${basename}_LIBRARIES ${TBB_${basename}_LIBRARY_DEBUG})
    endif()

    # If the debug & release library ends up being the same, omit the keywords
    if("${TBB_${basename}_LIBRARY_RELEASE}" STREQUAL "${TBB_${basename}_LIBRARY_DEBUG}")
      set(TBB_${basename}_LIBRARY ${TBB_${basename}_LIBRARY_RELEASE})
      set(TBB_${basename}_LIBRARIES ${TBB_${basename}_LIBRARY_RELEASE})
    endif()

    if(TBB_${basename}_LIBRARY)
      set(TBB_${basename}_FOUND ON)
    endif()
  endif()

  # Make variables changeable to the advanced user
  mark_as_advanced(TBB_${basename}_LIBRARY_RELEASE TBB_${basename}_LIBRARY_DEBUG)
endmacro()

# ~~~
# Detect changes in used variables.
# Compares the current variable value with the last one.
# In short form:
# v != v_LAST                      -> CHANGED = 1
# v is defined, v_LAST not         -> CHANGED = 1
# v is not defined, but v_LAST is  -> CHANGED = 1
# otherwise                        -> CHANGED = 0
# CHANGED is returned in variable named ${changed_var}
# ~~~
macro(_tbb_change_detect changed_var)
  set(${changed_var} 0)
  foreach(v ${ARGN})
    if(DEFINED _TBB_COMPONENTS_SEARCHED)
      if(${v})
        if(_${v}_LAST)
          string(COMPARE NOTEQUAL "${${v}}" "${_${v}_LAST}" _${v}_CHANGED)
        else()
          set(_${v}_CHANGED 1)
        endif()
      elseif(_${v}_LAST)
        set(_${v}_CHANGED 1)
      endif()
      if(_${v}_CHANGED)
        set(${changed_var} 1)
      endif()
    else()
      set(_${v}_CHANGED 0)
    endif()
  endforeach()
endmacro()

#
# Find the given library (var). Use 'build_type' to support different lib paths for RELEASE or DEBUG builds
#
macro(_tbb_find_library var build_type)
  find_library(${var} ${ARGN})

  if(${var})
    # If this is the first library found then save TBB_LIBRARY_DIR_[RELEASE,DEBUG].
    if(NOT TBB_LIBRARY_DIR_${build_type})
      get_filename_component(_dir "${${var}}" PATH)
      set(TBB_LIBRARY_DIR_${build_type}
          "${_dir}"
          CACHE PATH "TBB library directory ${build_type}" FORCE)
    endif()
  elseif(_TBB_FIND_LIBRARY_HINTS_FOR_COMPONENT)
    # Try component-specific hints but do not save TBB_LIBRARY_DIR_[RELEASE,DEBUG].
    find_library(${var} HINTS ${_TBB_FIND_LIBRARY_HINTS_FOR_COMPONENT} ${ARGN})
  endif()

  # If TBB_LIBRARY_DIR_[RELEASE,DEBUG] is known then search only there.
  if(TBB_LIBRARY_DIR_${build_type})
    set(_TBB_LIBRARY_SEARCH_DIRS_${build_type} ${TBB_LIBRARY_DIR_${build_type}} NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
    _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_LIBRARY_DIR_${build_type}")
    _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}"
                         "_TBB_LIBRARY_SEARCH_DIRS_${build_type}")
  endif()
endmacro()

# ------------------------------------------------------------------------------

#
# Get component dependencies.  Requires the dependencies to have been defined for the TBB release version.
#
# * component - the component to check
# * _ret - list of library dependencies
#
function(_tbb_component_dependencies component _ret)
  set(_TBB_TBBMALLOC_PROXY_DEPENDENCIES tbbmalloc)

  string(TOUPPER ${component} uppercomponent)
  set(${_ret}
      ${_TBB_${uppercomponent}_DEPENDENCIES}
      PARENT_SCOPE)

  string(REGEX REPLACE ";" " " _TBB_DEPS_STRING "${_TBB_${uppercomponent}_DEPENDENCIES}")
  if(NOT _TBB_DEPS_STRING)
    set(_TBB_DEPS_STRING "(none)")
  endif()
  # message(STATUS "Dependencies for TBB::${component}: ${_TBB_DEPS_STRING}")
endfunction()

#
# Determine if any missing dependencies require adding to the component list.
#
# Sets _TBB_${COMPONENT}_DEPENDENCIES for each required component
#
# * componentvar - the component list variable name
# * extravar - the indirect dependency list variable name
#
function(_tbb_missing_dependencies componentvar extravar)
  # * _TBB_unprocessed_components - list of components requiring processing
  # * _TBB_processed_components - components already processed (or currently being processed)
  # * _TBB_new_components - new components discovered for future processing

  list(APPEND _TBB_unprocessed_components ${${componentvar}})

  while(_TBB_unprocessed_components)
    list(APPEND _TBB_processed_components ${_TBB_unprocessed_components})
    foreach(component ${_TBB_unprocessed_components})
      string(TOUPPER ${component} uppercomponent)
      set(${_ret}
          ${_TBB_${uppercomponent}_DEPENDENCIES}
          PARENT_SCOPE)
      _tbb_component_dependencies("${component}" _TBB_${uppercomponent}_DEPENDENCIES)
      set(_TBB_${uppercomponent}_DEPENDENCIES
          ${_TBB_${uppercomponent}_DEPENDENCIES}
          PARENT_SCOPE)
      foreach(componentdep ${_TBB_${uppercomponent}_DEPENDENCIES})
        if(NOT ("${componentdep}" IN_LIST _TBB_processed_components OR "${componentdep}" IN_LIST _TBB_new_components))
          list(APPEND _TBB_new_components ${componentdep})
        endif()
      endforeach()
    endforeach()
    set(_TBB_unprocessed_components ${_TBB_new_components})
    unset(_TBB_new_components)
  endwhile()
  set(_TBB_extra_components ${_TBB_processed_components})
  if(_TBB_extra_components AND ${componentvar})
    list(REMOVE_ITEM _TBB_extra_components ${${componentvar}})
  endif()
  set(${componentvar}
      ${_TBB_processed_components}
      PARENT_SCOPE)
  set(${extravar}
      ${_TBB_extra_components}
      PARENT_SCOPE)
endfunction()

function(_tbb_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
  if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set(_arch intel64)
  else()
    set(_arch ia32)
  endif()

  if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC")
    if(MSVC_TOOLSET_VERSION GREATER_EQUAL 140)
      # Shared libraries
      list(APPEND ${componentlibvar} ${basedir}/redist/${_arch}/vc14)
      list(APPEND ${componentlibvar} ${basedir}/redist/${_arch}/vc14_uwp)
      # Shared libraries (legacy)
      list(APPEND ${componentlibvar} ${basedir}/bin/${_arch}/vc14)
      list(APPEND ${componentlibvar} ${basedir}/bin/${_arch}/vc14_uwp)
    elseif(MSVC_TOOLSET_VERSION GREATER_EQUAL 120)
      # Shared libraries (legacy)
      list(APPEND ${componentlibvar} ${basedir}/bin/${_arch}/vc12)
      list(APPEND ${componentlibvar} ${basedir}/bin/${_arch}/vc12_ui)
    endif()
    list(APPEND ${componentlibvar} ${basedir}/redist/${_arch}/vc_mt)
    list(APPEND ${componentlibvar} ${basedir}/bin/${_arch}/vc_mt)
  elseif(UNIX)
    list(APPEND ${componentlibvar} ${basedir}/lib64)
    list(APPEND ${componentlibvar} ${basedir}/lib)
    if(NOT APPLE)
      foreach(v 4.8 4.7 4.4)
        list(APPEND ${componentlibvar} ${basedir}/lib/${_arch}/gcc${v})
      endforeach()
    endif()
  endif()

  set(${componentlibvar}
      ${${componentlibvar}}
      PARENT_SCOPE)
endfunction()

function(_tbb_windows_set_import_library_path target basename)
  if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC")
    if(ARGC GREATER 2)
      set(property ${basename}_${ARGV2})
      set(implib_prop IMPORTED_IMPLIB_${ARGV2})
    else()
      set(property ${basename})
      set(implib_prop IMPORTED_IMPLIB)
    endif()
    get_target_property(_value ${target} ${property})
    if(_value)
      get_filename_component(_lib_name ${_value} NAME_WE)
      get_filename_component(_vc_dir ${_value} DIRECTORY)
      get_filename_component(_arch_dir ${_vc_dir} DIRECTORY)
      get_filename_component(_tbb_root ${_value}/../../../ ABSOLUTE)
      set_target_properties(${target} PROPERTIES ${implib_prop}
                                                 ${_tbb_root}/lib/${_arch_dir}/${_vc_dir}/${_lib_name}.lib)
    endif()
  endif()
endfunction()

# ==============================================================================
# Before we go searching, check whether a TBB cmake package is available, unless the user specifically asked NOT to
# search for one.
#
# If TBB_DIR is set, this behaves as any find_package call would. If not, it looks at TBB_ROOT and TBBROOT to find TBB.
#
if(NOT TBB_NO_TBB_CMAKE)
  # If TBB_DIR is not set, look for TBBROOT and TBB_ROOT as alternatives, since these are more conventional for TBB.
  if("$ENV{TBB_DIR}" STREQUAL "")
    if(NOT "$ENV{TBB_ROOT}" STREQUAL "")
      set(ENV{TBB_DIR} $ENV{TBB_ROOT})
    elseif(NOT "$ENV{TBBROOT}" STREQUAL "")
      set(ENV{TBB_DIR} $ENV{TBBROOT})
    endif()
  endif()

  set(_TBB_FIND_PACKAGE_ARGS "")
  if(TBB_NO_SYSTEM_PATHS)
    list(APPEND _TBB_FIND_PACKAGE_ARGS NO_CMAKE_SYSTEM_PATH NO_SYSTEM_ENVIRONMENT_PATH)
  endif()

  # Additional components may be required via component dependencies. Add any missing components to the list.
  _tbb_missing_dependencies(TBB_FIND_COMPONENTS _TBB_EXTRA_FIND_COMPONENTS)
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "_TBB_EXTRA_FIND_COMPONENTS")

  # Do the same find_package call but look specifically for the CMake version. Note that args are passed in the
  # TBB_FIND_xxxxx variables, so there is no need to delegate them to this find_package call.
  find_package(TBB QUIET NO_MODULE ${_TBB_FIND_PACKAGE_ARGS})
  if(DEFINED TBB_DIR)
    mark_as_advanced(TBB_DIR)
  endif()

  # If we found a TBB cmake package, then we're done. Print out what we found. Otherwise let the rest of the module try
  # to find it.
  if(TBB_FOUND)
    # Convert component found variables to standard variables if required
    if(TBB_FIND_COMPONENTS)
      foreach(_comp IN LISTS TBB_FIND_COMPONENTS)
        if(DEFINED TBB_${_comp}_FOUND)
          continue()
        elseif(TARGET TBB::${_comp})
          set(TBB_${_comp}_FOUND TRUE)
        endif()
        string(TOUPPER ${_comp} _uppercomp)
        if(DEFINED TBB_${_uppercomp}_FOUND)
          set(TBB_${_comp}_FOUND ${TBB_${_uppercomp}_FOUND})
        endif()
      endforeach()
    endif()

    foreach(_tgt ${TBB_IMPORTED_TARGETS})
      target_compile_definitions(${_tgt} INTERFACE ${_TBB_TARGET_DEFINITIONS})
    endforeach()

    find_package_handle_standard_args(TBB HANDLE_COMPONENTS CONFIG_MODE)

    # Restore project's policies
    cmake_policy(POP)
    return()
  endif()
endif()

# ==============================================================================
# Start of main.
# ==============================================================================

# If the user sets TBB_LIBRARY_DIR, use it as the default for both configurations.
if(NOT TBB_LIBRARY_DIR_RELEASE AND TBB_LIBRARY_DIR)
  set(TBB_LIBRARY_DIR_RELEASE "${TBB_LIBRARY_DIR}")
endif()
if(NOT TBB_LIBRARY_DIR_DEBUG AND TBB_LIBRARY_DIR)
  set(TBB_LIBRARY_DIR_DEBUG "${TBB_LIBRARY_DIR}")
endif()

if(NOT DEFINED TBB_FIND_RELEASE_ONLY)
  set(TBB_FIND_RELEASE_ONLY FALSE)
endif()
if(NOT DEFINED TBB_USE_DEBUG_LIBS AND NOT TBB_FIND_RELEASE_ONLY)
  set(TBB_USE_DEBUG_LIBS TRUE)
endif()
if(NOT DEFINED TBB_USE_RELEASE_LIBS)
  set(TBB_USE_RELEASE_LIBS TRUE)
endif()

_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_FIND_RELEASE_ONLY")
_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_NO_SYSTEM_PATHS")

# ------------------------------------------------------------------------------

# Collect environment variable inputs as hints.  Do not consider changes.
foreach(v TBBROOT TBB_ROOT TBB_INCLUDEDIR TBB_LIBRARYDIR)
  set(_env $ENV{${v}})
  if(_env)
    file(TO_CMAKE_PATH "${_env}" _ENV_${v})
  else()
    set(_ENV_${v} "")
  endif()
endforeach()
if(NOT _ENV_TBB_ROOT AND _ENV_TBBROOT)
  set(_ENV_TBB_ROOT "${_ENV_TBBROOT}")
endif()

# Collect inputs and cached results. Detect changes since the last run.
if(NOT TBB_ROOT AND TBBROOT)
  set(TBB_ROOT "${TBBROOT}")
endif()
set(_TBB_VARS_DIR TBB_ROOT TBB_NO_SYSTEM_PATHS)

_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_ROOT")
_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_ROOT" ENVIRONMENT)
_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_INCLUDEDIR")
_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_INCLUDEDIR" ENVIRONMENT)
_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_LIBRARYDIR")
_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_LIBRARYDIR" ENVIRONMENT)

# ==============================================================================
# Search for TBB include DIR

set(_TBB_PATH_SUFFIXES include include/oneapi include/tbb)
set(_TBB_VARS_INC TBB_INCLUDEDIR TBB_INCLUDE_DIR)
_tbb_change_detect(_TBB_CHANGE_INCDIR ${_TBB_VARS_DIR} ${_TBB_VARS_INC})
# Clear TBB_INCLUDE_DIR if it did not change but other input affecting the location did.  We will find a new one based
# on the new inputs.
if(_TBB_CHANGE_INCDIR AND NOT _TBB_INCLUDE_DIR_CHANGED)
  unset(TBB_INCLUDE_DIR CACHE)
endif()

if(NOT TBB_INCLUDE_DIR)
  set(_TBB_INCLUDE_SEARCH_DIRS "")
  if(TBB_INCLUDEDIR)
    list(APPEND _TBB_INCLUDE_SEARCH_DIRS ${TBB_INCLUDEDIR})
  elseif(_ENV_TBB_INCLUDEDIR)
    list(APPEND _TBB_INCLUDE_SEARCH_DIRS ${_ENV_TBB_INCLUDEDIR})
  endif()

  if(TBB_ROOT)
    list(APPEND _TBB_INCLUDE_SEARCH_DIRS ${TBB_ROOT})
  elseif(_ENV_TBB_ROOT)
    list(APPEND _TBB_INCLUDE_SEARCH_DIRS ${_ENV_TBB_ROOT})
  endif()

  if(TBB_NO_SYSTEM_PATHS)
    list(APPEND _TBB_INCLUDE_SEARCH_DIRS NO_CMAKE_SYSTEM_PATH NO_SYSTEM_ENVIRONMENT_PATH)
  else()
    list(
      APPEND
      _TBB_INCLUDE_SEARCH_DIRS
      PATHS
      /opt/intel/tbb # Linux
      /usr
      /usr/local/
      /usr/local/homebrew # Mac OS X
      /opt
      /opt/local
      /opt/local/var/macports/software # Mac OS X.
      /sw/local
      C:/TBB)
  endif()

  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "_TBB_INCLUDE_SEARCH_DIRS")
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "_TBB_PATH_SUFFIXES")

  # Look for a standard TBB header file.
  find_path(
    TBB_INCLUDE_DIR
    NAMES tbb.h
    HINTS ${_TBB_INCLUDE_SEARCH_DIRS}
    PATH_SUFFIXES ${_TBB_PATH_SUFFIXES})
endif()

# ------------------------------------------------------------------------
# Extract version information from version.hpp
# ------------------------------------------------------------------------

if(TBB_INCLUDE_DIR)
  # NB: tbb_stddef.h for TBB prior to 2021.01
  find_file(
    TBB_VERSION_H
    NAMES version.h tbb_stddef.h
    HINTS ${TBB_INCLUDE_DIR}
    PATH_SUFFIXES tbb REQUIRED
    NO_DEFAULT_PATH)
  mark_as_advanced(TBB_VERSION_H)

  _tbb_debug_print("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}"
                   "location of version.h/tbb_stddef.h: ${TBB_VERSION_H}")

  file(READ ${TBB_VERSION_H} _TBB_version_file)
  string(REGEX REPLACE ".*#define TBB_VERSION_MAJOR ([0-9]+).*" "\\1" TBB_VERSION_MAJOR "${_TBB_version_file}")
  string(REGEX REPLACE ".*#define TBB_VERSION_MINOR ([0-9]+).*" "\\1" TBB_VERSION_MINOR "${_TBB_version_file}")
  string(REGEX REPLACE ".*#define TBB_INTERFACE_VERSION ([0-9]+).*" "\\1" TBB_INTERFACE_VERSION "${_TBB_version_file}")
  string(REGEX REPLACE ".*#define TBB_COMPATIBLE_INTERFACE_VERSION ([0-9]+).*" "\\1" TBB_COMPATIBLE_INTERFACE_VERSION
                       "${_TBB_version_file}")

  math(EXPR TBB_INTERFACE_VERSION_MAJOR "${TBB_INTERFACE_VERSION} / 1000")
  math(EXPR TBB_INTERFACE_VERSION_MINOR "${TBB_INTERFACE_VERSION} % 1000 / 10")

  if(_TBB_version_file MATCHES "#define TBB_VERSION_PATCH ([0-9]+)")
    set(TBB_VERSION_PATCH ${CMAKE_MATCH_1})
  else()
    set(TBB_VERSION_PATCH 0)
  endif()

  if(_TBB_version_file MATCHES "#define __TBB_BINARY_VERSION ([0-9]+)")
    set(TBB_COMPATIBLE_INTERFACE_VERSION ${CMAKE_MATCH_1})
    set(TBB_BINARY_VERSION ${CMAKE_MATCH_1})
  elseif(_TBB_version_file MATCHES "#define TBB_COMPATIBLE_INTERFACE_VERSION ([0-9]+)") # legacy
    set(TBB_COMPATIBLE_INTERFACE_VERSION ${CMAKE_MATCH_1})
    set(TBB_BINARY_VERSION ${CMAKE_MATCH_1})
  endif()

  set(TBB_VERSION "${TBB_VERSION_MAJOR}.${TBB_VERSION_MINOR}.${TBB_VERSION_PATCH}")

  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_VERSION")
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_VERSION_MAJOR")
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_VERSION_MINOR")
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_VERSION_PATCH")
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_INTERFACE_VERSION")
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_INTERFACE_VERSION_MAJOR")
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_INTERFACE_VERSION_MINOR")
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_BINARY_VERSION")
endif()

# ==============================================================================
# Default initialization of components to search for

if(NOT TBB_FIND_COMPONENTS)
  if(TBB_VERSION VERSION_LESS 2020.0)
    set(TBB_FIND_COMPONENTS tbbmalloc_proxy tbbmalloc tbb)
  elseif(TBB_VERSION VERSION_LESS 2021.0)
    set(TBB_FIND_COMPONENTS tbbbind tbbmalloc_proxy tbbmalloc tbb)
  else()
    set(TBB_FIND_COMPONENTS tbbbind tbbbind_2_0 tbbbind_2_4 tbbmalloc_proxy tbbmalloc tbb)
  endif()
endif()

# ==============================================================================
# Begin finding TBB libraries

set(_TBB_VARS_LIB "")
foreach(c DEBUG RELEASE)
  set(_TBB_VARS_LIB_${c} TBB_LIBRARYDIR TBB_LIBRARY_DIR_${c})
  list(APPEND _TBB_VARS_LIB ${_TBB_VARS_LIB_${c}})
  _tbb_change_detect(_TBB_CHANGE_LIBDIR_${c} ${_TBB_VARS_DIR} ${_TBB_VARS_LIB_${c}} TBB_INCLUDE_DIR)
  # Clear TBB_LIBRARY_DIR_${c} if it did not change but other input affecting the location did.  We will find a new one
  # based on the new inputs.
  if(_TBB_CHANGE_LIBDIR_${c} AND NOT _TBB_LIBRARY_DIR_${c}_CHANGED)
    unset(TBB_LIBRARY_DIR_${c} CACHE)
  endif()

  # If TBB_LIBRARY_DIR_[RELEASE,DEBUG] is set, prefer its value.
  if(TBB_LIBRARY_DIR_${c})
    set(_TBB_LIBRARY_SEARCH_DIRS_${c} ${TBB_LIBRARY_DIR_${c}} NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
  else()
    set(_TBB_LIBRARY_SEARCH_DIRS_${c} "")
    if(TBB_LIBRARYDIR)
      list(APPEND _TBB_LIBRARY_SEARCH_DIRS_${c} ${TBB_LIBRARYDIR})
    elseif(_ENV_TBB_LIBRARYDIR)
      list(APPEND _TBB_LIBRARY_SEARCH_DIRS_${c} ${_ENV_TBB_LIBRARYDIR})
    endif()

    if(TBB_ROOT)
      list(APPEND _TBB_LIBRARY_SEARCH_DIRS_${c} ${TBB_ROOT})
      _tbb_update_library_search_dirs_with_prebuilt_paths(_TBB_LIBRARY_SEARCH_DIRS_${c} "${TBB_ROOT}")
    elseif(_ENV_TBB_ROOT)
      list(APPEND _TBB_LIBRARY_SEARCH_DIRS_${c} ${_ENV_TBB_ROOT})
      _tbb_update_library_search_dirs_with_prebuilt_paths(_TBB_LIBRARY_SEARCH_DIRS_${c} "${_ENV_TBB_ROOT}")
    endif()

    list(APPEND _TBB_LIBRARY_SEARCH_DIRS_${c} ${TBB_INCLUDE_DIR} ${TBB_INCLUDE_DIR}/../..)
    _tbb_update_library_search_dirs_with_prebuilt_paths(_TBB_LIBRARY_SEARCH_DIRS_${c} "${TBB_INCLUDE_DIR}/../..")
    _tbb_update_library_search_dirs_with_prebuilt_paths(_TBB_LIBRARY_SEARCH_DIRS_${c} "${TBB_INCLUDE_DIR}")

    if(TBB_NO_SYSTEM_PATHS)
      list(APPEND _TBB_LIBRARY_SEARCH_DIRS_${c} NO_CMAKE_SYSTEM_PATH NO_SYSTEM_ENVIRONMENT_PATH)
    else()
      list(APPEND _TBB_LIBRARY_SEARCH_DIRS_${c} PATHS C:/TBB /sw/local)
      _tbb_update_library_search_dirs_with_prebuilt_paths(_TBB_LIBRARY_SEARCH_DIRS_${c} "C:/TBB")
    endif()
  endif()
endforeach()

_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "_TBB_LIBRARY_SEARCH_DIRS_RELEASE")
_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "_TBB_LIBRARY_SEARCH_DIRS_DEBUG")

# Properly search for shared libraries on Windows with Visual Studio
if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC")
  set(_TBB_ORIG_CMAKE_FIND_LIBRARY_SUFFIXES ${CMAKE_FIND_LIBRARY_SUFFIXES})
  set(CMAKE_FIND_LIBRARY_SUFFIXES .dll)
endif()

# Additional components may be required via component dependencies. Add any missing components to the list.
_tbb_missing_dependencies(TBB_FIND_COMPONENTS _TBB_EXTRA_FIND_COMPONENTS)
_tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "_TBB_EXTRA_FIND_COMPONENTS")

# If the user changed any of our control inputs flush previous results.
if(_TBB_CHANGE_LIBDIR_DEBUG OR _TBB_CHANGE_LIBDIR_RELEASE)
  foreach(COMPONENT ${_TBB_COMPONENTS_SEARCHED})
    string(TOUPPER ${COMPONENT} UPPERCOMPONENT)
    foreach(c DEBUG RELEASE)
      set(_var TBB_${UPPERCOMPONENT}_LIBRARY_${c})
      unset(${_var} CACHE)
      set(${_var} "${_var}-NOTFOUND")
    endforeach()
  endforeach()
  set(_TBB_COMPONENTS_SEARCHED "")
endif()

foreach(COMPONENT ${TBB_FIND_COMPONENTS})
  string(TOUPPER ${COMPONENT} UPPERCOMPONENT)

  set(_TBB_docstring_release "TBB ${COMPONENT} library (release)")
  set(_TBB_docstring_debug "TBB ${COMPONENT} library (debug)")

  #
  # Find RELEASE libraries
  #
  if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC"
     AND TBB_VERSION VERSION_GREATER_EQUAL 2021.0
     AND COMPONENT STREQUAL tbb)
    set(_TBB_RELEASE_NAMES ${COMPONENT}${TBB_BINARY_VERSION})
  else()
    set(_TBB_RELEASE_NAMES ${COMPONENT})
  endif()

  _tbb_debug_print("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}"
                   "Searching for ${UPPERCOMPONENT}_LIBRARY_RELEASE: ${_TBB_RELEASE_NAMES}")

  # if TBB_LIBRARY_DIR_RELEASE is not defined, but TBB_LIBRARY_DIR_DEBUG is, look there first for RELEASE libs
  if(NOT TBB_LIBRARY_DIR_RELEASE AND TBB_LIBRARY_DIR_DEBUG)
    list(INSERT _TBB_LIBRARY_SEARCH_DIRS_RELEASE 0 ${TBB_LIBRARY_DIR_DEBUG})
  endif()

  if(TBB_USE_RELEASE_LIBS)
    _tbb_find_library(
      TBB_${UPPERCOMPONENT}_LIBRARY_RELEASE
      RELEASE
      NAMES
      ${_TBB_RELEASE_NAMES}
      HINTS
      ${_TBB_LIBRARY_SEARCH_DIRS_RELEASE}
      NAMES_PER_DIR
      DOC
      "${_TBB_docstring_release}")
  endif()
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}"
                       "TBB_${UPPERCOMPONENT}_LIBRARY_RELEASE")

  #
  # Find DEBUG libraries
  #
  if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC"
     AND TBB_VERSION VERSION_GREATER_EQUAL 2021.0
     AND COMPONENT STREQUAL tbb)
    set(_TBB_DEBUG_NAMES ${COMPONENT}${TBB_BINARY_VERSION}_debug)
  else()
    set(_TBB_DEBUG_NAMES ${COMPONENT}_debug)
  endif()

  _tbb_debug_print("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}"
                   "Searching for ${UPPERCOMPONENT}_LIBRARY_DEBUG: ${_TBB_DEBUG_NAMES}")

  # if TBB_LIBRARY_DIR_DEBUG is not defined, but TBB_LIBRARY_DIR_RELEASE is, look there first for DEBUG libs
  if(NOT TBB_LIBRARY_DIR_DEBUG AND TBB_LIBRARY_DIR_RELEASE)
    list(INSERT _TBB_LIBRARY_SEARCH_DIRS_DEBUG 0 ${TBB_LIBRARY_DIR_RELEASE})
  endif()

  if(TBB_USE_DEBUG_LIBS)
    _tbb_find_library(
      TBB_${UPPERCOMPONENT}_LIBRARY_DEBUG
      DEBUG
      NAMES
      ${_TBB_DEBUG_NAMES}
      HINTS
      ${_TBB_LIBRARY_SEARCH_DIRS_DEBUG}
      NAMES_PER_DIR
      DOC
      "${_TBB_docstring_debug}")
  endif()

  _tbb_adjust_lib_vars(${UPPERCOMPONENT})
endforeach()

# Restore the original find library ordering
if(_TBB_ORIG_CMAKE_FIND_LIBRARY_SUFFIXES)
  set(CMAKE_FIND_LIBRARY_SUFFIXES ${_TBB_ORIG_CMAKE_FIND_LIBRARY_SUFFIXES})
endif()

# ------------------------------------------------------------------------
# End finding TBB libraries

set(TBB_INCLUDE_DIRS ${TBB_INCLUDE_DIR})
set(TBB_LIBRARY_DIRS)
if(TBB_LIBRARY_DIR_RELEASE)
  list(APPEND TBB_LIBRARY_DIRS ${TBB_LIBRARY_DIR_RELEASE})
endif()
if(TBB_LIBRARY_DIR_DEBUG)
  list(APPEND TBB_LIBRARY_DIRS ${TBB_LIBRARY_DIR_DEBUG})
endif()
if(TBB_LIBRARY_DIRS)
  list(REMOVE_DUPLICATES TBB_LIBRARY_DIRS)
endif()

# ==============================================================================
# Call FPHSA helper, see https://cmake.org/cmake/help/latest/module/FindPackageHandleStandardArgs.html

# Define aliases as needed by the component handler in the FPHSA helper below
foreach(_comp IN LISTS TBB_FIND_COMPONENTS)
  string(TOUPPER ${_comp} _uppercomp)
  if(DEFINED TBB_${_uppercomp}_FOUND)
    set(TBB_${_comp}_FOUND ${TBB_${_uppercomp}_FOUND})
  endif()
  _tbb_debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "TBB_${_comp}_FOUND")
endforeach()

find_package_handle_standard_args(
  TBB
  REQUIRED_VARS TBB_INCLUDE_DIR
  VERSION_VAR TBB_VERSION
  HANDLE_COMPONENTS)

if(NOT TBB_FOUND)
  # TBB headers were not found so no components were found.
  foreach(COMPONENT ${TBB_FIND_COMPONENTS})
    string(TOUPPER ${COMPONENT} UPPERCOMPONENT)
    set(TBB_${UPPERCOMPONENT}_FOUND FALSE)
  endforeach()
endif()

# ==============================================================================
# Add imported targets

if(TBB_FOUND)
  foreach(_comp ${TBB_FIND_COMPONENTS})
    if(NOT TARGET TBB::${_comp})
      string(TOUPPER ${_comp} _uppercomp)
      if(TBB_${_uppercomp}_FOUND)
        add_library(TBB::${_comp} SHARED IMPORTED)
        target_compile_definitions(TBB::${_comp} INTERFACE ${_TBB_TARGET_DEFINITIONS})

        if(TBB_INCLUDE_DIRS)
          target_include_directories(TBB::${_comp} INTERFACE "${TBB_INCLUDE_DIRS}")
        endif()
        if(EXISTS "${TBB_${_uppercomp}_LIBRARY}")
          set_target_properties(TBB::${_comp} PROPERTIES IMPORTED_LINK_INTERFACE_LANGUAGES "CXX"
                                                         IMPORTED_LOCATION "${TBB_${_uppercomp}_LIBRARY}")
          _tbb_windows_set_import_library_path(TBB::${_comp} IMPORTED_LOCATION)
        endif()
        if(EXISTS "${TBB_${_uppercomp}_LIBRARY_RELEASE}")
          set_property(
            TARGET TBB::${_comp}
            APPEND
            PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
          set_target_properties(
            TBB::${_comp} PROPERTIES IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
                                     IMPORTED_LOCATION_RELEASE "${TBB_${_uppercomp}_LIBRARY_RELEASE}")
          _tbb_windows_set_import_library_path(TBB::${_comp} IMPORTED_LOCATION RELEASE)
        endif()
        if(EXISTS "${TBB_${_uppercomp}_LIBRARY_DEBUG}")
          set_property(
            TARGET TBB::${_comp}
            APPEND
            PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
          set_target_properties(TBB::${_comp} PROPERTIES IMPORTED_LINK_INTERFACE_LANGUAGES_DEBUG "CXX"
                                                         IMPORTED_LOCATION_DEBUG "${TBB_${_uppercomp}_LIBRARY_DEBUG}")
          _tbb_windows_set_import_library_path(TBB::${_comp} IMPORTED_LOCATION DEBUG)
        endif()

        if(_TBB_${_uppercomp}_DEPENDENCIES)
          unset(_TBB_${_uppercomp}_TARGET_DEPENDENCIES)
          foreach(dep ${_TBB_${_uppercomp}_DEPENDENCIES})
            list(APPEND _TBB_${_uppercomp}_TARGET_DEPENDENCIES TBB::${dep})
          endforeach()
          target_link_libraries(TBB::${_comp} INTERFACE "${_TBB_${_uppercomp}_TARGET_DEPENDENCIES}")
        endif()
      endif()
    endif()
    list(APPEND TBB_IMPORTED_TARGETS TBB::${_comp})
  endforeach()
endif()
list(REMOVE_DUPLICATES TBB_IMPORTED_TARGETS)

# ==============================================================================
# Finalize

# Report TBB_LIBRARIES
set(TBB_LIBRARIES "")
foreach(_comp IN LISTS TBB_FIND_COMPONENTS)
  string(TOUPPER ${_comp} _uppercomp)
  if(TBB_${_uppercomp}_FOUND)
    list(APPEND TBB_LIBRARIES ${TBB_${_uppercomp}_LIBRARY})
  endif()
endforeach()

# Configure display of cache entries in GUI.
foreach(v TBBROOT TBB_ROOT ${_TBB_VARS_INC} ${_TBB_VARS_LIB})
  get_property(
    _type
    CACHE ${v}
    PROPERTY TYPE)
  if(_type)
    set_property(CACHE ${v} PROPERTY ADVANCED 1)
    if("x${_type}" STREQUAL "xUNINITIALIZED")
      set_property(CACHE ${v} PROPERTY TYPE PATH)
    endif()
  endif()
endforeach()

# Record last used values of input variables so we can detect on the next run if the user changed them.
foreach(v ${_TBB_VARS_INC} ${_TBB_VARS_LIB} ${_TBB_VARS_DIR} ${_TBB_VARS_NAME})
  if(DEFINED ${v})
    set(_${v}_LAST
        "${${v}}"
        CACHE INTERNAL "Last used ${v} value.")
  else()
    unset(_${v}_LAST CACHE)
  endif()
endforeach()

# Maintain a persistent list of components requested anywhere since the last flush.
set(_TBB_COMPONENTS_SEARCHED "${_TBB_COMPONENTS_SEARCHED}")
list(APPEND _TBB_COMPONENTS_SEARCHED ${TBB_FIND_COMPONENTS})
list(REMOVE_DUPLICATES _TBB_COMPONENTS_SEARCHED)
list(SORT _TBB_COMPONENTS_SEARCHED)
set(_TBB_COMPONENTS_SEARCHED
    "${_TBB_COMPONENTS_SEARCHED}"
    CACHE INTERNAL "Components requested for this build tree.")

# Restore project's policies
cmake_policy(POP)

# ==============================================================================
