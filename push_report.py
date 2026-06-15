#!/usr/bin/env python3
"""GitHub Actions 定时推送：大盘+新闻+博主信号 → PushPlus 微信"""
import urllib.request, json, os, requests
from datetime import datetime

UA = 'Mozilla/5.0'
TOKEN = os.environ.get('PUSHPLUS_TOKEN', '')

def push(title, content):
    if not TOKEN:
        print('[SKIP] No PUSHPLUS_TOKEN set')
        return
    r = requests.post('http://www.pushplus.plus/send', data={
        'token': TOKEN, 'title': title, 'content': content,
        'template': 'markdown'
    }, timeout=10)
    print(f'Push: {r.status_code} {r.text[:100]}')

# 1. 大盘
indices = {'上证指数':'000001','创业板':'399006','科创50':'000688'}
pref = []
for c in indices.values():
    pref.append(f"sh{c}" if c.startswith(('6','9')) else f"sz{c}")
url = f"https://qt.gtimg.cn/q={','.join(pref)}"
req = urllib.request.Request(url); req.add_header('User-Agent', UA)
data = urllib.request.urlopen(req, timeout=10).read().decode('gbk')
market_lines = []
for line in data.strip().split(';'):
    if '=' not in line or '"' not in line: continue
    key = line.split('=')[0].split('_')[-1]
    vals = line.split('"')[1].split('~')
    if len(vals) < 40: continue
    code = key[2:]
    for k, v in indices.items():
        if v == code:
            market_lines.append(f"| {k} | {vals[3]} | {float(vals[32]):+.2f}% |")

# 2. 新闻
news_lines = []
try:
    r = requests.get('https://orz.ai/api/v1/dailynews/?platform=cls', timeout=15)
    items = r.json().get('data', [])
    for it in items[:5]:
        title = it.get('title', '')[:80]
        news_lines.append(f"- {title}")
except:
    news_lines.append('- 新闻获取失败')

# 3. Build report
now = datetime.now().strftime('%m-%d %H:%M')
content = f"""## 📊 {now} 快报

### 大盘
{'| 指数 | 现价 | 涨跌 |' + chr(10) + '|------|------|------|' + chr(10) + chr(10).join(market_lines)}

### 📰 今日头条
{chr(10).join(news_lines)}

### 🎯 博主最新信号
- 06-15 09:45: 上证站上4088满仓干
- 06-15 18:35: 冲高会被砸+周四美联储风险

---
🤖 自动推送 · GitHub Actions
"""

push(f"【{now}】早盘快报", content)
