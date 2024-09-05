#include "Arduino.h"
#include "stm32h7xx_hal.h"      // Portenta H7에 내장된 stm32h7용 라이브러리
#include <WiFi.h>               // WiFi 기능 사용을 위한 라이브러리
#include <PubSubClient.h>       // MQTT 통신을 위한 라이브러리
#include <ArduinoJson.h>        // JSON 데이터 처리 라이브러리

#define DEFINED_SSID "WIFI_SSID"        // Wi-Fi SSID
#define DEFINED_PASS "WIFI_PASSWORD"    // Wi-Fi 비밀번호
#define DEFINED_SERV "SERV_IP"          // MQTT 서버 IP 주소

#define NUM_FREQ    1           // 측정 주파수 개수 (기본값)
#define NUM_SAMPLES 3600        // 샘플링할 데이터 개수
#define UNOSERIAL Serial1       // UNO 보드간의 시리얼 통신용 객체
#define MQTTSIZE 65535          // MQTT 메시지 최대 크기 설정
#define JSONSIZE 60000          // JSON 메시지 최대 크기 설정


// STM32 보드의 ADC 핸들러
ADC_HandleTypeDef hadc1;
ADC_HandleTypeDef hadc2;
TIM_HandleTypeDef htim;

uint16_t len;                      // MQTT 메시지 길이
WiFiClient espClient;              // Wi-Fi 클라이언트 객체
String message;                    // UNO 보드와 통신할 때 사용할 문자열 변수
PubSubClient client(espClient);    // MQTT 클라이언트 객체

// 측정 시 보내는 정보
uint32_t* frequency;               // 측정하는 주파수의 목록
uint32_t sampletime;               // 측정하는 데 걸린 시간
uint32_t potentiometer;            // 측정 시 사용한 저항값
uint16_t samples1[NUM_SAMPLES];    // 측정한 전압 v_0
uint16_t samples2[NUM_SAMPLES];    // 측정한 전압 v_1

uint32_t delayarr[3];              // 모터 작동시키는 시간(밀리초)
uint32_t reqtime;                  // 요청 구별용 시작시간
uint32_t reqtype;                  // 요청의 종류 (훈련용 / 실제용)
int num_freq;                      // 측정하는 주파수의 개수

char ssid[] = DEFINED_SSID;
char pass[] = DEFINED_PASS;
char mqtt_server[] = DEFINED_SERV;

volatile uint32_t startTime;       // 샘플링 시작 시간
volatile uint32_t endTime;         // 샘플링 종료 시간
uint32_t potval;                   // 가변 저항 값
uint32_t frqval;                   // 주파수 값
char jsonString[JSONSIZE];         // 전송할 JSON 문자열 저장 변수

// Wi-Fi 연결 함수
void wificonnect() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

// MQTT 서버 연결 함수
void reconnect() {
  // 연결이 끊어졌을 때 반복하여 재시도
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "PortentaH7";
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe("KST/REQUEST");     // 측정 정보 전달받는 토픽 구독
      client.subscribe("KST/IRRIGATION");  // 모터 제어용 토픽 구독

    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

// 구독한 토픽으로부터 메시지가 오면 호출되는 콜백 함수
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.print ("length :");
  Serial.println(length);

  // 수신한 payload를 문자열로 변환
  String payloadstr = "";
  for (unsigned int i = 0; i < length; i++) {
    payloadstr += (char)payload[i];
  }

  // JSON 객체 생성 후 데이터 파싱
  DynamicJsonDocument doc(500);
  DeserializationError error = deserializeJson(doc, payloadstr);

  // KST/IRRIGATION 토픽이면 전달된 시간만큼 모터 개방
  if (strcmp(topic, "KST/IRRIGATION") == 0) {
    Serial.println("Starting pump"); 
    delayarr[0] = doc["N"];
    delayarr[1] = doc["P"];
    delayarr[2] = doc["K"];
    relay();
  
    return;
  }

  // frequencies 키가 존재하면 전압 측정 시작
  if (doc.containsKey("frequencies")) {
    
    reqtime = doc["request_time"];
    reqtype = doc["request_type"];
    JsonArray jsonfreq = doc["frequencies"];

    Serial.print("request_time:");
    Serial.println(reqtime);
    Serial.print("request_type:");
    Serial.println(reqtype);
    Serial.print("frequencies:");

    // frequencies 내 주파수 개수만큼 동적배열 생성
    num_freq = jsonfreq.size();
    frequency = (uint32_t *)malloc(sizeof(uint32_t) * num_freq);

    for (int i = 0; i < num_freq; i++) {
      frequency[i] = jsonfreq[i];
      Serial.print(frequency[i]);
      Serial.print(" ");
    }

    Serial.println("");
    Serial.println("Starting measurement");

    // 수신한 주파수에 대해 전압 샘플링
    sampleall();

    free(frequency);
    Serial.println("SAMPLING DONE");
  }
}

// 릴레이 모듈을 제어하는 함수
void relay() {
  // delayarr에 저장된 시간동안 펌프 열기
  // GPIO_PIN_RESET이 개방, GPIO_PIN_SET이 폐쇄
  HAL_GPIO_WritePin(GPIOH, GPIO_PIN_15, GPIO_PIN_RESET);
  HAL_Delay(delayarr[0]);
  HAL_GPIO_WritePin(GPIOH, GPIO_PIN_15, GPIO_PIN_SET);

  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_1, GPIO_PIN_RESET);
  HAL_Delay(delayarr[1]);
  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_1, GPIO_PIN_SET);

  HAL_GPIO_WritePin(GPIOJ, GPIO_PIN_11, GPIO_PIN_RESET);
  HAL_Delay(delayarr[2]);
  HAL_GPIO_WritePin(GPIOJ, GPIO_PIN_11, GPIO_PIN_SET);
}

// MQTT를 통해 데이터를 전송하는 함수
void send_data(int i) {  // int i를 받아서 해당 인덱스의 값을 처리
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // JSON 데이터를 생성하여 전송할 메시지 작성
  snprintf(jsonString, JSONSIZE, "{");
  
  strcat(jsonString, "\"req_time\":");
  char buffer[10];
  snprintf(buffer, sizeof(buffer), "%d", reqtime);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  strcat(jsonString, "\"req_type\":");
  snprintf(buffer, sizeof(buffer), "%d", reqtype);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  strncat(jsonString, "\"frequency\":[", JSONSIZE - strlen(jsonString) - 1);
  for (int j = 0; j < num_freq; j++) {
      snprintf(buffer, sizeof(buffer), "%d", frequency[j]);
      strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
      if (j < num_freq - 1) strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);
  }
  strncat(jsonString, "],", JSONSIZE - strlen(jsonString) - 1);

  strncat(jsonString, "\"target_freq\":", JSONSIZE - strlen(jsonString) - 1);
  snprintf(buffer, sizeof(buffer), "%d", frequency[i]);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  strncat(jsonString, "\"v_0\":[", JSONSIZE - strlen(jsonString) - 1);
  for (int j = 0; j < NUM_SAMPLES; j++) {
      snprintf(buffer, sizeof(buffer), "%d", samples1[j]);
      strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
      if (j < NUM_SAMPLES - 1) strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);
  }
  strncat(jsonString, "],", JSONSIZE - strlen(jsonString) - 1);

  strncat(jsonString, "\"v_1\":[", JSONSIZE - strlen(jsonString) - 1);
  for (int j = 0; j < NUM_SAMPLES; j++) {
      snprintf(buffer, sizeof(buffer), "%d", samples2[j]);
      strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
      if (j < NUM_SAMPLES - 1) strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);
  }
  strncat(jsonString, "],", JSONSIZE - strlen(jsonString) - 1);

  strncat(jsonString, "\"time\":", JSONSIZE - strlen(jsonString) - 1);
  snprintf(buffer, sizeof(buffer), "%d", sampletime);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  strncat(jsonString, "\"resistance\":", JSONSIZE - strlen(jsonString) - 1);
  snprintf(buffer, sizeof(buffer), "%d", potentiometer);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, ",", JSONSIZE - strlen(jsonString) - 1);

  strncat(jsonString, "\"temperature\":", JSONSIZE - strlen(jsonString) - 1);
  snprintf(buffer, sizeof(buffer), "%d", 25);
  strncat(jsonString, buffer, JSONSIZE - strlen(jsonString) - 1);
  strncat(jsonString, "}", JSONSIZE - strlen(jsonString) - 1);
  
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  delay(100);
  // 만들어진 메시지를 MQTT로 전송
  int result = client.publish("KST/DATA", jsonString);
  while (!result) {
      Serial.println("Failed to publish message");
      Serial.println(strlen(jsonString));
      Serial.println(client.state());
      if (!client.connected()) {
        reconnect();
      }
      client.loop();
      delay(100);
      result = client.publish("KST/DATA", jsonString);
  }
  Serial.println("Publish Success");
}

// 저항값 resval에 맞게 uno에 설정 전달
void set_pot(int resval) {
  message = "P";       // 접두사 P가 붙으면 뒤에 있는 값으로 저항 변경
  message += resval;
  Serial.print("Resistance of potentiometer: ");
  Serial.println(resval);
  // P50과 같은 문자열 전달하면 50으로 만들어줌
  UNOSERIAL.println(message);
  delay(1000);
  // UNO에서 변경 완료했다는 응답이 올 때까지 대기
  while (UNOSERIAL.available()<=0);
  Serial.print("UNO Message : ");
  Serial.println(UNOSERIAL.readString());

  Serial.println("Potentiometer set complete");

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

// 주파수 값 frqval을 설정하여 UNO에 전달
void set_freq(uint32_t frqval) {
  message = "F";      // 접두사 F가 붙으면 뒤에 있는 값으로 저항 변경
  message += frqval;
  Serial.print("Frequancy of generator: ");
  Serial.println(frqval);
  UNOSERIAL.println(message);
  while (UNOSERIAL.available()<=0);
  Serial.print("UNO Message : ");
  Serial.print(UNOSERIAL.readString());
  delay(500);

  Serial.println("Frequancy set complete");

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

// 릴레이모듈 제어에 쓰는 핀 H15, K1, J11
void MX_GPIO_Init(void) {
  // GPIO 클럭 활성화
  __HAL_RCC_GPIOH_CLK_ENABLE();
  Serial.println("__HAL_RCC_GPIOH_CLK_ENABLE set");
  __HAL_RCC_GPIOK_CLK_ENABLE();
  Serial.println("__HAL_RCC_GPIOK_CLK_ENABLE set");
  __HAL_RCC_GPIOJ_CLK_ENABLE();
  Serial.println("__HAL_RCC_GPIOJ_CLK_ENABLE set");

  // GPIO 핀 설정
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

  // 핀을 초기 상태로 리셋, RESET 상태가 릴레이 모듈이 켜진 상태
  HAL_GPIO_WritePin(GPIOH, GPIO_PIN_15, GPIO_PIN_SET);
  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_1, GPIO_PIN_SET);
  HAL_GPIO_WritePin(GPIOJ, GPIO_PIN_11, GPIO_PIN_SET);
}

// adc1(PA0_C), adc2(PA1_C) 핀 설정
void adcSetup() {
    __HAL_RCC_ADC12_CLK_ENABLE();

    // ADC1 설정
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

    // ADC2 설정
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
    __disable_irq();      // 인터럽트를 비활성화하여 안전하게 데이터 수집
    HAL_ADC_Start(&hadc1);
    HAL_ADC_Start(&hadc2);
    for (int i = 0; i < NUM_SAMPLES; i++) {  // NUM_SAMPLES 개수만큼 전압 측정
        HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);
        samples1[i] = HAL_ADC_GetValue(&hadc1);
        HAL_ADC_PollForConversion(&hadc2, HAL_MAX_DELAY);
        samples2[i] = HAL_ADC_GetValue(&hadc2);
    }
    HAL_ADC_Stop(&hadc1);
    HAL_ADC_Stop(&hadc2);
    __enable_irq();
}

// 샘플링 데이터를 확인하고 출력하는 함수
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

// 자동으로 전압비 1:1 맞추기 위한 함수
void autosacle_pot() {
  set_freq(0);       // 전압비 측정을 위해 DC로 설정

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

  Serial.print(v1);
  Serial.print(" ");
  Serial.println(v2);
  // 가변 저항을 자동으로 조절
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
  static uint32_t lastCheckedFreq = 0;      // 마지막으로 체크한 주파수를 저장
  static uint32_t currentSamplingTime = 0;  // 현재 설정된 샘플링 시간을 저장

  for (int i = 0; i < num_freq; i++) {
    if (!client.connected()) {
      reconnect();
    }
    client.loop();

    // 주파수가 변경되면 새로운 주파수로 설정
    if (frequency[i] != lastCheckedFreq) {
      lastCheckedFreq = frequency[i];

    
      uint32_t newSamplingTime;
      if (frequency[i] >= 10000) {
        newSamplingTime = ADC_SAMPLETIME_16CYCLES_5;
      } else if (frequency[i] >= 100) {
        newSamplingTime = ADC_SAMPLETIME_64CYCLES_5;
      } else {
        newSamplingTime = ADC_SAMPLETIME_810CYCLES_5;
      }


      // 샘플링 시간이 변경되면 ADC 재설정
      if (newSamplingTime != currentSamplingTime) {
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
    
    send_data(i);            // 샘플링 데이터를 서버로 전송
    Serial.print("END [");
    Serial.print(i+1);
    Serial.print("/");
    Serial.print(num_freq);
    Serial.println("]\n");
  }
}

// 에러 발생 시 동작을 중지하는 함수
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

// 메인 loop 함수, 지속적으로 MQTT 연결을 유지하고 서버로부터 명령을 처리
void loop() {
  // 서버연결 끊어졌으면 reconnect
  // loop마다 client.loop 지속적으로 해줘야 연결 유지됨
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // 시리얼 입력이 있으면 디폴트 주파수에 대해 샘플링 및 데이터 전송 실행
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

