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
import time, os
from gi.repository import Gtk, Gdk, GObject
from copy import deepcopy
from setup_parser import SetupParser
from lte_sim_helper import LteSimHelper
from multiprocessing import Process, Queue, Manager, cpu_count, active_children, current_process
from subprocess import call, Popen
from datetime import datetime


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
        self.no_sched_dlg = self.builder.get_object( 'no_sched_dlg' )
        self.no_flow_dlg = self.builder.get_object( 'no_flow_dlg' )
        self.pbar = self.builder.get_object( 'sim_pbar' )
        self.status_bar = self.builder.get_object( 'status_bar' )
        self.sim_done_dlg = self.builder.get_object( 'sim_done_dlg' )
        
       
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
    def on_no_sched_btn_clicked( self, widget, data=None ):
        self.no_sched_dlg.hide()
        self.main_window.show_all()
        
#------------------------------------------------------------------------------
    def on_no_flow_btn_clicked( self, widget, data=None ):       
        self.no_flow_dlg.hide()
        self.main_window.show_all()
       
#------------------------------------------------------------------------------       
    def update_progress_bar( self, user_data ):

        if not self.q_sim.empty():
            call_back = self.q_sim.get()
            self.frac = call_back[1]   
            self.pbar.set_show_text( True )
            self.pbar.set_text( call_back[0] )                 
            self.pbar.set_fraction( self.frac )
            self.main_window.show_all()
            if call_back[2] and ( not call_back[3] ):
                self.builder.get_object( 'res_pbar_frm' ).set_sensitive( True )
                self.builder.get_object( 'sim_pbar_frm' ).set_sensitive( False )
                self.pbar = self.builder.get_object( 'parse_pbar' )
                self.proc = Process( target=self.helper.compute_results, args=( self.q_sim, ) )            
                self.proc.start()   
            if call_back[2] and call_back[3]:
                self.builder.get_object( 'res_pbar_frm' ).set_sensitive( False )
                self.pbar = self.builder.get_object( 'sim_pbar' )
                self.sim_done_dlg.run()
                
                print 'DONE!'
        return True
            
#------------------------------------------------------------------------------
    def on_run_tool_btn_clicked( self, widget, data=None ):

        self.builder.get_object( 'sim_pbar_frm' ).set_sensitive( True )
        
        self.l = []

        self.frac = 0.0
        self.q_sim = Queue()

        self.timeout_id = GObject.timeout_add( 50, self.update_progress_bar, None )
        
        if self.generate_setup_file():
            self.helper = LteSimHelper()            
            self.proc = Process( target=self.helper.run_simulations, args=( self.q_sim, ) )            
            self.proc.start()       
            self.l.append( self.proc.pid )
            self.start = datetime.now()


#------------------------------------------------------------------------------
    def generate_setup_file( self ):
        
        cpu_cbx = self.builder.get_object( 'cpu_cbx' )
        cpu_model = cpu_cbx.get_model()
        n_cpu = str( cpu_model[cpu_cbx.get_active_iter()][0] )
        
        erase_chkbox = self.builder.get_object( 'erase_chkbox' )
        if erase_chkbox.get_active(): erase_flag = 'yes'
        else: erase_flag = 'no'
        
        dec_sbn = self.builder.get_object( 'dec_sbn' )
        n_dec = str( dec_sbn.get_value_as_int() )
        
        cdf_sbn = self.builder.get_object( 'cdf_sbn' )
        cdf_gran = str( cdf_sbn.get_value_as_int() )
        
        sim_tme_sbn = self.builder.get_object( 'sim_tme_sbn' )
        sim_time = str( sim_tme_sbn.get_value_as_int() )
        
        sim_tme_flw_sbn = self.builder.get_object( 'sim_tme_flw_sbn' )
        sim_time_flow = str( sim_tme_flw_sbn.get_value_as_int() )
        
        seed_cbx = self.builder.get_object( 'seed_cbx' )
        seed_model = seed_cbx.get_model()
        seed = str( seed_model[seed_cbx.get_active_iter()][0] )
        
        n_sim_sbn = self.builder.get_object( 'n_sim_sbn' )
        n_sim = str( n_sim_sbn.get_value_as_int() )
        
        bw_sbn = self.builder.get_object( 'bw_sbn' )
        bw = str( bw_sbn.get_value() )
        
        scen_cbx = self.builder.get_object( 'scen_cbx' )
        scen_model = scen_cbx.get_model()
        lte_scen = str( scen_model[scen_cbx.get_active_iter()][2] )
        cell_mode = str( scen_model[scen_cbx.get_active_iter()][1] )
        
        n_cell_sbn = self.builder.get_object( 'n_cell_sbn' )
        n_cell = str( n_cell_sbn.get_value_as_int() )
        
        cluster_sbn = self.builder.get_object( 'cluster_sbn' )
        clusters = str( cluster_sbn.get_value_as_int() )
        
        rad_sbn = self.builder.get_object( 'rad_sbn' )
        rad = str( rad_sbn.get_value() )
        
        n_ue_ety = self.builder.get_object( 'n_ue_ety' )
        n_ue = n_ue_ety.get_text()
        
        ue_speed_sbn = self.builder.get_object( 'ue_speed_sbn' )
        ue_speed = str( ue_speed_sbn.get_value_as_int() )
        
        ue_mob_cbx = self.builder.get_object( 'ue_mob_cbx' )
        ue_mob_model = ue_mob_cbx.get_model()
        ue_mob = str( ue_mob_model[ue_mob_cbx.get_active_iter()][1] )
        
        flow_flag = False
        voip_chkbox = self.builder.get_object( 'voip_chkbox' )
        if voip_chkbox.get_active(): 
            n_voip = '1'
            flow_flag = True
        else: n_voip = '0'
        
        video_chkbox = self.builder.get_object( 'video_chkbox' )
        if video_chkbox.get_active(): 
            n_video = '1'
            flow_flag = True
        else: n_video = '0'
        
        infbuf_chkbox = self.builder.get_object( 'infbuf_chkbox' )
        if infbuf_chkbox.get_active(): 
            n_infbuf = '1'
            flow_flag = True
        else: n_infbuf = '0'
        
        cbr_chkbox = self.builder.get_object( 'cbr_chkbox' )
        if cbr_chkbox.get_active(): 
            n_cbr = '1'
            flow_flag = True
        else: n_cbr = '0'
        
        if not flow_flag:
            self.no_flow_dlg.run()
            return False
        
        delay_sbn = self.builder.get_object( 'delay_sbn' )
        delay = str( delay_sbn.get_value_as_int() / 1000.0 )
        
        vbr_cbx = self.builder.get_object( 'vbr_cbx' )
        vbr_model = vbr_cbx.get_model()
        vbr = str( vbr_model[vbr_cbx.get_active_iter()][0] )
        
        schedulers = ''
        sched_flag = False
        for s in range( len( self.main_sched_chkbox ) ):
            if self.main_sched_chkbox[s][1].get_active():
                schedulers += self.main_sched_chkbox[s][0] + ' '
                sched_flag = True
        
        if not sched_flag:
            self.no_sched_dlg.run()
            return False
            
                
        prop_model_cbx = self.builder.get_object( 'prop_model_cbx' )
        prop_model_model = prop_model_cbx.get_model()
        prop_model = str( prop_model_model[prop_model_cbx.get_active_iter()][1] )
        
        frm_struct_cbx = self.builder.get_object( 'frm_struct_cbx' )
        frm_struct_model = frm_struct_cbx.get_model()
        frm_struct = str( frm_struct_model[frm_struct_cbx.get_active_iter()][0] )
        
        cqi_met_cbx = self.builder.get_object( 'cqi_met_cbx' )
        cqi_met_model = cqi_met_cbx.get_model()
        cqi_met = str( cqi_met_model[cqi_met_cbx.get_active_iter()][1] )
        
        cqi_mode_cbx = self.builder.get_object( 'cqi_mode_cbx' )
        cqi_mode_model = cqi_mode_cbx.get_model()
        cqi_mode = str( cqi_mode_model[cqi_mode_cbx.get_active_iter()][1] )        

        cqi_inter_sbn = self.builder.get_object( 'cqi_inter_sbn' )
        cqi_inter = str( cqi_inter_sbn.get_value_as_int() )                        
              
        f = open( 'setup.cfg', 'w' )
        
        f.write( 'LTE_SIM_PATH=' + self.lte_sim_path + '\n' + 
                 'SAVE_DIR=' + self.save_dir_path + '/\n' + 
                 'N_CPUs=' + n_cpu + '\n' + 
                 'ERASE_TRACE_FILES=' + erase_flag + '\n' + 
                 'N_DEC=' + n_dec + '\n' + 
                 'CDF_GRAN=' + cdf_gran + '\n' + 
                 'SIM_TIME_FLOW=' + sim_time + '\n' + 
                 'SIM_TIME=' + sim_time_flow + '\n' + 
                 'SEED=' + seed + '\n' + 
                 'NUM_SIM=' + n_sim + '\n' + 
                 'DL_BW=' + bw + '\n' + 
                 'LTE_SCENARIO=' + lte_scen + '\n' + 
                 'CELL_MODE=' + cell_mode + '\n' + 
                 'N_CELLS=' + n_cell + '\n' + 
                 'RADIUS=' + rad + '\n' + 
                 'CLUSTERS=' + clusters + '\n' + 
                 'USERS=' + n_ue + '\n' + 
                 'SPEED=' + ue_speed + '\n' + 
                 'MOBILITY_MODEL=' + ue_mob + '\n' + 
                 'N_VOIP=' + n_voip + '\n' + 
                 'N_VIDEO=' + n_video + '\n' + 
                 'N_BE=' + n_infbuf + '\n' + 
                 'N_CBR=' + n_cbr + '\n' + 
                 'MAX_DELAY=' + delay + '\n' + 
                 'VIDEO_BIT_RATE=' + vbr + '\n' + 
                 'SCHEDULERS=' + schedulers + '\n' + 
                 'PROP_MODEL=' + prop_model + '\n' + 
                 'FRAME_STRUCT=' + frm_struct + '\n' + 
                 'CQI_METHOD=' + cqi_met + '\n' + 
                 'CQI_REP_MODE=' + cqi_mode + '\n' + 
                 'CQI_REP_INTERVAL=' + cqi_inter + '\n' )

        return True


#------------------------------------------------------------------------------
    def on_cancel_sim_btn_clicked( self, widget, data=None ):
        print 'cancel sim'
        
        self.pbar.set_text( 'Canceled' )
        self.builder.get_object( 'sim_pbar_frm' ).set_sensitive( False )
       
        proc_name = self.lte_sim_path.split( '/' )[-1]
        call( ["ps -C " + proc_name + " | grep " + proc_name + " | tr -c '0123456789 \n' '?' | cut -d '?' -f1 | tr -d ' ' >> pid"], shell=True )
        
        Popen( ['kill -9 ' + str( self.proc.pid ) ], shell=True )        
       
        f = open( 'pid' )
        for line in f:
            Popen( ['kill -9 ' + line.rstrip( '\n' )], shell=True )
            
#------------------------------------------------------------------------------
    def on_cancel_res_btn_clicked( self, widget, data=None ):       
        self.pbar.set_text( 'Canceled' )
        self.builder.get_object( 'res_pbar_frm' ).set_sensitive( False )

        proc_name = os.path.abspath( __file__ ).split( '/' )[-1]
        call( ["ps -C " + proc_name + " | grep " + proc_name[:7] + " | tr -c '0123456789 \n' '?' | cut -d '?' -f1 | tr -d ' ' > pid"], shell=True )
       

        f = open( 'pid' )
        for line in f:
            if line.rstrip( '\n' ) != str( current_process().pid ):
                print 'killing ', line.rstrip( '\n' ) 
                Popen( ['kill -9 ' + line.rstrip( '\n' )], shell=True )
                
        print self.proc.pid
        Popen( ['kill -9 ' + str( self.proc.pid ) ], shell=True )        
        
        self.pbar = self.builder.get_object( 'sim_pbar' )        
        
       

        

#------------------------------------------------------------------------------
    def on_sim_done_btn_clicked( self, widget, data=None ):
        self.sim_done_dlg.hide()
        self.main_window.show_all()
#------------------------------------------------------------------------------
    #def( self, widget, data=None ):    

    

if __name__ == "__main__":
    my_gui = LteSimHelperGui()
    Gtk.main()    
