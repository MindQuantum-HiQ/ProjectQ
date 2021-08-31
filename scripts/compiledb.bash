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

current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
root_dir=$(realpath $current_dir/..)
build_dir=$(realpath $root_dir/build)

. $current_dir/_locate_cmake.bash

# ==============================================================================

mkdir -p $build_dir
echo "Calling CC=gcc CXX=g++ $CMAKE -B$build_dir -S$root_dir -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
CC=gcc CXX=g++ $CMAKE -B$build_dir -S$root_dir -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cat $build_dir/compile_commands.json
