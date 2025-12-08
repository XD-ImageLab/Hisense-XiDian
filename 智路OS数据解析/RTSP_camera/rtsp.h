/******************************************************************************  
 * Copyright 2022 The Airos Authors. All Rights Reserved.  
 *  
 * Licensed under the Apache License, Version 2.0 (the "License");  
 * you may not use this file except in compliance with the License.  
 * You may obtain a copy of the License at  
 *  
 * http://www.apache.org/licenses/LICENSE-2.0  
 *  
 * Unless required by applicable law or agreed to in writing, software  
 * distributed under the License is distributed on an "AS IS" BASIS,  
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  
 * See the License for the specific language governing permissions and  
 * limitations under the License.  
 *****************************************************************************/  
  
#pragma once  
  
#include <atomic>  
#include <memory>  
#include <mutex>  
#include <string>  
#include <thread>  
  
#include "base/device_connect/camera/camera_base.h"  
  
// Forward declarations for FFmpeg structures  
struct AVFormatContext;  
struct AVCodecContext;  
struct AVFrame;  
struct AVPacket;  
struct SwsContext;  
  
namespace airos {  
namespace base {  
namespace device {  
  
class RtspCamera : public CameraDevice {  
 public:  
  explicit RtspCamera(const CameraImageCallBack& cb);  
  virtual ~RtspCamera();  
  
  /**  
   * @brief Initialize RTSP camera with configuration  
   * @param config Camera initialization configuration  
   * @return true if initialization successful, false otherwise  
   */  
  bool Init(const CameraInitConfig& config) override;  
  
 private:  
  /**  
   * @brief Main decoding thread function  
   */  
  void DecodingThread();  
  
  /**  
   * @brief Initialize FFmpeg components  
   * @return true if successful, false otherwise  
   */  
  bool InitFFmpeg();  
  
  /**  
   * @brief Cleanup FFmpeg resources  
   */  
  void CleanupFFmpeg();  
  
  /**  
   * @brief Decode a video frame  
   * @param packet Input packet to decode  
   * @return true if frame decoded successfully, false otherwise  
   */  
  bool DecodeFrame(AVPacket* packet);  
  
  /**  
   * @brief Convert decoded frame to RGB/BGR format  
   * @param frame Source frame  
   * @param output_data Destination camera image data  
   * @return true if conversion successful, false otherwise  
   */  
  bool ConvertFrame(AVFrame* frame, std::shared_ptr<CameraImageData>& output_data);  
  
  // Configuration  
  CameraInitConfig config_;  
  std::string rtsp_url_;  
  
  // FFmpeg components  
  AVFormatContext* format_ctx_;  
  AVCodecContext* codec_ctx_;  
  AVFrame* frame_;  
  AVFrame* frame_rgb_;  
  AVPacket* packet_;  
  SwsContext* sws_ctx_;  
  int video_stream_index_;  
  
  // Thread management  
  std::unique_ptr<std::thread> decode_thread_;  
  std::atomic<bool> running_;  
  std::mutex mutex_;  
  
  // Frame counter  
  std::atomic<uint32_t> sequence_num_;  
  
  // Disable copy and move  
  RtspCamera(const RtspCamera&) = delete;  
  RtspCamera& operator=(const RtspCamera&) = delete;  
  RtspCamera(RtspCamera&&) = delete;  
  RtspCamera& operator=(RtspCamera&&) = delete;  
};  
  
}  // namespace device  
}  // namespace base  
}  // namespace airos