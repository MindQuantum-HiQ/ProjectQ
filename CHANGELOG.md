# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

-   HiQ-ProjectQ is now a namespace package.
    This should provide better oportunities for customizations in the future without the need to merge all changes into
    ProjectQ.
-   Support for parameterized quantum gates (e.g. Rx, Ry, Rz, QubitOperator, TimeEvolution, etc.)
-   Support for exporting HiQ-ProjectQ quantum circuits as JSON encoded strings
-   Support for reading/writing quantum circuits using OpenQASM
-   New implementation of the C++ simulator backend based on modern C++ (C++17)
-   Preliminary support for GPU computations within the C++ simulator backend
-   Add fSim gate (and related parametric version)

### Updated

-   Added option to DrawerMatplotlib backend to enable/disable LaTeX output of symbols

### Repository

-   Added some templates when creating GitHub issues


## [0.7.0] - 2021-08-31

### Added

-   HiQ-ProjectQ now based on ProjectQ v0.7.0
