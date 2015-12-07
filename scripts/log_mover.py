import os
import shutil

LOG_FOLDER = 'logs'

logs = os.listdir(LOG_FOLDER)
bases = []

# get log bases
for fn in logs:
    fn = os.path.splitext(fn)[0]
    if len(fn.split('_')) == 7:
        bases.append(fn)

# make log dirs
for b in bases:
    l_dir = os.path.join(LOG_FOLDER, b)
    try:
        os.mkdir(l_dir)
        print('made dir {}'.format(l_dir))
    except OSError:
        continue

# move logs into log dirs
for fn in logs:
    if os.path.isdir(fn):
        continue

    for b in bases:
        if fn.startswith(b):
            try:
                shutil.move(os.path.join(LOG_FOLDER, fn), os.path.join(LOG_FOLDER, b))
            except shutil.Error:
                pass
            continue
