# -*- coding: utf-8 -*-
"""消息面催化报告生成 - 2026-06-09"""
import urllib.request, json, time, random, os, re

# ── 腾讯API批量拉取 ──
def tencent_quote(codes):
    prefixed = []
    for c in codes:
        if c.startswith(('6','9')): prefixed.append(f'sh{c}')
        elif c.startswith('8'): prefixed.append(f'bj{c}')
        else: prefixed.append(f'sz{c}')
    url = 'https://qt.gtimg.cn/q=' + ','.join(prefixed)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = urllib.request.urlopen(req, timeout=10).read().decode('gbk')
    result = {}
    for line in data.strip().split(';'):
        if not line.strip() or '=' not in line or '"' not in line: continue
        key = line.split('=')[0].split('_')[-1]
        vals = line.split('"')[1].split('~')
        if len(vals) < 53: continue
        code = key[2:]
        result[code] = {
            'name': vals[1], 'price': float(vals[3]) if vals[3] else 0,
            'pe_ttm': float(vals[39]) if vals[39] else 0,
            'mcap_yi': float(vals[44]) if vals[44] else 0,
            'pb': float(vals[46]) if vals[46] else 0,
            'change_pct': float(vals[32]) if vals[32] else 0,
            'turnover_pct': float(vals[38]) if vals[38] else 0,
        }
    return result

# ── 东财个股资金流（push2his）──
def fund_flow(code, retries=2):
    url = 'https://push2his.eastmoney.com/api/qt/stock/fflow/kline/get'
    params = {
        'secid': f'1.{code}' if code.startswith(('6','9')) else f'0.{code}',
        'fields1': 'f1,f2,f3,f7', 'fields2': 'f51,f52,f53,f54,f55,f56,f57',
        'klt': '1', 'lmt': '5', 'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
    }
    for i in range(retries):
        try:
            req = urllib.request.Request(url + '?' + '&'.join(f'{k}={v}' for k,v in params.items()),
               headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.eastmoney.com/'})
            r = urllib.request.urlopen(req, timeout=10)
            d = json.loads(r.read())
            if d.get('data') and d['data'].get('klines'):
                total_in = total_out = 0
                for kline in d['data']['klines'][-3:]:
                    parts = kline.split(',')
                    if len(parts) >= 7:
                        total_in += float(parts[3])  # 主力净流入
                        total_out += float(parts[4]) # 主力净流出
                net = total_in - total_out
                return f'主力净流入{net/10000:.0f}万' if net > 0 else f'主力净流出{abs(net)/10000:.0f}万'
            return '无资金数据'
        except Exception:
            time.sleep(1)
    return '数据获取失败'

# ── 核心受益标的 ──
main_codes = ['300308','601138','002371','688981','688012','600584','002594','300750',
              '601857','600938','601899','600547','600988','600030','300059','300496',
              '301236','688256','688041','002463','300502','300394','603986','688525',
              '603259','002475','002241']

print("拉取腾讯行情...")
quotes = tencent_quote(main_codes)
for c, q in quotes.items():
    print(f"  {q['name']} {c}: {q['price']}元 PE={q['pe_ttm']} PB={q['pb']} 市值={q['mcap_yi']}亿 涨跌={q['change_pct']}%")

print("\n拉取资金流...")
funds = {}
for i, c in enumerate(main_codes):
    funds[c] = fund_flow(c)
    print(f"  {quotes.get(c,{}).get('name','?')} {c}: {funds[c]}")
    time.sleep(1.5 + random.uniform(0.1, 0.5))  # 限流

# ── 存储为json供HTML生成 ──
output = {
    'quotes': {c: q for c, q in quotes.items()},
    'funds': funds,
    'date': '2026-06-09',
    'weekday': '周二',
    'window': '6月8日（周一）开盘 → 6月9日（周二）开盘前',
    'us_ref': '美股科技股黑色星期五后反弹（SOX+5.6%, NVDA+1.73%）',
    'rating': '★★★★☆（中高）',
    'core_logic': '华为麒麟9050/昇腾950DT获国际认可+微信AI生态开放+比亚迪二代刀片电池9分钟闪充，国内科技产业趋势性拐点密集出现；中东局势恶化推升油价至$96-97，大宗商品通胀预期升温。国内外催化共振，短期结构性机会集中在科技自主+能源安全双主线。',
}

with open('report_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n数据已保存至 report_data.json")
print(f"共 {len(quotes)} 只标的行情 + {len(funds)} 只资金流")
