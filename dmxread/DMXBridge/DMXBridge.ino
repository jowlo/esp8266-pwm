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

// Prototypes
void gotDMXCallback(int slots);
void send_packet();


#define PWM_CMD  126 // 0x7e


WiFiUDP Udp;


const int DMX_LED = 14;
const int ACTIVE_LED = 16;
const int ACTIVE_SWITCH = 12;
const int PACKET_DELAY = 20;

int got_dmx = 0;
int got_dmx_time = 0;
int active = 0;
int last_packet_time = 0;


IPAddress broadcast_ip, localip, remoteip;

unsigned int localport, remoteport;

void setup() {
  

  // Setup outputs and inputs
  pinMode(BUILTIN_LED, OUTPUT);

  
  pinMode(DMX_LED, OUTPUT);
  pinMode(ACTIVE_LED, OUTPUT);
  pinMode(ACTIVE_SWITCH, INPUT_PULLUP);


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
  // remoteip[3] = 23;
  broadcast_ip = WiFi.localIP();
  broadcast_ip[3] = 255;

  /*
  Serial.begin(115200);
  Serial.println("WiFi connected");
  Serial.println("IP address (localip): ");
  Serial.println(WiFi.localIP());
  Serial.println("IP dst: ");  
  Serial.println(remoteip);
  */
  delay(1000);
}


// ***************** input callback function *************

void gotDMXCallback(int slots) {
  got_dmx = true;
  got_dmx_time = millis();
}

/************************************************************************

  The main loop checks to see if dmx input is available (got_dmx>0)
  And then reads the level of dimmer 1 to set PWM level of LED connected to pin 14
  
*************************************************************************/
void send_beacon();
int i = 0;
void loop() {
  // Read in switch
  int lastactive = active;
  active = (!digitalRead(ACTIVE_SWITCH));
  
  digitalWrite(ACTIVE_LED, active);
  
  if(got_dmx_time > (millis() - 200)){
    digitalWrite(DMX_LED, HIGH);
  } else {
    digitalWrite(DMX_LED, LOW);
  }

  if (!active && lastactive){
    ESP8266DMX.clearSlots();
    send_packet();
  }

  
  if (got_dmx) {
    got_dmx = 0;
    // Send DMX over Wifi if active, but not too many packets
    if (active && last_packet_time < (millis() - PACKET_DELAY)) {
      last_packet_time = millis();
      send_packet();
    }
  }
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

void send_packet() {
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

