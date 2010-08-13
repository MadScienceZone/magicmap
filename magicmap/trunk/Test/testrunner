#!/usr/bin/env python
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
import sys, unittestgui
sys.path.append('../lib')
import Test
import Tkinter
from Tkconstants import *
import traceback
import string
tk = Tkinter

class MyGUI (unittestgui.TkTestRunner):
    def notifyTestFailed(self, test, err):
        self.failCountVar.set(1 + self.failCountVar.get())
        self.errorListbox.insert(END, "Failure: %s: %s" % (test, err[1].message[:100]))
        self.errorInfo.append((test, err))

    def notifyTestErrored(self, test, err):
        self.errorCountVar.set(1 + self.errorCountVar.get())
        self.errorListbox.insert(END, "Error: %s: %s" % (test, err[1].message[:100]))
        self.errorInfo.append((test, err))

    def showSelectedError(self):
        selection = self.errorListbox.curselection()
        if not selection: return
        selected = int(selection[0])
        txt = self.errorListbox.get(selected)
        window = tk.Toplevel(self.root)
        window.title(txt)
        window.protocol('WM_DELETE_WINDOW', window.quit)
        test, error = self.errorInfo[selected]
        tk.Label(window, 
                text=str(test),
                foreground='red',
                justify=LEFT).pack(anchor=W)
        tracebackLines = apply(traceback.format_exception, error + (10,))
        tracebackText = '\n'.join(tracebackLines)
        tk.Label(window, text=tracebackText, justify=LEFT).pack()
        tk.Button(window, text='Close',
                command=window.quit).pack(side=BOTTOM)
        window.bind('<Key-Return>', lambda e, w=window: w.quit())
        window.mainloop()
        window.destroy()

root = tk.Tk()
root.title('testrunner (PyUnit)')
runner = MyGUI(root, 'Test.suite')
root.protocol('WM_DELETE_WINDOW', root.quit)
root.mainloop()

