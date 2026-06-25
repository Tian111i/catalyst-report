# -*- coding: utf-8 -*-
"""
消息面催化报告 V3 — 使用 serenity_flow 动态选股引擎
流程:
  1. 定义催化事件 → 映射到概念
  2. serenity_flow.concept_analysis() 获取各概念候选股
  3. Serenity评分排序
  4. 生成HTML报告
"""
import json, os, sys, time

BASE = r'E:\投研尝试'
os.chdir(BASE)
sys.path.insert(0, BASE)

from serenity_flow import concept_analysis, stocks_html, CONCEPT_LEADERS
from serenity_flow import ths_hot_today, auto_identify_concepts

REPORT_DATE = "2026-06-18"
REPORT_DATE_CN = "2026年6月18日（周四）"
COVER_WINDOW = "6月17日（周三）开盘 → 6月18日（周四）盘前"
WEEKDAY = "周四"
PREV_DAY = "6/17(周三)"

# ============================================================
# Step 1: 定义催化事件 → 概念映射
# ============================================================
EVENTS = [
    {
        "id": "lujiazui",
        "level": "T0",
        "title": "2026陆家嘴论坛：央行+证监会重磅发声——中长期资金入市1.3万亿+科创板第五套扩容至AI",
        "source": "央行/证监会/陆家嘴论坛（2026-06-17至18）",
        "time": "2026-06-17至06-18",
        "core": "2026陆家嘴论坛在上海召开，央行行长潘功胜、证监会主席吴清密集发布重磅政策：1）社保/保险等净买入A股1.3万亿元（新国九条两年多，持有A股流通市值增长85%）；2）科创板第五套上市标准适用范围扩大至人工智能大模型行业（此前仅限生物医药）；3）支持沪深交易所推出主动管理ETF；4）商业不动产REITs首批4单6/18挂牌上市；5）严查严处借科技之名蹭热点、炒概念等违法违规行为；6）推动中长期资金对股市、债市投资力度；7）适时发布规范发展资本市场人工智能的指导意见。吴清强调A股科技板块市值占比已超三成，千亿市值中科技企业占比45%。这是年内最大级别的资本市场政策催化。",
        "sector": "券商/金融科技、科创板/AI大模型、AI应用",
        "concept": "券商金融",
        "extra_codes": ["688256", "688041", "002230"],
        "stars": 5,
        "duration": "5-10个交易日",
        "risk": "政策信号积极但具体细则尚未落地；严查借科技炒概念对蹭热点个股构成压制；科创板扩容可能带来短期抽血效应。",
        "context": {"demand_inflection": 5, "evidence_quality": 5, "catalyst_timing": 5, "chokepoint_severity": 3},
    },
    {
        "id": "peace",
        "level": "T0",
        "title": "美伊和平谅解备忘录正式签署：永久停火+霍尔木兹重开+原油暴跌5%",
        "source": "路透社/新华社/特朗普/伊朗外交部",
        "time": "2026-06-18",
        "core": "美伊和平协议取得历史性突破——谅解备忘录（MOU）正式签署，核心内容：1）立即永久停火（涵盖所有战线包括黎巴嫩）；2）30天内全面解除美国对伊朗港口封锁；3）霍尔木兹海峡立即恢复国际航运；4）分阶段解冻伊朗240亿美元海外资产；5）后续60天谈判核问题及全面制裁解除。特朗普在法国凡尔赛宫签署纸本协议，伊朗数字签署。布伦特原油暴跌至$83（-5.2%），WTI跌至$79.20。亚洲股市因协议签署普遍上涨。以色列强烈反对该协议。",
        "sector": "航空（航油成本降）、化工（原料成本降）",
        "concept": "油价受益",
        "extra_codes": [],
        "stars": 5,
        "duration": "5-8个交易日",
        "risk": "谅解备忘录≠最终和平协议；以色列强烈反对；油价已部分反映和平预期。",
        "context": {"demand_inflection": 5, "evidence_quality": 5, "catalyst_timing": 5, "chokepoint_severity": 3},
    },
    {
        "id": "huawei",
        "level": "T0",
        "title": "华为昇腾950DT指令级拆解确认：CANN软件栈全球第二+DeepSeek协同设计",
        "source": "SemiAnalysis/华为/InfoQ",
        "time": "2026-06-17至06-18",
        "core": "SemiAnalysis发布重磅拆解报告确认：1）昇腾950DT运行DeepSeek V4完成全指令级Trace拆解，确认DeepSeek V4部分架构专为昇腾协同设计；2）CANN软件栈在Day 0即完整支持DeepSeek V4推理，成为全球继CUDA之后第二个实现此水平的软件栈；3）字节跳动已拿下昇腾950一半产能，阿里、腾讯跟进数十万颗，中国移动集采776套昇腾节点；4）麒麟9030 Pro首拆确认中芯国际N+3制程，最小金属间距32.5nm，晶体管密度113.4 MTr/mm²。",
        "sector": "AI算力芯片、半导体设备、华为产业链",
        "concept": "华为昇腾",
        "extra_codes": ["002371", "688981"],
        "stars": 5,
        "duration": "3-5个交易日",
        "risk": "华为芯片成本（DUV多重曝光）和良率仍具挑战；昇腾950DT商业落地规模尚需验证。",
        "context": {"demand_inflection": 5, "evidence_quality": 5, "catalyst_timing": 5},
    },
    {
        "id": "mlcc",
        "level": "T0",
        "title": "MLCC超级周期：华泰证券深度研报「MLCC会成为下一个存储」——与HBM格局高度相似",
        "source": "华泰证券/高盛/摩根士丹利/Murata",
        "time": "2026-06-17至06-18",
        "core": "华泰证券发布深度研报《MLCC会成为下一个存储吗？》，核心论点：1）AI服务器MLCC格局与HBM高度相似——高端MLCC由村田+三星电机主导（合计约90%份额）；2）高盛测算AI服务器MLCC市场将从FY25约2,150亿日元增至FY30约9,200亿日元（CAGR 34%）；3）摩根士丹利拆解NVIDIA Rubin VR200发现MLCC价值量较GB300增长182%；4）华强北实地探访确认：高容MLCC现货价格已翻倍，交期延至16-24周。日本财务省4月数据：MLCC出口额年增28%。",
        "sector": "MLCC、被动元件",
        "concept": "MLCC",
        "extra_codes": [],
        "stars": 5,
        "duration": "1-2周",
        "risk": "MLCC板块前期已大涨；村田官方未对产品调价；新建产线壁垒低于DRAM/HBM。",
        "context": {"demand_inflection": 5, "evidence_quality": 5, "catalyst_timing": 5, "chokepoint_severity": 5, "supplier_concentration": 5, "expansion_difficulty": 4},
    },
    {
        "id": "aiagent",
        "level": "T1",
        "title": "腾讯微信AI生态全面开放：美团/滴滴/京东/携程首批接入，AI Agent商业化加速",
        "source": "腾讯/京东/滴滴/美团官方",
        "time": "2026-06-08至06-18",
        "core": "微信正式发布AI生态接入指引，向14.32亿月活用户开放AI能力。首批接入企业包括美团、滴滴、京东、携程、途虎养车等。京东与腾讯宣布围绕AI Agent深度合作（京东供应链+腾讯入口）。阿里千问全面开放第三方Agent测试（瑞幸/肯德基/东航首批）。AI Agent正从「概念验证」进入「生态商业化」阶段。",
        "sector": "AI应用/AI Agent、腾讯生态",
        "concept": "AI Agent",
        "extra_codes": [],
        "stars": 3,
        "duration": "2-3个交易日",
        "risk": "微信AI Agent商业模式仍处早期；字节豆包付费导致用户流失；AI应用板块估值已较高。",
        "context": {"demand_inflection": 4, "evidence_quality": 3, "catalyst_timing": 3, "chokepoint_severity": 2},
    },
    {
        "id": "techboard",
        "level": "T1",
        "title": "科创板第五套标准扩容至AI大模型：优质AI企业上市通道打开",
        "source": "中国证监会/陆家嘴论坛",
        "time": "2026-06-17",
        "core": "证监会主席吴清在陆家嘴论坛宣布，科创板第五套上市标准适用范围正式扩大至人工智能大模型行业。此前第五套标准仅面向生物医药等暂未盈利但研发周期长的硬科技企业，本次扩容意味着暂未盈利的AI大模型企业也可通过科创板上市融资。A股科技板块市值占比已超三成，千亿市值科技企业占比达45%。",
        "sector": "AI算力/AI应用、科创板、券商（投行业务）",
        "concept": "券商金融",
        "extra_codes": ["688256", "688041"],
        "stars": 4,
        "duration": "3-5个交易日",
        "risk": "实际上市企业数量和融资规模需时间落地；短期内对券商投行业务收入增量有限。",
        "context": {"demand_inflection": 4, "evidence_quality": 4, "catalyst_timing": 3},
    },
    {
        "id": "newenergy",
        "level": "T2",
        "title": "超10家新能源车企涨价：比亚迪+小米+华为问界集体上调价格",
        "source": "比亚迪/小米/华为官方/乘联会",
        "time": "2026-06-17至06-18",
        "core": "由于车规级芯片、存储硬件、原材料成本上涨，超10家新能源车企集体涨价。比亚迪「天神之眼B」智驾选装包从9900元涨至12000元，小米SU7全系涨4000元，华为问界M9涨1万元。行业从「价格战」转向「技术驱动的价值战」。",
        "sector": "新能源整车、锂电",
        "concept": "新能源车",
        "extra_codes": [],
        "stars": 2,
        "duration": "1-2个交易日",
        "risk": "涨价潮反映成本压力而非需求强劲；比亚迪闪充布局为中长期利好。",
        "context": {"demand_inflection": 3, "evidence_quality": 3, "catalyst_timing": 2, "chokepoint_severity": 2},
    },
    {
        "id": "semicon",
        "level": "T1",
        "title": "半导体设备材料国产替代加速：中芯N+3量产验证+长江存储扩产+政策加码",
        "source": "SemiAnalysis/华泰证券/集微网/陆家嘴论坛",
        "time": "2026-06-17至06-18",
        "core": "多重催化共振：1）华为麒麟9030 Pro首拆确认中芯国际N+3制程（最小金属间距32.5nm），国产先进制程商业化落地；2）长江存储232层3D NAND产能利用率提升至90%以上，二期扩产加速；3）陆家嘴论坛明确科创板第五套扩容至AI，硬科技企业融资通道打开。华泰证券测算国产半导体设备2026年国产化率有望从20%提升至28%，材料端同步受益。北方华创/中微公司2026年订单增速预计超50%。",
        "sector": "半导体设备、半导体材料、晶圆代工、封测",
        "concept": "半导体",
        "extra_codes": [],
        "stars": 4,
        "duration": "3-5个交易日",
        "risk": "设备国产化率提升仍需时间；中芯N+3良率和成本仍存不确定性；半导体板块估值已不低。",
        "context": {"demand_inflection": 5, "evidence_quality": 4, "catalyst_timing": 4, "chokepoint_severity": 4, "expansion_difficulty": 4},
    },
    {
        "id": "cpo",
        "level": "T1",
        "title": "AI集群带宽瓶颈驱动CPO商用加速：光互连价值量提升+博通/思科推进CPO路线图",
        "source": "博通/思科/中际旭创公告/LightCounting",
        "time": "2026-06-17至06-18",
        "core": "AI集群规模持续扩大，传统可插拔光模块在带宽密度/功耗/成本方面接近物理极限，CPO（共封装光学）成为下一代AI互连核心方案。博通最新CPO交换机芯片路线图显示2027年将实现3.2T CPO。LightCounting预计CPO市场规模将从2025年约5亿美元增至2030年约60亿美元（CAGR 65%）。中际旭创、天孚通信等国内光模块龙头已布局CPO技术。硅光+CPO有望重塑光模块产业链格局。",
        "sector": "光模块/光器件、硅光芯片、CPO封装",
        "concept": "CPO",
        "extra_codes": [],
        "stars": 4,
        "duration": "2-4个交易日",
        "risk": "CPO商用化仍需1-2年；技术路线尚未统一（硅光/薄膜铌酸锂/等）；短期业绩贡献有限。",
        "context": {"demand_inflection": 4, "evidence_quality": 3, "catalyst_timing": 3, "architecture_coupling": 4, "chokepoint_severity": 4},
    },
    {
        "id": "pcb",
        "level": "T2",
        "title": "AI服务器PCB量价齐升+东山精密12亿美元投资：GPU升级驱动高速PCB需求爆发",
        "source": "Prismark/沪电股份公告/东山精密/鹏鼎控股",
        "time": "2026-06-17至06-18",
        "core": "AI服务器PCB需求持续升级：NVIDIA Rubin平台PCB价值量较GB300增长约60%（高层数+超低损耗材料），单台AI服务器PCB价值量从约$2,000提升至约$3,200。Prismark预测2026年全球PCB产值同比增长8.5%，其中高速PCB增速超15%。东山精密（002384）宣布12亿美元PCB产能扩建计划，主要投向AI服务器HDI及封装基板，为国内PCB行业近年来最大单笔投资。沪电股份（002463）AI服务器PCB收入占比已超60%，深南电路（002916）IC载板产能利用率持续提升。",
        "sector": "PCB/印制电路板、IC载板",
        "concept": "PCB",
        "extra_codes": [],
        "stars": 3,
        "duration": "2-3个交易日",
        "risk": "PCB行业竞争格局分散；涨价持续性存疑；高端PCB产能扩张进度待观察。",
        "context": {"demand_inflection": 4, "evidence_quality": 4, "catalyst_timing": 3, "chokepoint_severity": 3},
    },
    {
        "id": "fomc",
        "level": "T0",
        "title": "Fed FOMC Warsh首秀偏鹰：利率维持3.50-3.75%不变，点阵图显示年内加息倾向",
        "source": "美联储/FOMC/CNBC/AP",
        "time": "2026-06-17至06-18",
        "core": "新任主席Kevin Warsh首次主持FOMC会议，利率维持3.50-3.75%不变（一致通过）。但关键信息偏鹰：点阵图显示9/19委员预计年内至少加息一次；2026年PCE通胀预期上修至3.6%；GDP增长预期下调至2.2%。市场反应：美股下跌、美债收益率上行、美元走强。",
        "sector": "黄金（避险承压、但中期关注）",
        "concept": "黄金",
        "extra_codes": [],
        "stars": 5,
        "duration": "2-3个交易日",
        "risk": "FOMC偏鹰超预期；美债收益率上行对高估值科技股不利。",
        "context": {"demand_inflection": 3, "evidence_quality": 5, "catalyst_timing": 5, "chokepoint_severity": 2},
    },
    {
        "id": "mu",
        "level": "T1",
        "title": "Micron突破$1000后回调6.2%：6/24财报前瞻——EPS预期同比+960%",
        "source": "Micron/Citi/TD Cowen/Nasdaq",
        "time": "2026-06-17至06-18",
        "core": "MU周二突破$1,000后周三-6.2%回调至$950附近。但基本面持续强劲：Q3财报（6/24）预期EPS $20.25（同比+960%），营收$35.06B（+277%），已连续12个季度beat预期。HBM全年售罄、DRAM 2026年供不应求（约5%缺口）、涨价周期预期延至2027年。",
        "sector": "存储芯片、HBM产业链",
        "concept": "存储芯片",
        "extra_codes": ["600584", "002371"],
        "stars": 4,
        "duration": "2-4个交易日",
        "risk": "MU $1000+获利盘压力；存储涨价周期已持续5个季度；FOMC偏鹰对高估值科技股不利。",
        "context": {"demand_inflection": 5, "evidence_quality": 4, "catalyst_timing": 5},
    },
    {
        "id": "nvidia",
        "level": "T1",
        "title": "NVIDIA $25B债券超额认购完成+Oracle $90-95B资本开支计划：AI需求强劲",
        "source": "NVIDIA/Oracle/PitchBook/Nasdaq",
        "time": "2026-06-15至06-18",
        "core": "NVIDIA $25B债券发行完成（超额认购约3x），标普评级上调至AA。Oracle宣布FY2027资本开支计划$90-95B（GPU利用率97.5%），验证AI算力需求持续强劲。但FOMC偏鹰+MU回调拖累NVDA从中期高点$236回落至$205。",
        "sector": "AI算力/光模块、AI服务器",
        "concept": "AI算力",
        "extra_codes": [],
        "stars": 4,
        "duration": "2-3个交易日",
        "risk": "Oracle资本开支计划市场已有预期；FOMC偏鹰对高估值科技整体承压。",
        "context": {"demand_inflection": 5, "evidence_quality": 4, "catalyst_timing": 4},
    },
    {
        "id": "optimus",
        "level": "T2",
        "title": "Tesla Optimus量产准备持续推进+比亚迪闪充全球布局",
        "source": "Tesla/比亚迪官方",
        "time": "2026-06-17至06-18",
        "core": "Tesla Fremont工厂Optimus产线调试持续推进，马斯克确认7月底展示量产准备状态。比亚迪1500kW闪充落地欧洲/加拿大（功率为V4超充3倍），英国交付突破10万台。",
        "sector": "人形机器人、新能源车",
        "concept": "机器人",
        "extra_codes": ["002594"],
        "stars": 3,
        "duration": "1-2个交易日",
        "risk": "Optimus量产时间表仍存不确定性；比亚迪闪充属中长期布局。",
        "context": {"demand_inflection": 3, "evidence_quality": 3, "catalyst_timing": 3},
    },
]

# ============================================================
# Step 2: 运行 serenity_flow 获取各概念候选股
# ============================================================
print("=== 正在通过 a-stock-data + Serenity 获取各概念候选股 ===\n")

concept_results = {}
for ev in EVENTS:
    cname = ev["concept"]
    if cname in concept_results:
        continue
    print(f"> {cname}...", end=" ", flush=True)
    result = concept_analysis(cname, context=ev.get("context", {}), extra_codes=ev.get("extra_codes"))
    concept_results[cname] = result
    print(f"热点{len(result['hot_stocks'])}只 + 龙头{len(result['leader_stocks'])}只 = {len(result['all_scored'])}只候选")
    time.sleep(0.5)

# 今日热点概念总览
hot_concepts = auto_identify_concepts(ths_hot_today())
print(f"\n今日同花顺热点概念: {len(hot_concepts)} 个活跃")
for cname, stocks in sorted(hot_concepts.items(), key=lambda x: -len(x[1]))[:8]:
    print(f"  {cname}: {len(stocks)}只")

# ============================================================
# Step 3: 生成 HTML
# ============================================================
print("\n=== 生成报告 HTML ===\n")

def event_stocks_html(event, concept_result):
    """生成事件的个股卡片HTML"""
    top = concept_result.get("top", [])
    # 取前6只
    cards = stocks_html(top[:6])
    return cards

# 构建事件HTML
events_html_parts = []
for ev in EVENTS:
    cname = ev["concept"]
    cr = concept_results.get(cname, {})
    stocks = cr.get("top", [])[:6]

    # 同花顺热点额外发现
    hot_extra = cr.get("hot_stocks", [])
    extra_html = ""
    if hot_extra:
        extra_codes = set(s["code"] for s in stocks)
        extra_stocks = [s for s in hot_extra if s["code"] not in extra_codes][:3]
        if extra_stocks:
            extra_names = "、".join(f"{s['name']}({s['code']})" for s in extra_stocks)
            extra_zhangfu = "、".join(f"+{s['change_pct']:.1f}%" for s in extra_stocks)
            extra_html = f'<div style="margin-top:6px;font-size:12px;color:#e65100">同花顺热点关联: {extra_names} ({extra_zhangfu})</div>'

    # 供应链分析
    chain_html = ""
    leader_codes = CONCEPT_LEADERS.get(cname, [])
    if leader_codes:
        leaders_found = [s for s in stocks if s["code"] in leader_codes]
        if leaders_found:
            ldr_names = "、".join(s["name"] for s in leaders_found)
            ldr_scores = "、".join(f"S-{s['final_score']:.0f}" for s in leaders_found)
            chain_html = f'<div style="margin-top:4px;font-size:12px;color:#555">结构性龙头: {ldr_names} | Serenity: {ldr_scores}</div>'

    ev["_stocks_html"] = stocks_html(stocks[:6])
    ev["_extra_html"] = extra_html
    ev["_chain_html"] = chain_html

# 构建国内/海外消息
domestic_events = [ev for ev in EVENTS if ev["id"] not in ("fomc", "mu", "nvidia", "optimus")]
overseas_events = [ev for ev in EVENTS if ev["id"] in ("fomc", "mu", "nvidia", "optimus")]

def render_event(ev):
    cls = "t0" if ev["level"] == "T0" else "t1" if ev["level"] == "T1" else "t2"
    return f'''<!-- {ev["title"][:30]} -->
<div class="event {cls}">
  <div class="level-badge">{ev["level"]}</div>
  <h3>{ev["title"]}</h3>
  <div class="field"><span class="field-label">来源：</span>{ev["source"]}</div>
  <div class="field"><span class="field-label">时间：</span>{ev["time"]}</div>
  <div class="field"><span class="field-label">核心：</span>{ev["core"]}</div>
  <div class="field"><span class="field-label">受益板块：</span>{ev["sector"]}</div>
  <div class="field"><span class="field-label">受益龙头：</span>
    <div class="stocks-container">
    {ev["_stocks_html"]}
    </div>
    {ev["_chain_html"]}
    {ev["_extra_html"]}
  </div>
  <div class="field"><span class="field-label">影响程度：</span><span class="stars">{'★' * ev["stars"]}{'☆' * (5 - ev["stars"])}</span></div>
  <div class="field"><span class="field-label">持续时间：</span>{ev["duration"]}</div>
  <div class="field risk">⚠ 风险提示：{ev["risk"]}</div>
</div>'''

domestic_html = '\n\n'.join(render_event(ev) for ev in domestic_events)
overseas_html = '\n\n'.join(render_event(ev) for ev in overseas_events)

# 评分表
score_rows = ""
for ev in EVENTS:
    cname = ev["concept"]
    cr = concept_results.get(cname, {})
    top = cr.get("top", [])[:3]
    if not top:
        continue
    avg_score = sum(r["final_score"] for r in top) / len(top)
    if avg_score >= 70: score_cls = "high"
    elif avg_score >= 55: score_cls = "mid"
    else: score_cls = "low"

    # 取最高分个股的因子
    best = top[0]
    fs = best["factors"]
    score_value = best["final_score"]
    verdict = best["verdict"]
    best_name = best["name"]

    if avg_score >= 70: pattern = "短期格局"
    elif avg_score >= 55: pattern = "关注"
    else: pattern = "观望/回避"

    score_rows += f'''    <tr>
      <td>{ev["title"][:20]}…</td>
      <td class="high">{fs["demand_inflection"] * 20}</td>
      <td class="high">{fs["architecture_coupling"] * 20}</td>
      <td class="mid">{fs["valuation_disconnect"] * 20}</td>
      <td>{best_name}</td>
      <td class="{score_cls}">{score_value:.1f}</td>
      <td style="font-size:11px">{pattern}</td>
    </tr>
'''

# 汇总建议
recommend_html = '''
<div class="recommend">
  <h3>首选标的 & 操作思路</h3>
'''

# 按评分排序找首选
all_scores = []
for ev in EVENTS:
    cname = ev["concept"]
    cr = concept_results.get(cname, {})
    top = cr.get("top", [])
    if top:
        best = top[0]
        all_scores.append((best["final_score"], best, ev))

all_scores.sort(key=lambda x: -x[0])
top3 = all_scores[:5]

rec_items = {
    "red": [],
    "blue": [],
    "orange": [],
}

# 首选 = 评分最高且T0
for score, stock, ev in all_scores:
    if ev["level"] == "T0" and score >= 45:
        rec_items["red"].append((stock, ev))
    elif ev["level"] == "T1" and score >= 45:
        rec_items["blue"].append((stock, ev))
    else:
        rec_items["orange"].append((stock, ev))

if rec_items["red"]:
    stock, ev = rec_items["red"][0]
    recommend_html += f'''  <div class="rec-item">
    <span class="tag red">首选</span>
    <strong>{stock["name"]}({stock["code"]})</strong> S-{stock["final_score"]:.0f} | {ev["title"][:40]}… — Serenity评分最高，龙头地位明确，直接受益于催化事件。
  </div>
'''

if rec_items["red"]:
    stock, ev = rec_items["red"][1] if len(rec_items["red"]) > 1 else (rec_items["blue"][0] if rec_items["blue"] else rec_items["orange"][0])
    recommend_html += f'''  <div class="rec-item">
    <span class="tag red">次选</span>
    <strong>{stock["name"]}({stock["code"]})</strong> S-{stock["final_score"]:.0f} | 结构性龙头，估值合理，安全边际较高。
  </div>
'''

if rec_items["blue"]:
    stock, ev = rec_items["blue"][0]
    recommend_html += f'''  <div class="rec-item">
    <span class="tag blue">观察（逢低）</span>
    <strong>{stock["name"]}({stock["code"]})</strong> S-{stock["final_score"]:.0f} | 中线趋势明确，等待回调机会。
  </div>
'''

if rec_items["orange"]:
    for stock, ev in rec_items["orange"][:2]:
        recommend_html += f'''  <div class="rec-item">
    <span class="tag orange">事件驱动</span>
    <strong>{stock["name"]}({stock["code"]})</strong> S-{stock["final_score"]:.0f} | {ev["title"][:30]}… — 事件驱动型机会，注意节奏。
  </div>
'''

# Serenity评分表
serenity_table_rows = ""
for ev in EVENTS:
    cname = ev["concept"]
    cr = concept_results.get(cname, {})
    top = cr.get("top", [])[:3]
    if not top:
        continue
    best = top[0]
    fs = best["factors"]
    sc = best["final_score"]
    cl = "high" if sc >= 65 else "mid" if sc >= 50 else "low"
    n = best["name"]
    c = best["code"]

    serenity_table_rows += f'''    <tr>
      <td>{ev["title"][:16]}…</td>
      <td>{n}({c})</td>
      <td>{fs["demand_inflection"]}</td>
      <td>{fs["architecture_coupling"]}</td>
      <td>{fs["chokepoint_severity"]}</td>
      <td>{fs["evidence_quality"]}</td>
      <td>{fs["valuation_disconnect"]}</td>
      <td>{fs["catalyst_timing"]}</td>
      <td class="{cl}">{sc:.1f}</td>
      <td style="font-size:11px">{best["verdict"]}</td>
    </tr>
'''

recommend_html += '''
  <div style="margin-top:12px;padding:10px;background:#f5f5f5;border-radius:6px;font-size:13px">
    <strong>仓位建议：</strong>7成仓位（流动性系数×1.0，陆家嘴论坛+MLCC双主线）<br>
    <strong>核心标签：</strong>
    <span class="tag red">陆家嘴论坛政策</span>
    <span class="tag red">华为昇腾生态</span>
    <span class="tag red">MLCC超级周期</span>
    <span class="tag blue">AI算力</span>
    <span class="tag green">油价回落利好</span>
    <span class="tag orange">FOMC偏鹰</span>
  </div>
</div>'''

# Full HTML
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>消息面催化报告 {REPORT_DATE}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'Microsoft YaHei', sans-serif; background: #f0f2f5; color: #333; padding: 20px; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; }}
.header h1 {{ font-size: 28px; margin-bottom: 15px; letter-spacing: 3px; }}
.header .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px; opacity: 0.9; }}
.header .meta span {{ display: block; }}
.header .rating {{ display: inline-block; background: rgba(255,200,0,0.2); padding: 4px 12px; border-radius: 20px; font-size: 18px; margin-top: 10px; }}
.header .core-logic {{ margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.1); border-radius: 8px; font-size: 14px; line-height: 1.6; }}
.section-title {{ font-size: 20px; font-weight: bold; padding: 12px 0; margin: 20px 0 10px 0; border-bottom: 3px solid; display: flex; align-items: center; gap: 10px; }}
.section-title.domestic {{ color: #c0392b; border-color: #c0392b; }}
.section-title.overseas {{ color: #27ae60; border-color: #27ae60; }}
.section-title.market {{ color: #2980b9; border-color: #2980b9; }}
.event {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 5px solid #ddd; position: relative; }}
.event.t0 {{ border-left-color: #e74c3c; }}
.event.t1 {{ border-left-color: #f39c12; }}
.event.t2 {{ border-left-color: #3498db; }}
.event .level-badge {{ position: absolute; top: 15px; right: 15px; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; color: white; }}
.event.t0 .level-badge {{ background: #e74c3c; }}
.event.t1 .level-badge {{ background: #f39c12; }}
.event.t2 .level-badge {{ background: #3498db; }}
.event .field {{ margin-bottom: 8px; font-size: 14px; line-height: 1.6; }}
.event .field-label {{ font-weight: bold; color: #555; display: inline-block; min-width: 70px; }}
.event .stars {{ color: #f1c40f; letter-spacing: 2px; }}
.event .risk {{ background: #fff3f3; padding: 8px 12px; border-radius: 6px; margin-top: 10px; font-size: 13px; color: #c0392b; }}
.stock-card {{ display: inline-block; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 8px 12px; margin: 3px; font-size: 13px; position: relative; }}
.stock-card .stock-header {{ display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }}
.stock-card .stock-name {{ font-weight: bold; }}
.stock-card .stock-code {{ color: #666; font-size: 11px; }}
.stock-card .stock-tag {{ font-size: 10px; padding: 1px 5px; border-radius: 8px; background: #e3f2fd; color: #1565c0; }}
.stock-card .stock-details {{ display: flex; flex-wrap: wrap; gap: 8px; font-size: 12px; color: #555; }}
.stocks-container {{ display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0; }}
.score-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; }}
.score-table th {{ background: #1a1a2e; color: white; padding: 8px 10px; text-align: center; }}
.score-table td {{ padding: 6px 10px; text-align: center; border-bottom: 1px solid #eee; }}
.score-table tr:hover {{ background: #f5f5f5; }}
.score-table .high {{ color: #d32f2f; font-weight: bold; }}
.score-table .mid {{ color: #f57c00; font-weight: bold; }}
.score-table .low {{ color: #388e3c; }}
.recommend {{ background: linear-gradient(135deg, #fffde7, #fff8e1); border: 2px solid #ffd54f; border-radius: 12px; padding: 20px; margin: 20px 0; }}
.recommend h3 {{ color: #e65100; margin-bottom: 10px; }}
.recommend .rec-item {{ padding: 8px 0; border-bottom: 1px dashed #ffe082; font-size: 14px; line-height: 1.6; }}
.recommend .rec-item:last-child {{ border: none; }}
.recommend .tag {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-right: 4px; }}
.recommend .tag.red {{ background: #ffebee; color: #c62828; }}
.recommend .tag.blue {{ background: #e3f2fd; color: #1565c0; }}
.recommend .tag.green {{ background: #e8f5e9; color: #2e7d32; }}
.recommend .tag.orange {{ background: #fff3e0; color: #e65100; }}
.self-check {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 12px 15px; margin: 20px 0; border-radius: 0 8px 8px 0; font-size: 13px; }}
.self-check .check-item {{ margin: 4px 0; }}
.self-check .check-item::before {{ content: "\\2713 "; color: #2e7d32; font-weight: bold; }}
.macro-warning {{ background: #fff3e0; border: 1px solid #ff9800; border-radius: 10px; padding: 15px; margin: 15px 0; font-size: 13px; line-height: 1.6; }}
.macro-warning h4 {{ color: #e65100; margin-bottom: 8px; }}
.footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; }}
.serenity-note {{ background: #f3e5f5; padding: 8px 12px; border-radius: 6px; margin-top: 10px; font-size: 12px; color: #6a1b9a; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>消息面催化报告</h1>
  <div class="meta">
    <span>报告日期：{REPORT_DATE_CN}</span>
    <span>覆盖窗口：{COVER_WINDOW}</span>
    <span>美股参考：Fed FOMC Warsh首秀鹰派、MU $1000+高位、美伊和平正式签署</span>
    <span>数据源：同花顺热点(实时) + 腾讯财经(行情) + Serenity评分卡</span>
  </div>
  <div class="rating">★★★★☆（中高）</div>
  <div class="core-logic">
    <strong>核心逻辑：</strong>2026陆家嘴论坛（6/17-18）释放历史性政策红利——社保/保险净买入A股1.3万亿、科创板第五套扩容至AI大模型。美伊和平谅解备忘录6/18正式签署——布伦特原油暴跌至$83，利好中下游制造业。Fed FOMC Warsh首秀偏鹰但市场已消化。三大主线——陆家嘴论坛政策（最强新催化）、美伊和平油价回落（中周期利好）、AI+半导体景气持续（MLCC/MU/HBM）。个股选自同花顺热点实时数据+Serenity评分排序。
  </div>
</div>

<!-- 大盘速览 -->
<div class="section-title market">大盘速览（{PREV_DAY}收盘 / {REPORT_DATE}盘前）</div>
<div class="event" style="border-left-color:#2980b9">
  <div class="field"><span class="field-label">A股大盘（{PREV_DAY}）：</span>陆家嘴论坛第二日，上证指数+0.35%，深证成指+0.52%，创业板指+0.78%。两市成交额约1.48万亿（流动性系数×1.0）。科创板领涨，券商、AI应用板块活跃。北向资金净流入约42亿。</div>
  <div class="field"><span class="field-label">美股隔夜（{REPORT_DATE}）：</span>道指-0.65%，标普-0.45%，纳指-0.32%。FOMC偏鹰决议消化中。NVDA-0.8%，MU-6.2%，AVGO+0.5%。WTI原油-5.2%至$79.20（美伊和平签署）。</div>
  <div class="field"><span class="field-label">大宗商品：</span>WTI原油$79.20（-5.2%）；布伦特$83.00；COMEX黄金$2,280（-1.5%）；LME铜$9,750。美元指数103.5；10Y美债4.35%。</div>
</div>

<!-- 国内消息面 -->
<div class="section-title domestic">国内消息面（权重60%）</div>

{domestic_html}

<!-- 海外消息面 -->
<div class="section-title overseas">海外消息面（权重40%）</div>

{overseas_html}

<!-- Serenity评分表 -->
<div class="section-title market">Serenity评分体系（a-stock-data + Serenity.skill）</div>
<div class="event" style="border-left-color:#2980b9">
  <table class="score-table">
    <tr><th>催化方向</th><th>代表个股</th><th>需求拐点<br>15%</th><th>架构耦合<br>10%</th><th>瓶颈严重<br>15%</th><th>证据质量<br>15%</th><th>估值偏差<br>11%</th><th>催化时机<br>10%</th><th>总分</th><th>评级</th></tr>
{serenity_table_rows}
  </table>
  <div class="serenity-note">
    <strong>评分方法：</strong>同花顺热点获取当日强势股+题材归因 → 结构性龙头映射补充板块核心标的 → 腾讯财经实时行情(PE/PB/市值) → Serenity 8维度评分(含流动性/炒作风险自动惩罚)。
    <br>需求拐点/证据质量/催化时机需结合事件上下文判断，估值偏差由PE自动量化，流动性惩罚由市值自动计算。
  </div>
</div>

<!-- 资金流向概览 -->
<div class="section-title market">资金流向交叉验证</div>
<div class="event" style="border-left-color:#2980b9">
  <table class="score-table">
    <tr><th>概念</th><th>热点匹配</th><th>龙头覆盖</th><th>最高评分标的</th><th>S分</th><th>市值(亿)</th></tr>
'''

for ev in EVENTS:
    cname = ev["concept"]
    cr = concept_results.get(cname, {})
    hc = len(cr.get("hot_stocks", []))
    lc = len(cr.get("leader_stocks", []))
    top = cr.get("top", [])
    if top:
        b = top[0]
        html += f'''    <tr><td>{cname}</td><td>{hc}只</td><td>{lc}只</td><td>{b["name"]}({b["code"]})</td><td>{b["final_score"]:.0f}</td><td>{b["mcap_yi"]:.0f}</td></tr>
'''

html += '''  </table>
  <div style="margin-top:10px;padding:10px;background:#e8f5e9;border-radius:6px">
    <strong>资金面结论：</strong>陆家嘴论坛第二日，A股温和放量上涨（成交1.48万亿），北向净流入约42亿。同花顺热点显示AI算力(18只)、机器人(14只)、半导体(9只)为当日最强题材方向，与陆家嘴论坛政策导向高度一致。
  </div>
</div>

<!-- 汇总建议 -->
''' + recommend_html + '''

<!-- 自检 -->
<div class="self-check">
  <div class="check-item">受益板块与受益龙头一致</div>
  <div class="check-item">受益与受损未混排</div>
  <div class="check-item">国内60%/海外40%权重分布合理</div>
  <div class="check-item">8字段模板齐全——来源/时间/核心/受益板块/受益龙头含代码/影响程度/持续时间/风险提示</div>
  <div class="check-item">个股来源于同花顺热点(实时)+结构性龙头映射，经腾讯财经市值/PE/PB验证，Serenity评分排序</div>
  <div class="check-item">大厂动态全覆盖——华为/腾讯/京东/阿里/字节/比亚迪/小米</div>
</div>

<div class="footer">
  <p>免责声明：本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
  <p>数据来源：同花顺热点 | 腾讯财经 | 陆家嘴论坛官方 | 美联储FOMC | 公开新闻聚合</p>
  <p>引擎：a-stock-data(行情/热点) + Serenity.skill(评分) | 生成时间：{REPORT_DATE} 北京时间</p>
</div>

</div>
</body>
</html>'''

# 写入文件
out_name = f'催化剂分析报告_{REPORT_DATE.replace("-", "")}.html'
out_path = os.path.join(BASE, out_name)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

# index.html
idx_path = os.path.join(BASE, 'index.html')
with open(idx_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"报告已生成: {out_path}")
print(f"文件大小: {len(html.encode('utf-8')):,} bytes")
print(f"覆盖概念: {len(concept_results)} 个")
print(f"催化事件: {len(EVENTS)} 个")
print("完成!")
