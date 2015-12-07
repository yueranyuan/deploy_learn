import os
import shutil

for root, d, fns in os.walk('logs'):
    if len(d) > 0:
        continue

    base = os.path.split(root)[-1]
    for fn_full in fns:
        fn = fn_full[len(base):]
        fn, ext = os.path.splitext(fn)
        if fn[0] == '_':
            fn = fn[1:]
        if ext == '':
            ext = fn
            fn = 'log'

        shutil.move(os.path.join(root, fn_full), os.path.join(root, fn + ext))
