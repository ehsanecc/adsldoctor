import os, re
import numpy as np
import tkinter as tk
import configparser as cp
import matplotlib.pyplot as plt
from tkinter import messagebox
from dialogs.advancedconfig import AdvancedConfig
from libs.adsltelnet import ADSLTelnet
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler

class ADSLDoctor(tk.Frame):
    def __init__(self, master=None, config:cp.ConfigParser=None) -> None:
        super().__init__(master)
        self.master = master
        self.config = config

        # default values
        self.connection:ADSLTelnet = None
        self.available_commands = []
        self.adsl_cmd = ''
        self.adsl_info = {}
        self.adsl_profile = {}
        self.cur_to_des_margin = {
            '3':{'default':'100'},
            '6':{'default':'100', '4.5':'75', '3.0':'50'},
            '9':{'default':'100', '6.0':'50', '4.5':'25', '3.5':'1'},
            '12':{'default':'100', '9.0':'50', '6.5':'1', '6.0':'65550', '4.5':'65525', '3.0':'65500'},
            '15':{'default':'100', '12.0':'50', '9.0':'65550', '6.0':'65500', '4.5':'65475', '3.0':'65450'},
            '18':{'default':'100', '15.0':'50', '12.0':'65550', '9.0':'65500', '6.0':'65450', '4.5':'65425', '3.0':'65400'},
        }

        self.pack()
        self.create_widgets()

    def get_default_gateway(self):
        print('Looking for default gateway ... ', end='')
        ip = '192.168.1.1' # default
        if os.name == 'nt': # windows
            r = os.popen('ipconfig | findstr /i /r "Gateway.*"').read()
            rr = re.match(r'[^\d]+(\d+\.\d+\.\d+\.\d+)', r, re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)
            if rr != None:
                ip = rr[1]
        elif os.name == 'posix': # linux
            ip = os.popen('ip r | grep default | cut -d " " -f 3').read()
        print(ip)
        return ip
    
    def create_widgets(self):
        self.ip_label = tk.Label(self, text="Modem IP")
        self.ip = tk.Entry(self)
        self.ip.insert(0, self.get_default_gateway())
        self.ip_label.grid(row=0, column=0, pady=5)
        self.ip.grid(row=0, column=1, pady=5, padx=5)

        self.username_label = tk.Label(self, text="Username")
        self.username = tk.Entry(self)
        self.username.insert(0, self.config['login']['username'])
        self.username_label.grid(row=0, column=2, sticky=tk.W, pady=5)
        self.username.grid(row=0, column=3, pady=5, padx=5)

        self.password_label = tk.Label(self, text="Password")
        self.password = tk.Entry(self, show='*')
        self.password.insert(0, self.config['login']['password'])
        self.password_label.grid(row=0, column=4, sticky=tk.W, pady=5)
        self.password.grid(row=0, column=5, columnspan=2, pady=5, padx=5)

        self.login_button = tk.Button(self, text='Connect', fg='green', command=self.connect)
        self.login_button.grid(row=0, column=7, padx=5, pady=5)

        # self.log_list = tk.Listbox(self, height=5, width=80)
        # self.log_list.grid(row=2, column=0, columnspan=5)

        # self.quit = tk.Button(self, text="QUIT", fg="red",
        #                       command=self.master.destroy)
        # self.quit.pack(side="bottom")

    def config_window(self):
        # messagebox.showwarning(title='Attention', message='We cannot load your current configuration properly,'+\
        #     ' so what you see in the following window is not your current configuration.')
        self.cwindow = AdvancedConfig(master=self, connection=self.connection, adsl_cmd=self.adsl_cmd, config=self.profile)
        self.cwindow.grab_set()

    def disconnect(self):
        # disconnect process
        print('Disconnecting ... ')
        if self.connection != None:
            try:
                self.connection.send_cmd('exit')
                self.connection.close()
            except:
                pass
            print('Connection closed successfully!')
            self.connection = None
            self.tone_att.get_tk_widget().destroy()
            self.login_button.config(text='Connect', fg='green', command=self.connect)
            self.username['state'] = 'normal'
            self.password['state'] = 'normal'
            self.ip['state'] = 'normal'
            # destruction!
            self.mode_label.destroy()
            self.status_label.destroy()
            self.snr_label.destroy()
            self.margin_menu.destroy()
            self.save_button.destroy()
            self.refresh_button.destroy()

    def connect(self):
        print(f"Trying to connect ... telnet://{self.username.get()}:{'*'*len(self.password.get())}@{self.ip.get()}/")
        try:
            self.connection = ADSLTelnet(self.ip.get(), 23, 5, self.username.get(), self.password.get())
            if self.connection.login_success:
                messagebox.showinfo('Connected!', 'We connected to modem succesfully!!!')
                print('Connected!')

                # after succesful login
                self.login_button.config(text='Disconnect', fg='red', command=self.disconnect)
                self.username['state'] = 'disabled'
                self.password['state'] = 'disabled'
                self.ip['state'] = 'disabled'
                self.config['login']['username'] = self.username.get()
                self.config['login']['password'] = self.password.get()
                with open('config.ini', 'w') as of:
                    self.config.write(of)
                    print('Config file updated!')
            else:
                self.connection.close()
                messagebox.showerror('Wrong Credentials', 'Cannot connect with given credentials!')
        except:
            messagebox.showerror('Connect Error', 'Cannot connect to modem!')
        if self.connection != None and self.connection.login_success:
            self.after_login_init()

    def after_login_init(self):
        print('Getting available commands ... ', end='')
        self.get_available_commands()
        if len(self.available_commands) > 0:
            print(f'We found {len(self.available_commands)} commands!')
        print('Getting adsl command ... ', end='')
        if self.get_adsl_command() != '':
            print('done')
            print('Getting adsl info (SNR) ... ', end='')
            plot_x, plot_y = self.read_adsl_info_snr()
            print('done')

            print('Getting adsl info (show) ... ', end='')
            self.read_adsl_info_show()
            print('done')

            if 'Mode' in self.adsl_info:
                self.mode_label = tk.Label(self, text=f'Mode: {self.adsl_info["Mode"]}')
                self.mode_label.grid(row=1,column=0)
            if 'Status' in self.adsl_info:
                self.status_label = tk.Label(self, text=f'Status: {self.adsl_info["Status"]}', fg=('green' if self.adsl_info['Status'] == 'Showtime' else 'red'))
                self.status_label.grid(row=1,column=1)
            if 'SNR (dB)' in self.adsl_info:
                self.snr_label = tk.Label(self, text=f'SNR (dB): Down={self.adsl_info["SNR (dB)"][0]} Up={self.adsl_info["SNR (dB)"][1]}')
                self.snr_label.grid(row=1,column=2, columnspan=2)
                cur_margin = float(self.adsl_info["SNR (dB)"][0])
                curm = None
                if cur_margin > 4.5 and cur_margin < 7.5: # 6 dB
                    curm = '6'
                elif cur_margin > 7.5 and cur_margin < 10.5: # 9 dB
                    curm = '9'
                elif cur_margin > 10.5 and cur_margin < 13.5: # 12 dB
                    curm = '12'
                elif cur_margin > 13.5 and cur_margin < 16.5: # 15 dB
                    curm = '15'
                elif cur_margin > 16.5 and cur_margin < 19.5: # 18 dB
                    curm = '18'
                elif cur_margin < 4.5:
                    curm = '3'
                self.current_margin = curm
                if curm != None:
                    options = self.cur_to_des_margin[curm].keys()
                    self.marginVar = tk.StringVar(self, curm)
                    self.margin_menu = tk.OptionMenu(self, self.marginVar, *options, command=self.margin_change)
                    self.margin_menu.grid(row=1, column=4)

                    self.save_button = tk.Button(self, text='Save', state='disabled', command=self.save_new_profile)
                    self.save_button.grid(row=1, column=5)

                self.refresh_button = tk.Button(self, text='Refresh', fg='brown', command=self.refresh_window_data)
                self.refresh_button.grid(row=1, column=6)

                self.config_button = tk.Button(self, text='Config', bg='orange', command=self.config_window)
                self.config_button.grid(row=1, column=7)
        else:
            print('not available!')
        
        if 'plot_x' in locals():
            self.tone_att = self.make_plot(plot_x, plot_y)
            self.tone_att.get_tk_widget().grid(row=2, column=0, columnspan=8)

    def refresh_window_data(self):
        pass

    def save_new_profile(self):
        print('Saving ... ')
        print(self.connection.send_cmd('adsl profile --save'))
        self.save_button['state'] = 'disabled'

    def margin_change(self, margin):
        if margin != self.current_margin:
            print('Changing margin to ' + margin)
            # run command
            print(self.connection.send_cmd(f'{self.adsl_cmd} configure --snr {self.cur_to_des_margin[self.current_margin][margin]}'))
            messagebox.showinfo('Save it', 'You need to Save the profile, otherwise this configuration will not remain after modem reboot.')
            self.save_button.config(state='normal', fg='green')
            self.current_margin = margin.split('.')[0]
            # recalc options
            options = self.cur_to_des_margin[self.current_margin].keys()
            self.margin_menu['menu'].delete(0, 'end') # delete all to the end!
            for i in options:
                self.margin_menu['menu'].add_command(label=i)

    def get_available_commands(self):
        help_str = self.connection.send_cmd('help')
        self.available_commands = help_str.splitlines()
    
    def get_adsl_command(self):
        if len(self.available_commands) > 0:
            self.adsl_cmd = ''
            for cmd in ['adsl', 'adslctl', 'xdslctl', 'xdsl']:
                if cmd in self.available_commands:
                    self.adsl_cmd = cmd
                    break
            if self.adsl_cmd == '':
                print("Cannot find adsl command!")

            return self.adsl_cmd
        else:
            print('No commands are available!')

        return None

    def read_adsl_profile(self):
        cmd = f'{self.adsl_cmd} profile --show'
        adsl_profile_str = self.connection.send_cmd(cmd)
        key = ''
        for line in adsl_profile_str.splitlines():
            if line[0] not in [' ', '\t']:
                key = line
                if key != cmd: # our command echo
                    self.adsl_profile[key] = {}
            else:
                pair = re.match(r'(.+)( |\t)+(.+)$', line.strip())
                if pair != None:
                    self.adsl_profile[key]
    def read_adsl_info_show(self):
        adsl_info_str = self.connection.send_cmd(f'{self.adsl_cmd} info --show')
        for line in adsl_info_str.splitlines():
            matches = re.match(r'([^:]+):( |\t)+(.+)$', line)
            if matches != None:
                if matches[3].find('   ') != -1 or matches[3].find('\t') != -1: # split it
                    mm = re.match(r'([^ ]+)( |\t)+(.+)', matches[3])
                    self.adsl_info[matches[1]] = [mm[1], mm[3]]
                else:
                    self.adsl_info[matches[1]] = matches[3]
        print(self.adsl_info)

    def read_adsl_info_snr(self):
        adsl_info_str = self.connection.send_cmd(f'{self.adsl_cmd} info --SNR')
        matches = re.match(r'.*Max:.+Upstream rate ?= ?(\d{1,}).+Downstream rate ?= ?(\d{1,}).+Bearer:.+Upstream rate ?= ?(\d{1,}).+Downstream rate ?= ?(\d{1,})', \
            adsl_info_str, re.RegexFlag.IGNORECASE | re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)
        if matches != None:
            self.adsl_info = {
                'max': {
                    'upstream': matches[1],
                    'downstream': matches[2]
                },
                'bearer': {
                    'upstream': matches[3],
                    'downstream': matches[4]
                }
            }

        matches = re.match(r'.*Tone number.+SNR(.*)', adsl_info_str, re.RegexFlag.IGNORECASE | re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)
        if matches != None:
            snr = []
            for line in matches[1].splitlines():
                if len(line) > 3:
                    pair = re.match(r' +(\d+)( |\t)+(\d+\.\d+)', line)
                    if pair != None:
                        snr.append([int(pair[1]), float(pair[3])])

        return np.array(snr).transpose()

    def make_plot(self, x, y) -> FigureCanvasTkAgg:
        fig, ax = plt.subplots(1, 1, figsize=(6.5, 5))
        ax.plot(x, y, color='red')
        ax.set(xlabel='Tone number', ylabel='SNR(dB)', title=f"Maximum Download/Upload link : {self.adsl_info['max']['downstream']}/{self.adsl_info['max']['upstream']} Kbps")
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        return canvas

if __name__ == '__main__':
    print('Please run \'../main.py\' instead.')
    exit(-1)
