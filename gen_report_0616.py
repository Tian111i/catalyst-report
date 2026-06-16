# -*- coding: utf-8 -*-
"""消息面催化报告生成 - 2026-06-16"""
import urllib.request, json, time, random, os

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
    name_map = {}
    for line in data.strip().split(';'):
        if not line.strip() or '=' not in line or '"' not in line: continue
        key = line.split('=')[0].split('_')[-1]
        vals = line.split('"')[1].split('~')
        if len(vals) < 53: continue
        code = key[2:]
        name_map[code] = vals[1]
        result[code] = {
            'name': vals[1], 'price': float(vals[3]) if vals[3] else 0,
            'pe_ttm': float(vals[39]) if vals[39] else 0,
            'mcap_yi': float(vals[44]) if vals[44] else 0,
            'pb': float(vals[46]) if vals[46] else 0,
            'change_pct': float(vals[32]) if vals[32] else 0,
            'turnover_pct': float(vals[38]) if vals[38] else 0,
        }
    return result, name_map

codes = ['300308','601138','002371','688981','688012','600584','002594','300750',
         '601857','600938','601899','600547','600988','600030','300059','300496',
         '301236','688256','688041','002463','300502','300394','603986','688525',
         '603259','002475','002241','000636','300408','300285','603678','688126',
         '300274','605117','002920','688017','300124','002747','300607','600118',
         '600879','688347']

print("拉取腾讯行情...")
quotes, names = tencent_quote(codes)
for c, q in quotes.items():
    print(f"  {q['name']} {c}: {q['price']}元 PE={q['pe_ttm']} 市值={q['mcap_yi']}亿 涨跌={q['change_pct']}%")

output = {
    'quotes': {c: q for c, q in quotes.items()},
    'date': '2026-06-16',
    'weekday': '周二',
    'window': '6月15日（周一）开盘 → 6月16日（周二）开盘前',
    'us_ref': '美股芯片股财报季震荡，MLCC超级周期确认，NVIDIA $20B债券发行',
    'rating': '★★★★☆（中高）',
    'core_logic': 'MLCC超级周期全面确认（Murata+TDK涨价信号+高盛182%需求暴增测算）+日本半导体设备涨价+Bernstein强烈看多+长鑫科技IPO注册，半导体/电子产业链全面受益；NVIDIA Vera Rubin Q3出货+HBM4三供应商认证完成，AI算力持续高景气；美伊和平协议框架推进，油价回落利好中下游制造业成本改善。',
}

with open('report_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n数据已保存至 report_data.json")
print(f"共 {len(quotes)} 只标的行情")
