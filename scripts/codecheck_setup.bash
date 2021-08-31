#! /bin/bash
# ==============================================================================
#
# Copyright 2021 <Huawei Technologies Co., Ltd>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# ==============================================================================
# Locate compatible CMake version

current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON=$(which python3)

# ==============================================================================

repeat_cmd=5
allow_failure=0
failed=0

run_cmd()
{
    if [[ $allow_failure -eq 0 || $failed -eq 0 ]]; then
        echo "Calling $@"

        for (( c=1; c<=$repeat_cmd; c++ )); do
            "$@"
            ret=$?

            if [ $ret -eq 0 ]; then
                echo "  -> success on try $c"
                break
            elif [ $c -lt $repeat_cmd ]; then
                echo "  -> failed on try $c"
            else
                echo "  -> failed on last try"
            fi
        done

        if [ $allow_failure -eq 0 ]; then
            return $ret
        elif [ $ret -ne 0 ]; then
            failed=1
        fi
    else
        echo "Not calling (previous failure) $@"
    fi
}

run_python_cmd()
{
    python_locations=($PYTHON
                      /devcloud/codechecktools/CloudDragon/uccp2.0/tools/python/python3/linux/bin/python)

    for python in ${python_locations[@]}; do
        run_cmd $python "$@"
        ret=$?

        if [ $allow_failure -eq 0 ]; then
            return $ret
        elif [ $ret -ne 0 ]; then
            failed=1
        fi
    done
}

pip_cmd()
{
    run_python_cmd -m pip "$@"
}

pip_cmd config --user set global.index-url 'http://mirrors.tools.huawei.com/pypi/simple'
pip_cmd config --user set global.trusted-host mirrors.tools.huawei.com
pip_cmd config --user set global.timeout 120
pip_cmd install --user -U cmake 'pybind11>=2.6.2' 'setuptools>=42' wheel 'setuptools-scm[toml]>=3.4'

# ==============================================================================
# Find and setup compatible CMake version

. $current_dir/_locate_cmake.bash

# ==============================================================================

cd $WORKSPACE/code

echo 'Create fake tag for setuptools-scm'
run_cmd git tag v0.99

# echo 'Get history and tags for SCM versioning to work'
# run_cmd git fetch --prune --unshallow
# run_cmd git fetch --depth=1 origin +refs/tags/*:refs/tags/*

run_cmd $PYTHON setup.py gen_reqfile --include-extras=test,braket,pyparsing,docs

pip_cmd install --user -r requirements.txt
HIQ_DISABLE_CEXT=1 run_cmd $PYTHON setup.py develop --user --editable --build-directory pybuild --no-deps

# Install for pylint tool
PYTHON=/devcloud/codechecktools/CloudDragon/uccp2.0/tools/python/python3/linux/bin/python
HIQ_DISABLE_CEXT=1 run_cmd $PYTHON -m pip install .
