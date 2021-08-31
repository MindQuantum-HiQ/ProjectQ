.. _compilation:


Compilation and building
========================

Normally, you can compile HiQ-ProjectQ simply by launching one of these two commands:

.. code-block:: bash

   python -m pip install --user projectq

or

.. code-block:: bash

   python -m setup.py install

However, it is also possible to compile HiQ-ProjectQ using CMake directly which can be useful if you need to cross-compile for another architecture for example. The next sections are dedicated to showing you how to manually compile HiQ-ProjectQ using CMake.

Compiler intrinsics
~~~~~~~~~~~~~~~~~~~

It is possible to disable native compiler intrinsics or even completely disable the use of compiler intrinsics instructions when building HiQ-ProjectQ. You can either pass ``--no-arch-native`` flag to ``build_ext``

You will find below some examples of using those options to customize your build of HiQ-ProjectQ.

.. code-block:: bash

   python3 setup.py install build_ext --no-arch-native

   python3 -m pip install projectq --global-option=build_ext \
                --global-option=--no-arch-native


.. _cmake:

CMake build
~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

Getting started
---------------

In order to manually compile HiQ-ProjectQ using CMake, you need to create a build directory and then run CMake from within. This can be accomplished as follows:

.. code-block:: bash

   mkdir build
   cd build
   cmake ..

You can also specify relevant environment variable in order to change the compiler for example:

.. code-block:: bash

   mkdir build
   cd build
   CC=clang CXX=clang++ cmake ..


Python module build location
----------------------------

By default, the compiled C/C++ Python packages will be created within the CMake build directory. You can however control where those are built by using the ``_XXX_OUTPUT_DIR`` CMake variables (this is usually done automatically by ``setup.py``). Simply specify them on the command line or define them in the CMake GUI to tell CMake where you want your compiled Python packages to end up in.

.. code-block:: bash

   cmake -D_CPPSIM_OUTPUT_DIR=/some/path ..

In the above example, the ``_cppsim`` C++ Python package will be built and then copied to the ``/some/path`` directory.

If you plan on developping for HiQ-ProjectQ and you want to have an *in-place* build, you can also set the ``IN_PLACE_BUILD`` CMake variable to ``ON`` (e.g. ``cmake -DIN_PLACE_BUILD=ON ..``). CMake will then automatically set the proper variables to ensure that the compiled shared libraries end up in the correct directory in your checked out version of HiQ-ProjectQ.

.. code-block:: bash

   cmake -DIN_PLACE_BUILD=ON ..


CMake options
-------------

Here is an exhaustive list of available CMake options that you may set in order to influence the configuration, generation and build processes.

+-------------------------------------+-----------------+--------------------------------------------------+
| CMake options                       | Default value   | Description                                      |
+=====================================+=================+==================================================+
| ``BUILD_TESTING``                   | OFF             | Build the C++ test suite if ON                   |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``CUDA_ALLOW_UNSUPPORTED_COMPILER`` | OFF             | | Allow the use of an unsupported CUDA           |
|                                     |                 | | compiler (``-allow-unsupported-compiler``)     |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``CUDA_STATIC``                     | ON              | | Use static compilation for Nvidia CUDA         |
|                                     |                 | | libraries by default (also applies to nvc++)   |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``ENABLE_CUDA``                     | ON              | | Enable the compilation of CUDA                 |
|                                     |                 | | accelerated code.                              |
|                                     |                 | | Automatically set to OFF if no suitable        |
|                                     |                 | | CUDA compiler can be found.                    |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``ENABLE_DPCXX``                    | OFF             | | Enable building of DPC++ libraries             |
|                                     |                 | | (currently no DPC++ libraries are              |
|                                     |                 | | implemented)                                   |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``ENABLE_PROFILING``                | OFF             | Enable compilation with profiling flags.         |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``ENABLE_RUNPATH``                  | OFF             | Prefer RUNPATH over RPATH when linking           |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``ENABLE_STACK_PROTECTION``         | OFF             | | Enable the use of -fstack-protector during     |
|                                     |                 | | compilation                                    |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``IN_PLACE_BUILD``                  | OFF             | | Build the shared library directly in the       |
|                                     |                 | | directory hierarchy (mainly used for editable  |
|                                     |                 | | Python installations)                          |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``LINKER_DTAGS``                    | ON              | | Use ``--enable-new-dtags/--disable-new-dtags`` |
|                                     |                 | | during linking                                 |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``LINKER_NOEXECSTACK``              | OFF             | Use -z,noexecstack during linking                |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``LINKER_RELRO``                    | OFF             | Use -z,relro during linking for certain targets  |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``LINKER_RPATH``                    | OFF             | Enable the use of RPATH/RUNPATH during linking   |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``LINKER_STRIP_ALL``                | | OFF (Debug)   | Use --strip-all during linking if ON             |
|                                     | | ON  (Release) |                                                  |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``NVCXX_FAST_SEARCH``               | ON              | | Use a fast algorithm to test for the validity  |
|                                     |                 | | of nvc++ (set to OFF if detection fails)       |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``PYTHON_VIRTUALENV_COMPAT``        | | ON (MacOS)    | | Make CMake search for Python Framework         |
|                                     | | OFF (else)    | | *after* any available unix-style package.      |
|                                     |                 | | Can be useful in case of virtual environments. |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``USE_INTRINSICS``                  | ON              | | Enable/disable the use of compiler             |
|                                     |                 | | intrinsics                                     |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``USE_NATIVE_INTRINSICS``           | OFF             | | Use -march=native (or equivalent compiler      |
|                                     |                 | | flag)                                          |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``USE_OPENMP``                      | ON (see desc.)  | | Use OpenMP instead parallel STL.               |
|                                     |                 | | By default enabled except for those            |
|                                     |                 | | compilers:                                     |
|                                     |                 | - MSVC                                           |
|                                     |                 | - GNU GCC                                        |
|                                     |                 | - Intel                                          |
|                                     |                 | - IntelLLVM                                      |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``USE_PARALLEL_STL``                | OFF (see desc.) | | Use parallel STL algorithms                    |
|                                     |                 | | By default enabled except for those            |
|                                     |                 | | compilers:                                     |
|                                     |                 | - MSVC                                           |
|                                     |                 | - GNU GCC                                        |
|                                     |                 | - Intel                                          |
|                                     |                 | - IntelLLVM                                      |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``USE_VERBOSE_MAKEFILE``            | ON              | Use verbose Makefiles                            |
+-------------------------------------+-----------------+--------------------------------------------------+
+-------------------------------------+-----------------+--------------------------------------------------+
| ``BUILD_SHARED_LIBS``               | OFF             | (internal) Build shared libaries by default      |
+-------------------------------------+-----------------+--------------------------------------------------+
| ``IS_PYTHON_BUILD``                 | OFF             | (internal) Used by ``setup.py``                  |
+-------------------------------------+-----------------+--------------------------------------------------+

CMake variables
_______________

A list of CMake variables that may be defined to further customize the configuration/generation/build process.

+-----------------------------------------+------------+--------------------------------------------------+
| CMake variable                          | Value type | Description                                      |
+=========================================+============+==================================================+
| ``HIQ_SKIP_SYSTEM_PROCESSOR_DETECTION`` | Boolean    | | Disable processor architecture detection       |
|                                         |            | | If set, you need to define ``X86_64``, ``X86`` |
|                                         |            | | or ``AARCH64`` manually                        |
+-----------------------------------------+------------+--------------------------------------------------+
| ``NVCXX_FAST_SEARCH_FLAGS``             | String     | | Default flags to use when trying to identity   |
|                                         |            | | the Nvidia nvc++ compiler                      |
|                                         |            | | Defaults to: -stdpar -cuda -gpu=cc60           |
+-----------------------------------------+------------+--------------------------------------------------+

Environment variables
---------------------

You may also control the compiler/linker options used by CMake to build HiQ-ProjectQ by specifying some environment variables. Here is a non-exhaustive list of environment variables you may use:

+-------------------------------------+--------------------------------------------------+
| Environment variable                | Description                                      |
+=====================================+==================================================+
| ``CXX``                             | Path to the C++ compiler                         |
+-------------------------------------+--------------------------------------------------+
| ``CXXFLAGS``                        | Extra flags for the C++ compiler                 |
+-------------------------------------+--------------------------------------------------+
| ``CUDAFLAGS``                       | Extra flags for the CUDA compiler                |
+-------------------------------------+--------------------------------------------------+
| ``NVCXX``                           | Path to the Nvidia nvc++ compiler                |
+-------------------------------------+--------------------------------------------------+
| ``NVCXX_PATH``                      | | Root path to look for the Nvidia nvc++         |
|                                     | | (will try $NVCXX_PATH/bin)                     |
+-------------------------------------+--------------------------------------------------+
| ``NVCXXFLAGS``                      | Extra flags for the Nvidia nvc++ compiler        |
+-------------------------------------+--------------------------------------------------+
| ``NVCXX_LDFLAGS``                   | Extra linker flags for the Nvidia nvc++ compiler |
+-------------------------------------+--------------------------------------------------+
| ``DPCXX``                           | Path to the DPC++ compiler                       |
+-------------------------------------+--------------------------------------------------+
| ``DPCXXFLAGS``                      | Extra flags for the DPC++ compiler               |
+-------------------------------------+--------------------------------------------------+

CMake variables
---------------

Some compiler options can also be specified as CMake variables:

+-------------------------------------+--------------------------------------------------+
| Environment variable                | Description                                      |
+=====================================+==================================================+
| ``CMAKE_CXX_COMPILER``              | Path to the C++ compiler                         |
+-------------------------------------+--------------------------------------------------+
| ``CMAKE_CUDA_COMPILER``             | Path to the C++ compiler                         |
+-------------------------------------+--------------------------------------------------+
| ``CMAKE_NVCXX_COMPILER``            | Path to the Nvidia nvc++ compiler                |
+-------------------------------------+--------------------------------------------------+
| ``CMAKE_DPCXX_COMPILER``            | Path to the DPC++ compiler                       |
+-------------------------------------+--------------------------------------------------+


Cross-compilation
-----------------

If you are cross-compiling HiQ-ProjectQ for a different target architecture, you can do so simply by providing a CMake toolchain file. Some examples are provided in the ``toolchain`` folder. Simply copy an example, edit it to match your configuration and then tell CMake about it when configuring and you should be good to go.

.. code-block:: bash

   cp toolchain/aarch64-clang.cmake.example ../toolchain/aarch64-clang.cmake
   # Edit toolchain/aarch64-clang.cmake
   mkdir build
   cd build
   cmake -DCMAKE_TOOLCHAIN_FILE=../toolchain/aarch64-clang.cmake ..
