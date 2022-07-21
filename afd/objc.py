import subprocess
import os
from binaryninja import *
import time


class LLDBDecorator(BackgroundTaskThread):
    def __init__(self, bv, fnc=""):
        self.functions = []
        self.results = 0
        self.bv = bv
        self.fnc = fnc
        self.progress_bar = ""
        BackgroundTaskThread.__init__(self, self.progress_bar, True)

    def run(self):
        start = time.time()
        res = self.lldb_decorate()
        end = time.time() - start
        log_info("[AFD] [Objective-C] - LLDB decoration ended, {} decorated, {:2f} seconds elapsed".format(res, end))

    def lldb_decorate(self):
        res = 0
        exports = 0
        if self.fnc == "":
            self.functions = self.bv.functions
        elif self.fnc == "exports":
            exports = 1
            for sym in self.bv.get_symbols_of_type(SymbolType.FunctionSymbol):
                if sym.binding == SymbolBinding.GlobalBinding:
                    self.functions.append(self.bv.get_functions_by_name(sym.name)[0])
        else:
            self.functions.append(self.fnc)

        for fx in self.functions:
            start = time.time()
            self.fnc = fx

            self.progress_bar = f"[AFD] Decorating {self.fnc.name} with LLDB ..."
            dirname = os.path.dirname(__file__)

            if exports == 0:
                func_name = str(self.fnc.name)
                if "[" not in func_name and "]" not in func_name and " " not in func_name:
                    continue
                func_type = func_name.split("[")[0]
                class_name = func_name.split("[")[1].split("]")[0].split(" ")[0]
                selector_name = func_name.split("[")[1].split("]")[0].split(" ")[1]
                print(f"Class name: {class_name}")
                print(f"Selector name: {selector_name}")

                if "." in selector_name or "dealloc" in selector_name:
                    continue

                code = f"""
    #import <Foundation/Foundation.h>
    #import <objc/runtime.h>

    int main(void) {{
        Class c = NSClassFromString(@"{class_name}");
        void* p = method_getImplementation(class_getClassMethod(c, @selector({selector_name})));
        if (p == NULL) {{
            void* p = method_getImplementation(class_getInstanceMethod(c, @selector({selector_name})));
            NSLog(@"POINTER:%p", p);
        }}
        else {{
            NSLog(@"POINTER:%p", p);
        }}
        // NSLog(@"%@", [c performSelector: @selector({selector_name})]);
    }}
        """
            else:
                func_name = self.fnc.name[1:]
                code = f"""
    #import <Foundation/Foundation.h>
    #import <objc/runtime.h>
    
    extern id {func_name}();
    
    int main(void) {{
        NSLog(@"POINTER:%p", {func_name});
    }}
        """
            print(f"Code: {code}")

            # check if user has linked his framework for building:
            # with open("./xcode/test.xcodeproj/project.pbxproj", "r") as f

            with open(os.path.join(dirname, 'xcode/test/main.m'), "w") as f:
                f.write(code)

            subprocess.run(f"cd '{os.path.join(dirname, 'xcode')}' && xcodebuild -scheme test build", shell=True,
                           check=True)

            build_folder = \
                subprocess.check_output(f"cd '{os.path.join(dirname, 'xcode')}' && xcodebuild -project test.xcodeproj "
                                        f"-showBuildSettings | grep "
                                        " TARGET_BUILD_DIR", shell=True).replace(b"Release", b"Debug").decode().rstrip(
                    '\n')
            macho = build_folder.split("TARGET_BUILD_DIR = ")[1] + "/test"

            try:
                p_data = subprocess.check_output(f"{macho}", shell=True, stderr=subprocess.STDOUT).decode()
            except subprocess.CalledProcessError as e:
                p_data = e.output.decode()
            print(p_data)
            pointer = p_data.split("POINTER:")[1].split('\n')[0]

            dump_py = f"""import time

def dump(debugger, command, result, internal_dict):
    debugger.HandleCommand('break set -n main')
    debugger.HandleCommand('run')
    f = open("{os.path.join(dirname, 'dump.txt')}", "w")
    debugger.SetOutputFileHandle(f,True)
    debugger.HandleCommand('disas -a {pointer}')"""

            with open(os.path.join(dirname, 'dump.py'), "w") as f:
                f.write(dump_py)

            proc = subprocess.Popen(
                f"printf 'command script import \"{os.path.join(dirname, 'dump.py')}\"\\ncommand script add -f dump.dump "
                f"dmp\\ndmp\\n' | lldb {macho}",
                shell=True)
            proc.wait()
            print(
                f"printf 'command script import \"{os.path.join(dirname, 'dump.py')}\"\\ncommand script add -f dump.dump "
                f"dmp\\ndmp\\n' | lldb {macho}")

            with open(os.path.join(dirname, 'dump.txt'), "r") as f:
                func_disassembly = f.readlines()

            for i in range(1, len(func_disassembly)):
                # print(f"BinaryNinja ASM: {len(list(self.fnc.instructions))}, LLDB ASM: {len(func_disassembly)-1}")
                # assert(len(list(self.fnc.instructions)) == len(func_disassembly)-1)
                if "; " in func_disassembly[i].rstrip('\n'):
                    addr = int(func_disassembly[i].rstrip('\n').split("<")[0], 16)
                    comment = func_disassembly[i].rstrip('\n').split("; ")[1]
                    if "(void *)0x" in comment:
                        try:
                            comment = comment.split(": ")[1]
                        except IndexError:
                            log_warn(f"[AFD] [Objective-C] Cannot split {comment}")
                    print(f"Address: {hex(addr)}, comment: {comment}")
                    # hex(ins[1])[-3:] == hex(addr)[-3:]
                    # ins = list(self.fnc.instructions)[i-1]
                    # ins = list(self.fnc.instructions)[i - 1]
                    for ins in list(self.fnc.instructions):
                        if hex(ins[1])[-3:] == hex(addr)[-3:] and "objc_msgSend" not in comment \
                                and "symbol stub for:" not in comment \
                                and "<+" not in comment \
                                and "objc_retain" not in comment \
                                and "objc_release" not in comment \
                                and "objc_storeStrong" not in comment \
                                and "objc_alloc" not in comment and "objc_autoreleaseReturnValue" not in comment:
                            if isinstance(self.fnc.get_llil_at(ins[1]), LowLevelILSetReg):
                                try:
                                    if isinstance(self.fnc.get_llil_at(ins[1]).ssa_form.src, LowLevelILConstPtr):
                                        src = self.fnc.get_llil_at(ins[1]).ssa_form.src
                                        self.bv.get_data_var_at(src).name = comment
                                    else:
                                        src = self.fnc.get_llil_at(ins[1]).ssa_form.src.src
                                        self.bv.get_data_var_at(src).name = comment
                                        self.fnc.set_comment_at(ins[1], f"{comment}")
                                except Exception as e:
                                    log_warn(f"[AFD] [Objective-C] {e} - commenting only ...")
                                    self.fnc.set_comment_at(ins[1], f"{comment}")
                            else:
                                self.fnc.set_comment_at(ins[1], f"{comment}")
            end = time.time() - start
            log_info("[AFD] - LLDB decoration ended, {} decorated, {:2f} seconds elapsed".format(fx, end))
            res += 1
        return res


def lldb_dec_one(bv, f):
    decorator = LLDBDecorator(bv, f)
    decorator.start()


def lldb_dec_all(bv):
    decorator = LLDBDecorator(bv)
    decorator.start()


def lldb_dec_exports(bv):
    decorator = LLDBDecorator(bv, "exports")
    decorator.start()
