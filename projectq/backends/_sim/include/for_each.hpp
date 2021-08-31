//   Copyright 2021 <Huawei Technologies Co., Ltd>
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.

#ifndef FOR_EACH_HPP
#define FOR_EACH_HPP

#include <type_traits>

#if defined(__SYCL_COMPILER_VERSION)
#    include <sycl/algorithm>
#    include <sycl/execution>
#    define PARALLEL_STL_LOOP 1  // NOLINT
#    define OPENMP_LOOP       0  // NOLINT
#else
#    if defined(HIQ_WITH_CUDA) || (defined(ENABLE_MULTITHREADING) && defined(USE_PARALLEL_STL))
#        define PARALLEL_STL_LOOP 1  // NOLINT
#    else
#        define PARALLEL_STL_LOOP 0  // NOLINT
#    endif
#    if defined(ENABLE_MULTITHREADING) && defined(USE_OPENMP)
#        define OPENMP_LOOP 1  // NOLINT
#    else
#        define OPENMP_LOOP 0  // NOLINT
#    endif

#    include <algorithm>
#    if PARALLEL_STL_LOOP
#        include <execution>
#    endif  // PARALLEL_STL_LOOP

#endif  // __SYCL_COMPILER_VERSION

namespace parallel
{
    template <typename kernel_counter_t, typename unary_func_t>
    void for_each(const kernel_counter_t& counter, unary_func_t&& unary_func)
    {
#if PARALLEL_STL_LOOP
        std::for_each(std::execution::par_unseq, std::begin(counter), std::end(counter),
                      std::forward<unary_func_t>(unary_func));
#elif OPENMP_LOOP
#    pragma omp parallel for schedule(static) default(none) shared(counter, unary_func)
        for (auto it = counter.begin(); it < counter.end(); ++it) {
            unary_func(*it);
        }
#else
        std::for_each(std::begin(counter), std::end(counter), std::forward<unary_func_t>(unary_func));
#endif
    }
}  // namespace parallel

#undef PARALLEL_STL_LOOP
#undef OPENMP_LOOP

#endif
