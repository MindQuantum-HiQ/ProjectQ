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

# ==============================================================================

ver_cmp()
{
    local IFS=.
    local V1=($1) V2=($2) I
    for ((I=0 ; I<${#V1[*]} || I<${#V2[*]} ; I++)) ; do
        [[ ${V1[$I]:-0} -lt ${V2[$I]:-0} ]] && echo -1 && return
        [[ ${V1[$I]:-0} -gt ${V2[$I]:-0} ]] && echo 1 && return
    done
    echo 0
}

ver_le()
{
    [[ ! $(ver_cmp "$1" "$2") -eq 1 ]]
}

# ==============================================================================
# Look for compatible CMake version


cmakelists_txt=$root_dir/CMakeLists.txt
version_required=$(grep cmake_minimum_required $cmakelists_txt | egrep -o '([0-9]+\.[0-9]+)')

echo 'Extracting minimum CMake version from $cmakelists_txt'
echo "  -> minimum version required: $version_required"


for cmake in $(which -a cmake); do
    version=$($cmake --version | head -n1 | egrep -o '([0-9]+\.[0-9]+\.[0-9]+)')

    echo "Considering CMake ($version): $cmake"

    if [[ ! $(ver_cmp $version_required $version) -eq 1 ]]; then
        echo '  -> selected (version compatible)'
        CMAKE=$cmake
        break
    else
        echo '  -> rejected (version too old)'
    fi
done

if [ -z "$CMAKE" ]; then
    echo "Unable to locate a compatible CMake executable (minimum required version: $version_required)" 1>&2
    exit 1
fi

cmake_path=$(dirname $CMAKE)
echo "Modifying PATH variable by prepending: $cmake_path"
export PATH=$cmake_path:$PATH
echo "PATH = $PATH"
