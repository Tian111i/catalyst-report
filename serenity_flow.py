# -*- coding: utf-8 -*-
"""
Serenity 概念选股流程
=====================
三步走:
  1. a-stock-data: 同花顺热点获取当日题材+个股
  2. a-stock-data: 百度概念板块验证个股归属
  3. Serenity评分排序

调用 a-stock-data skill 中的 API 获取实时数据。
"""

import urllib.request, time, random, requests
from datetime import date

# ============================================================
# 腾讯财经实时行情（不封IP，a-stock-data §1.2）
# ============================================================
def tencent_quote(codes: list[str]) -> dict[str, dict]:
    """批量拉取腾讯财经实时行情"""
    if not codes: return {}
    prefixed = []
    for c in codes:
        if c.startswith(("6","9")): prefixed.append(f"sh{c}")
        elif c.startswith("8"): prefixed.append(f"bj{c}")
        else: prefixed.append(f"sz{c}")
    url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        data = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
    except Exception:
        return {}
    result = {}
    for line in data.strip().split(";"):
        if not line.strip() or "=" not in line or '"' not in line: continue
        key = line.split("=")[0].split("_")[-1]
        vals = line.split('"')[1].split("~")
        if len(vals) < 53: continue
        code = key[2:]
        result[code] = {
            "name": vals[1],
            "price": float(vals[3]) if vals[3] else 0,
            "change_pct": float(vals[32]) if vals[32] else 0,
            "turnover_pct": float(vals[38]) if vals[38] else 0,
            "pe_ttm": float(vals[39]) if vals[39] else 0,
            "mcap_yi": float(vals[44]) if vals[44] else 0,
            "pb": float(vals[46]) if vals[46] else 0,
        }
    return result


# ============================================================
# Step 1: a-stock-data §3.1 同花顺热点 — 当日强势股+题材归因
# ============================================================
def ths_hot_today() -> list[dict]:
    """
    同花顺当日强势股归因（a-stock-data §3.1）。
    返回 ~125 只强势股，含 reason（题材标签）。
    """
    today = date.today().strftime("%Y-%m-%d")
    url = f"http://zx.10jqka.com.cn/event/api/getharden/date/{today}/orderby/date/orderway/desc/charset/GBK/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/117.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data.get("errocode", 0) != 0: return []
        return [{
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "reason": item.get("reason", ""),
            "zhangfu": item.get("zhangfu", 0),
            "huanshou": item.get("huanshou", 0),
            "chengjiaoe": item.get("chengjiaoe", 0),
        } for item in (data.get("data") or [])]
    except Exception:
        return []


def ths_filter_by_concept(hot_stocks: list[dict], keywords: list[str]) -> list[dict]:
    """从同花顺热点中筛选题材标签匹配的个股"""
    matched = []
    for hs in hot_stocks:
        reason = hs.get("reason", "")
        if reason and any(kw in reason for kw in keywords):
            matched.append(hs)
    return matched


# ============================================================
# Step 2: a-stock-data §3.3 百度概念板块归属 — 验证个股概念标签
# ============================================================
def baidu_check_concept(code: str) -> list[str]:
    """
    百度股市通概念板块归属（a-stock-data §3.3）。
    返回个股所属的概念标签列表。
    """
    url = (f"https://finance.pae.baidu.com/api/getrelatedblock"
           f"?code={code}&market=ab&typeCode=all&finClientType=pc")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "application/vnd.finance-web.v1+json",
        "Origin": "https://gushitong.baidu.com",
        "Referer": "https://gushitong.baidu.com/",
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        d = r.json()
        if str(d.get("ResultCode", -1)) != "0": return []
        tags = []
        for block in d.get("Result", []):
            if "概念" in block.get("type", ""):
                for item in block.get("list", []):
                    tags.append(item.get("name", ""))
        return tags
    except Exception:
        return []


def baidu_batch_concepts(codes: list[str]) -> dict[str, list[str]]:
    """批量查概念的节流版本"""
    result = {}
    for i, code in enumerate(codes):
        result[code] = baidu_check_concept(code)
        if i < len(codes) - 1:
            time.sleep(0.3 + random.uniform(0.1, 0.3))
    return result


# ============================================================
# Step 3: 概念关键词匹配（用于同花顺搜索+百度验证）
# ============================================================

# ── 结构性龙头映射（轻量，仅覆盖各概念3-5只核心标的）──
# 用于补充同花顺热点未覆盖的龙头
CONCEPT_LEADERS = {
    "MLCC": ["000636", "300408", "300285", "002859"],
    "AI算力": ["300308", "300502", "300394", "601138", "002463"],
    "半导体": ["002371", "688012", "688981", "600584"],
    "存储芯片": ["603986", "688525", "688008", "688123"],
    "华为昇腾": ["688041", "688256", "002261", "301236"],
    "AI Agent": ["300496", "002230", "300229", "300170"],
    "券商金融": ["600030", "300059", "300033"],
    "机器人": ["688017", "300124", "603662", "002747"],
    "新能源车": ["002594", "300750", "300450"],
    "黄金": ["601899", "600547", "600988"],
    "油价受益": ["601111", "600029", "600309"],
    "液冷温控": ["002837", "300499"],
    "低空经济": ["600118", "600879"],
    "消费电子": ["002475", "002241"],
    "信创": ["688041", "301236"],
    "医药": ["603259"],
    "面板": ["000725"],
    "CPO": ["300308", "300502", "300394", "688498", "688313"],
    "PCB": ["002463", "002916", "300476", "600183", "002384"],
}

# 概念→搜索关键词映射
CONCEPT_KEYWORDS = {
    "AI算力": ["算力", "光模块", "AI服务器", "CPO", "GPU", "数据中心"],
    "半导体": ["半导体", "芯片设备", "光刻", "刻蚀", "CMP", "晶圆", "封测"],
    "MLCC": ["MLCC", "被动元件", "陶瓷电容", "片式多层"],
    "存储芯片": ["存储", "HBM", "DRAM", "NAND", "内存", "闪存"],
    "华为昇腾": ["昇腾", "华为", "鲲鹏", "鸿蒙", "海思"],
    "AI Agent": ["AI Agent", "智能体", "AI应用", "大模型", "AI助理"],
    "券商金融": ["券商", "证券", "金融科技", "互联网金融"],
    "机器人": ["机器人", "人形机器人", "具身", "减速器", "伺服电机", "传感器"],
    "新能源车": ["新能源车", "锂电池", "比亚迪", "充电", "固态电池"],
    "黄金": ["黄金", "贵金属", "金价"],
    "油价受益": ["航空", "航油", "油价下跌", "美伊和平", "化工"],
    "液冷温控": ["液冷", "温控", "散热", "冷却"],
    "低空经济": ["低空经济", "eVTOL", "飞行汽车", "无人机"],
    "消费电子": ["消费电子", "苹果", "果链", "MR", "折叠屏"],
    "信创": ["信创", "国产软件", "国产替代", "操作系统"],
    "医药": ["CXO", "创新药", "CRO", "CDMO", "医药研发"],
    "面板": ["面板", "OLED", "LCD", "显示"],
    "CPO": ["CPO", "共封装", "硅光", "光学引擎", "相干光"],
    "PCB": ["PCB", "印制电路板", "HDI", "IC载板", "高速板", "封装基板"],
    "AI算力芯片": ["算力芯片", "AI芯片", "GPU", "NPU", "ASIC"],
}

ALL_CONCEPT_NAMES = list(CONCEPT_KEYWORDS.keys())


def match_concept_keywords(text: str, concept: str) -> bool:
    """检查文本是否匹配某概念的任一关键词"""
    keywords = CONCEPT_KEYWORDS.get(concept, [concept])
    return any(kw in text for kw in keywords)


def auto_identify_concepts(hot_stocks: list[dict]) -> dict[str, list[dict]]:
    """自动识别同花顺热点中涉及了哪些概念，及其个股"""
    concept_map = {name: [] for name in ALL_CONCEPT_NAMES}
    for hs in hot_stocks:
        reason = hs.get("reason", "")
        if not reason: continue
        for cname in ALL_CONCEPT_NAMES:
            if match_concept_keywords(reason, cname):
                concept_map[cname].append(hs)
    return {k: v for k, v in concept_map.items() if v}


# ============================================================
# Step 4: Serenity 评分
# ============================================================

SERENITY_WEIGHTS = {
    "demand_inflection": 15,
    "architecture_coupling": 10,
    "chokepoint_severity": 15,
    "supplier_concentration": 12,
    "expansion_difficulty": 12,
    "evidence_quality": 15,
    "valuation_disconnect": 11,
    "catalyst_timing": 10,
}


def serenity_score(code: str, name: str, live: dict,
                   context: dict, role: str = "", layer: str = "",
                   hot_reason: str = "") -> dict:
    """Serenity评分"""
    factors = {}
    factors["demand_inflection"] = context.get("demand_inflection", 3)
    factors["architecture_coupling"] = context.get("architecture_coupling", 3.0)
    factors["chokepoint_severity"] = context.get("chokepoint_severity", 3.0)
    factors["supplier_concentration"] = context.get("supplier_concentration", 3.0)
    factors["expansion_difficulty"] = context.get("expansion_difficulty", 3.0)
    factors["evidence_quality"] = context.get("evidence_quality", 3)

    pe = live.get("pe_ttm", 0) or 0
    if pe <= 0 or pe > 500: val = 2.0
    elif pe <= 20: val = 4.5
    elif pe <= 40: val = 4.0
    elif pe <= 60: val = 3.0
    elif pe <= 100: val = 2.0
    else: val = 1.5
    mcap = live.get("mcap_yi", 0)
    if mcap < 100: val = min(4.0, val + 0.5)
    factors["valuation_disconnect"] = context.get("valuation_disconnect", val)
    factors["catalyst_timing"] = context.get("catalyst_timing", 3)

    total = sum(factors[k] / 5.0 * w for k, w in SERENITY_WEIGHTS.items())

    penalties = {}
    penalties["liquidity"] = 4.0 if mcap < 50 else 3.0 if mcap < 100 else 2.0 if mcap < 200 else 1.0 if mcap < 500 else 0.5
    turnover = live.get("turnover_pct", 0) or 0
    penalties["hype_risk"] = 4.0 if turnover > 20 else 3.0 if turnover > 10 else 2.0 if turnover > 5 else 1.0
    penalties["geopolitics"] = context.get("geopolitics", 2.0)
    penalties["cyclicality"] = context.get("cyclicality", 2.0)
    for k in ["dilution_financing", "governance", "accounting_quality", "alternative_design_risk"]:
        penalties[k] = context.get(k, 1.0)

    penalty_total = sum(v * 2.0 for v in penalties.values())
    final = max(0, min(100, total - penalty_total))

    if final >= 80: verdict = "Top priority"
    elif final >= 65: verdict = "High priority"
    elif final >= 50: verdict = "Worth tracking"
    else: verdict = "Low priority"

    # 同花顺题材摘要
    reason_short = hot_reason[:60] if hot_reason else ""

    return {
        "code": code, "name": name,
        "mcap_yi": mcap, "pe_ttm": pe, "pb": live.get("pb", 0),
        "change_pct": live.get("change_pct", 0), "turnover_pct": turnover,
        "role": role, "layer": layer,
        "factors": factors, "raw_total": round(total, 1),
        "penalty_total": round(penalty_total, 1),
        "final_score": round(final, 1), "verdict": verdict,
        "hot_reason": reason_short,
    }


# ============================================================
# 主流程: 概念 → a-stock-data获取 → Serenity分析
# ============================================================

def concept_analysis(concept_name: str,
                     context: dict = None,
                     extra_codes: list[str] = None) -> dict:
    """
    全流程:
      1. 同花顺热点 → 筛概念相关强势股
      2. 结构性龙头映射 → 补充不在热点中的板块龙头
      3. 腾讯行情 → 拉实时数据
      4. Serenity → 评分排序

    参数:
        concept_name: "MLCC" / "机器人" / "AI算力" 等
        context: Serenity上下文参数
        extra_codes: 额外补充的个股代码

    返回:
        {hot_stocks, leader_stocks, all_scored, top, ...}
    """
    context = context or {}
    keywords = CONCEPT_KEYWORDS.get(concept_name, [concept_name])

    # 1. 同花顺热点获取
    all_hot = ths_hot_today()
    hot_matched = ths_filter_by_concept(all_hot, keywords)
    hot_codes = [h["code"] for h in hot_matched]

    # 2. 结构性龙头映射补充
    leader_codes = CONCEPT_LEADERS.get(concept_name, [])

    # 3. 合并(去重)
    all_codes = list(dict.fromkeys(hot_codes + leader_codes + (extra_codes or [])))

    if not all_codes:
        return {"concept": concept_name, "hot_stocks": [], "extra_stocks": [],
                "all_scored": [], "top": [], "has_hot_data": bool(all_hot)}

    # 3. 腾讯实时行情
    live = tencent_quote(all_codes)

    # 4. 评分
    hot_by_code = {h["code"]: h for h in hot_matched}
    scored = []
    for code in all_codes:
        ld = live.get(code, {})
        h = hot_by_code.get(code, {})
        sr = serenity_score(
            code=code,
            name=ld.get("name", code),
            live=ld,
            context=context,
            role="",
            hot_reason=h.get("reason", "") if h else "",
        )
        sr["from_hot"] = code in hot_by_code
        scored.append(sr)

    # 排序: 热点股优先 + 评分
    scored.sort(key=lambda x: x["final_score"] + (10 if x["from_hot"] else 0), reverse=True)

    # 分类
    hot_scored = [s for s in scored if s["from_hot"]]
    leader_code_set = set(leader_codes)
    leader_scored = [s for s in scored if s["code"] in leader_code_set]
    extra_scored = [s for s in scored if not s["from_hot"] and s["code"] not in leader_code_set]

    return {
        "concept": concept_name,
        "keywords": keywords,
        "total_hot": len(all_hot),
        "hot_stocks": hot_scored,        # 同花顺热点发现的
        "leader_stocks": leader_scored,   # 结构性龙头
        "extra_stocks": extra_scored,     # 其他补充
        "all_scored": scored,
        "top": scored[:30],
        "has_hot_data": bool(all_hot),
    }


# ============================================================
# 概念自动发现: 从同花顺热点自动识别今天在炒什么
# ============================================================

def hot_concepts_today() -> list[dict]:
    """识别今日同花顺热点涉及的所有概念板块及热度"""
    all_hot = ths_hot_today()
    if not all_hot:
        return []
    concept_map = auto_identify_concepts(all_hot)
    result = []
    for cname, stocks in sorted(concept_map.items(), key=lambda x: -len(x[1])):
        result.append({
            "concept": cname,
            "count": len(stocks),
            "top_stocks": [{"name": s["name"], "code": s["code"],
                            "zhangfu": s["zhangfu"]} for s in stocks[:5]],
            "avg_zhangfu": sum(s["zhangfu"] or 0 for s in stocks) / max(len(stocks), 1),
        })
    return result


# ============================================================
# HTML 生成
# ============================================================

def stock_card_html(r: dict) -> str:
    mcap = r["mcap_yi"]
    pe = r["pe_ttm"]
    chg = r["change_pct"]
    score = r["final_score"]
    updown = "#d32f2f" if chg > 0 else "#2e7d32"
    tag = "千亿大盘" if mcap >= 1000 else "中盘成长" if mcap >= 200 else "小市值" if mcap >= 50 else "微盘"
    tc = {"千亿大盘": "#1a237e", "中盘成长": "#1565c0", "小市值": "#e65100", "微盘": "#6a1b9a"}[tag]
    sc = "#d32f2f" if score >= 80 else "#f57c00" if score >= 65 else "#388e3c" if score >= 50 else "#757575"
    from_hot = r.get("from_hot", False)
    hot_b = ' <span style="font-size:10px;background:#ffebee;color:#c62828;padding:1px 5px;border-radius:8px">热点</span>' if from_hot else ""
    reason = r.get("hot_reason", "")
    reason_html = f'<div style="font-size:10px;color:#888;margin-top:1px">{reason}</div>' if reason else ""

    return f'''<div class="stock-card" style="position:relative">
  <div style="position:absolute;top:4px;right:6px;font-size:10px;font-weight:bold;color:{sc}">S-{score:.0f}</div>
  <div class="stock-header">
    <span class="stock-name">{r["name"]}</span>
    <span class="stock-code">{r["code"]}</span>
    <span class="stock-tag" style="background:#e8eaf6;color:{tc}">{tag}</span>{hot_b}
  </div>
  <div class="stock-details">
    <span>市值：{mcap:.0f}亿</span>
    <span>PE：{pe:.1f}</span>
    <span style="color:{updown}">{chg:+.2f}%</span>
    <span style="color:{sc}">{r["verdict"]}</span>
  </div>{reason_html}
</div>'''


def stocks_html(results: list[dict]) -> str:
    return '\n    '.join(stock_card_html(r) for r in results)


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    import sys
    concept = sys.argv[1] if len(sys.argv) > 1 else "MLCC"
    ctx = {"demand_inflection": 5, "evidence_quality": 5, "catalyst_timing": 5}

    print(f"\n=== {concept} ===\n")

    result = concept_analysis(concept, context=ctx)
    print(f"同花顺热点总数: {result['total_hot']}")
    print(f"概念匹配: {len(result['hot_stocks'])} 只\n")

    top = result["top"][:10]
    print(f"{'名称':<10} {'代码':<8} {'S分':<6} {'评级':<18} {'来源':<6}")
    print("-" * 55)
    for r in top:
        src = "热点" if r["from_hot"] else "补充"
        print(f"{r['name']:<10} {r['code']:<8} {r['final_score']:<6} {r['verdict']:<18} {src}")

    # 今日热点概念盘点
    print(f"\n=== 今日热点概念总览 ===")
    hot_concepts = hot_concepts_today()
    for hc in hot_concepts[:10]:
        top_names = "/".join(s["name"] for s in hc["top_stocks"][:3])
        print(f"  {hc['concept']:<12} {hc['count']:>3}只  均涨{hc['avg_zhangfu']:>+.1f}%  {top_names}")
