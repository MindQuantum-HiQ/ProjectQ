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

#ifndef KERNEL_COUNTER_HPP
#define KERNEL_COUNTER_HPP

#include <cstddef>
#include <iterator>

namespace details
{
    // A minimal implementation of Boost/Thrust counting iterator,
    // as we need to iterate an index only, not a real data container.
    template <typename T, typename T_DIFF, T START>
    class kernel_counter
    {
        T length;

    public:
        explicit kernel_counter(T length_) : length(length_)
        {}

        class iterator
        {
        public:
            using iterator_category = std::random_access_iterator_tag;
            using difference_type = std::ptrdiff_t;
            using value_type = T;
            using pointer = int*;
            using reference = T;

            constexpr explicit iterator(T init = 0) noexcept : value(init)
            {}

            constexpr iterator& operator++() noexcept
            {
                ++value;
                return *this;
            }
            constexpr iterator& operator+=(unsigned int other) noexcept
            {
                value += other;
                return *this;
            }
            constexpr iterator operator+(unsigned int other) const noexcept
            {
                auto it(*this);
                it += other;
                return it;
            }
            constexpr friend iterator operator+(unsigned int lhs, iterator rhs) noexcept
            {
                rhs += lhs;
                return rhs;
            }

            constexpr iterator& operator--() noexcept
            {
                --value;
                return *this;
            }
            constexpr iterator& operator-=(unsigned int other) noexcept
            {
                value -= other;
                return *this;
            }
            constexpr iterator operator-(unsigned int other) const noexcept
            {
                auto it(*this);
                it -= other;
                return it;
            }

            constexpr difference_type operator-(iterator rhs) const noexcept
            {
                return static_cast<difference_type>(value) - rhs.value;
            }

            constexpr reference operator*() const noexcept
            {
                return value;
            }
            constexpr reference operator[](const iterator other) const noexcept
            {
                return value + other.value;
            }
            constexpr reference operator[](const value_type other) const noexcept
            {
                return value + other;
            }

            constexpr bool operator==(const iterator other) const noexcept
            {
                return value == other.value;
            }
            constexpr bool operator!=(const iterator other) const noexcept
            {
                return value != other.value;
            }
            constexpr bool operator<(const iterator other) const noexcept
            {
                return value < other.value;
            }

        private:
            T value{0};
        };

        iterator begin() const
        {
            return iterator(START);
        }
        iterator end() const
        {
            return iterator(START + length);
        }
    };

}  // namespace details

#endif /* KERNEL_COUNTER_HPP */
