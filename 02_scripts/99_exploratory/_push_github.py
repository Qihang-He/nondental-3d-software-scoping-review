# -*- coding: utf-8 -*-
"""Clone the public repository, replace its contents with the rebuilt repo, commit and push.

The access token is read from the environment and never written to the command line or output.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, '06_公共仓库')
REPO = 'Qihang-He/nondental-3d-software-scoping-review'
TMP = os.path.join(os.environ.get('TEMP', ROOT), 'nondental-repo-push')
AMEND = os.environ.get('AMEND', '') == '1'
MESSAGE = (sys.argv[1] if len(sys.argv) > 1 else
           'Revise dataset after software-scope audit (853 studies, 100 packages)')

TOKEN = os.environ.get('GITHUB_TOKEN', '').strip()
if not TOKEN:
    raise SystemExit('GITHUB_TOKEN not set')

URL = 'https://x-access-token:%s@github.com/%s.git' % (TOKEN, REPO)


def run(args, cwd=None, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    out = ((p.stdout or '') + (p.stderr or '')).replace(TOKEN, '***')
    if check and p.returncode != 0:
        raise SystemExit('git failed rc=%d: %s\n%s' % (p.returncode, ' '.join(args[:2]), out[-1500:]))
    return p.returncode, out


def _force_remove(func, path, _exc):
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def clean_dir(path):
    """Remove a checkout robustly: git marks packed objects read-only on Windows."""
    if not os.path.isdir(path):
        return
    shutil.rmtree(path, onerror=_force_remove)
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    if os.path.isdir(path):
        raise SystemExit('could not clear %s' % path)


clean_dir(TMP)

rc, out = run(['git', 'clone', '--quiet', URL, TMP])
print('cloned:', out.strip()[:200] or 'ok')

# replace contents, keep .git
for name in os.listdir(TMP):
    if name == '.git':
        continue
    path = os.path.join(TMP, name)
    shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
for name in os.listdir(SRC):
    s = os.path.join(SRC, name)
    d = os.path.join(TMP, name)
    if os.path.isdir(s):
        shutil.copytree(s, d)
    else:
        shutil.copy2(s, d)

rc, out = run(['git', 'add', '-A'], cwd=TMP)
commit_args = ['-m', MESSAGE]
if AMEND:
    commit_args = ['--amend'] + commit_args
rc, out = run(['git', '-c', 'user.name=Qihang He',
               '-c', 'user.email=qihanghe05@foxmail.com',
               'commit'] + commit_args + ['--allow-empty'], cwd=TMP)
print('commit:', out.strip().splitlines()[-1][:180] if out.strip() else '')

rc, out = run(['git', 'push', '--force-with-lease', 'origin', 'HEAD:main'], cwd=TMP)
print('push main:', out.strip()[:300] or 'ok')

# refresh the release tag so the pinned release matches the revised dataset
run(['git', 'push', 'origin', ':refs/tags/v2.0'], cwd=TMP, check=False)
run(['git', 'tag', '-f', 'v2.0'], cwd=TMP)
rc, out = run(['git', 'push', 'origin', 'refs/tags/v2.0'], cwd=TMP)
print('push tag v2.0:', out.strip()[:300] or 'ok')

rc, out = run(['git', 'log', '--oneline', '-3'], cwd=TMP)
print('--- log ---')
print(out.strip())
rc, out = run(['git', 'ls-files'], cwd=TMP)
files = out.strip().splitlines()
print('tracked files:', len(files))
bad = [f for f in files if any('\u4e00' <= ch <= '\u9fff' for ch in f)]
print('files with Chinese characters:', len(bad))
