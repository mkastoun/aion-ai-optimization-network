"""Local, configurable LLVM tools; no downloads or shell evaluation."""
import os
from pathlib import Path
import shutil

from .errors import AionError


def llvm_tool_candidates(name, compiler):
    key = 'AION_' + name.upper().replace('-', '_')
    configured = os.environ.get(key)
    if configured:
        path = shutil.which(configured)
        if not path:
            raise AionError(f'{key} names an unavailable executable: {configured}')
        return [str(Path(path).absolute())]
    directories = [Path(os.environ['AION_LLVM_BIN'])] if os.environ.get('AION_LLVM_BIN') else []
    if compiler is not None:directories.append(Path(compiler.path).parent)
    spellings = (name + '-' + str(compiler.major), name) if compiler is not None else (name,)
    names = [str(d / item) for d in directories for item in spellings]
    names += list(spellings)
    return list(dict.fromkeys(str(Path(path).absolute()) for item in names if (path := shutil.which(item))))


def find_llvm_tool(name, compiler=None, *, fallback=()):
    paths = llvm_tool_candidates(name, compiler)
    return next(iter(paths), None) or next((p for item in fallback if (p := shutil.which(item))), None)
