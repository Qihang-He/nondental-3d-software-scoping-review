# -*- coding: utf-8 -*-
"""Minimal DeepSeek connectivity test; never prints or stores the API key."""
import json, os, time
import requests
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = os.path.join(ROOT, '07_AI重跑原始记录', 'config.local.json')
with open(CFG, encoding='utf-8') as f:
    cfg = json.load(f)
key = os.environ.get('DEEPSEEK_API_KEY', '').strip() or str(cfg.get('deepseek_api_key', '')).strip()
if not key or 'REPLACE' in key.upper() or key == 'YOUR_DEEPSEEK_API_KEY_HERE':
    raise SystemExit('DeepSeek key is missing or still a placeholder; no request was sent.')
url = os.environ.get('DEEPSEEK_BASE_URL', cfg.get('base_url', 'https://api.deepseek.com/v1/chat/completions'))
requested_model = os.environ.get('DEEPSEEK_MODEL', cfg.get('model', 'deepseek-chat'))
payload = {
    'model': requested_model,
    'messages': [
        {'role': 'system', 'content': 'Return JSON only.'},
        {'role': 'user', 'content': 'Reply with {"ok":true}.'},
    ],
    'temperature': 0,
    'max_tokens': 20,
    'stream': False,
}
t0 = time.perf_counter()
r = requests.post(url, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, json=payload, timeout=30)
elapsed = time.perf_counter() - t0
print('HTTP status:', r.status_code)
print('Requested model:', requested_model)
print('Latency seconds: %.2f' % elapsed)
try:
    data = r.json()
except ValueError:
    print('Response was not JSON.')
    raise SystemExit(1)
print('Returned model:', data.get('model', '<not returned>'))
if r.ok:
    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
    print('Response content:', str(content)[:100])
else:
    print('API error type:', data.get('error', {}).get('type', '<unknown>'))
    print('API error message:', data.get('error', {}).get('message', '<unknown>'))
    raise SystemExit(1)
