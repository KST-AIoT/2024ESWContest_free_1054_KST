#include <AD9850.h>
#include <LapX9C10X.h>
#include <AltSoftSerial.h>

#define WCLK	13
#define FUUD	12
#define DATA	11
#define RESET	10
#define INC 7
#define UD 6
#define CS 5

AltSoftSerial altSerial; // RX 8번, 주황색 TX 9번
LapX9C10X pot(INC, UD, CS, LAPX9C10X_X9C104);

String msg;

double trimFreq = 124999500;

int phase = 0;
double freq = 50;
int potval = 99;

void setup() {
  Serial.begin(9600);
  altSerial.begin(9600);
  Serial.println("Starting");
  DDS.begin(WCLK, FUUD, DATA, RESET);
  DDS.calibrate(trimFreq);
  DDS.up();
  DDS.setfreq(freq, phase);
  delay(1000);
  pot.begin(potval);
  delay(5000);
  Serial.println("Start");
}

void loop(){
  if (altSerial.available() > 0) {
    String str = altSerial.readString();
    Serial.println(str);
    if (str.startsWith("P")) {
      potval = str.substring(1).toInt();
      pot.set(potval);
      msg = "Potentio set to ";
      msg += potval;
      Serial.println(msg);
      altSerial.println(msg);
    } else if (str.startsWith("F")) {
      freq = str.substring(1).toDouble();
      DDS.setfreq(freq, phase);
      msg = "Freq set to ";
      msg += freq;
      Serial.println(msg);
      altSerial.println(msg);
    }
  }
}