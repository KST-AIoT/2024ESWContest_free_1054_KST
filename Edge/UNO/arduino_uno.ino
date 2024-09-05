#include <AD9850.h>         // DDS 모듈 제어용 라이브러리
#include <LapX9C10X.h>      // 가변 저항 제어용 라이브러리
#include <AltSoftSerial.h>  // 소프트웨어 시리얼 통신 라이브러리

// DDS 모듈 핀 설정
#define WCLK 13
#define FUUD 12
#define DATA 11
#define RESET 10

// 가변 저항 핀 설정
#define INC 7
#define UD 6
#define CS 5

AltSoftSerial altSerial;                       // 소프트웨어 시리얼 통신 객체
LapX9C10X pot(INC, UD, CS, LAPX9C10X_X9C104);  // 가변 저항 객체

String msg;                   // 시리얼 통신 메시지 저장용 변수
double trimFreq = 124999500;  // DDS 모듈의 보정 주파수

int phase = 0;  // 초기 위상값
double freq = 50;  // 기본 주파수 50Hz
int potval = 99;   // 가변 저항 초기값

void setup() {
  Serial.begin(9600);  
  altSerial.begin(9600);
  
  // DDS 모듈 초기화, 주파수 보정 후 작동
  DDS.begin(WCLK, FUUD, DATA, RESET);
  DDS.calibrate(trimFreq);
  DDS.up();
  DDS.setfreq(freq, phase);
  delay(1000);
  
  // 가변 저항 초기화
  pot.begin(potval);
  delay(1000);
  
  Serial.println("Start");
}

void loop(){
  // 소프트웨어 시리얼로부터 데이터가 수신된 경우
  if (altSerial.available() > 0) {
    // 버퍼에 문자열 있으면 읽고 출력
    String str = altSerial.readString();
    Serial.println(str);
    
    // 접두사가 P일때 이후 값을 저항값으로 설정 후 응답메세지 전송
    if (str.startsWith("P")) {
      potval = str.substring(1).toInt();
      pot.set(potval);
      msg = "Potentio set to " + String(potval);
      Serial.println(msg);
      altSerial.println(msg);
    
    // 접두사가 F일때 이후 값을 주파수로 설정 후 응답메세지 전송
    } else if (str.startsWith("F")) {
      freq = str.substring(1).toDouble();
      DDS.setfreq(freq, phase);
      msg = "Freq set to " + String(freq);
      Serial.println(msg);
      altSerial.println(msg);
    }
  }
}
