# This code written by Ehsan Varasteh, 2021
# visit my website and enjoy!
# https://zaxis.ir/

import os
import tkinter as tk
import configparser as cp
from dialogs.adsldoctor import ADSLDoctor

app_name = 'ADSL Doctor v0.1 by Ehsan Varasteh'
cur_path = os.path.dirname(__file__) + os.path.sep

if __name__ == '__main__':
    print(app_name)
    config = {'login':{'username':'admin', 'password':'admin'}}
    print('Looking for config.ini ... ', end='')
    c = cp.ConfigParser()
    if os.path.isfile('config.ini'):
        print('reading ... ', end='')
        if len(c.read(cur_path + 'config.ini')) > 0:
            config = c
            print('done')
        else:
            print('error')
    else:
        print('not found, creating ... ', end='')
        c.read_dict(config)
        with open('config.ini', 'w') as of:
            c.write(of)
            print('done')

    root = tk.Tk(sync=True)
    root.title(app_name)
    root.iconbitmap(cur_path + 'res/main.ico')
    root.resizable(width=False, height=False)
    app = ADSLDoctor(master=root, config=config)
    print('Application initialized!')
    app.mainloop()
