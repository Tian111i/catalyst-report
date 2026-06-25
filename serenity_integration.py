# -*- coding: utf-8 -*-
"""
Serenity 动态概念选股引擎
=========================
三源融合:
  1. 同花顺热点(实时) → 当天哪些股在炒什么概念
  2. 百度概念板块归属 → 验证个股概念标签
  3. 行业知识库(静态) → 产业链映射 + 角色定义

用法:
    from serenity_integration import concept_to_stocks, stocks_html

    # 查概念
    result = concept_to_stocks("MLCC", context={...})
    result["top_stocks"]  # 评分排序后的个股
    result["hot_match"]   # 同花顺交叉验证

    # 生成HTML卡片
    html = stocks_html(result["top_stocks"])
"""

import json, os, urllib.request, time, random, requests

# ============================================================
# 腾讯财经实时行情
# ============================================================
def tencent_quote(codes: list[str]) -> dict[str, dict]:
    """批量拉取腾讯财经实时行情(不封IP)"""
    if not codes:
        return {}
    prefixed = []
    for c in codes:
        if c.startswith(("6", "9")): prefixed.append(f"sh{c}")
        elif c.startswith("8"): prefixed.append(f"bj{c}")
        else: prefixed.append(f"sz{c}")
    url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
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
# Part 1: 行业知识库 —— 产业链映射 + 个股角色
# 每个概念: {供应链层级, 瓶颈环节, 龙头/弹性/小市值}
# ============================================================

KNOWLEDGE_BASE = {
    "AI算力": {
        "sector": "AI算力、光模块、服务器",
        "supply_chain": "算力芯片→光互连→PCB/CCL→服务器整机→温控→电源",
        "scarce_layer": "光模块(带宽瓶颈)、高端PCB(工艺约束)",
        "stocks": [
            {"code": "300308", "role": "龙头", "desc": "光模块龙头(800G/1.6T)"},
            {"code": "300502", "role": "龙头", "desc": "光模块(400G/800G)"},
            {"code": "300394", "role": "龙头", "desc": "光引擎/FA/MT(光互连)"},
            {"code": "601138", "role": "龙头", "desc": "AI服务器代工"},
            {"code": "002463", "role": "龙头", "desc": "高端PCB(交换机/AI服务器)"},
            {"code": "603186", "role": "弹性", "desc": "高频高速CCL"},
            {"code": "002837", "role": "龙头", "desc": "AI温控/液冷"},
            {"code": "300870", "role": "弹性", "desc": "AI服务器电源"},
        ],
    },
    "半导体": {
        "sector": "半导体设备/材料/代工/封测",
        "supply_chain": "设备→材料→代工→封测",
        "scarce_layer": "刻蚀/CMP设备、光刻胶/抛光液耗材",
        "stocks": [
            {"code": "002371", "role": "龙头", "desc": "刻蚀/薄膜/CMP设备"},
            {"code": "688012", "role": "龙头", "desc": "刻蚀设备(高深宽比)"},
            {"code": "688981", "role": "龙头", "desc": "晶圆代工(大陆最大)"},
            {"code": "600584", "role": "龙头", "desc": "封测龙头"},
            {"code": "300054", "role": "龙头", "desc": "CMP抛光垫"},
            {"code": "688019", "role": "龙头", "desc": "CMP抛光液"},
            {"code": "300236", "role": "龙头", "desc": "光刻胶/湿化学品"},
            {"code": "603078", "role": "弹性", "desc": "光刻胶/配套试剂"},
            {"code": "688126", "role": "龙头", "desc": "大硅片"},
            {"code": "300395", "role": "龙头", "desc": "石英器件/纤维"},
        ],
    },
    "MLCC": {
        "sector": "MLCC、被动元件",
        "supply_chain": "上游粉体/瓷料→MLCC制造→下游(AI服务器/手机/汽车)",
        "scarce_layer": "高端MLCC(村田/三星电机寡头)、MLCC离型膜",
        "stocks": [
            {"code": "000636", "role": "龙头", "desc": "MLCC(军用+民用)"},
            {"code": "300408", "role": "龙头", "desc": "MLCC(中高压/特殊规格)"},
            {"code": "300285", "role": "龙头", "desc": "MLCC瓷粉/BaTiO3"},
            {"code": "603678", "role": "弹性", "desc": "MLCC/陶瓷电容"},
            {"code": "002859", "role": "龙头", "desc": "MLCC离型膜/载带"},
            {"code": "300319", "role": "弹性", "desc": "LTCC/SAW滤波器"},
            {"code": "600563", "role": "弹性", "desc": "薄膜电容(新能源/AI)"},
        ],
    },
    "存储芯片": {
        "sector": "存储芯片、HBM、模组",
        "supply_chain": "HBM→DRAM→NAND→模组→接口芯片",
        "scarce_layer": "HBM(寡头)、DRAM涨价周期",
        "stocks": [
            {"code": "603986", "role": "龙头", "desc": "NOR Flash/MCU"},
            {"code": "688525", "role": "龙头", "desc": "存储模组/嵌入式"},
            {"code": "688123", "role": "龙头", "desc": "EEPROM/存储芯片"},
            {"code": "688008", "role": "龙头", "desc": "内存接口(DDR5/MRDIMM)"},
        ],
    },
    "华为昇腾": {
        "sector": "AI算力芯片、华为产业链",
        "supply_chain": "昇腾芯片→CANN软件→整机伙伴→行业应用",
        "scarce_layer": "昇腾芯片、CANN生态绑定",
        "stocks": [
            {"code": "688041", "role": "龙头", "desc": "国产CPU/DCU"},
            {"code": "688256", "role": "龙头", "desc": "AI训练/推理芯片"},
            {"code": "002261", "role": "弹性", "desc": "昇腾/鸿蒙双生态"},
            {"code": "301236", "role": "龙头", "desc": "华为数字孪生/鸿蒙"},
            {"code": "000034", "role": "弹性", "desc": "昇腾整机伙伴"},
        ],
    },
    "AI Agent": {
        "sector": "AI应用/AI Agent",
        "supply_chain": "大模型→Agent框架→行业应用→数据服务",
        "scarce_layer": "AI应用中台、企业级部署",
        "stocks": [
            {"code": "300496", "role": "龙头", "desc": "智能座舱/AI Agent"},
            {"code": "002230", "role": "龙头", "desc": "AI语音+大模型"},
            {"code": "300229", "role": "弹性", "desc": "AI语义/政务AI"},
            {"code": "300170", "role": "弹性", "desc": "企业级AI Agent"},
            {"code": "300559", "role": "弹性", "desc": "AI教育"},
        ],
    },
    "券商金融": {
        "sector": "券商、金融科技",
        "supply_chain": "券商经纪→投行→资管→金融IT",
        "scarce_layer": "券商龙头(综合)、金融IT系统",
        "stocks": [
            {"code": "600030", "role": "龙头", "desc": "综合券商龙头"},
            {"code": "300059", "role": "龙头", "desc": "互联网券商"},
            {"code": "300033", "role": "龙头", "desc": "金融数据/AI资管"},
            {"code": "600446", "role": "弹性", "desc": "证券交易系统"},
            {"code": "603383", "role": "弹性", "desc": "券商核心交易系统"},
        ],
    },
    "机器人": {
        "sector": "人形机器人、零部件",
        "supply_chain": "关节电机→减速器→力矩传感器→整机",
        "scarce_layer": "六维力矩传感器、谐波减速器",
        "stocks": [
            {"code": "688017", "role": "龙头", "desc": "谐波减速器"},
            {"code": "300124", "role": "龙头", "desc": "伺服电机/控制"},
            {"code": "603662", "role": "龙头", "desc": "六维力矩传感器"},
            {"code": "002747", "role": "龙头", "desc": "工业机器人整机"},
            {"code": "603728", "role": "弹性", "desc": "步进电机/空心杯"},
            {"code": "603667", "role": "弹性", "desc": "精密轴承"},
        ],
    },
    "新能源车": {
        "sector": "新能源车、锂电",
        "supply_chain": "整车→电池→材料→充电",
        "scarce_layer": "电池(宁德)、整车龙头(比亚迪)",
        "stocks": [
            {"code": "002594", "role": "龙头", "desc": "新能源车全球龙头"},
            {"code": "300750", "role": "龙头", "desc": "动力电池龙头"},
            {"code": "300450", "role": "龙头", "desc": "锂电设备龙头"},
            {"code": "300274", "role": "龙头", "desc": "逆变器/储能"},
            {"code": "002920", "role": "龙头", "desc": "智能座舱/智驾"},
        ],
    },
    "黄金": {
        "sector": "黄金、贵金属",
        "supply_chain": "金矿开采→冶炼→ETF/Central Bank",
        "scarce_layer": "金矿资源(矿权/品位)",
        "stocks": [
            {"code": "601899", "role": "龙头", "desc": "黄金+铜矿(全球化)"},
            {"code": "600547", "role": "龙头", "desc": "黄金龙头(国内最大)"},
            {"code": "600988", "role": "弹性", "desc": "黄金(高成长)"},
        ],
    },
    "油价受益": {
        "sector": "航空、化工(油价回落受益)",
        "supply_chain": "航油成本→化工原料",
        "scarce_layer": "航司(成本弹性最大)",
        "stocks": [
            {"code": "601111", "role": "龙头", "desc": "国航(航油占比35%)"},
            {"code": "600029", "role": "龙头", "desc": "南航(航油占比33%)"},
            {"code": "600309", "role": "龙头", "desc": "万华化学(MDI龙头)"},
        ],
    },
    "液冷温控": {
        "sector": "液冷、温控",
        "supply_chain": "液冷整机柜→冷板→管路→冷却液→温控系统",
        "scarce_layer": "液冷整体解决方案",
        "stocks": [
            {"code": "002837", "role": "龙头", "desc": "AI温控/液冷"},
            {"code": "300499", "role": "弹性", "desc": "液冷/温控"},
            {"code": "002851", "role": "弹性", "desc": "电源/液冷"},
        ],
    },
    "低空经济": {
        "sector": "低空经济/eVTOL",
        "supply_chain": "整机→电池→飞控→运营→空管",
        "scarce_layer": "适航认证(先发优势)",
        "stocks": [
            {"code": "600118", "role": "龙头", "desc": "卫星制造"},
            {"code": "600879", "role": "龙头", "desc": "航天电子/无人机"},
        ],
    },
    "信创": {
        "sector": "信创、国产软件",
        "supply_chain": "CPU→OS→数据库→中间件→应用",
        "scarce_layer": "CPU(海光/鲲鹏)",
        "stocks": [
            {"code": "688041", "role": "龙头", "desc": "国产CPU/DCU"},
            {"code": "301236", "role": "龙头", "desc": "国产软硬一体"},
        ],
    },
    "消费电子": {
        "sector": "消费电子、果链",
        "supply_chain": "整机代工→精密件→芯片→显示",
        "scarce_layer": "精密制造(立讯)",
        "stocks": [
            {"code": "002475", "role": "龙头", "desc": "精密制造(Apple链)"},
            {"code": "002241", "role": "龙头", "desc": "声学/MR/VR"},
            {"code": "688608", "role": "弹性", "desc": "智能音频SoC"},
        ],
    },
    "面板": {
        "sector": "面板、显示",
        "supply_chain": "面板制造→材料→设备→终端",
        "scarce_layer": "大尺寸LCD(京东方/TCL寡头)",
        "stocks": [
            {"code": "000725", "role": "龙头", "desc": "LCD+OLED面板龙头"},
        ],
    },
    "医药CXO": {
        "sector": "CXO、创新药",
        "supply_chain": "药物发现→临床→CDMO",
        "scarce_layer": "CDMO产能(药明)",
        "stocks": [
            {"code": "603259", "role": "龙头", "desc": "CRO/CDMO全球龙头"},
        ],
    },
}

# 别名映射
CONCEPT_ALIAS = {}
for key in KNOWLEDGE_BASE:
    CONCEPT_ALIAS[key] = [key]
# 额外别名
CONCEPT_ALIAS["MLCC"].extend(["被动元件", "MLCC概念", "MLCC超级周期"])
CONCEPT_ALIAS["AI算力"].extend(["算力", "光模块", "AI服务器", "CPO"])
CONCEPT_ALIAS["半导体"].extend(["半导体设备", "半导体材料", "芯片", "集成电路", "设备材料"])
CONCEPT_ALIAS["机器人"].extend(["人形机器人", "具身智能", "减速器", "伺服"])
CONCEPT_ALIAS["华为昇腾"].extend(["昇腾", "华为产业链", "华为", "鲲鹏", "鸿蒙"])
CONCEPT_ALIAS["AI Agent"].extend(["智能体", "AI应用", "大模型", "AI智能体"])
CONCEPT_ALIAS["黄金"].extend(["贵金属", "有色黄金"])
CONCEPT_ALIAS["油价受益"].extend(["航空", "油价回落", "美伊和平"])
CONCEPT_ALIAS["存储芯片"].extend(["存储", "HBM", "DRAM", "NAND", "内存"])
CONCEPT_ALIAS["低空经济"].extend(["低空", "eVTOL", "飞行汽车"])
CONCEPT_ALIAS["液冷温控"].extend(["液冷", "温控", "散热", "冷却"])
CONCEPT_ALIAS["新能源车"].extend(["新能源", "锂电", "比亚迪", "充电", "电车"])
CONCEPT_ALIAS["消费电子"].extend(["果链", "苹果", "MR", "VR", "手机"])
CONCEPT_ALIAS["券商金融"].extend(["券商", "证券", "金融科技", "互联网金融"])


# ============================================================
# Part 2: 同花顺热点实时数据
# ============================================================

def ths_hot_today() -> list[dict]:
    """当日同花顺强势股 + 题材归因"""
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    url = f"http://zx.10jqka.com.cn/event/api/getharden/date/{today}/orderby/date/orderway/desc/charset/GBK/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/117.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data.get("errocode", 0) != 0:
            return []
        rows = data.get("data") or []
        result = []
        for item in rows:
            result.append({
                "code": item.get("code", ""),
                "name": item.get("name", ""),
                "reason": item.get("reason", ""),
                "zhangfu": item.get("zhangfu", 0),
                "huanshou": item.get("huanshou", 0),
                "chengjiaoe": item.get("chengjiaoe", 0),
            })
        return result
    except Exception:
        return []


def ths_filter_by_concept(hot_stocks: list[dict], keywords: list[str]) -> list[dict]:
    """从同花顺热点中筛选题材标签匹配的个股"""
    matched = []
    for hs in hot_stocks:
        reason = hs.get("reason", "")
        if not reason:
            continue
        if any(kw in reason for kw in keywords):
            matched.append(hs)
    return matched


# ============================================================
# Part 3: 百度概念板块归属验证
# ============================================================

def baidu_check_concept(code: str) -> list[str]:
    """查个股属于哪些概念板块"""
    url = f"https://finance.pae.baidu.com/api/getrelatedblock?code={code}&market=ab&typeCode=all&finClientType=pc"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "application/vnd.finance-web.v1+json",
        "Origin": "https://gushitong.baidu.com",
        "Referer": "https://gushitong.baidu.com/",
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        d = r.json()
        if str(d.get("ResultCode", -1)) != "0":
            return []
        tags = []
        for block in d.get("Result", []):
            if "概念" in block.get("type", ""):
                for item in block.get("list", []):
                    tags.append(item.get("name", ""))
        return tags
    except Exception:
        return []


# ============================================================
# Part 4: Serenity Scorecard
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
                   context: dict, role: str = "",
                   hot_info: dict = None) -> dict:
    """对单只个股执行Serenity评分"""
    factors = {}
    factors["demand_inflection"] = context.get("demand_inflection", 3)
    role_map = {"龙头": 4.0, "弹性": 3.0, "小市值": 2.5}
    factors["architecture_coupling"] = context.get("architecture_coupling", role_map.get(role, 3.0))
    factors["chokepoint_severity"] = context.get("chokepoint_severity", 4.0 if role == "龙头" else 3.0)
    factors["supplier_concentration"] = context.get("supplier_concentration", 3.0)
    factors["expansion_difficulty"] = context.get("expansion_difficulty", 3.0)
    factors["evidence_quality"] = context.get("evidence_quality", 3)

    pe = live.get("pe_ttm", 0) or 0
    if pe <= 0 or pe > 500:
        val = 2.0
    elif pe <= 20:
        val = 4.5
    elif pe <= 40:
        val = 4.0
    elif pe <= 60:
        val = 3.0
    elif pe <= 100:
        val = 2.0
    else:
        val = 1.5
    mcap = live.get("mcap_yi", 0)
    if mcap < 100:
        val = min(4.0, val + 0.5)
    factors["valuation_disconnect"] = context.get("valuation_disconnect", val)
    factors["catalyst_timing"] = context.get("catalyst_timing", 3)

    total = sum(factors[k] / 5.0 * w for k, w in SERENITY_WEIGHTS.items())

    # 惩罚项
    penalties = {}
    if mcap < 50:
        penalties["liquidity"] = 4.0
    elif mcap < 100:
        penalties["liquidity"] = 3.0
    elif mcap < 200:
        penalties["liquidity"] = 2.0
    elif mcap < 500:
        penalties["liquidity"] = 1.0
    else:
        penalties["liquidity"] = 0.5

    turnover = live.get("turnover_pct", 0) or 0
    if turnover > 20:
        penalties["hype_risk"] = 4.0
    elif turnover > 10:
        penalties["hype_risk"] = 3.0
    elif turnover > 5:
        penalties["hype_risk"] = 2.0
    else:
        penalties["hype_risk"] = 1.0

    penalties["geopolitics"] = context.get("geopolitics", 2.0)
    penalties["cyclicality"] = context.get("cyclicality", 2.0)
    for k in ["dilution_financing", "governance", "accounting_quality", "alternative_design_risk"]:
        penalties[k] = context.get(k, 1.0)

    penalty_total = sum(v * 2.0 for v in penalties.values())
    final = max(0, min(100, total - penalty_total))

    if final >= 80:
        verdict = "Top priority"
    elif final >= 65:
        verdict = "High priority"
    elif final >= 50:
        verdict = "Worth tracking"
    else:
        verdict = "Low priority"

    return {
        "code": code,
        "name": name,
        "mcap_yi": mcap,
        "pe_ttm": pe,
        "pb": live.get("pb", 0),
        "change_pct": live.get("change_pct", 0),
        "turnover_pct": turnover,
        "role": role,
        "factors": factors,
        "raw_total": round(total, 1),
        "penalty_total": round(penalty_total, 1),
        "final_score": round(final, 1),
        "verdict": verdict,
        "hot": hot_info.get("matched", False) if hot_info else False,
        "hot_reason": hot_info.get("reason", "") if hot_info else "",
        "hot_zhangfu": hot_info.get("zhangfu", 0) if hot_info else 0,
    }


# ============================================================
# Part 5: 主流程
# ============================================================

def concept_to_stocks(concept_name: str,
                      context: dict = None,
                      include_hot_extra: bool = True) -> dict:
    """
    核心入口: 概念名 → 候选个股 → Serenity评分排序

    参数:
        concept_name: "MLCC" / "人形机器人" / "昇腾" ...
        context: Serenity评分上下文
        include_hot_extra: 是否包含同花顺热点发现但知识库未覆盖的股

    返回:
        {concept, kb_entry, stocks, top_stocks, hot_match, hot_extra, ...}
    """
    context = context or {}

    # 1. 匹配知识库
    kb_entry = None
    matched_key = None
    if concept_name in KNOWLEDGE_BASE:
        kb_entry = KNOWLEDGE_BASE[concept_name]
        matched_key = concept_name
    else:
        for key, aliases in CONCEPT_ALIAS.items():
            if concept_name in aliases or any(a in concept_name for a in aliases):
                kb_entry = KNOWLEDGE_BASE.get(key)
                matched_key = key
                break

    if not kb_entry:
        return {"concept": concept_name, "kb_entry": None, "stocks": [],
                "top_stocks": [], "message": f"未找到概念'{concept_name}'的知识库映射"}

    # 2. 拉同花顺热点交叉验证
    all_hot = ths_hot_today()
    keywords = CONCEPT_ALIAS.get(matched_key or concept_name, [concept_name])
    hot_match = ths_filter_by_concept(all_hot, keywords)
    hot_by_code = {h["code"]: {"matched": True, "reason": h["reason"],
                                "zhangfu": h["zhangfu"]} for h in hot_match}

    # 3. 知识库个股 + 实时行情
    stocks = kb_entry["stocks"]
    codes = [s["code"] for s in stocks]
    live = tencent_quote(codes)

    # 4. Serenity评分
    scored = []
    for s in stocks:
        ld = live.get(s["code"], {})
        sr = serenity_score(
            code=s["code"],
            name=ld.get("name", s.get("name", s["code"])),
            live=ld,
            context=context,
            role=s.get("role", ""),
            hot_info=hot_by_code.get(s["code"]),
        )
        sr["desc"] = s.get("desc", "")
        # 同花顺热点中有的自动升一级
        if sr["hot"] and sr["role"] == "弹性":
            sr["role"] = "龙头(热)"
        scored.append(sr)

    # 5. 排序
    scored.sort(key=lambda x: x["final_score"] + (5 if x["hot"] else 0) + (3 if x["role"] in ["龙头", "龙头(热)"] else 0), reverse=True)

    # 6. 同花顺热点额外发现(知识库未覆盖)
    hot_extra = []
    if include_hot_extra:
        kb_codes = set(codes)
        for h in hot_match:
            if h["code"] not in kb_codes:
                ld = live.get(h["code"], tencent_quote([h["code"]]).get(h["code"], {}))
                hot_extra.append({
                    "code": h["code"],
                    "name": ld.get("name", h["name"]),
                    "reason": h["reason"],
                    "zhangfu": h["zhangfu"],
                    "mcap_yi": ld.get("mcap_yi", 0),
                })

    return {
        "concept": concept_name,
        "matched_key": matched_key,
        "kb_entry": {
            "sector": kb_entry["sector"],
            "supply_chain": kb_entry["supply_chain"],
            "scarce_layer": kb_entry["scarce_layer"],
        },
        "stocks": scored,
        "top_stocks": scored[:20],
        "hot_match": hot_match[:15],
        "hot_extra": hot_extra[:10],
        "has_hot_data": len(all_hot) > 0,
    }


# ============================================================
# Part 6: HTML生成
# ============================================================

def stock_card_html(r: dict) -> str:
    """Serenity评分个股卡片"""
    mcap = r["mcap_yi"]
    pe = r["pe_ttm"]
    chg = r["change_pct"]
    score = r["final_score"]
    role = r.get("role", "")
    updown = "#d32f2f" if chg > 0 else "#2e7d32"

    if mcap >= 1000:
        tag, tc = "千亿大盘", "#1a237e"
    elif mcap >= 200:
        tag, tc = "中盘成长", "#1565c0"
    elif mcap >= 50:
        tag, tc = "小市值", "#e65100"
    else:
        tag, tc = "微盘", "#6a1b9a"

    sc = "#d32f2f" if score >= 80 else "#f57c00" if score >= 65 else "#388e3c" if score >= 50 else "#757575"

    hot_b = ' <span style="font-size:10px;background:#ffebee;color:#c62828;padding:1px 5px;border-radius:8px">热点</span>' if r.get("hot") else ""

    return f'''<div class="stock-card" style="position:relative">
  <div style="position:absolute;top:4px;right:6px;font-size:10px;font-weight:bold;color:{sc}">S-{score:.0f}</div>
  <div class="stock-header">
    <span class="stock-name">{r["name"]}</span>
    <span class="stock-code">{r["code"]}</span>
    <span class="stock-tag" style="background:#e8eaf6;color:{tc}">{tag}</span>
    {f'<span class="stock-tag" style="background:#fff3e0;color:#e65100">{role}</span>' if role else ''}{hot_b}
  </div>
  <div class="stock-details">
    <span>市值：{mcap:.0f}亿</span>
    <span>PE：{pe:.1f}</span>
    <span style="color:{updown}">{chg:+.2f}%</span>
    <span style="color:{sc}">{r["verdict"]}</span>
  </div>
  {f'<div style="font-size:11px;color:#888;margin-top:2px">{r.get("desc","")}</div>' if r.get("desc") else ''}
</div>'''


def stocks_html(results: list[dict]) -> str:
    return '\n    '.join(stock_card_html(r) for r in results)


def supply_chain_html(kb: dict) -> str:
    return f'''<div style="background:#f5f5f5;padding:10px 14px;border-radius:8px;margin:8px 0;font-size:13px">
  <div><strong>供应链层级：</strong>{kb["supply_chain"]}</div>
  <div style="margin-top:4px"><strong>瓶颈环节：</strong><span style="color:#c62828">{kb["scarce_layer"]}</span></div>
</div>'''


def hot_extra_html(hot_extra: list[dict]) -> str:
    if not hot_extra:
        return ""
    items = "".join(f'<span style="display:inline-block;margin:2px 4px;font-size:12px;background:#fff3e0;padding:2px 8px;border-radius:4px">{h["name"]}({h["code"]}) +{h["zhangfu"]}% {h["reason"][:20]}</span>' for h in hot_extra[:6])
    return f'''<div style="margin-top:8px;padding:8px;background:#fff8e1;border-radius:6px;font-size:12px">
  <strong>同花顺热点匹配(额外):</strong> {items}
</div>'''


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    import sys
    concept = sys.argv[1] if len(sys.argv) > 1 else "MLCC"

    print(f"\n=== Serenity: {concept} ===\n")

    ctx = {
        "demand_inflection": 5,
        "evidence_quality": 5,
        "catalyst_timing": 5,
        "chokepoint_severity": 5,
    }

    result = concept_to_stocks(concept, context=ctx)

    if result.get("message"):
        print(result["message"])
        sys.exit(1)

    kb = result["kb_entry"]
    print(f"板块: {kb['sector']}")
    print(f"瓶颈: {kb['scarce_layer']}")
    print()

    top = result["top_stocks"][:10]
    print(f"{'名称':<10} {'代码':<8} {'角色':<10} {'S分':<6} {'评级':<18} {'热':<4}")
    print("-" * 60)
    for r in top:
        h = "🔥" if r.get("hot") else ""
        print(f"{r['name']:<10} {r['code']:<8} {r['role']:<10} {r['final_score']:<6} {r['verdict']:<18} {h}")

    if result.get("hot_match"):
        print(f"\n同花顺热点匹配 {len(result['hot_match'])} 只")
    if result.get("hot_extra"):
        print(f"同花顺额外发现 {len(result['hot_extra'])} 只(知识库未覆盖):")
        for h in result["hot_extra"][:5]:
            print(f"  {h['name']}({h['code']}) +{h['zhangfu']}% 题材:{h['reason'][:40]}")
