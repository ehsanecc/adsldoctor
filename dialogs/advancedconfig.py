import tkinter as tk

from numpy import timedelta64
from numpy.core.fromnumeric import var
from numpy.lib.arraypad import pad
from libs.adsltelnet import ADSLTelnet
from libs.tooltip import (ToolTip, createToolTip)
from tkinter import messagebox

"""
mod: checkbox (multiple)
    a All modulations are allowed.
    d G.DMT
    l G.Lite
    t T1.413
    2 ADSL2(G.992.3)
    p ADSL2+(G.992.5)
    e Annex L
    m Annex M
lpair: radio
    i inner loop pair
    o outer loop pair
bitswap: checkbox
    on/off
sra: checkbox
    on/off
trellis: checkbox
    on/off
sesdrop: checkbox
    on/off
CoMinMgn: checkbox
    on/off
i24k: checkbox
    on/off
monitorTone: checkbox
    on/off
forceJ43: checkbox
    on/off
toggleJ43B43: checkbox
    on/off
"""

class AdvancedConfig(tk.Toplevel):
    def __init__(self, master=None, connection:ADSLTelnet=None, adsl_cmd='adsl', config:dict=None) -> None:
        super().__init__(master)
        self.master = master
        self.conn = connection
        self.adsl_cmd = adsl_cmd
        self.resizable(False, False) # not resizable by user
        self.title('Advanced ADSL PHY Configurations')
        
        self.noch = [] # if any advanced (nochange) options changes, we add it to command
        lf_mod = tk.LabelFrame(self, text='Allowed modulations', width=600, heigh=230)
        lf_mod.grid_propagate(0)
        lf_mod.grid(column=0, columnspan=2, row=0, padx=5, pady=5, sticky='W')
        self.mod = {
            'a':{'var':tk.IntVar(), 'title':'All modulations are allowed.', 'command':self.onModChange}, # All modulations are allowed.
            'd':{'var':tk.IntVar(), 'title':'G.DMT', 'command':self.onChange}, # G.DMT
            'l':{'var':tk.IntVar(), 'title':'G.Lite', 'command':self.onChange}, # G.Lite
            't':{'var':tk.IntVar(), 'title':'T1.413', 'command':self.onChange}, # T1.413
            '2':{'var':tk.IntVar(), 'title':'ADSL2(G.992.3)', 'command':self.onChange}, # ADSL2(G.992.3)
            'p':{'var':tk.IntVar(), 'title':'Annex L', 'command':self.onChange}, # ADSL2+(G.992.5)
            'e':{'var':tk.IntVar(), 'title':'ADSL2+(G.992.5)', 'command':self.onChange}, # Annex L
            'm':{'var':tk.IntVar(), 'title':'Annex M', 'command':self.onChange}, # Annex M
        }
        self.optionFrame(lf_mod, self.mod)

        lf_pair = tk.LabelFrame(self, text='Phone line pair', width=600, height=80)
        lf_pair.grid_propagate(0)
        lf_pair.grid(column=0, columnspan=2, row=1, padx=5, pady=5, sticky='W')
        self.lpair_val = tk.StringVar()
        self.lpair_val.set('o')
        tk.Radiobutton(lf_pair, text='Outer loop pair', value='o', variable=self.lpair_val, command=self.onChange)\
            .grid(column=0, row=0, sticky='W')
        tk.Radiobutton(lf_pair, text='Inner loop pair', value='i', variable=self.lpair_val, command=self.onChange)\
            .grid(column=0, row=1, sticky='W')

        self.lf_cap = tk.LabelFrame(self, text='Capabilities', width=600, height=50)
        self.lf_cap.grid_propagate(0)
        self.lf_cap.grid(column=0, columnspan=2, row=2, padx=5, pady=5, sticky='W')
        self.cap = {
            'bitswap':{'var': tk.IntVar(self, 0), 'title':'Bitswap Enable', 'command':self.onChange},
            'sra':{'var': tk.IntVar(self, 0), 'title':'SRA Enable', 'command':self.onChange},

            'trellis':{'var': tk.IntVar(self, 0), 'title':'Trellis Coding Enable', 'noch':True, 'fg':'orange', 'command':self.onChange},
            'sesdrop':{'var': tk.IntVar(self, 0), 'title':'sesdrop Enable', 'noch':True, 'fg':'orange', 'command':self.onChange},
            'CoMinMgn':{'var': tk.IntVar(self, 0), 'title':'CoMinMgn Enable', 'noch':True, 'fg':'orange', 'command':self.onChange},
            'i24k':{'var': tk.IntVar(self, 0), 'title':'i24k Enable', 'noch':True, 'fg':'orange', 'command':self.onChange},
            'monitorTone':{'var': tk.IntVar(self, 0), 'title':'monitorTone Enable', 'noch':True, 'fg':'orange', 'command':self.onChange},
            'forceJ43':{'var': tk.IntVar(self, 0), 'title':'forceJ43 Enable', 'noch':True, 'fg':'orange', 'command':self.onChange},
            'toggleJ43B43':{'var': tk.IntVar(self, 0), 'title':'toggleJ43B43 Enable', 'noch':True, 'fg':'orange', 'command':self.onChange}
        }
        self.optionFrame(self.lf_cap, self.cap)

        self.cmd = tk.StringVar(self, value='')
        self.cmd_label = tk.Label(self, textvariable=self.cmd)
        self.cmd_label.grid(row=3, sticky='W')
        tk.Button(self, text='Execute', fg='red', command=self.exeCmd).\
            grid(column=1, row=3, sticky='E', padx=5, pady=5)

    def exeCmd(self):
        if self.cmd.get().find(self.adsl_cmd) > -1:
            print('Executing ' + self.cmd.get())
            self.conn.send_cmd(self.cmd.get())
            messagebox.showinfo(title='Success', message='Be sure to SAVE in main menu to make these changes permanent.')
        else:
            messagebox.showwarning(title='Nothing!', message='Nothing to execute! please make some change in options!')

    def optionFrame(self, frame:tk.LabelFrame, options:dict):
        for op in options.keys():
            tk.Checkbutton(frame, text=options[op]['title'], variable=options[op]['var'],\
                command=options[op]['command'] if 'command' in options[op] else None,\
                fg=options[op]['fg'] if 'fg' in options[op] else 'black').\
                    grid(column=0, sticky='W')
        frame.config( height=25 * (len(options.keys())+1) )

    def onModChange(self):
        if self.mod['a']['var'].get() == 1:
            self.mod['d']['var'].set(1)
            self.mod['l']['var'].set(1)
            self.mod['t']['var'].set(1)
            self.mod['2']['var'].set(1)
            self.mod['p']['var'].set(1)
            self.mod['e']['var'].set(1)
            self.mod['m']['var'].set(1)
        self.onChange()

    def onChange(self): # any option change
        options = []
        options.append('--mod '+''.join([k if self.mod[k]['var'].get() == 1 else '' for k in self.mod.keys()]) )
        options.append('--lpair '+self.lpair_val.get())
        for k in self.cap.keys():
            if 'noch' in self.cap[k] and self.cap[k]['var'].get() == 1 and k not in self.noch:
                if messagebox.askyesno(title='WARNING!!! ADVANCED OPTION!!!', \
                    message='You are about to change an advanced option in your modem!! Are you sure?'):
                    self.noch.append(k)
                else:
                    self.cap[k]['var'].set(0)
            if 'noch' not in self.cap[k] or self.cap[k]['noch'] == False or k in self.noch:
                options.append(f"--{k} {'on' if self.cap[k]['var'].get() == 1 else 'off'}")
        
        self.cmd.set(f"{self.adsl_cmd} configure {' '.join(options)}")