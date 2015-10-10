#include <stdbool.h>
#include <gtk/gtk.h>
#include <pthread.h>
#include "udpsend.h"

#include "datatypes.h"
#include "gui.h"
#include "effect.h"

GtkWidget         *main_window;
GtkWidget         *color_chooser;
GtkAdjustment     *glow_adjustment;
GtkAdjustment     *flicker_adjustment;
GtkListStore      *channel_list;
GtkTreeView       *channel_view;
GtkTreeSelection  *channel_select;
GtkEntry          *ip;
GtkEntry          *port;



pthread_t worker;
bool flicker_loop = false;
bool connected = false;

ledstate current_state;

int flicker_speed;
bool autosend = true;

u_int current_channel;

/* protos */
void flicker();
void glow();
void refresh_color_chooser();
void  set_channel_color(GtkTreeModel *model, GtkTreePath *path, GtkTreeIter *iter, gpointer data);
void  refresh_chooser_first_channel(GtkTreeModel *model, GtkTreePath *path, GtkTreeIter *iter, gpointer data);


effectinfo glowin;
effectinfo flickerin;


static inline u_int maxuint(u_int a, u_int b) {return a>b?a:b;}


int main (int argc, char *argv[])
{

    GtkBuilder      *builder; 
    GError          *error = NULL;
    
    gtk_init(&argc, &argv);

    builder = gtk_builder_new();
    if( ! gtk_builder_add_from_file (builder, "gui.glade", &error)){
      g_warning("%s", error->message);
      g_free(error);
      return(1);
    }
    

    color_chooser = GTK_WIDGET(gtk_builder_get_object(builder,"color_chooser"));
    main_window = GTK_WIDGET(gtk_builder_get_object(builder,"main_window"));
    glow_adjustment = GTK_ADJUSTMENT(gtk_builder_get_object(builder,"glow_steps"));
    flicker_adjustment= GTK_ADJUSTMENT(gtk_builder_get_object(builder,"flicker_speed"));
    ip = GTK_ENTRY(gtk_builder_get_object(builder,"net_ip"));
    port= GTK_ENTRY(gtk_builder_get_object(builder,"net_port"));

    //setting up channels
    channel_list= GTK_LIST_STORE(gtk_builder_get_object(builder,"channel_list"));
    channel_view= GTK_TREE_VIEW(gtk_builder_get_object(builder,"channel_view"));
    channel_select= GTK_TREE_SELECTION(gtk_builder_get_object(builder,"channel_selection"));

    GtkTreeIter channel_iter;

    for(int i = 0; i < STRIPS; i++){
      guint data = (guint)i;
      gtk_list_store_append(channel_list, &channel_iter);

      gtk_list_store_set(channel_list, &channel_iter, 0, data, -1);

    }
    GtkCellRenderer *renderer;
    GtkTreeViewColumn *column;

    renderer = gtk_cell_renderer_text_new();
    column = gtk_tree_view_column_new_with_attributes("Channel", renderer, "text", 0, NULL);
    gtk_tree_view_append_column(GTK_TREE_VIEW(channel_view), column);



    //connecting signals
    gtk_builder_connect_signals(builder, main_window);

    g_object_unref(G_OBJECT(builder));
        

    gtk_widget_show(main_window);                

    gtk_main ();

	  return 1;
}


void btn_autosend(GtkButton *button, gpointer user_data){
  autosend = gtk_switch_get_active((GtkSwitch *) button);
  if(autosend) color_changed();
}

void btn_connect_clicked(GtkButton *button, gpointer user_data){
  g_print("ip: %s\n", gtk_entry_get_text(ip));
  g_print("port: %s\n", gtk_entry_get_text(port));
  udp_setup((char *)gtk_entry_get_text(ip), (char *)gtk_entry_get_text(port));
  connected = true;
}


void color_changed (GObject *o, GParamSpec *pspect, gpointer data) {
	/*
  GdkRGBA rgba;
  gtk_color_selection_get_current_rgba((GtkColorSelection *)color_chooser, &rgba);

  current_state.rgba[current_channel] = rgba;
	
#ifdef DEBUG  
  printf("[color_changed in channel %d ]\n", current_channel);
  printf("red:   %g\n", current_state.rgba[current_channel].red);
  printf("green: %g\n", current_state.rgba[current_channel].green);
  printf("blue:  %g\n", current_state.rgba[current_channel].blue);
#endif
	*/

	gtk_tree_selection_selected_foreach(GTK_TREE_SELECTION(channel_select), set_channel_color, NULL);

  if(autosend && connected) send_state(current_state);
}

void btn_flicker_clicked(GtkButton *button, gpointer user_data){
  gboolean mode;
  mode = gtk_toggle_button_get_active((GtkToggleButton *) button);
  if(mode == TRUE){

  	flickerin.speed = (int)gtk_adjustment_get_value(flicker_adjustment);
    flickerin.loop = true;
		for(int i = 0; i < STRIPS; i++){
			flickerin.active[i] = 0;
		}
	
	  get_active_strips(flickerin.active);
	  flickerin.state = current_state;
	  if(pthread_create(&worker, NULL, flicker, &flickerin)) {
	  	g_print(stderr, "Error creating thread\n");
	  }  
  } else {
    flickerin.loop = false;
		printf("main thread: loop: %d\n", flickerin.loop);
  }
}


void btn_glow_clicked(GtkButton *button, gpointer user_data){
  glowin.steps = (int)gtk_adjustment_get_value(glow_adjustment);

	for(int i = 0; i < STRIPS; i++){
		glowin.active[i] = 0;
	}

  get_active_strips(glowin.active);
  glowin.state = current_state;

	if(pthread_create(&worker, NULL, glow, &glowin)) {
		g_print(stderr, "Error creating thread\n");
	}  
}


/*
void set_flicker_speed(GtkRange *range, gpointer  user_data){
		flicker_speed = (int)gtk_adjustment_get_value(range);
		g_print("flicker speed changed to %d\n", flicker_speed);
}

*/

/* callback for multiple selected channels */
void  set_channel_color(GtkTreeModel *model, GtkTreePath *path, GtkTreeIter *iter, gpointer data){
  GdkRGBA rgba;
  gtk_color_selection_get_current_rgba((GtkColorSelection *)color_chooser, &rgba);

  guint channel;
  gtk_tree_model_get(model, iter, 0, &channel, -1);
  current_state.rgba[(u_int)channel] = rgba;
  g_print("\tChannel %d: %g %g %g %g\n", channel, rgba.red, rgba.green, rgba.blue, rgba.alpha);

}



void channel_selection_changed(GtkTreeSelection *selection, gpointer data){
  GtkTreeIter iter;
  GtkTreeModel *model;
  guint channel;

	if(gtk_tree_selection_count_selected_rows(selection) == 1){
	  gtk_tree_selection_selected_foreach(GTK_TREE_SELECTION(channel_select), refresh_chooser_first_channel, NULL);
	}
/*
  if(gtk_tree_selection_get_selected(selection, &model, &iter)){
    gtk_tree_model_get(model, &iter, 0, &channel, -1);
    g_print("Selected channel %d\n", channel);

    current_channel = (u_int)channel;

    gtk_color_selection_set_current_rgba((GtkColorSelection *)color_chooser, &current_state.rgba[current_channel]);
    //g_free(channel);
  }
*/

}

/* callback for single selected channels */
void  refresh_chooser_first_channel(GtkTreeModel *model, GtkTreePath *path, GtkTreeIter *iter, gpointer data){
  GdkRGBA rgba;
  guint channel;
  gtk_tree_model_get(model, iter, 0, &channel, -1);
  gtk_color_selection_set_current_rgba((GtkColorSelection *)color_chooser, &current_state.rgba[channel]);
}

/* callback for active channel array generation */
void  get_active_strips_cb(GtkTreeModel *model, GtkTreePath *path, GtkTreeIter *iter, gpointer data){
  guint channel;
	bool *active;
	active = (bool *)data;
  gtk_tree_model_get(model, iter, 0, &channel, -1);
	if(gtk_tree_selection_iter_is_selected(GTK_TREE_SELECTION(channel_select),iter) == TRUE){
		 printf("channel %d active\n", channel);
		 active[channel] = 1;
	} 

}

void get_active_strips(bool *active){
	  gtk_tree_selection_selected_foreach(GTK_TREE_SELECTION(channel_select), get_active_strips_cb, active);
}
