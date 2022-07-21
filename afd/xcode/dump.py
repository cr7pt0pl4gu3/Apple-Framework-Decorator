import time

def dump(debugger, command, result, internal_dict):
    debugger.HandleCommand('break set -n main')
    debugger.HandleCommand('run')
    time.sleep(3)
    debugger.HandleCommand('disas -a 0x7ff92ec9b1db')
