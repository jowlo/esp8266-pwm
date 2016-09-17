/**************************************************************************

DMX Bridge for Netlights.

Simply reads in all 512 DMX channels and sends them over Wifi (UDP)
to a Netlights receiver.


Based upon LXESP8266DMX (github.com/claudeheintz/LXESP8266DMX) and 
WifiManager (github.com/tzapu/WiFiManager).

**************************************************************************/

#include <LXESP8266UARTDMX.h>
#include <ESP8266WiFi.h>
#include <DNSServer.h>            //Local DNS Server used for redirecting all requests to the configuration portal
#include <ESP8266WebServer.h>     //Local WebServer used to serve the configuration portal
#include <WiFiManager.h>          //https://github.com/tzapu/WiFiManager WiFi Configuration Magic
#include <WiFiUdp.h>
#include <ESP8266mDNS.h>
#include <Ticker.h>
#include "RGBConverter.h"

#include "config.h"

RGBConverter Color;
Ticker ticker;
WiFiUDP Udp;

// Prototypes
void gotDMXCallback(int slots);
void send_packet();

// Command to send to Controller
#define PWM_CMD  126 // 0x7e

// Define output pins
const int DMX_LED = 14;
const int ACTIVE_LED = 16;
const int ACTIVE_SWITCH = 12;
const int PACKET_DELAY = 20;

// Variables
int got_dmx = 0;
int got_dmx_time = 0;
int active = 0;
int last_packet_time = 0;


IPAddress remoteip;
unsigned int remoteport;
unsigned int localport = 5555;

/* 
 *  Typedef enum for different DMX modes.
 *  
 *  First channel (0) sets the mode:
 *  0-50:   RGB_SINGLE
 *          Each strip has 3 channels with RGB controlled individually
 *          
 *  50-100: HSV_ALL
 *          Channel 1: Hue
 *          Channel 2: Saturation
 *          Channel 3: Value
 *          
 *  > 100:  HSV_SINGLE
 *          Channel 1: Hue
 *          Channel 2: Saturation
 *          Channel 3 - 13: Value per Strip;
 */
typedef enum {RGB_SINGLE, HSV_ALL, HSV_SINGLE} dmx_mode;



// CALLBACKS

// Blink both lights during configuration
void config_blink() {
  int light = digitalRead(ACTIVE_LED);
  digitalWrite(ACTIVE_LED, !light);
  digitalWrite(DMX_LED, !light);
}

// Blink lights during connecting
void connecting_blink() {
  digitalWrite(ACTIVE_LED, !digitalRead(ACTIVE_LED));
  digitalWrite(DMX_LED, !digitalRead(ACTIVE_LED));  
}

// Blink lights when configuration mode is entered
void configModeCallback (WiFiManager *myWiFiManager) {
  ticker.detach();
  ticker.attach(0.2, config_blink);
}

// Set DMX flag to true.
// Is called when DMX is available
void gotDMXCallback(int slots) {
  got_dmx = true;
  got_dmx_time = millis();
}


void setup() {
  
  // Assemble configuration SSID
  String config_name = "Netlight-" + String(ESP.getChipId(), HEX);
  char hostname[15];  
  config_name.toCharArray(hostname, 15);

  // Setup outputs and inputs
  pinMode(BUILTIN_LED, OUTPUT);
  pinMode(DMX_LED, OUTPUT);
  pinMode(ACTIVE_LED, OUTPUT);
  pinMode(ACTIVE_SWITCH, INPUT_PULLUP);

  // Start blinking while connecting
  ticker.attach(0.6, connecting_blink);

  // Start wifi manager (connect to old AP if present, otherwise start config)
  WiFiManager wifiManager;
  
  // Reset settings - for testing
  // wifiManager.resetSettings();

  // Disable Serial debug
  wifiManager.setDebugOutput(false);

  // Set callback when entering configuration mode (for blinking)
  wifiManager.setAPCallback(configModeCallback);

  // Set connection attempt timeout before configuration
  wifiManager.setConnectTimeout(60);
  
  // Set configuration timeout before restart
  wifiManager.setTimeout(180);
  
  // Wait for connection/configuration
  if (!wifiManager.autoConnect(hostname)){
    ESP.reset();
    delay(1000);
  }

  // Connected to Wifi, blink faster
  ticker.detach();
  ticker.attach(0.2, connecting_blink);

  // Start mDNS
  MDNS.begin(hostname);

  // Look for controller
  int n = 0;
  while(n == 0){
    n = MDNS.queryService("netlight-ctrl", "udp");
  }
  remoteip = MDNS.IP(0);
  remoteport = MDNS.port(0);

  // Found controller, stop blinking
  ticker.detach();

  // Set callback if DMX is read
  ESP8266DMX.setDataReceivedCallback(&gotDMXCallback);
  // Start DMX reading
  ESP8266DMX.startInput();
}



void loop() {
  
  // Read in switch
  int lastactive = active;
  active = (!digitalRead(ACTIVE_SWITCH));

  digitalWrite(ACTIVE_LED, active);

  // If DMX has been available in the last 200ms, keep light on.
  if(got_dmx_time > (millis() - 200)){
    digitalWrite(DMX_LED, HIGH);
  } else {
    digitalWrite(DMX_LED, LOW);
  }

  // If deactivated by switch, switch off lights.
  if (!active && lastactive){
    ESP8266DMX.clearSlots();
    send_packet();
  }

  // If DMX channels available, send them out, if enough time is passed
  if (got_dmx) {
    got_dmx = 0;
    // Send DMX over Wifi if active, but not too many packets
    if (active && last_packet_time < (millis() - PACKET_DELAY)) {
      last_packet_time = millis();
      send_packet();
    }
  }
}


dmx_mode get_mode(int i){
  if (i < 51) return RGB_SINGLE;
  if (i < 101) return HSV_ALL;
  return HSV_SINGLE;
}


void send_packet() {
  // Read mode from first channel
  dmx_mode mode = get_mode(ESP8266DMX.getSlot(1));

  // Write command bytes
  Udp.beginPacket(remoteip, localport);
  Udp.write((uint8_t)0);
  Udp.write(PWM_CMD);
  
  switch (mode){
    case RGB_SINGLE:
    {
      for(int i = 2; i < 32; i++){
        uint8_t val = ESP8266DMX.getSlot(i);
        Udp.write(val>>4);
        Udp.write(val<<4);
      }
      break;
    }
      
    case HSV_ALL:
    {
      byte rgb[3], brg[3];
      double h = ESP8266DMX.getSlot(2) / 255.0;
      double s = ESP8266DMX.getSlot(3) / 255.0;
      double l = ESP8266DMX.getSlot(4) / 255.0;

      Color.hsvToRgb(h, s, l, rgb);
      
      // Strips are Blue-Red-Green
      brg[0] = rgb[2];
      brg[1] = rgb[0];
      brg[2] = rgb[1];

      for(int i = 0; i < 30; i++){
        Udp.write(brg[i % 3] >> 4);
        Udp.write(brg[i % 3] << 4);
      }
      break;
    }
      
    case HSV_SINGLE:
    {
      byte rgb[3], brg[3];
      double h = ESP8266DMX.getSlot(2) / 255.0;
      double s = ESP8266DMX.getSlot(3) / 255.0;
      double l;
      for(int i = 0; i < 10; i++){
        l = ESP8266DMX.getSlot(4 + i) / 255.0;
        
        Color.hsvToRgb(h, s, l, rgb);
        // Strips are Blue-Red-Green
        brg[0] = rgb[2];
        brg[1] = rgb[0];
        brg[2] = rgb[1];

        for(int j = 0; j < 3; j++){
          Udp.write(brg[j] >> 4);
          Udp.write(brg[j] << 4);
        }
      }
      break;    
    }
  } // switch
  Udp.endPacket();
}

