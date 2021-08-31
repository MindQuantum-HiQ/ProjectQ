#! /usr/bin/env bash
# Copyright 2020 <Huawei Technologies Co., Ltd>
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

DIST_DIR=$1
shift

# ==============================================================================

echo 'Setting up default repository'
cat << EOF > ~/.pypirc
[distutils]
index-servers=
    pypi

[pypi]
repository: $TWINE_REPOSITORY_URL
username: $TWINE_USERNAME
password: $TWINE_PASSWORD
EOF

echo 'Building source distribution'
python3 setup.py sdist

echo 'Building binary distributions'
python3 -m cibuildwheel --output-dir dist/

# Make sure that twine is installed (mostly for Mac OS)
python3 -m pip install twine

echo 'Running twine check'
python3 -m twine check $DIST_DIR/*

echo 'Running twine upload'
echo python3 -m twine upload $@ -r pypi dist/*
python3 -m twine upload $@ -r pypi dist/*

# ==============================================================================
