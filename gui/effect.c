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


void glow(glowinfo *inp){

  glowinfo in;
  in = *inp;
  double reduce = in.state.rgba[in.strip].alpha/in.steps;

#ifdef DEBUG
  g_print("=== glow ===\n");
  g_print("\tsteps %d\n", in.steps);
  g_print("\tstrip %d\n", in.strip);
  g_print("\tred %g\n", in.state.rgba[in.strip].red);
  g_print("\treduce %g\n", reduce);
#endif

  if((u_int)(in.state.rgba[in.strip].alpha * PWM_MAX) == 0){
    in.state.rgba[in.strip].alpha = 1;
  }

#ifdef DEBUG
  g_print("alpha before: %g\n", in.state.rgba[in.strip].alpha);
#endif

  for(int i = 0; i<in.steps; i++) { 
#ifdef DEBUG
    g_print("alpha: %g\n", in.state.rgba[in.strip].alpha);
#endif
    usleep(100);
    in.state.rgba[in.strip].alpha -= reduce;
    send_state(in.state);
  }
  in.state.rgba[in.strip].alpha = 0;
  send_state(in.state);
}

