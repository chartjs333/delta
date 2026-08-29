#pragma once

#include <delta/certificates/contracts.hpp>
#include <delta/qlora/context.hpp>

#include <string>
#include <string_view>

namespace delta::qlora {

inline constexpr std::string_view base_media_type =
    "application/vnd.deltareduce.qlora-base;version=1";
inline constexpr std::string_view tokenizer_media_type =
    "application/vnd.deltareduce.qlora-tokenizer;version=1";
inline constexpr std::string_view quantization_profile_media_type =
    "application/vnd.deltareduce.qlora-quantization-profile;version=1";
inline constexpr std::string_view adapter_checkpoint_media_type =
    "application/vnd.deltareduce.qlora-adapter-checkpoint;version=1";

enum class MediaDisposition { certified_base, applied_adapter };

[[nodiscard]] MediaDisposition validate_media_policy(
    const Context& context,
    std::string_view media_type,
    std::string_view object_id,
    const certificates::ApplyQc* apply_qc = nullptr);

}  // namespace delta::qlora
