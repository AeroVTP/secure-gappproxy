#! /usr/bin/env python
# coding=utf-8
#======================================================================
# SecureGAppProxy is a security-strengthened version of GAppProxy.
# http://secure-gappproxy.googlecode.com                               
# This file is a part of SecureGAppProxy.                              
# Copyright (C) 2011  nleven <www.nleven.com i@nleven.com>             
#                                                                      
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or    
# (at your option) any later version.                                  
#                                                                      
# This program is distributed in the hope that it will be useful,      
# but WITHOUT ANY WARRANTY; without even the implied warranty of       
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        
# GNU General Public License for more details.                         
#                                                                      
# You should have received a copy of the GNU General Public License    
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#                                                                      
# ACKNOWLEDGEMENT                                                      
# SecureGAppProxy is a based on the work of GAppProxy                  
# <http://gappproxy.googlecode.com> by Du XiaoGang <dugang@188.com>
#======================================================================


from distutils.core import setup
import py2exe
import glob
import common

MANIFEST_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
  />
  <description>%(prog)s</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel
            level="asInvoker"
            uiAccess="false">
        </requestedExecutionLevel>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="x86"
            publicKeyToken="1fc8b3b9a1e18e3b">
      </assemblyIdentity>
    </dependentAssembly>
  </dependency>
  <dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
  </dependency>
</assembly>
"""


setup(
    options = {"py2exe": 
        { "optimize": 2,
          "compressed": 0,
          "bundle_files": 1,
          "excludes":['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger',
                      'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl', 'Tkconstants',
                      'Tkinter'],
          "dll_excludes": ['w9xpopen.exe', 'mswsock.dll', 'powrprof.dll', 'uxTheme.dll',
                           'msvcp90.dll']
        }
    },
    zipfile='library/data',

    name = "Secure GAppProxy",
    version = common.VERSION,
    description = "A Branch of GAppProxy For Security Paranoia",

    console=[{'script':'console.py',
              'dest_base':'proxy_console',
              }],
    windows=[{'script':'gui.py',
              'dest_base':'proxy_gui',
              'icon_resources': [(0, 'image/logo.ico')],
              'other_resources': [(24, 1, MANIFEST_TEMPLATE % dict(prog="Secure GAppProxy"))],
              }],
    
    data_files = [
        ('cert_default', glob.glob('cert_default/*')),
        ('.', ['proxy.conf']),
        ('image', glob.glob('image/*'))
    ]
)
