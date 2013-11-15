#!/usr/bin/python
# -*- coding: utf-8 -*-
# communicate.py
import wx
#from wx import aui
#from wx.lib.agw import supertooltip as stt
#import wx.lib.agw.toasterbox as tb
#import wx.lib.agw.shapedbutton as sb
import wx.lib.masked.numctrl as nc
import wx.lib.buttons as bt
#import wx.lib.dialogs as dl

import threading
import time
import os.path
import sys

import common
import proxycore

import config

TRAY_ICON = os.path.join(common.dir, 'image', 'logo.ico')
PLAY_ICON = os.path.join(common.dir, 'image', 'play.png')
STOP_ICON = os.path.join(common.dir, 'image', 'stop.png')

OPT_ICON = os.path.join(common.dir, 'image', 'option.png')
RED_ICON = os.path.join(common.dir, 'image', 'circle_red.png')
ORANGE_ICON = os.path.join(common.dir, 'image', 'circle_orange.png')
GREEN_ICON = os.path.join(common.dir, 'image', 'circle_green.png')
BLUE_ICON = os.path.join(common.dir, 'image', 'circle_blue.png')
WND_ICON = os.path.join(common.dir, 'image', 'logo.ico')

ABOUT_ICON = os.path.join(common.dir, 'image', 'logo_about.png')
ABOUTBTN_ICON = os.path.join(common.dir, 'image', 'logo_button.png')

ICON_HANDLE = None
WINDOW_HANDLE = None

COLOUR_NORMAL = (235, 235, 235)
COLOUR_LIGHT = (240, 240, 240)

def GetRoundBitmap( w, h, r ):
    maskColor = wx.Color(0,0,0)
    shownColor = wx.Color(5,5,5)
    b = wx.EmptyBitmap(w,h)
    dc = wx.MemoryDC(b)
    dc.SetBrush(wx.Brush(maskColor))
    dc.DrawRectangle(0,0,w,h)
    dc.SetBrush(wx.Brush(shownColor))
    dc.SetPen(wx.Pen(shownColor))
    dc.DrawRoundedRectangle(0,0,w,h,r)
    dc.SelectObject(wx.NullBitmap)
    b.SetMaskColour(maskColor)
    return b

def GetRoundShape( w, h, r ):
    return wx.RegionFromBitmap( GetRoundBitmap(w,h,r) )

class MyTipWindow(wx.Frame):
    def __init__(self, parent, target, bind=True, size=(300,40), text=""):
        #Only support windows right now
        if wx.Platform != '__WXMSW__':
            return
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, parent, title='FancyToolTip', style = style)

        self.target = target
        self.text = text

        self.size=size
        self.pos = self.target.GetScreenRect().GetBottomLeft().Get()
        self.SetPosition( self.pos )
        
        self.SetTransparent( 200 )

        self.Bind(wx.EVT_MOTION, self.OnMouse)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.lock = threading.Lock()
        self.bind = bind
        if bind:
            self.target.Bind(wx.EVT_SET_FOCUS, self.ShowTip)

        self.thread_alive = False
        self.thread = threading.Thread(target=self.MonitorMouse)
            

    def __del__(self):
        #Only support windows right now
        if wx.Platform != '__WXMSW__':
            return
            
        if self.thread.is_alive():
            self.thread_alive = False
            self.thread.join()

    def HideTip(self, event):
        self.target.Unbind(wx.EVT_KILL_FOCUS)
        if self.thread.is_alive():
            self.thread_alive = False
            #self.thread.join()
        
        self.Hide()
        self.target.Bind(wx.EVT_SET_FOCUS, self.ShowTip)
        

    def ShowTip(self, event):
        self.target.Unbind(wx.EVT_SET_FOCUS)
        self.pos = self.target.GetScreenRect().GetBottomLeft().Get()
        self.SetPosition(self.pos)
        self.Show()
        
        self.target.SetFocus()
        self.target.Bind(wx.EVT_KILL_FOCUS, self.HideTip)

        if not self.thread.is_alive():
            self.thread_alive = True
            self.thread = threading.Thread(target=self.MonitorMouse)
            self.thread.start()
        

    
    def SetRoundShape(self, event=None):
        w, h = self.GetSizeTuple()
        self.SetShape(GetRoundShape( w,h, 5 ) )
        
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc = wx.GCDC(dc)
        
        textline = self.text.split('\n')
        textrect = map(dc.GetTextExtent, textline)
        w = max(map(lambda x:x[0], textrect)) + 10
        h_array = map(lambda i:sum(map(lambda x:x[1], textrect[:i])) + 5 * i + 5,
                      range(len(textrect)+1)
                      )
        h = h_array[-1]
        r = 5

        self.size=(w,h)
        self.SetSize( (w,h) )
        self.SetRoundShape()
            
        dc.SetBrush( wx.Brush("#000000"))
        dc.DrawRoundedRectangle( 0,0,w,h,r )
        dc.SetTextForeground(wx.WHITE)

        for i, text in enumerate(textline):
            dc.DrawText( text, 5, h_array[i])

            
    def MonitorMouse(self):
        while self.thread_alive:
            if False and not self.target.IsExposedPoint(wx.Point(2,2)):
                self.target.Unbind(wx.EVT_KILL_FOCUS)
                self.thread_alive = False
                self.Hide()
                self.target.Bind(wx.EVT_SET_FOCUS, self.ShowTip)
                return
            self.pos = self.target.GetScreenRect().GetBottomLeft().Get()
            x, y = wx.GetMousePosition() - self.pos
            pos = wx.Point(self.pos[0], self.pos[1])
            w, h = self.size
            if 0 <= y <= h and 0 <= x <= w:
                if y < h/2:
                    self.SetPosition(pos + wx.Point(0, y+1))
                    self.SetTransparent( max(0, 200 - ((y)/float(h))**0.5*300) )
                else:
                    self.SetPosition(pos-wx.Point(0, h-y))
                    self.SetTransparent( max(0, 200 - ((h-y)/float(h))**0.5*300) )
            else:
                self.SetPosition(pos)
                self.SetTransparent( 200 )
            time.sleep(0.04)
        
    def OnMouse(self, event):
        self.pos = self.target.GetScreenRect().GetBottomLeft().Get()
        x, y = event.GetPosition() + self.GetPosition() - self.pos
        pos = wx.Point(self.pos[0], self.pos[1])
        w, h = self.size
        if 0 <= y <= h and 0 <= x <= w:
            if y < h/2:
                self.SetPosition(pos + wx.Point(0, y))
                self.SetTransparent( max(0, 200 - ((y)/float(h))**0.5*300) )
            else:
                self.SetPosition(pos-wx.Point(0, h-y))
                self.SetTransparent( max(0, 200 - ((h-y)/float(h))**0.5*300) )

        



def CreateMenuItem(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.AppendItem(item)
    return item

class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self):
        super(TaskBarIcon, self).__init__()
        
        icon = wx.IconFromBitmap(wx.Bitmap(TRAY_ICON))
        self.SetIcon(icon, 'Secure GAppProxy %s' % common.VERSION)
        
        self.Bind(wx.EVT_TASKBAR_LEFT_UP, self.OnShow)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        CreateMenuItem(menu, 'Show', self.OnShow)
        menu.AppendSeparator()
        CreateMenuItem(menu, 'Exit', self.OnExit)
        return menu
    
        
    def OnShow(self, event):
        global WINDOW_HANDLE
        WINDOW_HANDLE.Show()
        
        wx.CallAfter(self.Destroy)
        
    def OnExit(self, event):
        wx.CallAfter(self.Destroy)
        wx.CallAfter(WINDOW_HANDLE.Destroy)
        

class CloseConfirmDialog(wx.Dialog):
    def on_close_now(self, event):
        self.EndModal(1)

    def on_minimize(self, event):
        self.EndModal(2)
        
    def on_cancel(self, event):
        self.EndModal(3)
        
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, title='Confirm')
        sizer_all = wx.BoxSizer(wx.VERTICAL)
        sizer_all.Add(wx.StaticText(self, label='Are you sure to close?'), flag=wx.ALIGN_CENTER|wx.ALL, border=20)
        sizer_buttons = wx.BoxSizer()
        self.btnclose = wx.Button(self, label='Close Now')
        self.btnmintotray = wx.Button(self, label='Minimize To Tray')
        self.btncancel = wx.Button(self, label='Cancel')
        self.btnclose.Bind(wx.EVT_BUTTON, self.on_close_now)
        self.btnmintotray.Bind(wx.EVT_BUTTON, self.on_minimize)
        self.btncancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        sizer_buttons.Add(self.btnclose, )
        sizer_buttons.Add(self.btnmintotray, flag=wx.LEFT, border = 10)
        sizer_buttons.Add(self.btncancel, flag=wx.LEFT, border = 10)
        sizer_all.Add(sizer_buttons, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM, border = 20)
        self.SetSizer(sizer_all)

        sizer_all.Fit(self)
        self.CenterOnParent()

        
class AboutDialog(wx.Dialog):
    def on_ok(self, event):
        self.Close()
        
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, title='About')
        about_panel = self
        sizer_about = wx.BoxSizer(wx.VERTICAL)
        font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD, False, u'')
        sizer_header = wx.BoxSizer(wx.HORIZONTAL)

        logo = bt.GenBitmapButton(about_panel, -1, bitmap=wx.Bitmap(ABOUT_ICON),size=(50,50), style=wx.NO_BORDER)
        logo.SetBitmapDisabled(wx.Bitmap(ABOUT_ICON))
        logo.Disable()
        sizer_header.Add(logo)

        sizer_header_right = wx.BoxSizer(wx.VERTICAL)
        ctrl = wx.StaticText(about_panel, label='Secure GAppProxy %s' % common.VERSION)
        ctrl.SetFont(font1)
        sizer_header_right.Add(ctrl)
        sizer_copyright = wx.BoxSizer()
        
        sizer_copyright.Add(wx.StaticText(about_panel, label='Copyright (C) 2011 '))
        sizer_copyright.Add(wx.HyperlinkCtrl(about_panel, -1, label='nleven', url='http://www.nleven.com/'))
        sizer_header_right.Add(sizer_copyright, flag = wx.TOP, border = 10)

        description = """An anti-censorship software running on Google App Engine.
It's a branch of GAppProxy focused on improving security by
utilizing state-of-the-art cryptographic techniques. 
"""
        sizer_header_right.Add(wx.StaticText(about_panel, label=description), flag = wx.TOP, border = 10)
        
        sizer_header_right.Add(wx.HyperlinkCtrl(about_panel, -1, label='Project Home on Google Code', url='https://code.google.com/p/secure-gappproxy/'))

        sizer_header.Add(sizer_header_right, flag=wx.LEFT, border=10)

        sizer_about.Add(sizer_header, flag=wx.ALL, border=10)
        


        licence = """LICENCE
Secure GAppProxy is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""
        sizer_about.Add(wx.StaticText(about_panel, label=licence), flag = wx.ALL, border = 10)
        acknowledgement = """ACKNOWLEDGEMENT
SecureGAppProxy is based on GAppProxy and WallProxy.
Some icons are from www.icons-land.com, Oliver Scholtz and Capital18."""
        
        sizer_about.Add(wx.StaticText(about_panel, label=acknowledgement), flag = wx.ALL, border = 10)
        
        self.okbtn = wx.Button(about_panel, label='Okay', size=(-1,35))
        self.okbtn.Bind(wx.EVT_BUTTON, self.on_ok)
        sizer_about.Add(self.okbtn, flag = wx.ALIGN_CENTER |  wx.ALL, border = 20)

        self.SetSizer(sizer_about)
        sizer_about.Fit(self)
        self.CenterOnParent()

class VerifyCodeDlg(wx.Dialog):
    def OnOk(self, event):
        self.result = self.code.GetValue()
        self.Close()

    def GetResult(self):
        return self.result
    
    def OnClose(self, event):
        self.event.set()
        wx.CallAfter(self.Destroy)
    
    def __init__(self, parent, msg, url, event):
        wx.Dialog.__init__(self, parent, -1, title='Verification code:')
        self.result=''
        self.event = event
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        sizer_bigbox = wx.BoxSizer(wx.VERTICAL)
        
        sizer_smallbox = wx.BoxSizer(wx.VERTICAL)
        
        sizer_smallbox.Add(wx.StaticText(self, label=msg),
                           flag=wx.BOTTOM, border=10)
        sizer_smallbox.Add(wx.HyperlinkCtrl(self, -1, label='Click Here!', url=url),
                           flag=wx.BOTTOM, border=15)

        sizer_smallbox.Add(wx.StaticText(self, label='Verification Code:'),
                           flag=wx.BOTTOM, border=5)
        
        self.code = wx.TextCtrl(self, size=(310,-1), style=wx.TE_PROCESS_ENTER)
        self.code.Bind(wx.EVT_TEXT_ENTER, self.OnOk)
        
        sizer_smallbox.Add(self.code, flag=wx.BOTTOM, border=10)

        self.okbtn = wx.Button(self, size=(-1,35), label='Okay')
        self.okbtn.Bind(wx.EVT_BUTTON, self.OnOk)
        sizer_smallbox.Add(self.okbtn, flag=wx.ALIGN_RIGHT)


        sizer_bigbox.Add(sizer_smallbox, flag=wx.ALL, border=10)
        self.SetSizer(sizer_bigbox)
        sizer_bigbox.Fit(self)
        self.CenterOnParent()


class MainFrame(wx.Frame):

    def OnToggleOptions(self, event):
        self.Notify()   
        s_w, s_h = wx.DisplaySize()
        if self.GetScreenRect().GetBottom() > s_h:
            w, h = self.GetSizeTuple()
            left, _ = self.GetPosition()
            self.SetPosition((left, (s_h - h)/2))
        
    notimpexp = Exception("Not implemented!\nThis is not your fault. It's mine.\nFuture versions will implement this feature. Stay tuned.")
    def async_start(self):
        if self.core.Running():
            self.core.StopProxy()
        else:
            self.core.Initialize()
            self.core.StartProxy(persistent=False)
            
        if self.core.Running():
            self.startbtn.SetBitmapLabel(wx.Bitmap(STOP_ICON))            
        else:
            self.startbtn.SetBitmapLabel(wx.Bitmap(PLAY_ICON))
            self.PushStatusText('SecureGAppProxy is not running.', RED_ICON)
        self.startbtn.Enable()
            
    def OnStart(self, event):
        if self.core.Running():
            self.PushStatusText("Stopping...", ORANGE_ICON)
        else:
            if self.servertext.GetValue() == '':
                self.servertext.SetFocus()
                return
            if not self.pwdfake and self.pwdtext.GetValue() == '':
                self.pwdtext.SetFocus()
                return
            
            self.SaveConfig(simple=True)
                
        self.startbtn.Disable()
        self.start_thread = threading.Thread(target=self.async_start)
        self.start_thread.setDaemon(True)
        self.start_thread.start()

    def __async_restart(self):
        self.core.StopProxy()
        self.async_start()

    def OnSaveApply(self, event):
        self.SaveConfig()
        if self.core.Running():
            self.startbtn.Disable()
            self.start_thread = threading.Thread(target=self.__async_restart)
            self.start_thread.setDaemon(True)
            self.start_thread.start()
        
    def on_clear_cert(self, event):
        raise MainFrame.notimpexp
    
    def on_install_cert(self, event):
        raise MainFrame.notimpexp

    def Notify(self):
        if not self.optbtn.GetValue():
            self.SetMinSize(self.min_size)
            self.SetClientSize(self.min_size)
        else:
            self.SetMinSize(self.expand_size)
            self.SetClientSize(self.expand_size)
            
        if self.proxycheck.IsChecked():
            self.proxytext.Enable()
            self.proxyporttext.Enable()
            self.proxyauthcheck.Enable()
        else:
            self.proxytext.Disable()
            self.proxyporttext.Disable()
            self.proxytext.SetValue('')
            self.proxyporttext.SetValue('')
            self.proxyauthcheck.Disable()

        if self.proxycheck.IsChecked() and self.proxyauthcheck.IsChecked():
            self.proxyusertext.Enable()
            self.proxypwdtext.Enable()
        else:
            self.proxyusertext.Disable()
            self.proxypwdtext.Disable()
            self.proxyusertext.SetValue('')
            self.proxypwdtext.SetValue('')
            
    def on_check_proxy(self, event):
        self.Notify()
            

    def on_about(self, event):
        aboutdlg = AboutDialog(self)
        aboutdlg.ShowModal()

    def on_close(self, event):
        dlg = CloseConfirmDialog(self)
        ret = dlg.ShowModal()
        if ret == 1:
            if self.core.Running():
                self.core.StopProxy()
            self.Destroy()
        elif ret == 2:
            ICON_HANDLE = TaskBarIcon()
            self.Hide()
        elif ret == 3:
            pass
        else:
            raise Exception('Unknown return code %s from CloseConfirmDialog' % str(ret))
            

    def on_paint_status(self, event):
        obj = event.GetEventObject()
        dc = wx.PaintDC(obj)
        dc = wx.GCDC(dc)
        

        if wx.Platform != '__WXMSW__':
            font1 = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.FONTWEIGHT_NORMAL, False, u'')
            dc.SetFont(font1)

        w,h = obj.GetSizeTuple()
        t_w, t_h = dc.GetTextExtent(self.statustext)

        text = self.statustext
        #Omit from the center if the status text is too long
        max_t_w = w - 32

        if t_w > max_t_w:
            while t_w > max_t_w:
                mid = len(text) / 2
                text = text[:mid] + text[mid+1:]
                t_w, t_h = dc.GetTextExtent(text)
            if len(text) >= 5:
                mid = len(text) / 2
                text = text[:mid-1] + '...' + text[mid+2:]
                
        d_w, d_h = t_w+32, h
        d_left, d_top = w - d_w, h-d_h
        b_left, b_top = d_left + 5, d_top + 5
        t_left, t_top = b_left + 22, d_top + max(0, (d_h-t_h)/2)
        r=12
        
        dc.BeginDrawing()
        dc.SetBrush( wx.Brush("#999999"))
        dc.SetPen( wx.Pen("#999999", width = 2 ) )
        dc.DrawRoundedRectangle( d_left,d_top,d_w,d_h,r)
        dc.DrawRectangle(d_left+d_w-r,d_top, r,d_h)

        dc.SetTextForeground("#ffffff")
        dc.DrawBitmap(self.statusicon, b_left, b_top, True)
        dc.DrawText( text, t_left, t_top)
        dc.EndDrawing()

    def SaveConfig(self, simple=False, persistent=True):
        """Save the user settings to the configuration file."""
        config.SetParam('fetch_server', self.servertext.GetValue())
        if self.rememberchk.GetValue() and self.pwdtext.GetValue() != '':
            if not self.pwdfake:
                import pkcs5
                password = pkcs5.PBKDF1(self.pwdtext.GetValue(), config.GetParam('fetch_server').lower())
                config.SetParam('password', password)
                self.pwdfake = True
        else:
            config.DeleteParam('password')

        if not simple:
            config.SetParam('listen_port', self.porttext.GetValue())
            if self.httpschk.GetValue():
                config.SetParam('fetch_protocol', 'https')
            else:
                config.SetParam('fetch_protocol', 'http')
            
            config.SetParam('auto_redirect', True)

            if self.proxycheck.GetValue():
                if self.proxyauthcheck.GetValue():
                    config.SetParam('local_proxy',
                                    '%s:%s@%s:%d' % (self.proxyusertext.GetValue(),
                                                     self.proxypwdtext.GetValue(),
                                                     self.proxytext.GetValue(),
                                                     self.proxyporttext.GetValue() )
                                    )
                else:
                    config.SetParam('local_proxy',
                                    '%s:%d' % (self.proxytext.GetValue(),
                                               self.proxyporttext.GetValue() )
                                    )
            else:
                config.SetParam('local_proxy', '')

            
            if wx.Platform == '__WXMSW__' and common.we_are_frozen():
                if self.autostartchk.GetValue():
                    try:
                        import _winreg
                        hkey = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
                        _winreg.SetValueEx(hkey, "secure-gappproxy", 0, _winreg.REG_SZ, sys.executable)
                        _winreg.CloseKey(hkey)
                    except:
                        _winreg.CloseKey(hkey)
                else:
                    try:
                        import _winreg
                        hkey = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
                        _winreg.DeleteValue(hkey, "secure-gappproxy")
                        _winreg.CloseKey(hkey)
                    except:
                        _winreg.CloseKey(hkey)


        if persistent: 
            config.SaveConfig()
        
        
        
    def LoadConfig(self):
        """Load configuration to UI controls."""
        self.servertext.SetValue( config.GetParam('fetch_server') )
        self.porttext.SetValue( config.GetParam('listen_port') )
        self.httpschk.SetValue( config.GetParam('fetch_protocol') == 'https' )
        self.hostchk.SetValue( config.GetParam('auto_redirect') )
        if config.GetParam('password') != None:
            #We cannot extract the original password from the stored hash
            #Therefore, we have to place a fake place holder in the password box to fool the user
            self.rememberchk.SetValue( True )
            self.pwdtext.SetValue('PigPigLaLaLa~~')
            self.pwdfake = True
        else:
            self.rememberchk.SetValue( False )

        localproxy = config.GetParam('local_proxy')
        self.proxycheck.SetValue(localproxy != "")
        self.proxyauthcheck.SetValue('@' in localproxy)
        #Proxy requires authentication
        if '@' in localproxy:
            userpwd, _, hostport = localproxy.partition('@')
            user, _, pwd = userpwd.partition(':')
            self.proxyusertext.SetValue(user)
            self.proxypwdtext.SetValue(pwd)
        else:
            hostport = localproxy
        host, _, port = hostport.partition(':')
        self.proxytext.SetValue(host)
        self.proxyporttext.SetValue(port)

        if wx.Platform == '__WXMSW__' and common.we_are_frozen():
            import _winreg
            try:
                hkey = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
                val, _ = _winreg.QueryValueEx(hkey, "secure-gappproxy")
                self.autostartchk.SetValue( val == sys.executable)
                _winreg.CloseKey(hkey)
            except:
                self.autostartchk.SetValue(False)
                _winreg.CloseKey(hkey)


        #Notify the change of checkbox states
        self.Notify()
        
    def OnPwdFocus(self, event):
        #If password is fake, we should not allow the user to edit it
        #Therefore, simply clear it.
        if self.pwdfake:
            self.pwdfake = False
            self.pwdtext.SetValue('')

    def OnEnterSubmit(self, event):
        self.OnStart(None)
        
    def OnCheckRememberPwd(self, event):
        self.SaveConfig(simple=True)
        
    def PushStatusText(self, text, icon=BLUE_ICON):
        self.statustext = text
        self.statusicon = wx.Bitmap(icon)
        self.statusbar.Refresh()
    
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.FULL_REPAINT_ON_RESIZE)
        #Initialize proxy core
        self.core = proxycore.ProxyCore(Notifier(self))

        
        self.start_thread = None

        self.SetIcon(wx.Icon(WND_ICON, wx.BITMAP_TYPE_ICO))
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.out_panel = wx.Panel(self)
        
        simple_panel = wx.Panel(self.out_panel)
        self.simple_panel = simple_panel
        sizer_opts = wx.FlexGridSizer(rows=2,cols=2,vgap=10,hgap=5)
        sizer_opts.Add(wx.StaticText(simple_panel, label='Fetch Server:'), flag=wx.EXPAND | wx.TOP, border=3)
        self.servertext = wx.TextCtrl(simple_panel, value='your-appspot-id.appspot.com',size=(210,-1), style=wx.TE_PROCESS_ENTER)
        self.servertext.Bind(wx.EVT_TEXT_ENTER, self.OnEnterSubmit)
        sizer_opts.Add(self.servertext, flag=wx.EXPAND)
        sizer_opts.Add(wx.StaticText(simple_panel, label='Password:'), flag=wx.EXPAND | wx.TOP, border=3)
        sizer_pwd = wx.BoxSizer(wx.VERTICAL)
        self.pwdtext = wx.TextCtrl(simple_panel, value='', size=(210,-1), style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
        self.pwdtext.Bind(wx.EVT_SET_FOCUS, self.OnPwdFocus)
        self.pwdtext.Bind(wx.EVT_TEXT_ENTER, self.OnEnterSubmit)
        self.pwdfake = False
        sizer_pwd.Add(self.pwdtext, flag=wx.EXPAND | wx.BOTTOM, border=10)
        self.rememberchk = wx.CheckBox(simple_panel, label="Remember password.")
        sizer_pwd.Add(self.rememberchk, flag=wx.EXPAND)
        self.rememberchk.Bind(wx.EVT_CHECKBOX, self.OnCheckRememberPwd)
        sizer_pwd.Add(wx.StaticText(simple_panel, label="Do NOT check this if it's a public computer."), flag=wx.TOP, border=3)
        sizer_opts.Add(sizer_pwd, flag=wx.EXPAND)
        
        self.optbtn = bt.GenBitmapTextToggleButton(simple_panel, -1, bitmap=wx.Bitmap(OPT_ICON), style=wx.NO_BORDER, label='Options')
        self.optbtn.Bind(wx.EVT_BUTTON, self.OnToggleOptions)
        sizer_opts.Add(self.optbtn)
        
        sizer_start = wx.BoxSizer(wx.HORIZONTAL)
        sizer_start.Add(sizer_opts, flag=wx.EXPAND| wx.ALL, border=10)
        self.startbtn = bt.GenBitmapButton(simple_panel, -1, bitmap=wx.Bitmap(PLAY_ICON),size=(81,81), style=wx.NO_BORDER)
        if wx.Platform != '__WXMSW__':
            #Some hack
            self.startbtn.SetBackgroundColour(COLOUR_NORMAL)
            self.startbtn.faceDnClr = COLOUR_NORMAL
        else:
            self.startbtn.faceDnClr = self.startbtn.GetBackgroundColour()
        self.startbtn.Bind(wx.EVT_BUTTON, self.OnStart)
        sizer_start.Add(self.startbtn, flag=wx.ALIGN_TOP | wx.ALL, border=10)

        sizer_out = wx.BoxSizer(wx.VERTICAL)
        sizer_out.Add(sizer_start, flag=wx.EXPAND | wx.ALL, border=10)


        simple_panel.SetSizer(sizer_out)
        
        

        adv_panel = wx.Panel(self.out_panel)
        self.adv_panel = adv_panel
        sizer_adv = wx.FlexGridSizer(rows=5, cols=2, vgap=10, hgap=5)
        
        sizer_adv.Add(wx.StaticText(adv_panel, label='Local Proxy:'), flag=wx.EXPAND | wx.TOP, border=3)
        sizer_proxy_out = wx.BoxSizer(wx.VERTICAL)
        self.proxycheck = wx.CheckBox(adv_panel, label='Check this if you are behind a proxy.')
        self.proxycheck.Bind(wx.EVT_CHECKBOX, self.on_check_proxy)
        sizer_proxy_out.Add(self.proxycheck, flag=wx.EXPAND|wx.TOP, border=5)
        sizer_proxy = wx.BoxSizer(wx.HORIZONTAL)
        sizer_proxy.Add(wx.StaticText(adv_panel, label='Host:'), flag=wx.EXPAND | wx.TOP, border=3)
        self.proxytext = wx.TextCtrl(adv_panel, value='', size=(160,-1))
        MyTipWindow(self, self.proxytext, text='Your local proxy. e.g. proxy.company.com')
        sizer_proxy.Add(self.proxytext, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
        sizer_proxy.Add(wx.StaticText(adv_panel, label='Port:'), flag=wx.EXPAND | wx.TOP, border=3)
        self.proxyporttext = nc.NumCtrl( adv_panel, id = -1, value = None, integerWidth=5, allowNone=True, limited=True, limitOnFieldChange=True,selectOnEntry = True, groupDigits = False, min = 1, max = 65535 )
        MyTipWindow(self, self.proxyporttext, text='The port of the proxy. e.g. 8080')
        sizer_proxy.Add(self.proxyporttext, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
        
        sizer_proxy_out.Add(sizer_proxy, flag=wx.TOP, border=5)

        self.proxyauthcheck = wx.CheckBox(adv_panel, label='Check this if proxy requires authentication.')
        sizer_proxy_out.Add(self.proxyauthcheck, flag=wx.EXPAND|wx.TOP, border=5)
        self.proxyauthcheck.Bind(wx.EVT_CHECKBOX, self.on_check_proxy)
        sizer_auth = wx.BoxSizer(wx.HORIZONTAL)
        sizer_auth.Add(wx.StaticText(adv_panel, label='Username:'), flag=wx.EXPAND | wx.TOP, border=3)
        self.proxyusertext = wx.TextCtrl(adv_panel, value='', size=(90,-1))
        sizer_auth.Add(self.proxyusertext, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        sizer_auth.Add(wx.StaticText(adv_panel, label='Password:'), flag=wx.EXPAND|wx.TOP, border=3)        
        self.proxypwdtext = wx.TextCtrl(adv_panel, value='', size=(90,-1), style=wx.TE_PASSWORD)
        sizer_auth.Add(self.proxypwdtext, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        sizer_proxy_out.Add(sizer_auth, flag=wx.EXPAND|wx.TOP, border=5)
        
        
        sizer_adv.Add(sizer_proxy_out)

        

        sizer_adv.Add(wx.StaticText(adv_panel, label='Listen port:'), flag=wx.EXPAND | wx.TOP, border=3)
        self.porttext = nc.NumCtrl( adv_panel, id = -1, value = 8000, limited=True, limitOnFieldChange=True,selectOnEntry = True, groupDigits = False, min = 1, max = 65535 )
        MyTipWindow(self, self.porttext, text='The local port Secure GAppProxy listens on. There\'re very few reasons to change this.\nPort number should be from 1 to 65535.')
        sizer_adv.Add(self.porttext)
        
        sizer_adv.Add(wx.StaticText(adv_panel, label='Options:'), flag=wx.EXPAND | wx.TOP, border=3)
        sizer_advopts = wx.BoxSizer(wx.VERTICAL)
        self.httpschk = wx.CheckBox(adv_panel, label='Connect fetch server with HTTPS.')
        sizer_advopts.Add(self.httpschk, flag=wx.EXPAND | wx.BOTTOM, border=10)
        self.hostchk = wx.CheckBox(adv_panel, label='Try to detect and resolve connectivity issues on startup.')
        sizer_advopts.Add(self.hostchk, flag=wx.EXPAND | wx.BOTTOM, border=10)
        if wx.Platform == '__WXMSW__' and common.we_are_frozen():
            self.autostartchk = wx.CheckBox(adv_panel, label='Start proxy with Windows.')
            sizer_advopts.Add(self.autostartchk)
        sizer_adv.Add(sizer_advopts)
        
        ##sizer_adv.Add(wx.StaticText(adv_panel, label='Certificate:'), flag=wx.EXPAND | wx.TOP, border=3)
        ##sizer_certopts = wx.BoxSizer(wx.VERTICAL)
        ##self.clearcachebtn = wx.Button(adv_panel, label='Clear Certificate Cache')
        ##self.clearcachebtn.Bind(wx.EVT_BUTTON, self.on_clear_cert)
        ##sizer_certopts.Add(self.clearcachebtn)
        ##self.installcertbtn = wx.Button(adv_panel, label='Install Root Certificate')
        ##self.installcertbtn.Bind(wx.EVT_BUTTON, self.on_install_cert)
        ##sizer_certopts.Add(self.installcertbtn)
        ##sizer_adv.Add(sizer_certopts)

        sizer_adv_box = wx.BoxSizer(wx.VERTICAL)
        sizer_adv_box.Add(sizer_adv, flag=wx.EXPAND | wx.ALL, border=20)
        

        self.savebtn = wx.Button(adv_panel, size=(-1,35), label='Save and Apply')
        self.savebtn.Bind(wx.EVT_BUTTON, self.OnSaveApply)
        sizer_adv_box.Add((-1, 30))
        sizer_adv_box.Add(self.savebtn, flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT, border=20)
        
        adv_panel.SetSizer(sizer_adv_box)

        sizer_final = wx.BoxSizer(wx.VERTICAL)
        sizer_final.Add(simple_panel, flag=wx.EXPAND)
        sizer_final.Add(adv_panel, flag=wx.EXPAND)

        self.out_panel.SetSizer(sizer_final)
        
        MyTipWindow(self, self.servertext, text='Fetch server running on GAE. e.g. your-appspot-id.appspot.com')

        self.min_size = sizer_out.GetMinSize().Get()
        w1, h1 = sizer_out.GetMinSize().Get()
        w2, h2 = sizer_adv_box.GetMinSize().Get()
        self.expand_size = (max(w1,w2), h1+h2)
        self.Notify()

        self.Center()
        self.Show(True)
        self.startbtn.SetFocus()


        w,h = self.min_size
        self.statusbar = wx.Panel(simple_panel, style=wx.NO_BORDER, size=(300,25), pos=(w-300, h-35))
        self.statustext='SecureGAppProxy is not running.'
        self.statusicon = wx.Bitmap(RED_ICON)
        self.statusbar.Bind(wx.EVT_PAINT, self.on_paint_status)
        self.statusbar.Refresh()

        self.about_btn = bt.GenBitmapTextButton(adv_panel, -1, bitmap=wx.Bitmap(ABOUTBTN_ICON), style=wx.NO_BORDER, label='About')
        
        self.about_btn.Bind(wx.EVT_BUTTON, self.on_about)
        if wx.Platform != '__WXMSW__':
            self.about_btn.SetBackgroundColour(COLOUR_NORMAL)
            self.about_btn.faceDnClr = COLOUR_NORMAL
        self.about_btn.SetBestSize((-1,-1))
        p1, p2 = adv_panel.GetClientRect().GetBottomLeft().Get()
        q1, q2 = self.about_btn.GetSizeTuple()
        self.about_btn.SetPosition((0, p2-q2))

        if wx.Platform != '__WXMSW__':
            #Set background colour
            self.out_panel.SetBackgroundColour(COLOUR_NORMAL)
            simple_panel.SetBackgroundColour(COLOUR_NORMAL)
            adv_panel.SetBackgroundColour(COLOUR_NORMAL)
            self.statusbar.SetBackgroundColour(COLOUR_NORMAL)
        

        self.LoadConfig()

        #If we have the parameters needed, automatically connect
        if config.GetParam('password') != None and config.GetParam('fetch_server') != '':
            self.OnStart(None)
            

        

        
class Notifier:
    def __init__(self, mainframe):
        self.frame = mainframe
        
    def PushStatus(self, text):
        self.frame.PushStatusText(text)

    def PushError(self, text):
        wx.CallAfter(lambda:self.__dlg_helper(lambda:wx.MessageDialog(self.frame, text, 'Error', wx.ICON_ERROR)))

    def PushMessage(self, text):
        wx.CallAfter(lambda:self.__dlg_helper(lambda:wx.MessageDialog(self.frame, text, 'Messagae', wx.ICON_EXCLAMATION)))

    def __dlg_helper(self, dlg_creator, dlg_holder=None):
        dlg = dlg_creator()
        if dlg_holder:
            dlg_holder[0] = dlg
        dlg.ShowModal()
        
    def RequestCaptcha(self, msg, url):
        event = threading.Event()
        dlg_holder = [None]
        wx.CallAfter(lambda:self.__dlg_helper(lambda:VerifyCodeDlg(WINDOW_HANDLE, msg, url,event),
                                              dlg_holder))
        event.wait()
        return dlg_holder[0].GetResult()
        

    def RequestPassword(self):
        assert not self.frame.pwdfake
        return self.frame.pwdtext.GetValue()




app = wx.App()
WINDOW_HANDLE = MainFrame(None, -1, 'Secure GAppProxy %s' % common.VERSION)



app.MainLoop()
