from telnetlib import Telnet
from time import sleep

class ADSLTelnet(Telnet):
    def __init__(self, host: str, port: int, timeout: float, username: str, password: str) -> None:
        super().__init__(host=host, port=port, timeout=timeout)
        self.default_timeout = 5
        self.login_success = False
        self.command_prompt = b''
        self.last_message = self.read_until_ex(b'ogin').decode('ascii')
        if self.last_message.find('failed') == -1:
            self.login_success = self.login(usr=username, pwd=password)
        else:
            self.login_success = False
        if self.login_success:
            print('ADSLTelnet: Login success')
        else:
            print('ADSLTelnet: Login failed!\r\nErrMsg:' + self.last_message)

    def read_until_ex(self, match, delay=0.2):
        r = self.read_until(match, self.default_timeout)
        sleep(delay)
        return r + self.read_very_lazy()

    def send_line(self, cmd: str):
        self.write(cmd.encode('ascii') + b'\n')

    def send_cmd(self, cmd: str):
        self.send_line(cmd)
        b = self.read_until_ex(self.command_prompt)
        self.last_message = b.decode('ascii')
        return self.last_message

    def login(self, usr='admin', pwd='admin'):
        self.send_line(usr)
        self.read_until_ex(b'assword')
        self.send_line(pwd)
        sleep(1.0)
        r = (self.read_some() + self.read_very_lazy()).decode('ascii')
        self.last_message = r
        if r.find('>') != -1:
            self.command_prompt = r.encode('ascii')
            return True
        return False
        
if __name__ == '__main__':
    print('Please run \'../main.py\' instead.')
    exit(-1)
    