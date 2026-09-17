# -*- coding: utf-8 -*-
"""Clone the public repository, replace its contents with the rebuilt repo, commit and push.

The access token is read from the environment and never written to the command line or output.
"""
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, '06_公共仓库')
REPO = 'Qihang-He/nondental-3d-software-scoping-review'
TMP = os.path.join(os.environ.get('TEMP', ROOT), 'nondental-repo-push')

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


if os.path.isdir(TMP):
    shutil.rmtree(TMP, ignore_errors=True)

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
rc, out = run(['git', '-c', 'user.name=Qihang He',
               '-c', 'user.email=qihanghe05@foxmail.com',
               'commit', '-m',
               'Revise dataset after software-scope audit (853 studies, 100 packages)'
               '\n\n- Re-verify every recorded package against the nondental 3D software definition'
               '\n- Remove 10 non-conforming entries (programming/ML platforms, libraries,'
               ' dental-specific tools)'
               '\n- Exclude 8 records that named no other eligible package (861 -> 853)'
               '\n- Regenerate all statistics, figures, supplementary files and documents',
               '--allow-empty'], cwd=TMP)
print('commit:', out.strip().splitlines()[-1][:180] if out.strip() else '')

rc, out = run(['git', 'push', 'origin', 'HEAD:main'], cwd=TMP)
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
