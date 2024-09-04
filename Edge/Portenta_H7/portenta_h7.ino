#include "Arduino.h"
#include "stm32h7xx_hal.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Before use, change the WIFI INFO and MQTT Broker Server IP
#define DEFINED_SSID "ID"
#define DEFINED_PASS "PASSWORD"
#define DEFINED_SERV "SERV_IP"

#define NUM_FREQ    1
#define NUM_SAMPLES 3600
#define UNOSERIAL Serial1
#define MQTTSIZE 65535
#define JSONSIZE 60000

ADC_HandleTypeDef hadc1;
ADC_HandleTypeDef hadc2;
TIM_HandleTypeDef htim;

uint16_t len;
WiFiClient espClient;
String message;
PubSubClient client(espClient);

uint32_t* frequency;
uint32_t sampletime;
uint32_t potentiometer;
uint16_t samples1[NUM_SAMPLES];
uint16_t samples2[NUM_SAMPLES];
uint16_t delayarr[3];
uint32_t reqtime;
uint32_t reqtype;
int num_freq;

char ssid[] = DEFINED_SSID;
char pass[] = DEFINED_PASS;
char mqtt_server[] = DEFINED_SERV;

volatile uint32_t startTime;
volatile uint32_t endTime;
uint32_t potval;
uint32_t frqval;
char jsonString[JSONSIZE];

// 입력된 ssid, 패스워드로 와이파이 연결
void wificonnect() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

// MQTT 서버에 연걸하기
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "PortentaH7";
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe("KST/REQUEST"); // 서버에서 받는건 KST/REQUEST
      // client.publish("KST/DATA", "portenta ready"); // 서버에 보내는건 KST/DATA

    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

// subscribe한 토픽 메세지가 오면 실행하는 함수
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.print ("length :");
  Serial.println(length);
  // byte* 배열이 들어오기 때문에 문자열로 바꿔서 delay로 바꿔주야 할듯
  String payloadstr = "";
  for (unsigned int i = 0; i < length; i++) {
    payloadstr += (char)payload[i];
  }

  DynamicJsonDocument doc(500);

  DeserializationError error = deserializeJson(doc, payloadstr);

  if (doc.containsKey("frequencies")) {
    
    reqtime = doc["request_time"];
    reqtype = doc["request_type"];
    JsonArray jsonfreq = doc["frequencies"];

    Serial.print("request_time:");
    Serial.println(reqtime);
    Serial.print("request_type:");
    Serial.println(reqtype);
    Serial.print("frequencies:");

    num_freq = jsonfreq.size();
    frequency = (uint32_t *)malloc(sizeof(uint32_t) * num_freq);

    for (int i = 0; i < num_freq; i++) {
      frequency[i] = jsonfreq[i];
      Serial.print(frequency[i]);
      Serial.print(" ");
    }

    Serial.println("");
    Serial.println("Starting measurement");

    sampleall();

    free(frequency);
    Serial.println("SAMPLING DONE");
  } if (doc.containsKey("DELAY")){
    Serial.println("Starting pump"); 
    JsonArray delayArray = doc["DELAY"];
    for (int i = 0; i < 3; i++) {
      delayarr[i] = delayArray[i];
    }
    relay();
  }
}

void relay() {
  HAL_GPIO_WritePin(GPIOH, GPIO_PIN_15, GPIO_PIN_SET);
  delayMicroseconds(delayarr[0]);
  HAL_GPIO_WritePin(GPIOH, GPIO_PIN_15, GPIO_PIN_RESET);

  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_1, GPIO_PIN_SET);
  delayMicroseconds(delayarr[1]);
  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_1, GPIO_PIN_RESET);

  HAL_GPIO_WritePin(GPIOJ, GPIO_PIN_11, GPIO_PIN_SET);
  delayMicroseconds(delayarr[2]);
  HAL_GPIO_WritePin(GPIOJ, GPIO_PIN_11, GPIO_PIN_RESET);
}

void send_data(int i) {  // int i를 받아서 해당 인덱스의 값을 처리
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // JSON 문자열 시작
  snprintf(jsonString, JSONSIZE, "{");
  
  // req_time 값 추가
  strcat(jsonString, "\"req_time\":");
  char buffer[10];
  snprintf(buffer, sizeof(buffer), "%d", reqtime);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  // req_type 값 추가
  strcat(jsonString, "\"req_type\":");
  snprintf(buffer, sizeof(buffer), "%d", reqtype);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  // freq 배열 추가
  strncat(jsonString, "\"frequency\":[", JSONSIZE - strlen(jsonString) - 1);
  for (int j = 0; j < num_freq; j++) {
      snprintf(buffer, sizeof(buffer), "%d", frequency[j]);
      strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
      if (j < num_freq - 1) strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);
  }
  strncat(jsonString, "],", JSONSIZE - strlen(jsonString) - 1);

  // freq 값 추가
  strncat(jsonString, "\"target_freq\":", JSONSIZE - strlen(jsonString) - 1);
  snprintf(buffer, sizeof(buffer), "%d", frequency[i]);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  // v_0 배열 추가
  strncat(jsonString, "\"v_0\":[", JSONSIZE - strlen(jsonString) - 1);
  for (int j = 0; j < NUM_SAMPLES; j++) {
      snprintf(buffer, sizeof(buffer), "%d", samples1[j]);
      strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
      if (j < NUM_SAMPLES - 1) strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);
  }
  strncat(jsonString, "],", JSONSIZE - strlen(jsonString) - 1);

  // v_1 배열 추가
  strncat(jsonString, "\"v_1\":[", JSONSIZE - strlen(jsonString) - 1);
  for (int j = 0; j < NUM_SAMPLES; j++) {
      snprintf(buffer, sizeof(buffer), "%d", samples2[j]);
      strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
      if (j < NUM_SAMPLES - 1) strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);
  }
  strncat(jsonString, "],", JSONSIZE - strlen(jsonString) - 1);

  // time 값 추가
  strncat(jsonString, "\"time\":", JSONSIZE - strlen(jsonString) - 1);
  snprintf(buffer, sizeof(buffer), "%d", sampletime);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  // resistance 값 추가
  strncat(jsonString, "\"resistance\":", JSONSIZE - strlen(jsonString) - 1);
  snprintf(buffer, sizeof(buffer), "%d", potentiometer);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  // temperature 값 추가
  strncat(jsonString, "\"temperature\":", JSONSIZE - strlen(jsonString) - 1);
  snprintf(buffer, sizeof(buffer), "%d", 25);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, "}", JSONSIZE - strlen(jsonString) - 1);

  // 여기서 jsonString을 전송하거나 사용할 수 있습니다
  // Serial.println(strlen(jsonString));
  // Serial.print("Message ");
  // Serial.print(i);
  // Serial.println(": ");
  
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  int result = client.publish("KST/DATA", jsonString);
  while (!result) {
      Serial.println("Failed to publish message");
      Serial.println(strlen(jsonString));
      Serial.println(client.state());
      if (!client.connected()) {
        reconnect();
      }
      client.loop();
      result = client.publish("KST/DATA", jsonString);
  }
  Serial.println("Publish Success");
}

// 저항값 resval, 주파수 frqval에 맞게 uno에 설정 전달
void set_pot(int resval) {
  message = "P";
  message += resval;
  Serial.print("Resistance of potentiometer: ");
  Serial.println(resval);
  // P50과 같은 문자열 전달하면 50으로 만들어줌
  UNOSERIAL.println(message);
  delay(1000);
    // 우노에서 다 됐다는 신호 올때까지 기다려야 안전할듯
  while (UNOSERIAL.available()<=0);
  Serial.print("UNO Message : ");
  Serial.println(UNOSERIAL.readString());

  Serial.println("Potentiometer set complete");

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

void set_freq(uint32_t frqval) {
  message = "F";
  message += frqval;
  Serial.print("Frequancy of generator: ");
  Serial.println(frqval);
  UNOSERIAL.println(message);
  while (UNOSERIAL.available()<=0);
  Serial.print("UNO Message : ");
  Serial.print(UNOSERIAL.readString());
  delay(1000);

  Serial.println("Frequancy set complete");

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

// 릴레이모듈 제어에 쓰는 핀 H15, K1, J11
void MX_GPIO_Init(void) {
  __HAL_RCC_GPIOH_CLK_ENABLE();
  Serial.println("__HAL_RCC_GPIOH_CLK_ENABLE set");
  __HAL_RCC_GPIOK_CLK_ENABLE();
  Serial.println("__HAL_RCC_GPIOK_CLK_ENABLE set");
  __HAL_RCC_GPIOJ_CLK_ENABLE();
  Serial.println("__HAL_RCC_GPIOJ_CLK_ENABLE set");

  GPIO_InitTypeDef GPIO_InitStruct = {0};
  Serial.println("GPIO_InitTypeDef set");

  GPIO_InitStruct.Pin = GPIO_PIN_15;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_MEDIUM;
  HAL_GPIO_Init(GPIOH, &GPIO_InitStruct);
  Serial.println("GPIOH set");

  GPIO_InitStruct.Pin = GPIO_PIN_1;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_MEDIUM;
  HAL_GPIO_Init(GPIOK, &GPIO_InitStruct);
  Serial.println("GPIOK set");

  GPIO_InitStruct.Pin = GPIO_PIN_11;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_MEDIUM;
  HAL_GPIO_Init(GPIOJ, &GPIO_InitStruct);
  Serial.println("GPIOJ set");

  HAL_GPIO_WritePin(GPIOH, GPIO_PIN_15, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_1, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOJ, GPIO_PIN_11, GPIO_PIN_RESET);
}

// adc1(PA0_C), adc2(PA1_C) 핀 설정
void adcSetup() {
    __HAL_RCC_ADC12_CLK_ENABLE();

    hadc1.Instance = ADC1;
    hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
    hadc1.Init.Resolution = ADC_RESOLUTION_12B;
    hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
    hadc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
    hadc1.Init.LowPowerAutoWait = DISABLE;
    hadc1.Init.ContinuousConvMode = ENABLE;
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    hadc1.Init.ConversionDataManagement = ADC_CONVERSIONDATA_DR;
    hadc1.Init.Overrun = ADC_OVR_DATA_PRESERVED;
    hadc1.Init.LeftBitShift = ADC_LEFTBITSHIFT_NONE;
    hadc1.Init.OversamplingMode = DISABLE;

    if (HAL_ADC_Init(&hadc1) != HAL_OK) {
        Serial.println("ADC1 initialization failed");
        Error_Handler(__FILE__, __LINE__);
    }

    hadc2.Instance = ADC2;
    hadc2.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
    hadc2.Init.Resolution = ADC_RESOLUTION_12B;
    hadc2.Init.ScanConvMode = ADC_SCAN_DISABLE;
    hadc2.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
    hadc2.Init.LowPowerAutoWait = DISABLE;
    hadc2.Init.ContinuousConvMode = ENABLE;
    hadc2.Init.DiscontinuousConvMode = DISABLE;

    hadc2.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    hadc2.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    hadc2.Init.ConversionDataManagement = ADC_CONVERSIONDATA_DR;
    hadc2.Init.Overrun = ADC_OVR_DATA_PRESERVED;
    hadc2.Init.LeftBitShift = ADC_LEFTBITSHIFT_NONE;
    hadc2.Init.OversamplingMode = DISABLE;

    if (HAL_ADC_Init(&hadc2) != HAL_OK) {
        Serial.println("ADC2 initialization failed");
        Error_Handler(__FILE__, __LINE__);
    }

    ADC_ChannelConfTypeDef sConfig = {0};
    sConfig.Channel = ADC_CHANNEL_0;
    sConfig.Rank = ADC_REGULAR_RANK_1;
    sConfig.SamplingTime = ADC_SAMPLETIME_810CYCLES_5;
    sConfig.SingleDiff = ADC_SINGLE_ENDED;
    sConfig.OffsetNumber = ADC_OFFSET_NONE;
    sConfig.Offset = 0;
    if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK) {
        Serial.println("ADC1 channel configuration failed");
        Error_Handler(__FILE__, __LINE__);
    }

    sConfig.Channel = ADC_CHANNEL_1;
    if (HAL_ADC_ConfigChannel(&hadc2, &sConfig) != HAL_OK) {
        Serial.println("ADC2 channel configuration failed");
        Error_Handler(__FILE__, __LINE__);
    }
}

// 전압 측정후 받은 주파수 배열 안에다 저장
void sampleADC() {
    __disable_irq();
    HAL_ADC_Start(&hadc1);
    HAL_ADC_Start(&hadc2);
    for (int i = 0; i < NUM_SAMPLES; i++) {
        HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);
        samples1[i] = HAL_ADC_GetValue(&hadc1);
        HAL_ADC_PollForConversion(&hadc2, HAL_MAX_DELAY);
        samples2[i] = HAL_ADC_GetValue(&hadc2);
    }
    HAL_ADC_Stop(&hadc1);
    HAL_ADC_Stop(&hadc2);
    __enable_irq();
}

void printADC() {
  for (int i = 0; i < NUM_SAMPLES; i+=500) {
    Serial.print(samples1[i]);
    Serial.print(" ");
    Serial.println(samples2[i]);
  }
  
  uint32_t timeTaken = endTime - startTime;
  float sps = (float)NUM_SAMPLES / ((float)timeTaken / 1000000);
  Serial.print("Samples Per Second (SPS): ");
  Serial.println(sps);
}

// 전압비 1:1 만들어주는 코드
void autosacle_pot() {
  set_freq(0);

  __disable_irq();
  HAL_ADC_Start(&hadc1);
  HAL_ADC_Start(&hadc2);
  HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);
  uint16_t v1 = HAL_ADC_GetValue(&hadc1);
  HAL_ADC_PollForConversion(&hadc2, HAL_MAX_DELAY);
  uint16_t v2 =  HAL_ADC_GetValue(&hadc2);
  HAL_ADC_Stop(&hadc1);
  HAL_ADC_Stop(&hadc2);
  __enable_irq();
  // 전압 단 한번 재고 나서

  Serial.print(v1);
  Serial.print(" ");
  Serial.println(v2);
  // 비율에 맞도록 가변저항 조절
  potval = potval * v2 / (v1 - v2);
  Serial.print("Potentiometer set to ");
  Serial.println(potval);

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

// sampleADC를 num_freq번 실행, 온도, 주파수, 시간, 저항정보 모두 저장
void sampleall() {
  static uint32_t lastCheckedFreq = 0;  // 마지막으로 체크한 주파수를 저장
  static uint32_t currentSamplingTime = 0;  // 현재 설정된 샘플링 시간을 저장

  for (int i = 0; i < num_freq; i++) {
    if (!client.connected()) {
      reconnect();
    }
    client.loop();

    if (frequency[i] != lastCheckedFreq) {  // 이전 주파수와 다를 때만 조정
      lastCheckedFreq = frequency[i];

    
      uint32_t newSamplingTime;
      if (frequency[i] >= 10000) {
        newSamplingTime = ADC_SAMPLETIME_16CYCLES_5;
      } else if (frequency[i] >= 100) {
        newSamplingTime = ADC_SAMPLETIME_64CYCLES_5;
      } else {
        newSamplingTime = ADC_SAMPLETIME_810CYCLES_5;
      }


      if (newSamplingTime != currentSamplingTime) {  // 새로운 샘플링 시간이 현재와 다를 때만 설정
        currentSamplingTime = newSamplingTime;

        ADC_ChannelConfTypeDef sConfig = {0};
        sConfig.Channel = ADC_CHANNEL_0;
        sConfig.Rank = ADC_REGULAR_RANK_1;
        sConfig.SingleDiff = ADC_SINGLE_ENDED;
        sConfig.OffsetNumber = ADC_OFFSET_NONE;
        sConfig.Offset = 0;
        sConfig.SamplingTime = currentSamplingTime;

        if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK) {
          Serial.println("ADC1 channel configuration failed");
          Error_Handler(__FILE__, __LINE__);
        }

        sConfig.Channel = ADC_CHANNEL_1;
        if (HAL_ADC_ConfigChannel(&hadc2, &sConfig) != HAL_OK) {
          Serial.println("ADC2 channel configuration failed");
          Error_Handler(__FILE__, __LINE__);
        }

        Serial.print("ADC_SAMPLE CYCLE CHANGED AT FREQ: ");
        Serial.println(lastCheckedFreq);
      }
    }

    // autosacle_pot();
    potentiometer = potval;
    // set_pot(potval);
    set_freq(frequency[i]);
    
    startTime = micros();
    sampleADC();
    endTime = micros();
    sampletime = endTime - startTime;

    send_data(i);
    Serial.print("END [");
    Serial.print(i+1);
    Serial.print("/");
    Serial.print(num_freq);
    Serial.println("]\n");
  }
}

void Error_Handler(const char *file, int line) {
    Serial.print("Error in file: ");
    Serial.print(file);
    Serial.print(" at line: ");
    Serial.println(line);
    while (1) {
      digitalWrite(LEDR, LOW);
      delay(500);
      digitalWrite(LEDR, HIGH);
      delay(500);
    }
}

void SystemClock_Config(void) {
}

void setup() {
  Serial.begin(115200);
  UNOSERIAL.begin(9600); // 주황색이 아래
  delay(3000);

  Serial.println("HAL_Init start");
  HAL_Init();
  Serial.println("HAL_Init end");

  Serial.println("SystemClock_Config start");
  SystemClock_Config();
  Serial.println("SystemClock_Config end");

  Serial.println("MX_GPIO_Init start");
  MX_GPIO_Init();
  Serial.println("MX_GPIO_Init end");

  Serial.println("adcSetup start");
  adcSetup();
  Serial.println("adcSetup end");

  // 와이파이, MQTT 서버 연결
  Serial.println("wificonnect start");
  wificonnect();
  Serial.println("wificonnect end");

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  client.setKeepAlive(5);
  client.setSocketTimeout(10);
  Serial.print("setbuffer:");
  Serial.println(client.setBufferSize(MQTTSIZE));  // 버퍼 크기를 1024바이트로 증가
  // 전압 측정 후 비율 맞도록 가변저항값 조절
}

void loop() {
  // 서버연결 끊어졌으면 reconnect
  // loop마다 client.loop 지속적으로 해줘야 연결 유지됨
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  if (Serial.available() > 0) {
    Serial.readString();
    reqtime = 123123;
    reqtype = 0;
    num_freq = NUM_FREQ;
    frequency = (uint32_t *)malloc(sizeof(uint32_t));
    
    for (int i = 0; i < num_freq; i++) {
      frequency[i] = (1000 * (i + 1));
    }
    sampleall();
    free(frequency);
    
  }
}

