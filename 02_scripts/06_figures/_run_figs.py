# -*- coding: utf-8 -*-
"""仅在需要时生成指定图：python _run_figs.py 2 3 4 5"""
import sys
import importlib.util
import os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures_v3.py')
spec = importlib.util.spec_from_file_location('mf3', p)
mf3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mf3)

want = sys.argv[1:] or ['1', '2', '3', '4', '5']
for w in want:
    fn = getattr(mf3, 'fig' + w)
    fn()
print('done:', want)
