// Copyright 2017 ProjectQ-Framework (www.projectq.ch)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef FUSION_HPP_
#define FUSION_HPP_

#include "aligned_allocator.hpp"

#include <algorithm>
#include <complex>
#include <iostream>
#include <set>
#include <vector>

namespace fusion
{
    static constexpr auto alignment = 64;

    class Item
    {
    public:
        using Index = unsigned;
        using IndexVector = std::vector<Index>;
        using Complex = std::complex<double>;
        using Matrix = std::vector<Complex, aligned_allocator<Complex, alignment>>;
        Item(Matrix mat, IndexVector idx) : mat_(std::move(mat)), idx_(std::move(idx))
        {}
        Matrix& get_matrix()
        {
            return mat_;
        }
        IndexVector& get_indices()
        {
            return idx_;
        }

    private:
        Matrix mat_;
        IndexVector idx_;
    };

    class Fusion
    {
    public:
        using Index = unsigned;
        using IndexSet = std::set<Index>;
        using IndexVector = std::vector<Index>;
        using Complex = std::complex<double>;
        using Matrix = std::vector<Complex, aligned_allocator<Complex, alignment>>;
        using ItemVector = std::vector<Item>;

        unsigned num_qubits()
        {
            return set_.size();
        }

        [[nodiscard]] auto size() const
        {
            return items_.size();
        }

        void insert(Matrix matrix, IndexVector index_list, IndexVector const& ctrl_list = {})
        {
            for (auto idx: index_list) {
                set_.emplace(idx);
            }

            handle_controls(matrix, index_list, ctrl_list);
            Item item(matrix, index_list);
            items_.push_back(item);
        }

        // NOLINTNEXTLINE
        void perform_fusion(Matrix& fused_matrix, IndexVector& index_list, IndexVector& ctrl_list)
        {
            for (const auto& idx: set_) {
                index_list.push_back(idx);
            }

            std::size_t N = num_qubits();
            std::size_t dim = 1UL << N;
            fused_matrix = Matrix(dim * dim);
            auto& M = fused_matrix;

            for (std::size_t i = 0; i < dim; ++i) {
                M[i * dim + i] = 1.;
            }

            for (auto& item: items_) {
                auto dim2 = static_cast<std::size_t>(sqrt(item.get_matrix().size()));
                auto const& idx = item.get_indices();
                IndexVector idx2mat(idx.size());
                for (std::size_t i = 0; i < idx.size(); ++i) {
                    idx2mat[i] = static_cast<unsigned>(
                        std::equal_range(index_list.begin(), index_list.end(), idx[i]).first - index_list.begin());
                }

                for (std::size_t k = 0; k < dim; ++k) {  // loop over big matrix columns
                    // check if column index satisfies control-mask
                    // if not: leave it unchanged
                    std::vector<Complex> oldcol(1UL << N);
                    for (std::size_t i = 0; i < (1UL << N); ++i) {
                        oldcol[i] = M[i * dim + k];
                    }

                    for (std::size_t i = 0; i < (1UL << N); ++i) {
                        std::size_t local_i = 0;
                        for (std::size_t l = 0; l < idx.size(); ++l) {
                            local_i |= ((i >> idx2mat[l]) & 1UL) << l;
                        }

                        Complex res = 0.;
                        for (std::size_t j = 0; j < (1UL << idx.size()); ++j) {
                            std::size_t locidx = i;
                            for (std::size_t l = 0; l < idx.size(); ++l) {
                                if (((j >> l) & 1UL) != ((i >> idx2mat[l]) & 1UL)) {
                                    locidx ^= (1UL << idx2mat[l]);
                                }
                            }
                            res += oldcol[locidx] * item.get_matrix()[local_i * dim2 + j];
                        }
                        M[i * dim + k] = res;
                    }
                }
            }
            ctrl_list.reserve(ctrl_set_.size());
            for (const auto& ctrl: ctrl_set_) {
                ctrl_list.push_back(ctrl);
            }
        }

    private:
        static void add_controls(Matrix& matrix, IndexVector& indexList, IndexVector const& new_ctrls)
        {
            indexList.reserve(indexList.size() + new_ctrls.size());
            indexList.insert(indexList.cend(), new_ctrls.cbegin(), new_ctrls.cend());

            auto dim = static_cast<std::size_t>(sqrt(matrix.size()));
            std::size_t F = (1UL << new_ctrls.size()) * dim;
            Matrix newmatrix(F * F);

            std::size_t Offset = F - dim;

            for (std::size_t i = 0; i < Offset; ++i) {
                newmatrix[i * F + i] = 1.;
            }
            for (std::size_t i = 0; i < dim; ++i) {
                for (std::size_t j = 0; j < dim; ++j) {
                    newmatrix[(Offset + i) * F + Offset + j] = matrix[i * dim + j];
                }
            }
            matrix = std::move(newmatrix);
        }

        void handle_controls(Matrix& matrix, IndexVector& indexList, IndexVector const& ctrlList)
        {
            auto unhandled_ctrl = ctrl_set_;  // will contain all ctrls that are not part of the new command
            // --> need to be removed from the global mask and the controls incorporated into the old
            // commands (the ones already in the list).

            for (auto ctrlIdx: ctrlList) {
                if (ctrl_set_.count(ctrlIdx) == 0U) {  // need to either add it to the list or to the command
                    if (!items_.empty()) {             // add it to the command
                        add_controls(matrix, indexList, {ctrlIdx});
                        set_.insert(ctrlIdx);
                    }
                    else {  // add it to the list
                        ctrl_set_.emplace(ctrlIdx);
                    }
                }
                else {
                    unhandled_ctrl.erase(ctrlIdx);
                }
            }
            // remove global controls which are no longer global (because the current command didn't have it)
            if (!unhandled_ctrl.empty()) {
                IndexVector new_ctrls;
                new_ctrls.reserve(unhandled_ctrl.size());
                for (const auto& idx: unhandled_ctrl) {
                    new_ctrls.push_back(idx);
                    ctrl_set_.erase(idx);
                    set_.insert(idx);
                }
                for (auto& item: items_) {
                    add_controls(item.get_matrix(), item.get_indices(), new_ctrls);
                }
            }
        }

        IndexSet set_;
        ItemVector items_;
        IndexSet ctrl_set_;
    };

}  // namespace fusion

#endif
