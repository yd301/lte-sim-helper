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


class LteSimHelperGui(Gtk.Window):
    
    def __init__(self):
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file( 'lte-sim-helper-gui.glade' )
        
        

        self.window = self.builder.get_object( 'main_window' )
        
        self.create_cpu_cbx()
        self.create_schedulers_grid()

        self.builder.connect_signals(self)
        
            
    def create_cpu_cbx(self):
        cpu_store = Gtk.ListStore(int)
        
        l_cpus = []
        for i in range(cpu_count()):
            l_cpus.append(i+1)
            
        for cpu in l_cpus:
            cpu_store.append([cpu])
            
        cpu_cbx = self.builder.get_object('cpu_cbx')
        cpu_cbx.set_model(cpu_store)
        cpu_renderer_text = Gtk.CellRendererText()
        cpu_cbx.pack_start(cpu_renderer_text, True)
        cpu_cbx.add_attribute(cpu_renderer_text, "text", 0)
        
    def create_schedulers_grid(self):
#        sched_align = self.builder.get_object('sched_align')
#        sched_grid = Gtk.Grid()
#        sched_align.add(sched_grid)
        sched_par = self.builder.get_object('sim_par_box')
        sched_grid = Gtk.Grid()
        sched_par.pack_end(sched_grid, False, False, 0)
        
        sched_chkbtn1 = Gtk.CheckButton("PF")
        sched_chkbtn2 = Gtk.CheckButton("MT")
        
        sched_grid.attach(sched_chkbtn1, 1, 0, 2, 1)
        #sched_grid.add(sched_chkbtn2)
        
            

   
    def on_cpu_cbx_changed(self, widget, data=None):
        print 'CCCCCC'

    def on_main_window_destroy(self, widget, data=None):
        Gtk.main_quit()
        exit(0)


if __name__ == "__main__":
    my_gui = LteSimHelperGui()
    my_gui.window.show()
    Gtk.main()    
#window = MenuExampleWindow()        
#window.connect("delete-event", Gtk.main_quit)
#window.show_all()
#Gtk.main()