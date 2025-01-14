#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# projectq documentation build configuration file, created by
# sphinx-quickstart on Tue Nov 29 11:51:46 2016.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

"""Configuration file for generating the documentation for ProjectQ."""

# pylint: disable=invalid-name

import functools
import inspect
import os
import sys

try:
    import importlib
    import importlib.metadata as importlib_metadata  # pragma: no cover (PY38+)
except ImportError:
    import importlib_metadata  # pragma: no cover (<PY38)


sys.path.insert(0, os.path.realpath('..'))  # for projectq
sys.path.append(os.path.realpath('.'))  # for package_description

# ==============================================================================

# Import helper module manually without resorting to importing the full projectq
spec = importlib.util.spec_from_file_location(
    'projectq.libs',
    os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'projectq', 'libs', 'utils', '__init__.py')),
)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)


# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.autosummary',
    'sphinx.ext.linkcode',
]

autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'ProjectQ'
copyright = '2017-2021, ProjectQ'  # pylint: disable=redefined-builtin
author = 'ProjectQ'

release = importlib_metadata.version('hiq-projectq')  # Full version string
version = '.'.join(release.split('.')[:3])  # X.Y.Z

# The language for content autogenerated by Sphinx. Refer to documentation for a list of supported languages.
language = None

# List of patterns, relative to source directory, that match files and directories to ignore when looking for source
# files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README.rst']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Output file base name for HTML help builder.
htmlhelp_basename = 'projectqdoc'

# -- Options for LaTeX output ---------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples (source start file, target name, title, author,
# documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'projectq.tex', 'projectq Documentation', 'a', 'manual'),
]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples (source start file, name, description, authors, manual section).
man_pages = [(master_doc, 'projectq', 'projectq Documentation', [author], 1)]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples (source start file, target name, title, author, dir
# menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        'projectq',
        'projectq Documentation',
        author,
        'projectq',
        'One line description of project.',
        'Miscellaneous',
    ),
]

# -- Options for sphinx.ext.linkcode --------------------------------------


def recursive_getattr(obj, attr, *args):
    """Recursively get the attributes of a Python object."""

    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split('.'))


def linkcode_resolve(domain, info):
    """Change URLs in documentation on the fly."""
    # Copyright 2018 ProjectQ (www.projectq.ch), all rights reserved.
    on_rtd = os.environ.get('READTHEDOCS') == 'True'
    github_url = "https://github.com/Huawei-HiQ/ProjectQ/tree/"
    github_tag = 'v' + version
    if on_rtd:
        rtd_tag = os.environ.get('READTHEDOCS_VERSION')
        if rtd_tag == 'latest':
            github_tag = 'develop'
        elif rtd_tag == 'stable':
            github_tag = 'master'
        else:
            # RTD changes "/" in branch name to "-"
            # As we use branches like fix/cool-feature, this is a
            # problem -> as a fix we require that all branch names
            # which contain a '-' must first contain one '/':
            if list(rtd_tag).count('-'):
                github_tag = list(rtd_tag)
                github_tag[github_tag.index('-')] = '/'
                github_tag = ''.join(github_tag)
            else:
                github_tag = rtd_tag

    if domain != 'py':
        return None
    try:
        module = importlib.import_module(info['module'])
        obj = recursive_getattr(module, info['fullname'])
    except (AttributeError, ValueError):
        # AttributeError:
        # Object might be a non-static attribute of a class, e.g., self.num_qubits, which would only exist after init
        # was called.
        # For the moment we don't need a link for that as there is a link for the class already
        #
        # ValueError:
        # No key with 'module' exist within info or it is empty
        return None
    try:
        filepath = inspect.getsourcefile(obj)
        line_number = inspect.getsourcelines(obj)[1]
    except (TypeError, OSError):
        # obj might be a property or a static class variable, e.g.,
        # loop_tag_id in which case obj is an int and inspect will fail
        try:
            # load obj one hierarchy higher (either class or module)
            new_higher_name = info['fullname'].split('.')
            module = importlib.import_module(info['module'])
            if len(new_higher_name) > 1:
                obj = module
            else:
                obj = recursive_getattr(module, '.' + '.'.join(new_higher_name[:-1]))

            filepath = inspect.getsourcefile(obj)
            line_number = inspect.getsourcelines(obj)[1]
        except AttributeError:
            return None

    # Only require relative path projectq/relative_path
    projectq_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..')) + os.path.sep
    idx = len(projectq_path)
    relative_path = filepath[idx:]

    url = github_url + github_tag + "/" + relative_path + "#L" + str(line_number)
    return url


# ------------------------------------------------------------------------------

desc = importlib.import_module('package_description')
PackageDescription = desc.PackageDescription

# ------------------------------------------------------------------------------
# Define the description of ProjectQ packages and their submodules below.
#
# In order for the automatic package recognition to work properly, it is
# important that PackageDescription of sub-packages appear earlier in the list
# than their parent package (see for example libs.math compared to libs).
#
# It is also possible to customize the presentation of submodules (see for
# example the setups and setups.decompositions) or even to have private
# sub-modules listed in the documentation page of a parent packages (see for
# example the cengines package)

descriptions = [
    PackageDescription('backends'),
    PackageDescription(
        'cengines',
        desc='''
The ProjectQ compiler engines package.
''',
    ),
    PackageDescription(
        'libs.math',
        desc='''
A tiny math library which will be extended thoughout the next weeks. Right now, it only contains the math functions
necessary to run Beauregard's implementation of Shor's algorithm.
''',
    ),
    PackageDescription(
        'libs.hist',
        desc='''
Library implementing support for plotting results using histogram graphs.
''',
    ),
    PackageDescription(
        'libs.qasm',
        desc='''
Library implementing support for reading from OpenQASM files using either Qiskit or pyparsing.
''',
    ),
    PackageDescription(
        'libs',
        desc='''
The library collection of ProjectQ which, for now, consists of a tiny math library, a small library to print simulation
results as histograms graphs and some OpenQASM support library.
Soon, more libraries will be added.
''',
    ),
    PackageDescription(
        'meta',
        desc='''
Contains meta statements which allow more optimal code while making it easier for users to write their code.
Examples are `with Compute`, followed by an automatic uncompute or `with Control`, which allows the user to condition
an entire code block upon the state of a qubit.
''',
    ),
    PackageDescription(
        'ops',
        desc='''
The operations collection consists of various default gates and is a work-in-progress, as users start to work with
ProjectQ.
''',
        module_special_members='__init__,__or__',
    ),
    PackageDescription(
        'setups.decompositions',
        desc='''
The decomposition package is a collection of gate decomposition / replacement rules which can be used by,
e.g., the AutoReplacer engine.
''',
    ),
    PackageDescription(
        'setups',
        desc='''
The setups package contains a collection of setups which can be loaded by the `MainEngine`.
Each setup contains a `get_engine_list` function which returns a list of compiler engines:

Example:
    .. code-block:: python

        import projectq.setups.ibm as ibm_setup
        from projectq import MainEngine
        eng = MainEngine(engine_list=ibm_setup.get_engine_list())
        # eng uses the default Simulator backend

The subpackage decompositions contains all the individual decomposition rules
which can be given to, e.g., an `AutoReplacer`.
''',
        submodules_desc='''
Each of the submodules contains a setup which can be used to specify the
`engine_list` used by the `MainEngine` :''',
        submodule_special_members='__init__',
    ),
    PackageDescription(
        'types',
        (
            'The types package contains quantum types such as Qubit, Qureg, and WeakQubitRef. With further development '
            'of the math library, also quantum integers, quantum fixed point numbers etc. will be added.'
        ),
    ),
]
# ------------------------------------------------------------------------------
# Automatically generate ReST files for each package of ProjectQ

docgen_path = os.path.join(os.path.dirname(os.path.realpath('__file__')), '_doc_gen')
if not os.path.isdir(docgen_path):
    os.mkdir(docgen_path)

for desc in descriptions:
    fname = os.path.join(docgen_path, 'projectq.{}.rst'.format(desc.name))
    lines = None
    if os.path.exists(fname):
        with utils.fdopen(fname, 'r') as fd:
            lines = [line[:-1] for line in fd.readlines()]

    new_lines = desc.get_ReST()

    if new_lines != lines:
        with utils.fdopen(fname, 'w') as fd:
            fd.write('\n'.join(desc.get_ReST()))
