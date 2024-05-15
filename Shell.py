import os
import platform
import subprocess
from argparse import Namespace, ArgumentParser
from ctypes import CFUNCTYPE, c_int

import llvmlite.binding as llvm
import llvmlite.ir

from Context import Context, VarMap
from Error import Error
from IrBuilder import IrBuilder
from Lexer import Lexer
from Methods import fail, print_err
from Parser import Parser


def start():
    args = parse_args()
    for arg in args.d:
        globals()[arg.upper() + '_DEBUG'] = True
    if args.run:
        globals()['RUN'] = True
    with open(args.file_path) as f:
        text = f.read()
    if args.o:
        globals()['OUTPUT'] = args.o
    else:
        globals()['OUTPUT'] = args.file_path.replace('.tss', '.exe' if platform.system() == 'Windows' else '')
    global OPT
    OPT = args.no_opt
    run(text, args.file_path)


def parse_args() -> Namespace:
    arg_parser = ArgumentParser(prog='Teness', description='LLVM implementation of a TenessScript compiler',
                                epilog='Exit Status:\n\tReturns 0 unless an error occurs')

    arg_parser.add_argument('file_path', type=str, help='Path to your entry point Teness file. (e.g. main.tss)')
    arg_parser.add_argument('-d', type=str, action='append', choices=['tokens', 'ast', 'ir', 'asm'], help='Dump')
    arg_parser.add_argument('-o', type=str, help='The emitted output file. (e.g. main.exe)')
    arg_parser.add_argument('-no_opt', action='store_false', help='Turn off all the optimisations')
    arg_parser.add_argument('-run', action='store_true',
                            help='Run the given file via JIT compilation, dont create an executable')
    return arg_parser.parse_args()


TOKENS_DEBUG = False
AST_DEBUG = False
IR_DEBUG = False
ASM_DEBUG = False
RUN = False
OPT = True
OUTPUT: str | None = None


def run(text: str, file: str):
    file = file.split(os.sep)[-1]
    file, _ = os.path.splitext(file)
    ctx = Context(None, '<main>', VarMap(), file, text)
    lexer = Lexer(ctx)
    tokens = lexer.make_tokens()
    if TOKENS_DEBUG:
        with open(OUTPUT + '.tokens', 'w') as f:
            f.write(tokens.__str__())
    parser = Parser(tokens, ctx)
    ast = parser.parse()
    if isinstance(ast, Error):
        fail(ast)
    if AST_DEBUG:
        with open(OUTPUT + '.json', 'w') as f:
            f.write(ast.__str__())
    builder = IrBuilder(ctx)
    builder.build(ast)
    module = builder.module
    module.triple = llvm.get_default_triple()
    if IR_DEBUG:
        with open(OUTPUT + '.ll', 'w') as f:
            if OPT:
                module = opt(module)
            f.write(module.__str__())
    if RUN:
        run_jit(module, file)
    else:
        cmp(module)


def opt(module: llvmlite.ir.Module) -> llvm.ModuleRef:
    module_ref = llvm.parse_assembly(module.__str__())
    if OPT:
        pmb = llvm.PassManagerBuilder()
        pmb.opt_level = 3
        pm = llvm.ModulePassManager()
        pmb.populate(pm)
        pm.run(module_ref)
    return module_ref


def cmp(module: llvmlite.ir.Module):
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    try:
        llvm_module = opt(module)
        llvm_module.verify()
    except Exception as e:
        print(e)
        raise

    target = llvm.Target.from_default_triple().create_target_machine()

    try:
        with open(OUTPUT + '_temp.o', "xb") as f:
            obj = target.emit_object(llvm_module)
            f.write(obj)
        if ASM_DEBUG:
            with open(OUTPUT + '.s') as f:
                assembly = target.emit_assembly(llvm_module)
                f.write(assembly)

        subprocess.run(['gcc', OUTPUT + '_temp.o', '-o', OUTPUT], capture_output=True, text=True)
    except Exception as e:
        print_err(e)
    finally:
        os.remove(OUTPUT + '_temp.o')


def run_jit(module: llvmlite.ir.Module, file: str):
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    try:
        llvm_module = opt(module)
        llvm_module.verify()
    except Exception as e:
        print(e)
        raise

    target = llvm.Target.from_default_triple().create_target_machine()
    engine = llvm.create_mcjit_compiler(llvm_module, target)
    engine.finalize_object()

    if ASM_DEBUG:
        with open(OUTPUT + '.s') as f:
            assembly = target.emit_assembly(llvm_module)
            f.write(assembly)

    entry = engine.get_function_address('main')
    if entry == 0:
        entry = engine.get_function_address(f'load_{file}')
    c_func = CFUNCTYPE(c_int)(entry)
    print('Starting...\n')
    result = c_func()
    print(f'\nReturned {result}')
