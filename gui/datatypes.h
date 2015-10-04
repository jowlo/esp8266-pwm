#ifndef DATATYPES_H
#define DATATYPES_H

#include <gdk/gdk.h>
#include <gtk/gtk.h>
#include <stdbool.h>

#define STRIPS 2
#define PWM_MAX 1024

typedef struct {
  GdkRGBA rgba[STRIPS];
} ledstate;

typedef struct {
  bool  active[STRIPS];
  u_int steps;
  ledstate state;
  GtkWidget *color_chooser;
} glowinfo;

#endif /* DATATYPES_H */
