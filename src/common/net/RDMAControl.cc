#include "common/net/RDMAControl.h"

#include "common/monitor/Recorder.h"
#include "common/net/Waiter.h"
#include "common/net/ib/IBSocket.h"
#include "common/serde/ClientContext.h"
#include "common/utils/Duration.h"
#include "core/user/UserToken.h"  // C5: Add for token validation
#include "common/utils/LogUtil.h"  // C5: Add for logging authentication failures

namespace hf3fs::net {
namespace {

monitor::ValueRecorder currentRDMATransmission{"common.rdma_control.current", std::nullopt, false};
monitor::LatencyRecorder transmissionPrepareLatency{"common.transmission.prepare_latency"};
monitor::LatencyRecorder transmissionWaitLatency{"common.transmission.wait_latency"};
monitor::LatencyRecorder transmissionNetworkLatency{"common.transmission.network_latency"};

}  // namespace

CoTask<void> RDMATransmissionLimiter::co_wait() {
  co_await semaphore_.co_wait();
  currentRDMATransmission.set(++current_);
}

void RDMATransmissionLimiter::signal(Duration latency) {
  currentRDMATransmission.set(--current_);
  semaphore_.signal();
  transmissionNetworkLatency.addSample(latency);
}

CoTryTask<RDMATransmissionRsp> RDMAControlImpl::apply(serde::CallContext &ctx, const RDMATransmissionReq &req) {
  // C5: Validate authentication token before processing any RDMA request
  if (req.authToken.empty()) {
    XLOG(ERR, "RDMA authentication failed: missing auth token for request uuid {}", req.uuid);
    co_return makeError(StatusCode::kAuthenticationFail, "Authentication token required for RDMA operations");
  }

  // C5: Validate the token against the existing UserToken system
  auto tokenResult = hf3fs::core::decodeUidFromUserToken(req.authToken);
  if (!tokenResult) {
    XLOG(ERR, "RDMA authentication failed: invalid auth token for request uuid {} - {}", req.uuid, tokenResult.error());
    co_return makeError(StatusCode::kAuthenticationFail, "Invalid authentication token for RDMA operations");
  }

  XLOGF(DBG5, "RDMA authentication successful for uid {} request uuid {}", tokenResult->id(), req.uuid);
  
  auto startTime = RelativeTime::now();
  co_await limiter_->co_wait();
  transmissionWaitLatency.addSample(RelativeTime::now() - startTime);
  auto prepareLatency = Waiter::instance().setTransmissionLimiterPtr(req.uuid, limiter_, startTime);
  if (UNLIKELY(!prepareLatency)) {
    limiter_->signal(0_ms);
  } else {
    transmissionPrepareLatency.addSample(*prepareLatency);
  }
  co_return RDMATransmissionRsp{};
}

}  // namespace hf3fs::net
