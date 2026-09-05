/**
 * Indriyo (ইন্দ্রিয়) - Intelligent Motorcycle ADAS Edge Streamer
 * Firmware for ESP32-CAM (AI-Thinker OV2640)
 *
 * Provides ultra-low-latency MJPEG video streaming over Wi-Fi
 * directly to the Indriyo Core AI Engine or ThrottleIQ Mobile App.
 *
 * Features:
 * - Standalone SoftAP Mode (No external Wi-Fi router needed on bike)
 * - Station Mode fallback (Can connect to motorcycle master hotspot)
 * - High-speed zero-copy MJPEG HTTP multipart stream (/stream)
 * - Snapshot capture endpoint (/capture)
 * - JSON Telemetry & Health endpoint (/status)
 * - Dynamic parameter adjustment (/control)
 * - Anti-brownout safeguard
 * - Tail-mirror horizontal flip pre-processing
 */

#include "esp_camera.h"
#include <WiFi.h>
#include "esp_timer.h"
#include "img_converters.h"
#include "Arduino.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include "esp_http_server.h"

// Define camera model
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// ================= CONFIGURATION =================
// Set to 1 for LEFT blind-spot camera, 0 for RIGHT blind-spot camera
#define IS_LEFT_CAMERA 1

#if IS_LEFT_CAMERA
  #define CAMERA_ROLE       "LEFT"
  #define AP_SSID           "Indriyo_Left_Cam"
  #define AP_PASSWORD       "indriyo1234"
  #define DEVICE_HOSTNAME   "indriyo-left"
  #define DEFAULT_HFLIP     1  // Mirror view for natural rearview display
#else
  #define CAMERA_ROLE       "RIGHT"
  #define AP_SSID           "Indriyo_Right_Cam"
  #define AP_PASSWORD       "indriyo1234"
  #define DEVICE_HOSTNAME   "indriyo-right"
  #define DEFAULT_HFLIP     1
#endif

// Uncomment to connect to a master motorcycle router/phone hotspot instead of standalone AP
// #define CONNECT_TO_STATION
// #define STA_SSID     "Indriyo_Master_AP"
// #define STA_PASSWORD "indriyo1234"

#define STREAM_PORT 81
#define HTTP_PORT   80

// Boundary delimiter for multipart MJPEG
#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t stream_httpd = NULL;
httpd_handle_t control_httpd = NULL;

unsigned long lastStatusBlink = 0;
uint32_t frameCount = 0;
uint32_t activeClients = 0;

// ================= STREAM HANDLER =================
static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t *_jpg_buf = NULL;
  char part_buf[64];

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if (res != ESP_OK) {
    return res;
  }

  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  activeClients++;

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("[Indriyo-CAM] Camera capture failed");
      res = ESP_FAIL;
      break;
    }

    if (fb->format != PIXFORMAT_JPEG) {
      bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
      esp_camera_fb_return(fb);
      fb = NULL;
      if (!jpeg_converted) {
        Serial.println("[Indriyo-CAM] JPEG compression failed");
        res = ESP_FAIL;
        break;
      }
    } else {
      _jpg_buf_len = fb->len;
      _jpg_buf = fb->buf;
    }

    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
    }
    if (res == ESP_OK) {
      size_t hlen = snprintf(part_buf, sizeof(part_buf), _STREAM_PART, _jpg_buf_len);
      res = httpd_resp_send_chunk(req, part_buf, hlen);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    }

    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if (_jpg_buf) {
      free(_jpg_buf);
      _jpg_buf = NULL;
    }

    if (res != ESP_OK) {
      break;
    }
    frameCount++;
  }

  if (activeClients > 0) activeClients--;
  return res;
}

// ================= SNAPSHOT HANDLER =================
static esp_err_t capture_handler(httpd_req_t *req) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }

  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  esp_err_t res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
  esp_camera_fb_return(fb);
  return res;
}

// ================= STATUS HANDLER =================
static esp_err_t status_handler(httpd_req_t *req) {
  char json[256];
  sensor_t *s = esp_camera_sensor_get();
  uint32_t freeHeap = esp_get_free_heap_size();
  
  snprintf(json, sizeof(json),
    "{\"system\":\"Indriyo\",\"role\":\"%s\",\"ip\":\"%s\",\"frames\":%u,\"clients\":%u,\"free_heap\":%u,\"framesize\":%d,\"hflip\":%d,\"vflip\":%d}",
    CAMERA_ROLE,
    WiFi.getMode() == WIFI_MODE_AP ? WiFi.softAPIP().toString().c_str() : WiFi.localIP().toString().c_str(),
    frameCount,
    activeClients,
    freeHeap,
    s ? s->status.framesize : -1,
    s ? s->status.hflip : -1,
    s ? s->status.vflip : -1
  );

  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, json, strlen(json));
}

// ================= CONTROL HANDLER =================
static esp_err_t control_handler(httpd_req_t *req) {
  char* buf;
  size_t buf_len;
  char variable[32] = {0,};
  char value[32] = {0,};

  buf_len = httpd_req_get_url_query_len(req) + 1;
  if (buf_len > 1) {
    buf = (char*)malloc(buf_len);
    if (httpd_req_get_url_query_str(req, buf, buf_len) == ESP_OK) {
      if (httpd_query_key_value(buf, "var", variable, sizeof(variable)) == ESP_OK &&
          httpd_query_key_value(buf, "val", value, sizeof(value)) == ESP_OK) {
      }
    }
    free(buf);
  }

  int val = atoi(value);
  sensor_t * s = esp_camera_sensor_get();
  int res = 0;

  if(!strcmp(variable, "framesize")) {
    if(s->pixformat == PIXFORMAT_JPEG) res = s->set_framesize(s, (framesize_t)val);
  } else if(!strcmp(variable, "quality")) res = s->set_quality(s, val);
  else if(!strcmp(variable, "contrast")) res = s->set_contrast(s, val);
  else if(!strcmp(variable, "brightness")) res = s->set_brightness(s, val);
  else if(!strcmp(variable, "saturation")) res = s->set_saturation(s, val);
  else if(!strcmp(variable, "hflip")) res = s->set_hmirror(s, val);
  else if(!strcmp(variable, "vflip")) res = s->set_vflip(s, val);
  else if(!strcmp(variable, "flash")) {
    digitalWrite(LED_FLASH_GPIO_NUM, val ? HIGH : LOW);
  } else {
    res = -1;
  }

  if(res) {
    return httpd_resp_send_500(req);
  }

  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, "OK", 2);
}

// ================= SERVER INITIALIZATION =================
void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = HTTP_PORT;
  config.ctrl_port = HTTP_PORT;

  httpd_uri_t capture_uri = {
    .uri       = "/capture",
    .method    = HTTP_GET,
    .handler   = capture_handler,
    .user_ctx  = NULL
  };

  httpd_uri_t status_uri = {
    .uri       = "/status",
    .method    = HTTP_GET,
    .handler   = status_handler,
    .user_ctx  = NULL
  };

  httpd_uri_t control_uri = {
    .uri       = "/control",
    .method    = HTTP_GET,
    .handler   = control_handler,
    .user_ctx  = NULL
  };

  if (httpd_start(&control_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(control_httpd, &capture_uri);
    httpd_register_uri_handler(control_httpd, &status_uri);
    httpd_register_uri_handler(control_httpd, &control_uri);
    Serial.printf("[Indriyo-CAM] Control server started on port %d\n", HTTP_PORT);
  }

  // High performance dedicated stream port
  config.server_port = STREAM_PORT;
  config.ctrl_port = STREAM_PORT;

  httpd_uri_t stream_uri = {
    .uri       = "/stream",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    Serial.printf("[Indriyo-CAM] Live MJPEG stream active on port %d\n", STREAM_PORT);
  }
}

// ================= SETUP =================
void setup() {
  // 1. Disable brownout detector during Wi-Fi activation to prevent boot loops
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  Serial.println("\n==========================================");
  Serial.println("  INDRIYO (ইন্দ্রিয়) - Motorcycle ADAS");
  Serial.printf("  Role: %s Blind Spot Camera\n", CAMERA_ROLE);
  Serial.println("==========================================");

  pinMode(LED_FLASH_GPIO_NUM, OUTPUT);
  pinMode(LED_STATUS_GPIO_NUM, OUTPUT);
  digitalWrite(LED_FLASH_GPIO_NUM, LOW);
  digitalWrite(LED_STATUS_GPIO_NUM, HIGH); // Active LOW on ESP32-CAM

  // 2. Camera Configuration
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Optimized for PSRAM
  if(psramFound()){
    Serial.println("[Indriyo-CAM] PSRAM detected! Setting CIF resolution (400x296) for high FPS");
    config.frame_size = FRAMESIZE_CIF;  // Ideal balance for Edge AI latency (<80ms)
    config.jpeg_quality = 12;          // 0-63 (lower = better quality)
    config.fb_count = 2;               // Double buffer
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    Serial.println("[Indriyo-CAM] No PSRAM! Falling back to QVGA (320x240)");
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 16;
    config.fb_count = 1;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  }

  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[Indriyo-CAM] Camera init failed with error 0x%x\n", err);
    while (true) {
      digitalWrite(LED_STATUS_GPIO_NUM, LOW);
      delay(150);
      digitalWrite(LED_STATUS_GPIO_NUM, HIGH);
      delay(150);
    }
  }

  // Camera sensor tuning for motorcycle rearview
  sensor_t * s = esp_camera_sensor_get();
  s->set_hmirror(s, DEFAULT_HFLIP); // Horizontal flip for mirror view
  s->set_vflip(s, 0);
  s->set_brightness(s, 1);          // Slight boost for night/dusk visibility
  s->set_contrast(s, 1);
  s->set_saturation(s, 0);
  s->set_special_effect(s, 0);
  s->set_whitebal(s, 1);
  s->set_awb_gain(s, 1);
  s->set_wb_mode(s, 0);
  s->set_exposure_ctrl(s, 1);
  s->set_aec2(s, 1);                // Night headlight compensation
  s->set_ae_level(s, 0);
  s->set_aec_value(s, 300);
  s->set_gain_ctrl(s, 1);
  s->set_agc_gain(s, 0);
  s->set_gainceiling(s, (gainceiling_t)2);
  s->set_bpc(s, 1);
  s->set_wpc(s, 1);

  // 3. Wi-Fi Setup
#ifdef CONNECT_TO_STATION
  Serial.printf("[Indriyo-CAM] Connecting to Wi-Fi SSID: %s\n", STA_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(DEVICE_HOSTNAME);
  WiFi.begin(STA_SSID, STA_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\n[Indriyo-CAM] Wi-Fi Connected!");
  Serial.printf("[Indriyo-CAM] IP Address: %s\n", WiFi.localIP().toString().c_str());
#else
  Serial.printf("[Indriyo-CAM] Creating Access Point: %s\n", AP_SSID);
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD, 1, 0, 4); // Channel 1, max 4 connections
  Serial.printf("[Indriyo-CAM] SoftAP IP: %s\n", WiFi.softAPIP().toString().c_str());
#endif

  // 4. Start HTTP & Stream Servers
  startCameraServer();

  Serial.println("\n==========================================");
  Serial.println("  INDRIYO STREAM READY");
  Serial.printf("  MJPEG Stream URL: http://%s:%d/stream\n",
    WiFi.getMode() == WIFI_MODE_AP ? WiFi.softAPIP().toString().c_str() : WiFi.localIP().toString().c_str(),
    STREAM_PORT);
  Serial.printf("  Status API URL:   http://%s:%d/status\n",
    WiFi.getMode() == WIFI_MODE_AP ? WiFi.softAPIP().toString().c_str() : WiFi.localIP().toString().c_str(),
    HTTP_PORT);
  Serial.println("==========================================\n");
}

// ================= LOOP =================
void loop() {
  // Status heartbeat
  unsigned long now = millis();
  if (now - lastStatusBlink >= 1000) {
    lastStatusBlink = now;
    // Blink LED to indicate operational state
    digitalWrite(LED_STATUS_GPIO_NUM, LOW);
    delay(20);
    digitalWrite(LED_STATUS_GPIO_NUM, HIGH);
  }
  delay(10);
}
