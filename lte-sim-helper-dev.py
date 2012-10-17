#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
Copyright (c) 2012 Federal University of Uberlândia

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3 as
published by the Free Software Foundation;

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.

Author: Saulo da Mata <damata.saulo@gmail.com>
'''

from subprocess import call
from multiprocessing import Process, Queue, cpu_count
import sys, time, numpy, random
from datetime import timedelta, datetime
from copy import deepcopy



class LteSimHelper(object):
    
    def __init__(self):

        print '>> Hi, welcome!\n>> I`m processing your simulation parameters... '                
        self.par_dict = self.parse_setup_file('setup-dev.cfg')
        self.users_list = self.get_users_list()
        
        self.schedulers_list = self.par_dict['SCHEDULERS'].split()      

        self.bw = float(self.par_dict['DL_BW']) * pow(10, 6)
        self.n_dec = int(self.par_dict['N_DEC'])

        self.cdf_gran = int(self.par_dict['CDF_GRAN'])        
        self.cdf_factor = pow(10, len(self.par_dict['CDF_GRAN']) - 1)
        
        self.start = datetime.now() 

        call(['mkdir -p ' + self.par_dict['SAVE_DIR'] + 'sim'], shell=True)
        call(['mkdir -p ' + self.par_dict['SAVE_DIR'] + 'dat'], shell=True)
               
        self.flow_list = []                               
        if int(self.par_dict['N_VOIP']):
            self.flow_list.append('VOIP')
            call(['mkdir -p ' + self.par_dict['SAVE_DIR'] + 'dat/' + 'VOIP'], shell=True)
        
        if int(self.par_dict['N_VIDEO']):
            self.flow_list.append('VIDEO')
            call(['mkdir -p ' + self.par_dict['SAVE_DIR'] + 'dat/' + 'VIDEO'], shell=True)            
        
        if int(self.par_dict['N_BE']):
            self.flow_list.append('INF_BUF')
            call(['mkdir -p ' + self.par_dict['SAVE_DIR'] + 'dat/' + 'INF_BUF'], shell=True)            
            
            
        
       
#------------------------------------------------------------------------------        
    def get_parameters(self):
        
           
        commands = []
        
        for s in self.schedulers_list:
            for u in self.users_list:      
                for i in range(int(self.par_dict['NUM_SIM'])):
                    if self.par_dict['SEED'] == 'RANDOM':
                        seed = random.randint(0, 1000000)
                    else:
                        seed = i+1
                    tmp = self.par_dict['LTE_SIM_DIR'] + 'LTE-Sim '
                    tmp += self.par_dict['LTE_SCENARIO'] + ' ' + str(u) + ' '
                    tmp += s + ' ' + str(seed)
                    tmp2 = self.par_dict['SAVE_DIR'] + 'sim/'+ self.par_dict['LTE_SCENARIO'] + '_' + s + '_' + self.par_dict['N_CELLS'] + 'C' + str(u) + 'U_' + str(i+1) + '.sim' 
                    commands.append((tmp, tmp2, u))

        return commands
    
#------------------------------------------------------------------------------
    def run_simulations(self):        
        
        n_cpu = cpu_count()
        commands = self.get_parameters()
        n_scen = len(commands)
        running = 0
        finished = 0
        q = Queue()
               
        print '>> You have ' + str(n_scen) + ' simulations to run!'
        print '>> You`re using ' + self.par_dict['N_CPUs'] + ' of ' + str(n_cpu) + ' CPUs available in this machine!'
        self.start = datetime.now()   
        print '>> Starting simulations at ' + str(self.start) + '\n'                         
            
        try:
            while finished < n_scen:
                while len(commands):
                    if running < int(self.par_dict['N_CPUs']):
                        running += 1                   
                        if len(commands) == 1:                    
                            p = Process(target=self.trigger_simulation, args=(commands[-1], q,))
                            commands.pop()
                            self.counter('\trunning: ', running, 
                                         '\twaiting: ', len(commands), 
                                         '\tfinished: ', finished)
                            p.start()
                            p.join()
                        else:
                            p = Process(target=self.trigger_simulation, args=(commands[-1], q,))
                            p.start()
                            commands.pop()
                    else:
                        if not q.empty():
                            q.get()
                            running -= 1
                            finished += 1                        
                        time.sleep(1)
                    self.counter('\trunning: ', running, 
                                 '\twaiting: ', len(commands), 
                                 '\tfinished: ', finished)
                                        
                if not q.empty():
                    q.get()
                    running -= 1
                    finished += 1
                time.sleep(1)
                self.counter('\trunning: ', running, 
                             '\twaiting: ', len(commands), 
                             '\tfinished: ', finished)
        except KeyboardInterrupt:
            print '\n\n>> Ctrl+c pressed! Exiting...\n'
            exit()
                   
        self.counter('\trunning: ', running, 
                     '\twaiting: ', len(commands), 
                     '\tfinished: ', finished)
        print '\n\n>> The simulations have finished!' 


#------------------------------------------------------------------------------
    def trigger_simulation(self, command, q):
        
        output_file = open(command[1], 'w')
        call([command[0]], shell=True, stdout=output_file)             
        q.put([1])        

#------------------------------------------------------------------------------

    def compute_results(self):
        
        print '\n>> Processing results...'
        commands = self.get_parameters()
        self.initialize_lists(commands)
        self.spawn_processes(commands)
        
        self.write_to_file_per_flow()
               
        if self.par_dict['ERASE_TRACE_FILES'] == 'yes':
            call(['rm -rf ' + self.par_dict['SAVE_DIR'] + 'sim'], shell=True)


        end = datetime.now()
        print '\n\n>> done! (at ' + str(end) + ')\tTotal time: ',   (end - self.start)        
        print '\n>> Check your SAVE DIRECTORY!\n>> Bye!'

                              
#------------------------------------------------------------------------------
    def initialize_lists(self, commands):

        self.l_th = []
        self.l_th_2 = []
        self.l_th_bearers = []
        self.l_rx = []
        self.l_tx = []
        self.l_delay = []
        self.l_delay_occur = []
                
        for c in commands:        
            tmp_th   = []
            tmp_th_2 = []
            tmp_fi   = []
            tmp_rx   = []
            tmp_tx   = []
            tmp_delay = []
            tmp_delay_occur = []
            for f in self.flow_list:
                tmp_fi_2 = []
                tmp_th.append(0)
                tmp_th_2.append(0)                
                tmp_rx.append(0)
                tmp_tx.append(0)
                tmp_delay.append(0)
                tmp_delay_occur.append(0)
                for u in range(int(c[2])*(len(self.flow_list))):
                    tmp_fi_2.append(0)
                tmp_fi.append(tmp_fi_2)
            self.l_th.append(tmp_th)
            self.l_th_2.append(tmp_th_2)
            self.l_th_bearers.append(tmp_fi)
            self.l_rx.append(tmp_rx)
            self.l_tx.append(tmp_tx)
            self.l_delay.append(tmp_delay)        
            self.l_delay_occur.append(tmp_delay_occur)
            

#------------------------------------------------------------------------------
    def spawn_processes(self, commands):
        
        n_scen = len(commands)
        running = 0
        finished = 0
        q = Queue()        

        try:        
            while finished < n_scen:
                while len(commands):
                    if running < int(self.par_dict['N_CPUs']):
                        running += 1                   
                        if len(commands) == 1:                    
                            p = Process(target=self.parse_result_file, 
                                        args=(commands[-1][1], commands[-1][2], len(commands) - 1, q,))
                            commands.pop()
                            self.counter('\trunning: ', running, 
                                         '\twaiting: ', len(commands), 
                                         '\tfinished: ', finished)
                            p.start()
                            p.join()
                        else:
                            p = Process(target=self.parse_result_file, 
                                        args=(commands[-1][1], commands[-1][2], len(commands) - 1, q,))
                            p.start()
                            commands.pop()
                    else:
                        if not q.empty():
                            cb = q.get()
                            for k in range(len(cb[1])):
                                self.l_th[cb[0]][k] = cb[1][k]/float(self.par_dict['SIM_TIME_FLOW'])
                                self.l_th_2[cb[0]][k] = cb[1][k]/float(self.par_dict['SIM_TIME'])                            
                                self.l_rx[cb[0]][k] = cb[3][k] 
                                self.l_tx[cb[0]][k] = cb[4][k]
                                self.l_delay[cb[0]][k] = cb[5][k]
                                self.l_delay_occur[cb[0]][k] = deepcopy(cb[6][k])
                                for j in range(len(cb[2][k])):
                                    self.l_th_bearers[cb[0]][k][j] = cb[2][k][j]/float(self.par_dict['SIM_TIME_FLOW'])                            
                            running -= 1
                            finished += 1                        
                        time.sleep(0.01)
                    self.counter('\trunning: ', running, 
                                 '\twaiting: ', len(commands), 
                                 '\tfinished: ', finished)                                    
                if not q.empty():
                    cb = q.get()
                    for k in range(len(cb[1])):
                        self.l_th[cb[0]][k] = cb[1][k]/float(self.par_dict['SIM_TIME_FLOW'])
                        self.l_th_2[cb[0]][k] = cb[1][k]/float(self.par_dict['SIM_TIME'])                    
                        self.l_rx[cb[0]][k] = cb[3][k] 
                        self.l_tx[cb[0]][k] = cb[4][k]
                        self.l_delay[cb[0]][k] =  cb[5][k]             
                        self.l_delay_occur[cb[0]][k] = deepcopy(cb[6][k])
                        for j in range(len(cb[2][k])):
                            self.l_th_bearers[cb[0]][k][j] = cb[2][k][j]/float(self.par_dict['SIM_TIME_FLOW'])
                    running -= 1
                    finished += 1
                time.sleep(0.01)
                self.counter('\trunning: ', running, 
                             '\twaiting: ', len(commands), 
                             '\tfinished: ', finished)
        except KeyboardInterrupt:
            print '\n\n>> Ctrl+c pressed! Exiting...\n'
            exit()
                                       
        self.counter('\trunning: ', running, 
                     '\twaiting: ', len(commands), 
                     '\tfinished: ', finished)
        
#------------------------------------------------------------------------------
    def parse_result_file(self, file_name, u, i, q):
        
        f_data = open(file_name)
        sum_size_th = []
        sum_size_fi = []
        sum_rx = []
        sum_tx = []
        sum_delay = []      
        occur = []
        
        for f in self.flow_list:
            tmp = []
            sum_size_th.append(0)
            sum_rx.append(0)
            sum_tx.append(0)
            sum_delay.append(0)
            tmp2 = []
            for j in range(self.cdf_gran):
                tmp2.append(0)
            occur.append(tmp2)
            for s in range(int(u)*len(self.flow_list)):
                tmp.append(0)
            sum_size_fi.append(tmp)            
            
        for line in f_data:
            for f in self.flow_list:
                if line.startswith('RX ' + f):
                    tmp = line.split()
                    sum_size_th[self.flow_list.index(f)] += float(tmp[7]) * 8                         #*8: bytes to bits
                    sum_size_fi[self.flow_list.index(f)][int(tmp[5])] += float(tmp[7]) * 8
                    sum_rx[self.flow_list.index(f)] += 1
                    sum_delay[self.flow_list.index(f)] += float(tmp[13])
                    for j in range(self.cdf_gran):
                        if int(numpy.ceil(float(tmp[13])*self.cdf_gran))<=j:
                            occur[self.flow_list.index(f)][j] += 1
                    break
                elif line.startswith('TX ' + f):
                    sum_tx[self.flow_list.index(f)] += 1
                                    
        q.put([i, sum_size_th, sum_size_fi, sum_rx, sum_tx, sum_delay, occur])                            
                              
#------------------------------------------------------------------------------
    def write_to_file_per_flow(self):
        
        l_se = []
        f_se = open(self.par_dict['SAVE_DIR'] + 'dat/' + self.par_dict['LTE_SCENARIO'] + '_spectral_efficiency.dat', 'w' )
        self.insert_header_scheduler(f_se, '#SPECTRAL EFFICIENCY (bits/s/Hz)\n#USERS')
        
        for f in range(len(self.flow_list)):
            f_th = open(self.par_dict['SAVE_DIR']+ 'dat/' + self.flow_list[f] +'/'+ self.par_dict['LTE_SCENARIO'] + '_' + self.flow_list[f] + '_aggregate_throughput.dat', 'w' )
            f_th_user = open(self.par_dict['SAVE_DIR']+ 'dat/'+ self.flow_list[f] +'/'+ self.par_dict['LTE_SCENARIO'] + '_' + self.flow_list[f] + '_user_throughput.dat', 'w' )            
            f_fi = open(self.par_dict['SAVE_DIR']+ 'dat/'+ self.flow_list[f] +'/'+ self.par_dict['LTE_SCENARIO'] + '_' + self.flow_list[f] + '_fairness_index.dat', 'w' )
            f_plr = open(self.par_dict['SAVE_DIR']+ 'dat/'+ self.flow_list[f] +'/'+ self.par_dict['LTE_SCENARIO'] + '_' + self.flow_list[f] + '_packet_loss_rate.dat', 'w' )
            f_delay = open(self.par_dict['SAVE_DIR']+ 'dat/'+ self.flow_list[f] +'/'+ self.par_dict['LTE_SCENARIO'] + '_' + self.flow_list[f] + '_delay.dat', 'w' )  
            f_se_2 = open(self.par_dict['SAVE_DIR']+ 'dat/'+ self.flow_list[f] +'/'+ self.par_dict['LTE_SCENARIO'] + '_' + self.flow_list[f] + '_spectral_efficiency.dat', 'w' )        
            self.insert_header_scheduler(f_th, '#AGGREGATE CELL THROUGHPUT (Mbps)\n#USERS')
            self.insert_header_scheduler(f_th_user, '#AVERAGE USER THROUGHPUT (Mbps)\n#USERS')            
            self.insert_header_scheduler(f_fi, '#FAIRNESS INDEX\n#USERS')
            self.insert_header_scheduler(f_plr, '#PACKET LOSS RATE\n#USERS')
            self.insert_header_scheduler(f_delay, '#AVERAGE CELL DELAY (s)\n#USERS')
            self.insert_header_scheduler(f_se_2, '#SPECTRAL EFFICIENCY (bits/s/Hz)\n#USERS')            
            c = 0   
            for u in self.users_list:
                f_cdf = open(self.par_dict['SAVE_DIR']+ 'dat/'+ self.flow_list[f] +'/'+ self.par_dict['LTE_SCENARIO'] + '_' + self.flow_list[f] + '_CDF_' + str(u) + '.dat', 'w' )
                self.insert_header_scheduler(f_cdf, '#CDF ' + str(u) + ' Users\n#Delay')                
                f_th.write(str(u))
                f_th_user.write(str(u))                
                f_fi.write(str(u))
                f_plr.write(str(u))
                f_delay.write(str(u))
                f_se_2.write(str(u))                              
                for s in range(len(self.schedulers_list)):                
                    tmp_th = []
                    tmp_th_user = []                    
                    tmp_fi = []
                    tmp_plr = []
                    tmp_delay = []    
                    tmp_se = []                     
                    for i in range(int(self.par_dict['NUM_SIM'])):
                        h = i+c+(s*len(self.users_list)*int(self.par_dict['NUM_SIM']))
                        tmp_th.append(self.l_th[h][f])
                        tmp_th_user.append(self.l_th[h][f]/float(u)) 
                        try:                       
                            tmp_plr.append(1 - self.l_rx[h][f]/float(self.l_tx[h][f]))
                        except ZeroDivisionError:
                            print "\n\n>> ERROR! I could not find a throughput value. I`m quite sure that your simulation has failed!"
                            print "\tPlease take a look in .sim files!"
                            exit()
                        try:
                            tmp_delay.append(self.l_delay[h][f]/float(self.l_rx[h][f]))
                        except ZeroDivisionError:
                            tmp_delay.append(0)    
                        tmp_se.append(self.l_th_2[h][f])      
                        sum_goodput = 0
                        sum_sq_goodput = 0
                        for k in self.l_th_bearers[h][f]:
                            sum_goodput += k
                            sum_sq_goodput += pow(k,2)                                                             
                        sq_sum_goodput = pow(sum_goodput, 2)
                        try:
                            tmp_fi.append(sq_sum_goodput/float(((len(self.l_th_bearers[h][f])/len(self.flow_list)) * sum_sq_goodput)))
                        except ZeroDivisionError:
                            tmp_fi.append(0)                            
                    th_mean = round(numpy.mean(tmp_th) * pow(10, -6), self.n_dec)                    # transform to Mbps
                    th_user_mean = round(numpy.mean(tmp_th_user) * pow(10, -6), self.n_dec)          # transform to Mbps                    
                    fi_mean = round(numpy.mean(tmp_fi), self.n_dec)
                    plr_mean = round(numpy.mean(tmp_plr), self.n_dec)
                    delay_mean = round(numpy.mean(tmp_delay), self.n_dec)
                    se_mean = round(numpy.mean(tmp_se)/self.bw, self.n_dec)
                    if delay_mean == 0.0: delay_mean = 'INFINITE'
                    l_se.append((str(u), numpy.mean(tmp_se)))
                    f_th.write('\t' + str(th_mean))
                    f_th_user.write('\t' + str(th_user_mean))                    
                    f_fi.write('\t' + str(fi_mean))
                    f_plr.write('\t' + str(plr_mean))
                    f_delay.write('\t' + str(delay_mean))
                    f_se_2.write('\t' + str(se_mean))
                                        
                for w in range(self.cdf_gran):
                    f_cdf.write(str(w/float(self.cdf_gran)))
                    for s in range(len(self.schedulers_list)):
                        tmp_cdf_2 = []                      
                        for i in range(int(self.par_dict['NUM_SIM'])):
                            h = i+c+(s*len(self.users_list)*int(self.par_dict['NUM_SIM']))
                            try:
                                tmp_cdf_2.append(self.l_delay_occur[h][f][w]/float(self.l_rx[h][f]))
                            except ZeroDivisionError:
                                tmp_cdf_2.append(0)
                        cdf_mean = round(numpy.mean(tmp_cdf_2), self.n_dec)
                        f_cdf.write('\t' + str(cdf_mean))
                    f_cdf.write('\n')
                f_cdf.close()
                        
                c+=int(self.par_dict['NUM_SIM'])                    
                f_th.write('\n')
                f_th_user.write('\n')                
                f_fi.write('\n')      
                f_plr.write('\n')
                f_delay.write('\n')      
                f_se_2.write('\n')                
            f_th.close()
            f_th_user.close()            
            f_fi.close()
            f_plr.close()
            f_delay.close()
            f_se_2.close()
                  
        x = 0
        for i in range(len(self.users_list)):
            f_se.write(l_se[i*len(self.schedulers_list)][0])
            for s in range(len(self.schedulers_list)):
                tmp = []
                y = 0
                for f in range(len(self.flow_list)):
                        tmp.append(l_se[y+x][1])
                        y+= len(self.schedulers_list)*len(self.users_list)
                x+=1
                f_se.write('\t' + str(round(numpy.sum(tmp)/self.bw, self.n_dec)))
            f_se.write('\n')
        f_se.close()

#------------------------------------------------------------------------------        
    def parse_setup_file(self, file_path):
        
        par_dict = {}
        b = ' '
        
        try:
            f_config = open(file_path)
        except IOError:
            print '\n>> PARSE ERROR!! "' + file_path + '" is not a valid file path!'
            exit ()
         
        for line in f_config:
            value = ''
            #  ignoring comments and blank lines 
            if not (line.startswith('#') or line.startswith(' ') or len(line) == 1):
                if line.find('#') > 0: tmp = line.split('#')[0]
                else: tmp = line
                tmp = tmp.rstrip().split("=")
                name = tmp[0].rstrip()
                if len(tmp) > 2:
                    tmp.pop (0)
                    for v in tmp:
                        value += b + v.lstrip()
                    par_dict[name] = value
                else:
                    value = tmp[1].lstrip()
                    par_dict[name] = value
                    
        f_config.close ()

        return par_dict
    
#------------------------------------------------------------------------------    
    
    def get_users_list(self):
        tmp = self.par_dict['USERS'].split(',')
        users_list = []
        for i in tmp:
            if i.find(':') > 0:
                start = int(i.split(':')[0])
                step = int(i.split(':')[1])
                end = int(i.split(':')[2])
                n_steps = ((end - start) / step) + 1
                for n in range(n_steps):
                    users_list.append((n * step) + start)
            else:
                users_list.append(int(i))
        return users_list
                         

#------------------------------------------------------------------------------ 
    def counter (self, string1, c1, string2, c2, string3, c3):
        
       sys.stdout.write('\r' + string1 + ' ' + str(c1) + '  ' + string2 + ' ' + str(c2) + '  ' + string3 + ' ' + str(c3) + ' ')
       sys.stdout.flush()
        
#------------------------------------------------------------------------------       
    def insert_header_scheduler(self, f, title):        

        tmp = title
        for i in self.schedulers_list:
            tmp += '\t' + i
        f.write(tmp + '\n')        
        
       
#------------------------------------------------------------------------------
                
        
if __name__ == '__main__':
    
    myHelper = LteSimHelper()
    myHelper.run_simulations()
    myHelper.compute_results()    
    


