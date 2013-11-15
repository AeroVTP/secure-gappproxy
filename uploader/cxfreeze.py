import sys

from cx_Freeze import setup, Executable

base = None
extension = ''

if sys.platform == "win32":
    extension = '.exe'

buildOptions = dict(
        compressed = True,
        optimize = 2,
        create_shared_zip = True,
        include_files =[('cacerts/', 'cacerts/'),
                        ('pwddict', 'pwddict'),
                        ('../fetchserver/', 'fetchserver/'),
                        ], )


setup(
        name = "SecureGAppProxy Uploader",
        description = "A Branch of GAppProxy For Security Paranoia",
        options = dict(build_exe = buildOptions),
        executables = [Executable("uploader.py",
                                  base = 'Console',
                                  targetName='uploader%s'%extension,
                                  ),
                       ])
