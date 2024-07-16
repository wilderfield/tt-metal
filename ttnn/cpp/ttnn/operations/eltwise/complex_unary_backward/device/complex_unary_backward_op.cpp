// SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
//
// SPDX-License-Identifier: Apache-2.0


#include "third_party/magic_enum/magic_enum.hpp"

#include "tt_eager/tt_dnn/op_library/eltwise_unary/eltwise_unary_op.hpp"
#include "tt_eager/tt_dnn/op_library/composite/composite_ops.hpp"
#include "tt_metal/common/constants.hpp"
#include "tt_metal/host_api.hpp"
#include "tt_metal/tools/profiler/op_profiler.hpp"
#include "ttnn/operations/eltwise/complex_unary_backward/device/complex_unary_backward_op.hpp"
#include "ttnn/cpp/ttnn/operations/eltwise/binary/binary.hpp"

namespace ttnn::operations::complex_unary_backward {

// polar
// grad_abs = torch.real(grad_conj * torch.sgn(result))
// result_mul_1_j = result * torch.tensor(0.0 + 1.0j)
// grad_angle = torch.real(grad_conj * result_mul_1_j)
// polar fwd op uses sin and cos hence input_b range is (0, 2*pi)
std::vector<ComplexTensor> _polar_bw(const ComplexTensor& grad, const ComplexTensor& input, const MemoryConfig& output_mem_config) {
    std::vector<ComplexTensor> grad_tensor;
    ComplexTensor result = polar(input, output_mem_config);
    Tensor abs_result = complex_abs(result, output_mem_config);
    Tensor sgn_result_r = where(ttnn::eqz(abs_result, output_mem_config), ttnn::operations::creation::zeros_like(result.real(), result.real().get_dtype(), result.real().get_layout(), std::nullopt, output_mem_config), ttnn::multiply(result.real(), ttnn::reciprocal(abs_result, output_mem_config), std::nullopt, output_mem_config), output_mem_config );
    Tensor sgn_result_i = where(ttnn::eqz(abs_result, output_mem_config), ttnn::operations::creation::zeros_like(result.imag(), result.imag().get_dtype(), result.imag().get_layout(), std::nullopt, output_mem_config), ttnn::multiply(result.imag(), ttnn::reciprocal(abs_result, output_mem_config), std::nullopt, output_mem_config), output_mem_config );
    abs_result.deallocate();
    ComplexTensor sgn_result = ComplexTensor({ sgn_result_r, sgn_result_i });
    sgn_result_r.deallocate();
    sgn_result_i.deallocate();
    Tensor grad_abs = real(complex_mul(conj(grad, output_mem_config), sgn_result, output_mem_config), output_mem_config);
    sgn_result.deallocate();
    ComplexTensor flip_tensor = ComplexTensor({ttnn::operations::creation::zeros_like(input.real(), input.real().get_dtype(), input.real().get_layout(), std::nullopt, output_mem_config), ttnn::operations::creation::full_like(input.imag(), 1.0) });
    Tensor grad_angle = real(complex_mul(conj(grad, output_mem_config), complex_mul(result, flip_tensor, output_mem_config), output_mem_config), output_mem_config);
    result.deallocate();
    flip_tensor.deallocate();
    ComplexTensor grad_result = ComplexTensor({grad_abs, grad_angle});
    grad_abs.deallocate();
    grad_angle.deallocate();
    grad_tensor.emplace_back(grad_result);
    return grad_tensor;
}

// complex imag
// imag: at::imag(grad)
std::vector<ComplexTensor> _imag_bw(const Tensor& grad, const ComplexTensor& input, const MemoryConfig& output_mem_config) {
    std::vector<ComplexTensor> grad_tensor;
    Tensor real_input = real(input, output_mem_config);
    Tensor r = ttnn::operations::creation::zeros_like(real_input, real_input.get_dtype(), real_input.get_layout(), std::nullopt, output_mem_config);
    ComplexTensor grad_result = ComplexTensor({r,grad});
    r.deallocate();
    grad_tensor.emplace_back(grad_result);
    return grad_tensor;
}

}  // namespace ttnn::operations::complex_unary_backward