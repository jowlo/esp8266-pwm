#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>

struct addrinfo hints;
struct addrinfo* res;
int fd;

static inline u_int max(u_int a, u_int b) {return a > b ? a : b; }
static inline u_int qsub(u_int a, u_int b) { return max(a-b, 0); }

//
// prototypes
//
u_int fire(u_int h);

int udp_setup(char* hostname, char* portname) {
  
  memset(&hints,0,sizeof(hints));
  
  hints.ai_family=AF_INET;
  hints.ai_socktype=SOCK_DGRAM;
  hints.ai_protocol=0;
  hints.ai_flags=AI_ADDRCONFIG;
  

  int err=getaddrinfo(hostname,portname,&hints,&res);
  if (err!=0) {
      printf("failed to resolve remote socket address (err=%d)",err);
  }
  
  fd = socket(res->ai_family,res->ai_socktype,res->ai_protocol);
  if (fd==-1) {
      printf("%s",strerror(errno));
  }

  printf("socket: %d \n", fd);

  return err;
  
}


int udp_send(size_t size, char* data) {
  int err = sendto(fd,data,size,0, res->ai_addr,res->ai_addrlen);
  if (err==-1) {
      printf("%s",strerror(errno));
  }
  g_print("sending... %s", data);
  return err;

}

u_int * color_byte_to_pwm(u_int *color, u_int *out){
  out[0] = color[0] * 4;
  out[1] = color[1] * 4;
  out[2] = color[2] * 4;
}

void send_color(u_int *color, u_int alpha) {
  unsigned char packet[8];

  u_int out[3];
  color_byte_to_pwm(color, out);
  brightness(alpha, out);

  packet[0] = 0;
  packet[1] = 0x7e; // pwm command
  packet[2+ 0] = (out[0] >> 8) & 0xff;
  packet[2+ 1] = out[0] & 0xff;

  packet[2+ 2] = (out[1] >> 8) & 0xff;
  packet[2+ 3] = out[1] & 0xff;

  packet[2+ 4] = (out[2] >> 8) & 0xff;
  packet[2+ 5] = out[2] & 0xff;

  //printf("color: %d, %d, %d\n", color[0], color[1],color[2]);
  //printf("packet: %x %x, %x %x, %x %x\n", packet[2], packet[3], packet[4], packet[5], packet[6], packet[7]);
  udp_send(8, packet);
}

void send_rgb(u_int r, u_int g, u_int b, u_int alpha){
  u_int colors[3] = {r, g, b};
  send_color(colors, alpha);
}

void rgbhex(char *hexstr, u_int *out){
  u_int color = strtoul(hexstr, 0, 16);
  for(int i = 0; i < 3; i++){
    out[2-i] = ((color >> (8*i))) & 0xff;
  }
}

/* dim is in percentage */
void brightness(u_int dim, u_int *color){
  for(int i = 0; i < 3; i++){
    color[i] = (color[i]*dim) / 100;
  }
}

void heat_to_color(u_int *color, u_int temp) {
 
  // Scale 'heat' down from 0-255 to 0-191,
  // which can then be easily divided into three
  // equal 'thirds' of 64 units each.
  u_int t192 = (temp*70)/100;
 
  // calculate a value that ramps up from
  // zero to 255 in each 'third' of the scale.
  u_int heatramp = t192 & 0x3F; // 0..63
  heatramp <<= 2; // scale up to 0..252
 
  // now figure out which third of the spectrum we're in:
  if(t192 & 0x80) {
    // we're in the hottest third
    color[0] = 255; // full red
    color[1] = 255; // full green
    color[2] = heatramp; // ramp up blue
  } else if(t192 & 0x40 ) {
    // we're in the middle third
    color[0] = 255; // full red
    color[1] = heatramp; // ramp up green
    color[2] = 0; // no blue
  } else {
    // we're in the coolest third
    color[0] = heatramp; // ramp up red
    color[1] = 0; // no green
    color[2] = 0; // no blue
  }
}
