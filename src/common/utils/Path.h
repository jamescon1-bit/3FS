#pragma once

#include <boost/filesystem.hpp>
#include <filesystem>
#include <fmt/format.h>
#include <stdexcept>
#include <string>

namespace hf3fs {

class SecurePath {
private:
  boost::filesystem::path path_;
  
public:
  // C2: Add secure path validation wrapper
  explicit SecurePath(const std::string& path_str) {
    // Validate and sanitize the path
    if (path_str.empty()) {
      throw std::invalid_argument("Path cannot be empty");
    }
    
    // Check for null bytes (potential security issue)
    if (path_str.find('\0') != std::string::npos) {
      throw std::invalid_argument("Path cannot contain null bytes");
    }
    
    // Detect path traversal attempts
    if (path_str.find("../") != std::string::npos || 
        path_str.find("..\\") != std::string::npos ||
        path_str.find("/..") != std::string::npos ||
        path_str.find("\\..") != std::string::npos) {
      throw std::invalid_argument("Path traversal detected");
    }
    
    // Check for excessive length
    if (path_str.length() > 4096) {
      throw std::invalid_argument("Path too long");
    }
    
    try {
      path_ = boost::filesystem::path(path_str);
      // Canonicalize to resolve any remaining issues
      if (boost::filesystem::exists(path_)) {
        path_ = boost::filesystem::canonical(path_);
      }
    } catch (const boost::filesystem::filesystem_error& e) {
      throw std::invalid_argument("Invalid path: " + std::string(e.what()));
    }
  }
  
  // Allow conversion to boost::filesystem::path
  operator boost::filesystem::path() const { return path_; }
  const boost::filesystem::path& get() const { return path_; }
  std::string string() const { return path_.string(); }
};

using Path = boost::filesystem::path;

// Utility function to validate paths
inline void validatePath(const std::string& path) {
  SecurePath validated(path);  // This will throw if invalid
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
