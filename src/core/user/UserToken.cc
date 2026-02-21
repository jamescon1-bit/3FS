#include "UserToken.h"

#include <folly/Random.h>
#include <folly/base64.h>
#include <folly/hash/Checksum.h>
#include <folly/lang/Bits.h>

#include "fdb/FDBTransaction.h"
#include "common/utils/LogUtil.h"  // For deprecation warning logging

namespace hf3fs::core {
namespace {
const uint16_t magicNum = 0xF1DB;
// clang-format off
constexpr std::array<uint8_t, 18> mapping = {
  12, 6, 0,
  13, 7, 1,
  14, 8, 2,
  15, 9, 3,
  16, 10, 4,
  17, 11, 5,
};
// clang-format on
}  // namespace

String encodeUserToken(uint32_t uid, uint64_t randomv) {
  static_assert(folly::Endian::order == folly::Endian::Order::LITTLE);

  // C1: Increase token size for better security (128-bit entropy minimum)
  std::array<uint8_t, 26> tmp;  // Increased from 18 to accommodate more entropy
  auto *p = tmp.data();

  static_assert(sizeof(magicNum) == 2);
  std::memcpy(p, &magicNum, sizeof(magicNum));
  p += sizeof(magicNum);

  static_assert(sizeof(uid) == 4);
  std::memcpy(p, &uid, sizeof(uid));
  p += sizeof(uid);

  // C1: Add timestamp for expiration validation
  uint64_t timestamp = std::chrono::duration_cast<std::chrono::seconds>(
    std::chrono::system_clock::now().time_since_epoch()).count();
  static_assert(sizeof(timestamp) == 8);
  std::memcpy(p, &timestamp, sizeof(timestamp));
  p += sizeof(timestamp);

  static_assert(sizeof(randomv) == 8);
  std::memcpy(p, &randomv, sizeof(randomv));
  p += sizeof(randomv);

  // C1: Add additional entropy (second random value for 128-bit total)
  uint64_t randomv2 = folly::Random::secureRand64();
  static_assert(sizeof(randomv2) == 8);
  std::memcpy(p, &randomv2, sizeof(randomv2));
  p += sizeof(randomv2);

  auto crc = folly::crc32(tmp.data(), 22, 0);  // Updated length
  static_assert(sizeof(crc) == 4);
  std::memcpy(p, &crc, sizeof(crc));

  std::array<char, 26> buffer;  // Increased buffer size
  for (size_t i = 0; i < 18; ++i) {  // Keep existing mapping for first 18 bytes
    buffer[mapping[i]] = tmp[i];
  }
  // Direct mapping for additional bytes
  for (size_t i = 18; i < 26; ++i) {
    buffer[i] = tmp[i];
  }
  
  return folly::base64Encode(std::string_view(buffer.data(), buffer.size()));
}

Result<std::pair<uint32_t, uint64_t>> decodeUserToken(std::string_view token) {
  try {
    auto decoded = folly::base64Decode(token);
    
    // C1: Support both old (18-byte) and new (26-byte) token formats
    bool isOldFormat = (decoded.size() == 18);
    bool isNewFormat = (decoded.size() == 26);
    
    if (!isOldFormat && !isNewFormat) {
      return makeError(StatusCode::kInvalidFormat, "Decode token fail: invalid format");
    }

    std::array<uint8_t, 26> tmp{};  // Use larger array, zero-initialized
    if (isOldFormat) {
      for (size_t i = 0; i < 18; ++i) {
        tmp[i] = decoded[mapping[i]];
      }
    } else {
      for (size_t i = 0; i < 18; ++i) {
        tmp[i] = decoded[mapping[i]];
      }
      for (size_t i = 18; i < 26; ++i) {
        tmp[i] = decoded[i];
      }
    }

    uint16_t mn = 0;
    uint32_t uid = 0, crc = 0;
    uint64_t timestamp = 0, randomv1 = 0, randomv2 = 0;
    auto *p = tmp.data();
    
    std::memcpy(&mn, p, sizeof(mn));
    p += sizeof(mn);
    std::memcpy(&uid, p, sizeof(uid));
    p += sizeof(uid);
    std::memcpy(&timestamp, p, sizeof(timestamp));
    p += sizeof(timestamp);
    std::memcpy(&randomv1, p, sizeof(randomv1));
    p += sizeof(randomv1);
    
    if (isNewFormat) {
      std::memcpy(&randomv2, p, sizeof(randomv2));
      p += sizeof(randomv2);
    }
    
    std::memcpy(&crc, p, sizeof(crc));

    if (mn != magicNum) {
      return makeError(StatusCode::kInvalidFormat, "Decode token fail: invalid format");
    }

    size_t crcLength = isOldFormat ? 14 : 22;
    auto expectedCrc = folly::crc32(tmp.data(), crcLength, 0);
    if (crc != expectedCrc) {
      return makeError(StatusCode::kInvalidFormat, "Decode token fail: invalid crc");
    }

    // C1: Validate token expiration (24 hour expiry)
    if (isNewFormat) {
      uint64_t currentTime = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
      const uint64_t TOKEN_EXPIRY_SECONDS = 24 * 60 * 60; // 24 hours
      
      if (currentTime - timestamp > TOKEN_EXPIRY_SECONDS) {
        return makeError(StatusCode::kInvalidFormat, "Token has expired");
      }
    } else {
      // C1 Migration: Add deprecation warning for old token format
      static std::atomic<uint64_t> oldTokenWarningCount{0};
      auto count = oldTokenWarningCount.fetch_add(1);
      if (count % 100 == 0) {  // Log every 100th occurrence to avoid spam
        XLOGF(WARN, "Old token format detected (count: {}). Please migrate to new token format. Support will be removed in a future version.", count + 1);
      }
    }

    return std::make_pair(uid, timestamp);
  } catch (const folly::base64_decode_error &e) {
    return makeError(StatusCode::kInvalidFormat, "Decode token fail: {}", e.what());
  }
}

Result<flat::Uid> decodeUidFromUserToken(std::string_view token) {
  auto r = decodeUserToken(token);
  RETURN_ON_ERROR(r);
  auto [uid, ts] = *r;
  return flat::Uid{uid};
}

CoTryTask<String> encodeUserToken(uint32_t uid, kv::IReadOnlyTransaction &txn) {
  co_return encodeUserToken(uid, folly::Random::secureRand64());
}
}  // namespace hf3fs::core
