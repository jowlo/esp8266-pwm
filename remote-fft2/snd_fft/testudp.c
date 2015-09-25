#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h> 


const char* hostname=0; /* wildcard */
const char* portname="8000";

struct addrinfo hints;

int socketfd;
FILE *ctrlfd;

void setup(){
	memset(&hints,0,sizeof(hints));
	hints.ai_family=AF_INET;
	hints.ai_socktype=SOCK_DGRAM;
	hints.ai_protocol=0;
	hints.ai_flags=AI_PASSIVE|AI_ADDRCONFIG;
	struct addrinfo* res=0;
	
	int err=getaddrinfo(hostname,portname,&hints,&res);
	if (err!=0) {
	    printf("failed to resolve local socket address (err=%d)",err);
	}
	
	socketfd=socket(res->ai_family,res->ai_socktype,res->ai_protocol);
	if (socketfd==-1) {
	    printf("%s",strerror(errno));
	}
	
	if (bind(socketfd,res->ai_addr,res->ai_addrlen)==-1) {
	    printf("%s",strerror(errno));
	}

	//ctrlfd=fopen("/dev/pigpio", "w");
}

void receive() {
	char buffer[4096];
	struct sockaddr_storage src_addr;
	socklen_t src_addr_len=sizeof(src_addr);
	ssize_t count=recvfrom(socketfd,buffer,sizeof(buffer),0,(struct sockaddr*)&src_addr,&src_addr_len);
	if (count==-1) {
	    printf("%s",strerror(errno));
	} else if (count==sizeof(buffer)) {
	    printf("datagram too large for buffer: truncated");
	} else {
	    handle_datagram(buffer,count);
	}
	
}


void handle_datagram(char* buf, ssize_t count){
  for(int i =0; i < count; i++){
	  printf("%d:%d ", i, buf[1]);
  }
  printf("\n");
}

int main(int argc, char**argv) {
	setup();
	while(1){
		receive();
		//fprintf(ctrlfd, "p 4 255\n");
	}

}

