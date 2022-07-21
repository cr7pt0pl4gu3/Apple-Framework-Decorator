import time

def dump(debugger, command, result, internal_dict):
    debugger.HandleCommand('break set -n main')
    debugger.HandleCommand('run')
    f = open("/Users/cr7pt0pl4gu3/Library/Application Support/Binary Ninja/plugins/AFD/afd/dump.txt", "w")
    debugger.SetOutputFileHandle(f,True)
    debugger.HandleCommand('disas -a 0x7ffb1b97f128')