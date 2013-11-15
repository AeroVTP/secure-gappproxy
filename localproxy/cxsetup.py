# A simple setup script to create an executable running wxPython. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.
#
# wxapp.py is a very simple "Hello, world" type wxPython application
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

import sys
import common

from cx_Freeze import setup, Executable

base = None
extension = ''

if sys.platform == "win32":
    base = "Win32GUI"
    extension = '.exe'

buildOptions = dict(
        compressed = True,
        optimize = 2,
        create_shared_zip = True,
        include_files =[('image/', 'image/'),
                        ('cert_default/', 'cert_default/'),
                        ('proxy.conf', 'proxy.conf'),
                        ], )


setup(
        name = "Secure GAppProxy",
        version = common.VERSION,
        description = "A Branch of GAppProxy For Security Paranoia",
        options = dict(build_exe = buildOptions),
        executables = [Executable("gui.py",
                                  icon='image/logo.ico',
                                  base = base,
                                  targetName='proxy_gui%s'%extension,
                                  ),
                       Executable("console.py",
                                  base = 'Console',
                                  targetName='proxy_console%s'%extension,
                                  ),
                       ])
