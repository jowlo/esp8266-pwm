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
  //printf("sending... %s", data);
  return err;

}

int main(int argc, char* argv[]){


  if (argc >4 && strcmp(argv[1], "c") == 0){
    udp_setup(argv[2], argv[3]);

    u_int color[3];
    printf("showing color %s\n", argv[4]);
    rgbhex(argv[4], color);
    if(argc > 5)
      brightness(atoi(argv[5]), color);

    send_color(color);

    
  } else if (argc >3 && strcmp(argv[1], "test") == 0){

    printf("testing color spectrum...");

    udp_setup(argv[2], argv[3]);

/*    u_int color[3] = {0, 0, 0};

    int change = 0;
    while(change < 4){
        color[change]++;
        //if(change > 0) color[change-1]--;
        send_color(color);
        usleep(10000);
        if(color[change] == 255) change++;
    }
*/

    u_int red, green, blue;
    
    for (red = 0; red <= 255; red++) {
        for (green = 0; green <= 255; green++) {
            for (blue = 0; blue <= 255; blue++) {
                send_rgb(red, green, blue);
                usleep(10000);
            }
        }
    }

  } else {
    printf("not testing...");
    printf("Have %d arguments:", argc);
    for (int i = 0; i < argc; ++i) {
        printf("%s", argv[i]);
    }
    return 1;
  }
}

void send_color(u_int *color) {
  unsigned char packet[8];
  packet[0] = 0;
  packet[1] = 0x7e; // pwm command
  packet[2+ 0] = (color[0] >> 8) & 0xff;
  packet[2+ 1] = color[0] & 0xff;

  packet[2+ 2] = (color[1] >> 8) & 0xff;
  packet[2+ 3] = color[1] & 0xff;

  packet[2+ 4] = (color[2] >> 8) & 0xff;
  packet[2+ 5] = color[2] & 0xff;

  printf("color: %d, %d, %d\n", color[0], color[1],color[2]);
  printf("packet: %x, %x, %x\n", packet[2], packet[4], packet[6]);
  udp_send(8, packet);
}

void send_rgb(u_int r, u_int g, u_int b){
  u_int colors[3] = {4*r, 4*g, 4*b};
  send_color(colors);
}

void rgbhex(char *hexstr, u_int *out){
  u_int color = strtoul(hexstr, 0, 16);
  for(int i = 0; i < 3; i++){
    out[2-i] = ((color >> (8*i))) & 0xff;
  }
}

/* dim is inpercentage */
void brightness(u_int dim, u_int *color){
  for(int i = 0; i < 3; i++){
    color[i] = (color[i]*dim) / 100;
  }
  
}
