from .afd.dyld import *
from .afd.objc import *


def init(bv):
    pass


def scan(bv):
    log_info("[AFD] - initializing ...")
    init(bv)
    log_info("[AFD] - initialized.")


PluginCommand.register("AFD\\dyld_shared_cache\\Compare SSDEEP",
                       "Compares SSDEEP hashes for two different dyld shared cache"
                       " fingerprints from previous calculations", compare_ssdeep_hashes)
PluginCommand.register_for_function("AFD\\Objective-C\\Decorate CURRENT Objective-C Method (LLDB)",
                                    "Launches LLDB to decorate the function using runtime info comments", lldb_dec_one)

PluginCommand.register("AFD\\Objective-C\\Decorate ALL Objective-C Methods (LLDB)",
                       "Launches LLDB to decorate the function using runtime info comments", lldb_dec_all)
PluginCommand.register("AFD\\Objective-C\\Decorate ALL C-like Exports (LLDB)",
                       "Launches LLDB to decorate the C-like exports using runtime info comments", lldb_dec_exports)
