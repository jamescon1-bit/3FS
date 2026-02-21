#pragma once

#include <boost/filesystem.hpp>
#include <filesystem>
#include <fmt/format.h>
#include <stdexcept>
#include <string>
#include "common/utils/Result.h"  // For Result<> pattern

namespace hf3fs {

class SecurePath {
private:
  boost::filesystem::path path_;
  
  // Private constructor - use create() factory method instead
  explicit SecurePath(const boost::filesystem::path& path) : path_(path) {}
  
public:
  // C2: Factory method for secure path creation that returns Result<> instead of throwing
  static Result<SecurePath> create(const std::string& path_str) {
    // Validate and sanitize the path
    if (path_str.empty()) {
      return makeError(StatusCode::kInvalidArg, "Path cannot be empty");
    }
    
    // Check for null bytes (potential security issue)
    if (path_str.find('\0') != std::string::npos) {
      return makeError(StatusCode::kInvalidArg, "Path cannot contain null bytes");
    }
    
    // Detect path traversal attempts
    if (path_str.find("../") != std::string::npos || 
        path_str.find("..\\") != std::string::npos ||
        path_str.find("/..") != std::string::npos ||
        path_str.find("\\..") != std::string::npos) {
      return makeError(StatusCode::kInvalidArg, "Path traversal detected");
    }
    
    // Check for excessive length
    if (path_str.length() > 4096) {
      return makeError(StatusCode::kInvalidArg, "Path too long");
    }
    
    try {
      boost::filesystem::path path = boost::filesystem::path(path_str);
      // Canonicalize to resolve any remaining issues
      if (boost::filesystem::exists(path)) {
        path = boost::filesystem::canonical(path);
      }
      return SecurePath(path);
    } catch (const boost::filesystem::filesystem_error& e) {
      return makeError(StatusCode::kInvalidArg, "Invalid path: {}", e.what());
    }
  }
  
  // Allow conversion to boost::filesystem::path
  operator boost::filesystem::path() const { return path_; }
  const boost::filesystem::path& get() const { return path_; }
  std::string string() const { return path_.string(); }
};

using Path = boost::filesystem::path;

// Utility function to validate paths
inline Result<Void> validatePath(const std::string& path) {
  auto result = SecurePath::create(path);
  if (!result) {
    return makeError(std::move(result.error()));
  }
  return Void{};
}

}  // namespace hf3fs

template <>
struct std::hash<hf3fs::Path> {
  size_t operator()(const hf3fs::Path &path) const;
};

FMT_BEGIN_NAMESPACE

template <>
struct formatter<hf3fs::Path> : formatter<std::string_view> {
  template <typename FormatContext>
  auto format(const hf3fs::Path &path, FormatContext &ctx) const {
    return formatter<std::string_view>::format(path.string(), ctx);
  }
};

FMT_END_NAMESPACE
