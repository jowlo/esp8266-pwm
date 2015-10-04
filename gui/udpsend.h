#ifndef UDPSEND_H
#define UDPSEND_H


#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>

#include "datatypes.h"

int udp_setup(char* hostname, char* portname);


int udp_send(size_t size, char* data);
void send_color(u_int *color, u_int alpha);
void send_state(ledstate state);
void send_rgb(u_int r, u_int g, u_int b, u_int alpha);
void rgbhex(char *hexstr, u_int *out);


#endif /* UDPSEND_H */
