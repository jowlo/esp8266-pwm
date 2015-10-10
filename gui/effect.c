#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>

#include "udpsend.h"

#include "datatypes.h"
#include "gui.h"
#include "effect.h"


void glow(effectinfo *inp){

  effectinfo in;
  in = *inp;
  double reduce[STRIPS];
	for(int i = 0; i < STRIPS; i++){
		printf("active %d: %d", i, in.active[i]);
		if(in.active[i] == 1){
			reduce[i] = in.state.rgba[i].alpha/in.steps;
	  	if((u_int)(in.state.rgba[i].alpha * PWM_MAX) == 0){
 		 	  in.state.rgba[i].alpha = 1;
  		}
		} else {
			reduce[i] = 0;
		}
	}

#ifdef DEBUG
  g_print("=== glow ===\n");
  g_print("\tsteps %d\n", in.steps);
  g_print("\treduce %g\n", reduce);
#endif


  for(int i = 0; i <in.steps; i++) { 
    usleep(100);
    for(int i = 0; i < STRIPS; i++){
			in.state.rgba[i].alpha -= reduce[i];
		}
    send_state(in.state);
  }
	for(int i = 0; i < STRIPS; i++){
  	if(in.active[i] == 1) in.state.rgba[i].alpha = 0;
	}
		
  send_state(in.state);
}




void flicker(effectinfo *inp){
	effectinfo in;
	in = *inp;
	double basealpha[STRIPS];
  for(int i = 0; i < STRIPS; i++){
	  basealpha[i] = in.state.rgba[i].alpha;
  }

  while(inp->loop == true) {
    usleep(1000*in.speed);
		for(int i = 0; i < STRIPS; i++){
			if(in.active[i] == 1){
				in.state.rgba[i].alpha = in.state.rgba[i].alpha - rand()/((double)RAND_MAX/2);
				if(in.state.rgba[i].alpha < 0) in.state.rgba[i].alpha = 0;
		    if(rand() % 100 > 60) {
		        in.state.rgba[i].alpha = in.state.rgba[i].alpha + rand()/(double)RAND_MAX;
		        if(in.state.rgba[i].alpha > basealpha[i]) in.state.rgba[i].alpha = basealpha[i];
		    }
			}
  	}
  	send_state(in.state);
	}
}
