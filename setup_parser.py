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

class SetupParser( object ):
    
    def parse( self, file_path ):
        
        par_dict = {}
        b = ' '
        
        try:
            f_config = open( file_path )
        except IOError:
            print '\n>> PARSE ERROR!! "' + file_path + '" is not a valid file path!'
            exit ()
         
        for line in f_config:
            value = ''
            #  ignoring comments and blank lines 
            if not ( line.startswith( '#' ) or line.startswith( ' ' ) or len( line ) == 1 ):
                if line.find( '#' ) > 0: tmp = line.split( '#' )[0]
                else: tmp = line
                tmp = tmp.rstrip().split( "=" )
                name = tmp[0].rstrip()
                if len( tmp ) > 2:
                    tmp.pop ( 0 )
                    for v in tmp:
                        value += b + v.lstrip()
                    par_dict[name] = value
                else:
                    value = tmp[1].lstrip()
                    par_dict[name] = value
                    
        f_config.close ()

        return par_dict
