#define PCA9685_SERIAL_DEBUG

#include <PCA9685.h>

#include <WiFiClientSecure.h>
#include <ESP8266WiFi.h>
#include <WiFiServer.h>
#include <WiFiClient.h>
#include <ESP8266WiFiMulti.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <ESP8266mDNS.h>

#include "config.h"

// Command flags
#define PWM_CMD  126 // 0x7e

// Prototypes
int scan_i2c();
int read2b(byte *buf, int start);
void printWifiStatus();
void parse_pwm(byte* buf, int start, int total);



// no-cost stream operator as described at 
// http://arduiniana.org/libraries/streaming/
template<class T>
inline Print &operator <<(Print &obj, T arg)
{  
  obj.print(arg); 
  return obj; 
}


/* inline functions */
inline int max ( int a, int b ) { return a > b ? a : b; }
inline int min ( int a, int b ) { return a > b ? b : a; }


 
int status = WL_IDLE_STATUS;

unsigned int localPort = 5555;      // local port to listen for UDP packets

byte buf[512]; //buffer to hold incoming packets


int pca_count;
int* pin_values;
int* pca_address;
//PCA9685* pca;

PCA9685 pca[] = {
  PCA9685(0x40, PCA9685_MODE_N_DRIVER, 800),
  PCA9685(0x41, PCA9685_MODE_N_DRIVER, 800),
  PCA9685(0x42, PCA9685_MODE_N_DRIVER, 800),
  PCA9685(0x43, PCA9685_MODE_N_DRIVER, 800),
  PCA9685(0x44, PCA9685_MODE_N_DRIVER, 800)
};

int pwm_max = PCA9685_MAX_VALUE;
int pwm_min = 0;


WiFiUDP Udp;

void setup()
{

  // Open serial communications
  Serial.begin(115200);

  
  // Assemble hostname
  String config_name = "Netlight-Ctrl-" + String(ESP.getChipId(), HEX);
  char hostname[15];  
  config_name.toCharArray(hostname, 15);

  // Start mDNS and DNS-SD
  if (!MDNS.begin(hostname)) {
    Serial << "Error setting up MDNS responder!";
  }
  Serial << "mDNS responder started\n";
  
  // Announce controller udp service on localPort
  MDNS.addService("netlight-ctrl", "udp", localPort);


  // set up I2C
  Wire.begin(12, 14);

  // Scan I2C-Bus
  pca_count = scan_i2c();
  //pca_count = 2;

  // Initialize PWM value buffer
  
  pin_values = (int*) malloc(pca_count * 15 * sizeof(int));  

  // set up pca pwm boards
  for(int i = 0; i < pca_count; i++){
    Serial << "Board #" << i+1 << "set up.\n";
    //pca[i] = PCA9685(pca_address[i], PCA9685_MODE_N_DRIVER, 800);
    pca[i].setup();
  }


  WiFi.disconnect();

  delay(100);
  
  WiFi.mode(WIFI_AP);
  // setting up Station AP
  // WiFi.begin(ssid, pass);
  WiFi.softAP(APssid);


  printWifiStatus();

  Serial << "Connected to WiFi.\n";

  Udp.begin(localPort);
  Serial << "Udp server started at port " << localPort << "\n";
}

void loop()
{
  int noBytes = Udp.parsePacket();
  
  if ( noBytes ) {

    // We've received a packet, read the data from it
    Udp.read(buf,noBytes); // read the packet into the buffer


    //display_packet(buf, noBytes);
    
    int cmd = read2b(buf, 0);
    //Serial << "Command ";
    //Serial.println(cmd, HEX);
    switch(cmd){
      case PWM_CMD:
        //Serial.println("pwm cmd");
        parse_pwm(buf, 2, noBytes);
        break;
      default:
        Serial.println("cmd n/a");
        break;
    }
  }
}

void display_packet(byte *buf, int noBytes){
    Serial.print(millis() / 1000);
    Serial.print(":Packet of ");
    Serial.print(noBytes);
    Serial.print(" received from ");
    Serial.print(Udp.remoteIP());
    Serial.print(":");
    Serial.println(Udp.remotePort());
  
    String received_packet = "";
    for (int i=1;i<=noBytes;i++)
    {
      Serial.print(buf[i-1],HEX);
      received_packet = received_packet + char(buf[i - 1]);
      if (i % 32 == 0)
      {
        Serial.println();
      }
      else Serial.print(' ');
    } // end for
        
    Serial.println();
    
    Serial.println(received_packet);
    Serial.println();
}

int read2b(byte *buf, int start) {
  return 256*buf[start] + buf[start+1];
}

void parse_pwm(byte* buf, int start, int total){
  for(byte i = 0; i < pca_count*15; i++){
      pin_values[i] = min(pwm_max, read2b(buf, start+(2*i)));
      
    //Serial << "Setting Board #" << i/15 << " Pin #" << i%15 << " to " << pin_values[i] << "\n";
    pca[i/15].getPin(i%15).setValue(pin_values[i]);
    
    //analogWrite(pins[i], );
  }
  for(int i = 0; i < pca_count; i++){
    //Serial << "Writing to Board #" << i << "\n";
    pca[i].writeAllPins();
  }
}

void printWifiStatus() {
  // print the SSID of the network you're attached to:
  Serial << "SSID: " <<  WiFi.SSID() << "\n";
  IPAddress ip = WiFi.softAPIP();
  Serial << "IP Address: " << ip << "\n";
  WiFi.printDiag(Serial);
}

int scan_i2c() {
  byte error, address;
  int nDevices;

  Serial.println("Scanning i2c-Bus...");

  nDevices = 0;
  for(address = 1; address < 127; address++ ) 
  {
    // The i2c_scanner uses the return value of
    // the Write.endTransmisstion to see if
    // a device did acknowledge to the address.
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0 && address != 112) // filter pca-broadcast
    {
      Serial << "I2C device found at address 0x";
      if (address<16) 
        Serial << "0";
      Serial.print(address,HEX);
      Serial << "\n";
      nDevices++;
    }
    else if (error==4) 
    {
      Serial.print("Unknow error at address 0x");
      if (address<16) 
        Serial.print("0");
      Serial.println(address,HEX);
    }    
  }
  if (nDevices == 0)
    Serial.println("No I2C devices found\n");

  return nDevices;
}

