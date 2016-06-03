/**************************************************************************/
/*!
    @file     DMXInputTest.ino
    @author   Claude Heintz
    @license  BSD (see LXESP8266DMX LICENSE)
    @copyright 2015 by Claude Heintz

    SControl brightness of LED on GPIO14 with DMX address 1
    @section  HISTORY

    v1.00 - First release
    v1.01 - Updated for single LX8266DMX class
*/
/**************************************************************************/
#include <LXESP8266UARTDMX.h>
#include <WiFiClientSecure.h>
#include <ESP8266WiFi.h>
#include <WiFiServer.h>
#include <WiFiClient.h>
#include <ESP8266WiFiMulti.h>
#include <WiFiUdp.h>
#include "config.h"

void gotDMXCallback(int slots);


#define PWM_CMD  126 // 0x7e


WiFiUDP Udp;

int got_dmx = 0;

IPAddress broadcast_ip, localip, remoteip;

unsigned int localport, remoteport;

void setup() {
  
  pinMode(BUILTIN_LED, OUTPUT);
  pinMode(14, OUTPUT);
  ESP8266DMX.setDataReceivedCallback(&gotDMXCallback);
  delay(1000);        //avoid boot print??
  ESP8266DMX.startInput();

  /* WIFI */
  WiFi.mode(WIFI_STA);


  //WiFi.begin(ssid, password);
  WiFi.begin(ssid);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  localip = WiFi.localIP();
  localport = 5555;
  remoteport = 5555;
  remoteip = WiFi.localIP();
  remoteip[3] = 1;
  broadcast_ip = WiFi.localIP();
  broadcast_ip[3] = 255;

  /*
  Serial.println("WiFi connected");
  Serial.println("IP address (localip): ");
  Serial.println(WiFi.localIP());
  Serial.println("IP dst: ");  
  Serial.println(remote_ip);
  */
  delay(1000);
}


// ***************** input callback function *************

void gotDMXCallback(int slots) {
  got_dmx = slots;
}

/************************************************************************

  The main loop checks to see if dmx input is available (got_dmx>0)
  And then reads the level of dimmer 1 to set PWM level of LED connected to pin 14
  
*************************************************************************/
void send_beacon();
void loop() {
  if ( got_dmx ) {
    /* DMX */
    // ESP8266 PWM is 10bit 0-1024
    int a = ESP8266DMX.getSlot(1);
    analogWrite(14,2*a);
    Udp.beginPacket(remoteip, localport);
    Udp.write((uint8_t)0);
    Udp.write(PWM_CMD);
    for(int i = 1; i < 31; i++){
      uint8_t val = ESP8266DMX.getSlot(i);
      Udp.write(val>>4);
      Udp.write(val<<4);
    }
    Udp.endPacket();
  }
  delay(30);
}

void send_beacon() {
  // transmit broadcast package
  Udp.beginPacket(broadcast_ip, localport);
  Udp.write("Hello\n I am a DMX Bridge at ");
  Udp.write(broadcast_ip);
  Udp.write(":");
  Udp.write(localport);
  Udp.write(". No connection.");
  Udp.endPacket();
}

