#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>

struct addrinfo hints;
struct addrinfo* res;
int fd;


int udp_setup(char* hostname, char* portname) {
  
  hostname=0; /* localhost */
  portname="8000";
  
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
  printf("sending... %s", data);
  return err;

}
