#include <WiFiClientSecure.h>
#include <ESP8266WiFi.h>
#include <WiFiServer.h>
#include <WiFiClient.h>
#include <ESP8266WiFiMulti.h>
#include <WiFiUdp.h>


#include "config.h"
/*
 * 31 mar 2015
 * This sketch display UDP packets coming from an UDP client.
 * On a Mac the NC command can be used to send UDP. (nc -u 192.168.1.101 2390). 
 *
 * Configuration : Enter the ssid and password of your Wifi AP. Enter the port number your server is listening on.
 *
 */

// Command flags
#define PWM_CMD  126 // 0x7e

#define SET_CMD  127 // 0x7f
  #define SET_CMD_MIN    15 // 0x0f
  #define SET_CMD_MAX    16 // 0x10
  #define SET_CMD_REDUCE  2 // 0x02
  #define SET_CMD_CUTOFF  3 // 0x03    
  #define SET_CMD_1CH     4 // 0x04 (set to 0 disable, counting channels from 1
  #define SET_CMD_BIN     5 // 0x04 (set to 0 disable, counting channels from 1




/* inline functions */
inline int max ( int a, int b ) { return a > b ? a : b; }
inline int min ( int a, int b ) { return a > b ? b : a; }

 
int status = WL_IDLE_STATUS;

unsigned int localPort = 5555;      // local port to listen for UDP packets

byte buf[512]; //buffer to hold incoming and outgoing packets

const byte pinouts = 3;
// red, green, blue
byte pins[pinouts] = {  4, 12, 14, };

int pin_values[pinouts] = {0,0,0};

int pwm_max = 1023;
int pwm_min = 0;

int reduce = 1023;

int cutoff = 0;

int single_channel = 0;

int binary_mode = 0;

WiFiUDP Udp;

void setup()
{
  // Open serial communications and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }

  // setting up Station AP
  WiFi.begin(ssid, pass);
  
  // Wait for connect to AP
  Serial.print("[Connecting] ");
  Serial.print(ssid);
  int tries=0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    tries++;
    if (tries > 100){
      break;
    }
  }
  Serial.println();


printWifiStatus();

  Serial.println("Connected to wifi");
  Serial.print("Udp server started at port ");
  Serial.println(localPort);
  Udp.begin(localPort);
}

void loop()
{
  int noBytes = Udp.parsePacket();
  
  if ( noBytes ) {

    // We've received a packet, read the data from it
    Udp.read(buf,noBytes); // read the packet into the buffer


    //display_packet(buf, noBytes)
    
    int cmd = read2b(buf, 0);
    //Serial.print("Command ");
    //Serial.println(cmd, HEX);
    switch(cmd){
      case PWM_CMD:
        //Serial.println("pwm cmd");
        parse_pwm(buf, 2, noBytes);
        break;
      case SET_CMD:
        parse_set(buf, 2, noBytes);
        break;
      default:
        Serial.println("cmd n/a");
        break;
    }
  } // end if


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
  for(byte i = 0; i < pinouts; i++){
    if(single_channel) {
      pin_values[i] = max( pin_values[i]-reduce, min(pwm_max, max(pwm_min, read2b(buf, start+(2*(single_channel-1))))));
    } else {
      pin_values[i] = max( pin_values[i]-reduce, min(pwm_max, max(pwm_min, read2b(buf, start+(2*i))))); // val has to be bigger than pwm_min, smaller than max, and bigger than (currentvalue -reduce)
    }
    if(binary_mode) {
      pin_values[i] = pin_values[i] > cutoff ? pwm_max : 0;
    }
    analogWrite(pins[i], (pin_values[i] < cutoff)? 0 : pin_values[i]);
  }
}
/* settings cmd
 *  3 byte per settting. 1st byte is field flag, 2byte value
 *  
 */
void parse_set(byte* buf, int start, int total){
  Serial.println("set cmd");
  while(start+2 < total){
    switch(buf[start]){
      case(SET_CMD_REDUCE):
        reduce = (read2b(buf, start+1));
        Serial.print("set reduce to ");
        Serial.println(reduce);
        break;
      case(SET_CMD_MAX):
        pwm_max = (read2b(buf, start+1));
        Serial.print("set pwm_max to ");
        Serial.println(pwm_max);
        break;
      case(SET_CMD_MIN):
        pwm_min = (read2b(buf, start+1));
        Serial.print("set pwm_min to ");
        Serial.println(pwm_min);
        break;     
      case(SET_CMD_CUTOFF):
        cutoff = (read2b(buf, start+1));
        Serial.print("set cutoff to ");
        Serial.println(cutoff);
        break;   
      case(SET_CMD_1CH):
        single_channel = (read2b(buf, start+1));
        Serial.print("set single channel to ");
        Serial.println(single_channel);
        break;   
      case(SET_CMD_BIN):
        binary_mode = (read2b(buf, start+1));
        Serial.print("set binary mode to ");
        Serial.println(binary_mode);
        break;           
      default:
        Serial.print("set cmd fields n/a");
        break;
    }
    start += 3;
  }
}

void printWifiStatus() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
}
