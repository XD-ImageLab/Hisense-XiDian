/******************************************************************************  
 * Copyright 2022 The Airos Authors. All Rights Reserved.  
 *****************************************************************************/  
  
#include "rtsp_camera.h"  
  
#include <chrono>  
#include <string> // 确保包含 string
  
extern "C" {  
#include <libavcodec/avcodec.h>  
#include <libavformat/avformat.h>  
#include <libavutil/imgutils.h>  
#include <libswscale/swscale.h>  
}  
  
#include "base/common/log.h"  
#include "base/common/time_util.h"  
#include "base/device_connect/camera/camera_factory.h"  
  
namespace airos {  
namespace base {  
namespace device {  
  
RtspCamera::RtspCamera(const CameraImageCallBack& cb)  
    : CameraDevice(cb)  
    , format_ctx_(nullptr)  
    , codec_ctx_(nullptr)  
    , frame_(nullptr)  
    , frame_rgb_(nullptr)  
    , packet_(nullptr)  
    , sws_ctx_(nullptr)  
    , video_stream_index_(-1)  
    , running_(false)  
    , sequence_num_(0) {  
  LOG_INFO << "RtspCamera constructed";  
}  
  
RtspCamera::~RtspCamera() {  
  LOG_INFO << "RtspCamera destructor called";  
  running_ = false;  
    
  // Wait for decoding thread to finish  
  if (decode_thread_ && decode_thread_->joinable()) {  
    decode_thread_->join();  
  }  
    
  CleanupFFmpeg();  
}  
  
bool RtspCamera::Init(const CameraInitConfig& config) {  
  std::lock_guard<std::mutex> lock(mutex_);  
    
  LOG_INFO << "Initializing RTSP camera: " << config.camera_name;  
    
  config_ = config;  
    
  // ---  大华摄像头接入 ---
  
  // 1. 基础部分：rtsp://user:pass@ip:554/
  if (!config.user.empty() && !config.password.empty()) {  
    // 2. 路径部分：修改为大华 (Dahua) 格式
    // （大华格式）: cam/realmonitor?channel=2&subtype=1
    rtsp_url_ = "rtsp://" + config.user + ":" + config.password + "@" +   
                config.ip + ":554/";  // 显式加上端口 554
    rtsp_url_ += "cam/realmonitor?channel=" + std::to_string(config.channel_num) + 
               "&subtype=1";

  } else if (config.user == "UserTest" && config.password == "PassTest") {  
    // 3. 测试账号部分：使用测试账号访问本地视频推流
    rtsp_url_ = "rtsp://" + config.ip + ":8554/";  
    rtsp_url_+= "Videos";
  }
    

  LOG_INFO << "RTSP URL: " << rtsp_url_;  
    
  // Initialize FFmpeg  
  if (!InitFFmpeg()) {  
    LOG_ERROR << "Failed to initialize FFmpeg for camera: " << config.camera_name;  
    return false;  
  }  
    
  // Start decoding thread  
  running_ = true;  
  decode_thread_.reset(new std::thread(&RtspCamera::DecodingThread, this));
    
  LOG_INFO << "RTSP camera initialized successfully: " << config.camera_name;  
  return true;  
}  
  
bool RtspCamera::InitFFmpeg() {  
  int ret;  
    
  // Allocate format context  
  format_ctx_ = avformat_alloc_context();  
  if (!format_ctx_) {  
    LOG_ERROR << "Failed to allocate AVFormatContext";  
    return false;  
  }  
    
  // Set options for RTSP  
  AVDictionary* options = nullptr;  
  
  // 针对 TCP 传输更稳定，防止花屏
  av_dict_set(&options, "rtsp_transport", "tcp", 0);  
  
  // 优化缓冲区，减少解码延迟
  av_dict_set(&options, "stimeout", "5000000", 0);  // 5 second timeout  
  av_dict_set(&options, "buffer_size", "1024000", 0); 
    
  // Open RTSP stream  
  ret = avformat_open_input(&format_ctx_, rtsp_url_.c_str(), nullptr, &options);  
  av_dict_free(&options);  
    
  if (ret < 0) {  
    char errbuf[AV_ERROR_MAX_STRING_SIZE];  
    av_strerror(ret, errbuf, sizeof(errbuf));  
    LOG_ERROR << "Failed to open RTSP stream: " << errbuf;  
    CleanupFFmpeg();  
    return false;  
  }  
    
  // Retrieve stream information  
  ret = avformat_find_stream_info(format_ctx_, nullptr);  
  if (ret < 0) {  
    LOG_ERROR << "Failed to find stream information";  
    CleanupFFmpeg();  
    return false;  
  }  
    
  // Find video stream  
  video_stream_index_ = -1;  
  for (unsigned int i = 0; i < format_ctx_->nb_streams; i++) {  
    if (format_ctx_->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {  
      video_stream_index_ = i;  
      break;  
    }  
  }  
    
  if (video_stream_index_ == -1) {  
    LOG_ERROR << "No video stream found";  
    CleanupFFmpeg();  
    return false;  
  }  
    
  // Get codec parameters  
  AVCodecParameters* codec_params = format_ctx_->streams[video_stream_index_]->codecpar;  
    
  // Find decoder  
  const AVCodec* codec = avcodec_find_decoder(codec_params->codec_id);  
  if (!codec) {  
    LOG_ERROR << "Codec not found";  
    CleanupFFmpeg();  
    return false;  
  }  
    
  // Allocate codec context  
  codec_ctx_ = avcodec_alloc_context3(codec);  
  if (!codec_ctx_) {  
    LOG_ERROR << "Failed to allocate codec context";  
    CleanupFFmpeg();  
    return false;  
  }  
    
  // Copy codec parameters to context  
  ret = avcodec_parameters_to_context(codec_ctx_, codec_params);  
  if (ret < 0) {  
    LOG_ERROR << "Failed to copy codec parameters";  
    CleanupFFmpeg();  
    return false;  
  }  
    
  // Open codec  
  ret = avcodec_open2(codec_ctx_, codec, nullptr);  
  if (ret < 0) {  
    LOG_ERROR << "Failed to open codec";  
    CleanupFFmpeg();  
    return false;  
  }  
    
  // Allocate frames  
  frame_ = av_frame_alloc();  
  frame_rgb_ = av_frame_alloc();  
  if (!frame_ || !frame_rgb_) {  
    LOG_ERROR << "Failed to allocate frames";  
    CleanupFFmpeg();  
    return false;  
  }  
    
  // Allocate packet  
  packet_ = av_packet_alloc();  
  if (!packet_) {  
    LOG_ERROR << "Failed to allocate packet";  
    CleanupFFmpeg();  
    return false;  
  }  
    
  LOG_INFO << "FFmpeg initialized successfully. Video: "   
           << codec_ctx_->width << "x" << codec_ctx_->height;  
    
  return true;  
}  
  
void RtspCamera::CleanupFFmpeg() {  
  if (sws_ctx_) {  
    sws_freeContext(sws_ctx_);  
    sws_ctx_ = nullptr;  
  }  
    
  if (packet_) {  
    av_packet_free(&packet_);  
  }  
    
  if (frame_rgb_) {  
    av_frame_free(&frame_rgb_);  
  }  
    
  if (frame_) {  
    av_frame_free(&frame_);  
  }  
    
  if (codec_ctx_) {  
    avcodec_free_context(&codec_ctx_);  
  }  
    
  if (format_ctx_) {  
    avformat_close_input(&format_ctx_);  
  }  
    
  LOG_INFO << "FFmpeg resources cleaned up";  
}  
  
void RtspCamera::DecodingThread() {  
  LOG_INFO << "Decoding thread started for camera: " << config_.camera_name;  
    
  while (running_) {  
    int ret = av_read_frame(format_ctx_, packet_);  
      
    if (ret < 0) {  
      if (ret == AVERROR_EOF) {  
        LOG_WARN << "End of stream reached";  
        break;  
      } else if (ret == AVERROR(EAGAIN)) {  
        // Temporary error, retry  
        std::this_thread::sleep_for(std::chrono::milliseconds(10));  
        continue;  
      } else {  
        char errbuf[AV_ERROR_MAX_STRING_SIZE];  
        av_strerror(ret, errbuf, sizeof(errbuf));  
        LOG_ERROR << "Error reading frame: " << errbuf;  
        break;  
      }  
    }  
      
    // Check if packet belongs to video stream  
    if (packet_->stream_index == video_stream_index_) {  
      if (!DecodeFrame(packet_)) {  
        LOG_ERROR << "Failed to decode frame";  
      }  
    }  
      
    av_packet_unref(packet_);  
  }  
    
  LOG_INFO << "Decoding thread stopped for camera: " << config_.camera_name;  
}  
  
bool RtspCamera::DecodeFrame(AVPacket* packet) {  
  // Send packet to decoder  
  int ret = avcodec_send_packet(codec_ctx_, packet);  
  if (ret < 0) {  
    LOG_ERROR << "Error sending packet to decoder";  
    return false;  
  }  
    
  // Receive decoded frame  
  while (ret >= 0) {  
    ret = avcodec_receive_frame(codec_ctx_, frame_);  
      
    if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {  
      return true;  
    } else if (ret < 0) {  
      LOG_ERROR << "Error receiving frame from decoder";  
      return false;  
    }  
      
    // Create output data  
    auto output_data = std::make_shared<CameraImageData>();  
      
    // Convert and fill data  
    if (ConvertFrame(frame_, output_data)) {  
      // Fill metadata  
      output_data->device_id = config_.gpu_id;  
      output_data->camera_name = config_.camera_name;  
      output_data->camera_manufactor = config_.camera_manufactor;  
      output_data->lens_type = config_.lens_type;  
      output_data->mode = config_.img_mode;  
      output_data->width = codec_ctx_->width;  
      output_data->height = codec_ctx_->height;  
      output_data->timestamp = airos::base::TimeUtil::GetCurrentTime();
      output_data->sequence_num = sequence_num_++;  
        
      // Send data via callback  
      if (image_sender_) {  
        image_sender_(output_data);  
      }  
    }  
  }  
    
  return true;  
}  
  
bool RtspCamera::ConvertFrame(  
    AVFrame* frame, std::shared_ptr<CameraImageData>& output_data) {  
  std::lock_guard<std::mutex> lock(mutex_);  
    
  // Determine output format based on config  
  AVPixelFormat out_format;  
  
  // [修复] 删除了 unused variable: int num_channels; 
    
  switch (config_.img_mode) {  
    case Color::RGB:  
      out_format = AV_PIX_FMT_RGB24;  
      break;  
    case Color::BGR:  
      out_format = AV_PIX_FMT_BGR24;  
      break;  
    case Color::GRAY:  
      out_format = AV_PIX_FMT_GRAY8;  
      break;  
    default:  
      LOG_ERROR << "Unsupported image mode";  
      return false;  
  }  
    
  // Initialize SWS context if needed  
  if (!sws_ctx_ ||   
      frame->width != codec_ctx_->width ||   
      frame->height != codec_ctx_->height) {  
    if (sws_ctx_) {  
      sws_freeContext(sws_ctx_);  
    }  
      
    sws_ctx_ = sws_getContext(  
        frame->width, frame->height, static_cast<AVPixelFormat>(frame->format),  
        frame->width, frame->height, out_format,  
        SWS_BILINEAR, nullptr, nullptr, nullptr);  
      
    if (!sws_ctx_) {  
      LOG_ERROR << "Failed to create SWS context";  
      return false;  
    }  
  }  
    
  // Allocate Image8U  
  output_data->image = std::make_shared<Image8U>(  
      frame->width, frame->height, config_.img_mode);  
    
  // Setup frame_rgb buffer  
  int ret = av_image_fill_arrays(  
      frame_rgb_->data, frame_rgb_->linesize,  
      output_data->image->mutable_host_data(),  
      out_format, frame->width, frame->height, 1);  
    
  if (ret < 0) {  
    LOG_ERROR << "Failed to fill image arrays";  
    return false;  
  }  
    
  // Convert frame  
  sws_scale(  
      sws_ctx_, frame->data, frame->linesize, 0, frame->height,  
      frame_rgb_->data, frame_rgb_->linesize);  
    
  return true;  
}  
  
// Register the camera with the factory  
AIROS_CAMERA_REG_FACTORY(RtspCamera, "rtsp_camera");  
  
}  // namespace device  
}  // namespace base  
}  // namespace airos
