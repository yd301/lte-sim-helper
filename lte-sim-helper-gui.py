#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Copyright (c) 2012 Federal University of Uberlândia

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation;

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Author: Saulo da Mata <damata.saulo@gmail.com>

'''

from gi.repository import Gtk, Gdk
from multiprocessing import cpu_count
from copy import deepcopy
from setup_parser import SetupParser


class LteSimHelperGui( Gtk.Window ):
    
    def __init__( self ):

        self.builder = Gtk.Builder()
        self.builder.add_from_file( 'lte-sim-helper-gui.glade' )
        
        self.builder.connect_signals( self )
        
        self.parser = SetupParser()
        self.pref = self.parser.parse( 'preferences.cfg' )

        self.main_window = self.builder.get_object( 'main_window' )
        self.start_dlg = self.builder.get_object( 'start_dlg' )
        
        self.set_ask_chkbox = self.builder.get_object( 'set_ask_chkbox' )
        
        if self.pref['START_DLG'] == 'TRUE':                       
            self.start_dlg.run()
        else:
            self.load_main_window()
       
       
        
        
       
#------------------------------------------------------------------------------
    def load_main_window( self ):        
        self.create_cpu_cbx()
        self.main_sched_grid, self.main_sched_chkbox = self.create_schedulers_grid( 'sched_align' )
        self.dlg_sched_grid, self.dlg_sched_chkbox = self.create_schedulers_grid( 'dlg_sched_align' )

        self.add_sched_dlg = self.builder.get_object( 'add_sched_dlg' )
        self.rm_sched_dlg = self.builder.get_object( 'rm_sched_dlg' )
        self.new_sched_ety = self.builder.get_object( 'new_sched_ety' )
        self.no_add_dlg = self.builder.get_object( 'no_add_dlg' )
        
        self.lte_sim_path = self.pref['LTE_SIM_PATH'] 
        self.save_dir_path = self.pref['SAVE_DIR_PATH'] 
        
       
#------------------------------------------------------------------------------       
    def on_start_ok_btn_clicked( self, widget, data=None ):
       
        start_chkbox = self.builder.get_object( 'start_chkbox' )
        
        if start_chkbox.get_active():
            self.save_preference( 'START_DLG', 'TRUE' )
            self.set_ask_chkbox.set_active( True )
        else:
            self.save_preference( 'START_DLG', 'FALSE' )
            
        self.lte_sim_path = self.builder.get_object( 'start_lte_fc' ).get_filename()
        self.save_dir_path = self.builder.get_object( 'start_save_fc' ).get_filename()
        
        if self.lte_sim_path == None:
            self.no_lte_path_dlg = self.builder.get_object( 'no_lte_path_dlg' )
            self.no_lte_path_dlg.run()
        else:
            self.save_preference( 'LTE_SIM_PATH', self.lte_sim_path )
            self.save_preference( 'SAVE_DIR_PATH', self.save_dir_path )
            self.load_main_window()
            self.start_dlg.hide()
           
#------------------------------------------------------------------------------
    def save_preference( self, key, value ):
        f = open( 'preferences.cfg' ).readlines()
        f_new = deepcopy( f )
        
        for line in f:
            if line.startswith( key ):
                f_new[f_new.index( line )] = key + '=' + value + '\n'
                    
        f = open( 'preferences.cfg', 'w' )
        for line in f_new:
            f.write( line )            
        f.close()        
        
        self.pref = self.parser.parse( 'preferences.cfg' )
        


#------------------------------------------------------------------------------       
    def on_start_cancel_btn_clicked( self, widget, data=None ):
        exit()
        
#------------------------------------------------------------------------------       
    def on_start_dlg_destroy( self, widget, data=None ):
        exit()        

#------------------------------------------------------------------------------        
     
    def create_cpu_cbx( self ):
        cpu_store = Gtk.ListStore( int )
        
        l_cpus = []
        for i in range( cpu_count() ):
            l_cpus.append( i + 1 )
            
        for cpu in l_cpus:
            cpu_store.append( [cpu] )
            
        cpu_cbx = self.builder.get_object( 'cpu_cbx' )
        cpu_cbx.set_model( cpu_store )
        cpu_renderer_text = Gtk.CellRendererText()
        cpu_cbx.pack_start( cpu_renderer_text, True )
        cpu_cbx.add_attribute( cpu_renderer_text, "text", 0 )

#------------------------------------------------------------------------------        
    def create_schedulers_grid( self, align ):
        sched_align = self.builder.get_object( align )
        sched_grid = Gtk.Grid()
        sched_align.add( sched_grid )
        
        f = open( 'schedulers.cfg' )
        
        l_sched_chkbtn = []

        for line in f:
            if not ( line == ' ' or len( line ) == 1 ):
                l_sched_chkbtn.append( ( line.rstrip(), Gtk.CheckButton( line.rstrip() ) ) )
            
        t = 0
        l = 0
        for s in range( len( l_sched_chkbtn ) ):
            if l == 8:
                l = 0
                t += 1
            sched_grid.attach( l_sched_chkbtn[s][1], l, t, 1, 1 )            
            l += 1
        
        self.main_window.show_all()
        
        return sched_grid, l_sched_chkbtn 

#------------------------------------------------------------------------------                         
    def on_open_tool_btn_clicked( self, widget, data=None ):
        print "LOAD"

#------------------------------------------------------------------------------        
    def on_add_tool_btn_clicked( self, widget, data=None ):
        self.add_sched_dlg.run()
        self.new_sched_ety.set_text( '' )
        self.new_sched_ety.set_placeholder_text( 'PF' )        

#------------------------------------------------------------------------------        
    def on_cancel_add_sched_btn_clicked( self, widget, data=None ):
        self.add_sched_dlg.hide()

#------------------------------------------------------------------------------        
    def on_add_sched_btn_clicked( self, widget, data=None ):
        f = open( 'schedulers.cfg', 'a' )
        if self.new_sched_ety.get_text() == '':
            self.no_add_dlg.run()
        else:
            f.write( self.new_sched_ety.get_text() + '\n' )
        f.close()
        self.main_sched_grid.destroy()
        self.main_sched_grid, self.main_sched_chkbox = self.create_schedulers_grid( 'sched_align' )
        self.add_sched_dlg.hide()
        
#------------------------------------------------------------------------------   
    def on_rm_tool_btn_clicked( self, widget, data=None ):
        self.dlg_sched_grid.destroy()
        self.dlg_sched_grid, self.dlg_sched_chkbox = self.create_schedulers_grid( 'dlg_sched_align' )
        self.rm_sched_dlg.show_all()
        self.rm_sched_dlg.run()

#------------------------------------------------------------------------------        
    def on_cancel_rm_sched_btn_clicked( self, widget, data=None ):
        self.rm_sched_dlg.hide()

#------------------------------------------------------------------------------        
    def on_rm_sched_btn_clicked( self, widget, data=None ):
        selected = self.get_chkbox_selected( self.dlg_sched_chkbox )  
        f = open( 'schedulers.cfg' ).readlines()
        f_new = deepcopy( f )
        
        for line in f:
            for s in selected:
                if s == line.rstrip():
                    f_new.remove( line )
                    
        f = open( 'schedulers.cfg', 'w' )
        for line in f_new:
            f.write( line )            
        f.close()
        
        self.dlg_sched_grid.destroy()
        self.dlg_sched_grid, self.dlg_sched_chkbox = self.create_schedulers_grid( 'dlg_sched_align' )
        self.main_sched_grid.destroy()
        self.main_sched_grid, self.main_sched_chkbox = self.create_schedulers_grid( 'sched_align' )
        self.rm_sched_dlg.hide()

#------------------------------------------------------------------------------        
    def get_chkbox_selected( self, l_chkbox ):
        selected = []
        for c in range( len( l_chkbox ) ):
            if l_chkbox[c][1].get_active():
                selected.append( l_chkbox[c][0] )
        
        return selected

#------------------------------------------------------------------------------
    def on_no_add_btn_clicked( self, widget, data=None ):
        self.no_add_dlg.hide()
        self.add_sched_dlg.run()

#------------------------------------------------------------------------------
    def on_set_tool_btn_clicked( self, widget, data=None ):
        self.set_lte_fc = self.builder.get_object( 'set_lte_fc' )
        self.set_lte_fc.set_filename( self.lte_sim_path )
        
        self.set_save_fc = self.builder.get_object( 'set_save_fc' )
        self.set_save_fc.set_filename( self.save_dir_path )
        
        self.set_dlg = self.builder.get_object( 'set_dlg' )
        self.set_dlg.run()
               
#------------------------------------------------------------------------------
    def on_quit_tool_btn_clicked( self, widget, data=None ):
        Gtk.main_quit()
        exit( 0 )

#------------------------------------------------------------------------------                        
    def on_cpu_cbx_changed( self, widget, data=None ):
        print 'CCCCCC'

#------------------------------------------------------------------------------
    def on_main_window_destroy( self, widget, data=None ):
        Gtk.main_quit()
        exit( 0 )

#------------------------------------------------------------------------------
    def on_set_cancel_btn_clicked( self, widget, data=None ):
        self.set_dlg.hide()
    
    
#------------------------------------------------------------------------------
    def on_set_save_btn_clicked( self, widget, data=None ):
        self.save_preference( 'LTE_SIM_PATH', self.set_lte_fc.get_filename() )
        self.save_preference( 'SAVE_DIR_PATH', self.set_save_fc.get_filename() )
        
        if self.set_ask_chkbox.get_active():
            self.save_preference( 'START_DLG', 'TRUE' )
        else:
            self.save_preference( 'START_DLG', 'FALSE' )
            
        self.set_dlg.hide()
    
    
#------------------------------------------------------------------------------
    def on_no_lte_path_btn_clicked( self, widget, data=None ):
        self.no_lte_path_dlg.hide()
        self.start_dlg.run()
#------------------------------------------------------------------------------
#    def( self, widget, data=None ):    


if __name__ == "__main__":
    my_gui = LteSimHelperGui()
    Gtk.main()    
#window = MenuExampleWindow()        
#window.connect("delete-event", Gtk.main_quit)
#window.show_all()
#Gtk.main()
