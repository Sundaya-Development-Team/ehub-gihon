import subprocess
import re
from subprocess import Popen

def send_command(commands):
    commands = commands.split(" ")
    p = Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output, errors = p.communicate()
    return output

def check_program_active_time(program):
    output = send_command(f'sudo systemctl status {program}').rstrip()
    filtered = re.search(r'(\d+-\d+-\d+.*\d+:\d+:\d+)', output)
    active_time = filtered.group(1)
    return active_time
