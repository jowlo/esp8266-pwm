#include <stdbool.h>
#include <gtk/gtk.h>
#include <pthread.h>
#include "udpsend.h"

GtkWidget* main_window;
GtkWidget* box;
GtkWidget* color_chooser;
GtkWidget* btn_send_color;

pthread_t worker;
bool flicker_loop = false;

u_int current_color[3];
u_int current_alpha;

int flicker_speed;
int glow_speed;
bool autosend = true;

/* protos */
void flicker();
void glow();


static inline u_int maxuint(u_int a, u_int b) {return a>b?a:b;}


int main (int argc, char *argv[])
{
  	udp_setup("192.168.178.37", "5555");

    GtkBuilder      *builder; 
    GError          *error = NULL;
    
    gtk_init(&argc, &argv);

    builder = gtk_builder_new();
    if( ! gtk_builder_add_from_file (builder, "gui.glade", &error)){
      g_warning("%s", error->message);
      g_free(error);
      return(1);
    }
    

    //box = GTK_WIDGET(gtk_builder_get_object(builder,"hbox"));
    color_chooser = GTK_WIDGET(gtk_builder_get_object(builder,"color_chooser"));
    main_window = GTK_WIDGET(gtk_builder_get_object(builder,"main_window"));

    gtk_builder_connect_signals(builder, main_window);

    g_object_unref(G_OBJECT(builder));
        

    gtk_widget_show(main_window);                

    gtk_main ();

    return 0;
}

void gtk_send_color(){
  send_color(current_color, current_alpha);
}

void gdkRGBA_to_color(GdkRGBA in, u_int *out){
  out[0] = (int)(in.red*256);
  out[1] = (int)(in.green*256);
  out[2] = (int)(in.blue*256);
}

void btn_autosend(GtkButton *button, gpointer user_data){
  autosend = gtk_switch_get_active((GtkSwitch *) button);
  if(autosend) color_changed();
}

void color_changed (GObject *o, GParamSpec *pspect, gpointer data) {
  GdkRGBA rgba;
  gtk_color_selection_get_current_rgba((GtkColorSelection *)color_chooser, &rgba);
  g_print ("color changed: %g %g %g %g\n", rgba.red, rgba.green, rgba.blue, rgba.alpha); 

  gdkRGBA_to_color(rgba, current_color);
  current_alpha = (u_int)(rgba.alpha * 256);
  if(autosend) gtk_send_color(NULL, NULL);
}

void btn_flicker_clicked(GtkButton *button, gpointer user_data){
  gboolean mode;
  mode = gtk_toggle_button_get_active((GtkToggleButton *) button);
  if(mode == TRUE){
	  if(pthread_create(&worker, NULL, flicker, NULL)) {
	  	g_print(stderr, "Error creating thread\n");
	  }  
  } else {
    flicker_loop = false;
  }
}

void flicker(){
  u_int alpha;
  alpha = current_alpha;
  flicker_loop = true;

  while(flicker_loop) { 
    send_color(current_color, alpha);
    usleep(100*flicker_speed);
    alpha = maxuint(1, alpha-1);
    if(rand() % 200 > 195) {
        alpha = maxuint(alpha + rand() % 40, 100);
    }
  }
}

void btn_glow_clicked(GtkButton *button, gpointer user_data){
	if(pthread_create(&worker, NULL, glow, NULL)) {
		g_print(stderr, "Error creating thread\n");
	}  
}

void glow(){
  u_int alpha, color;
  alpha = current_alpha;

  g_print("alpha before: %d", current_alpha);

  while(alpha > 0) { 
    g_print("alpha: %d", alpha);
    usleep(10000+glow_speed);
    alpha--;
    send_color(current_color, alpha);
  }
  send_color(current_color, 0);
}

void set_flicker_speed(GtkRange *range, gpointer  user_data){
		flicker_speed = (int)gtk_adjustment_get_value(range);
		g_print("flicker speed changed to %d\n", flicker_speed);
}

void set_glow_speed(GtkRange *range, gpointer  user_data){
		glow_speed = (int)gtk_adjustment_get_value(range);
		g_print("glow speed changed to %d\n", glow_speed);
}


