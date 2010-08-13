# vi:set ai sm nu ts=4 sw=4 expandtab:

import wx

# wx.Frame(parent, id, title, pos, size, style, name)
#  style: DEFAULT_FRAME_STYLE = MINIMIZE_BOX|MAXIMIZE_BOX|RESIZE_BORDER|SYSTEM_MENU|CAPTION|CLOSE_BOX|CLIP_CHILDREN
#  .SetSize((w,h))
#  .Move(Point)                 \
#  .MoveXY(x,y)                 | what's the difference?
#  .SetPosition(Point)          |
#  .SetDimensions(Point, Size)  /
#  .Maximize()
#  .Centre()

class LeftPanel (wx.Panel):
    def __init__(self, parent, **kw):
        wx.Panel.__init__(self, parent, style=wx.BORDER_SUNKEN, **kw)
        self.text = parent.GetParent().rightPanel.text
        button1 = wx.Button(self, label='+', pos=(10,10))
        button2 = wx.Button(self, label='-', pos=(10,60))
        self.Bind(wx.EVT_BUTTON, self.OnPlus, button1)
        self.Bind(wx.EVT_BUTTON, self.OnMinus, button2)

    def OnPlus(self, event):
        self.text.SetLabel(str(int(self.text.GetLabel()) + 1))

    def OnMinus(self, event):
        self.text.SetLabel(str(int(self.text.GetLabel()) - 1))


class RightPanel (wx.Panel):
    def __init__(self, parent, **kw):
        wx.Panel.__init__(self, parent, style=wx.BORDER_SUNKEN, **kw)
        self.text = wx.StaticText(self, label='0', pos=(40,60))

class CommDemo (wx.Frame):
    def __init__(self, parent, *a, **kw):
        wx.Frame.__init__(self, parent, *a, size=(280,200), **kw)
        panel = wx.Panel(self)
        self.rightPanel = RightPanel(panel)
        leftPanel = LeftPanel(panel)
        hbox = wx.BoxSizer()
        hbox.Add(leftPanel, 1, wx.EXPAND | wx.ALL, 5)
        hbox.Add(self.rightPanel, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(hbox)
        self.Centre()
        self.Show(True)

class SimpleMenu (wx.Frame):
    def __init__(self, parent, *a, **kw):
        wx.Frame.__init__(self, parent, *a, size=(250,150), **kw)
        menubar = wx.MenuBar()
        file = wx.Menu()
        file.Append(-1, 'Quit', 'Quit application')
        menubar.Append(file, '&File')
        self.SetMenuBar(menubar)

        self.Centre()
        self.Show(True)

class MyApp (wx.App):
    def OnInit(self):
        #self.cdemo = CommDemo(None, title="simple")
        self.cdemo = SimpleMenu(None, title='menu example')
        return True

if __name__=='__main__':
    MyApp(redirect=False).MainLoop()
