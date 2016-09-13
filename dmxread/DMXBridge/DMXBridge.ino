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

#include "config.h"

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



// CALLBACKS

// Blink both lights during configuration
void config_blink() {
  digitalWrite(ACTIVE_LED, !digitalRead(ACTIVE_LED));
  digitalWrite(DMX_LED, !digitalRead(DMX_LED));
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

