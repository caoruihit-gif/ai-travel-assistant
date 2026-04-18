import html
import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

# ==============================================
# 配置
# ==============================================
st.set_page_config(
    page_title="旅途计划 · AI 旅行助手",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_TITLE = "旅途计划"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

TRAVEL_QUOTES = [
    "下一站未必要很远，只要足够让你期待。",
    "把旅途安排得刚刚好，出发本身就会变得很迷人。",
    "说出你想去的地方，剩下那些顺路与惊喜，我来慢慢替你拼好。",
    "一份让人心动的计划，不是堆景点，而是每个转场都舒服。",
    "真正让人想出发的，从来不是距离，而是那一点点被认真准备的期待。",
]

LOADING_MESSAGES = [
    "正在为你梳理更顺的路线组合……",
    "正在为你筛选更贴合预算的酒店……",
    "正在为你比较更合适的用餐选择……",
    "正在为你压缩折返和无效通勤……",
    "正在为你搭配更舒适的旅途节奏……",
    "正在为你整理预算和随身清单……",
    "正在为你最终检查行程结构……",
    "旅行计划已生成，请耐心等待",
]

PUBLIC_WELFARE_CONTENT = [
    {
        "icon": "🌿",
        "title": "轻一点打扰环境",
        "text": "自带水杯、少用一次性用品、优先公共交通或顺路打车，旅行的体验不会变差，但留下的负担会更少。",
    },
    {
        "icon": "🤝",
        "title": "文明比打卡更重要",
        "text": "排队不插队、拍照不挡路、公共空间降一点音量。一个人的体面，往往决定一群人的旅行感受。",
    },
    {
        "icon": "🧭",
        "title": "给行程留一点弹性",
        "text": "别把时间压得太满。成熟的计划不是塞满景点，而是留得出休息、转场和临时变化的余地。",
    },
]

SPECIAL_OPTIONS = [
    "美食优先",
    "拍照出片",
    "自然风光",
    "人文历史",
    "夜景优先",
    "亲子友好",
    "老人同行",
    "下雨也能玩",
    "少走路",
    "不赶路",
    "咖啡馆",
    "购物",
]

DESTINATION_THEMES = {
    "厦门": {
        "hero": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80",
        "page": "linear-gradient(180deg, rgba(240,249,255,0.96), rgba(248,250,252,0.99)), radial-gradient(circle at top right, rgba(59,130,246,0.14), transparent 26%), radial-gradient(circle at top left, rgba(45,212,191,0.12), transparent 22%)",
        "hint": "海风、散步、夜色和一点点慢生活。",
        "primary": "#0f766e",
        "secondary": "#2dd4bf",
        "accent": "#f59e0b",
    },
    "杭州": {
        "hero": "https://images.unsplash.com/photo-1527631746610-bca00a040d60?auto=format&fit=crop&w=1600&q=80",
        "page": "linear-gradient(180deg, rgba(246,250,247,0.97), rgba(248,250,252,0.99)), radial-gradient(circle at top right, rgba(16,185,129,0.12), transparent 25%), radial-gradient(circle at top left, rgba(96,165,250,0.09), transparent 21%)",
        "hint": "湖边慢逛、茶香、寺庙和恰到好处的留白。",
        "primary": "#166534",
        "secondary": "#10b981",
        "accent": "#f59e0b",
    },
    "成都": {
        "hero": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1600&q=80",
        "page": "linear-gradient(180deg, rgba(252,248,243,0.97), rgba(250,250,249,0.99)), radial-gradient(circle at top right, rgba(249,115,22,0.13), transparent 26%), radial-gradient(circle at top left, rgba(251,191,36,0.10), transparent 22%)",
        "hint": "火锅、茶馆、公园，还有一整座城市的松弛感。",
        "primary": "#b45309",
        "secondary": "#f97316",
        "accent": "#facc15",
    },
    "上海": {
        "hero": "https://images.unsplash.com/photo-1549692520-acc6669e2f0c?auto=format&fit=crop&w=1600&q=80",
        "page": "linear-gradient(180deg, rgba(245,247,250,0.97), rgba(248,250,252,0.99)), radial-gradient(circle at top right, rgba(99,102,241,0.12), transparent 25%), radial-gradient(circle at top left, rgba(14,165,233,0.09), transparent 22%)",
        "hint": "天际线、咖啡馆和一整天都走不腻的街角。",
        "primary": "#4338ca",
        "secondary": "#0ea5e9",
        "accent": "#f59e0b",
    },
    "长春": {
        "hero": "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=1600&q=80",
        "page": "linear-gradient(180deg, rgba(246,248,251,0.97), rgba(248,250,252,0.99)), radial-gradient(circle at top right, rgba(59,130,246,0.12), transparent 25%), radial-gradient(circle at top left, rgba(125,211,252,0.09), transparent 22%)",
        "hint": "历史肌理、电影气息和带着季节感的城市散步。",
        "primary": "#1d4ed8",
        "secondary": "#38bdf8",
        "accent": "#f59e0b",
    },
    "重庆": {
        "hero": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
        "page": "linear-gradient(180deg, rgba(253,245,245,0.97), rgba(248,250,252,0.99)), radial-gradient(circle at top right, rgba(239,68,68,0.12), transparent 25%), radial-gradient(circle at top left, rgba(249,115,22,0.09), transparent 22%)",
        "hint": "坡城、夜色、火锅和转角就有风景。",
        "primary": "#be123c",
        "secondary": "#f97316",
        "accent": "#facc15",
    },
    "北京": {
        "hero": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?auto=format&fit=crop&w=1600&q=80",
        "page": "linear-gradient(180deg, rgba(247,247,244,0.97), rgba(248,250,252,0.99)), radial-gradient(circle at top right, rgba(168,85,247,0.11), transparent 25%), radial-gradient(circle at top left, rgba(245,158,11,0.09), transparent 22%)",
        "hint": "古都的厚重感，配上一点轻松的城市节奏。",
        "primary": "#7c3aed",
        "secondary": "#f59e0b",
        "accent": "#22c55e",
    },
    "西安": {
        "hero": "https://images.unsplash.com/photo-1470004914212-05527e49370b?auto=format&fit=crop&w=1600&q=80",
        "page": "linear-gradient(180deg, rgba(251,246,242,0.97), rgba(248,250,252,0.99)), radial-gradient(circle at top right, rgba(234,88,12,0.12), transparent 25%), radial-gradient(circle at top left, rgba(202,138,4,0.09), transparent 22%)",
        "hint": "城墙、博物馆和一口接一口都停不下来的碳水。",
        "primary": "#c2410c",
        "secondary": "#f59e0b",
        "accent": "#ef4444",
    },
}

DEFAULT_THEME = {
    "hero": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
    "page": "linear-gradient(180deg, #eef8f4 0%, #f6fbfa 36%, #fbfdfc 100%), radial-gradient(circle at 12% 10%, rgba(20,184,166,0.18), transparent 24%), radial-gradient(circle at 86% 8%, rgba(59,130,246,0.14), transparent 22%), radial-gradient(circle at 50% 100%, rgba(245,158,11,0.08), transparent 28%)",
    "hint": "答案都在路上，自由都在风里。",
    "primary": "#0f766e",
    "secondary": "#14b8a6",
    "accent": "#f59e0b",
}

PREVIEW_GUIDES = {
    "厦门": {
        "image": DESTINATION_THEMES["厦门"]["hero"],
        "title": "适合把两天过得像一场会呼吸的小假期",
        "intro": "一边看海，一边把节奏放慢。白天去海边和老街，晚上把散步和小吃留给灯亮起来之后。",
        "highlights": ["鼓浪屿 / 环岛路 / 沙坡尾的轻松路线", "更适合情侣、朋友或想慢下来的人", "吃住搭配通常很好做，预算也比较容易控"],
    },
    "杭州": {
        "image": DESTINATION_THEMES["杭州"]["hero"],
        "title": "适合边走边停，留一点空白给风景",
        "intro": "西湖边的慢逛、茶馆里的休息、寺院和山路的留白，是那种不用赶也会觉得很满的城市。",
        "highlights": ["西湖 + 灵隐/法喜 + 咖啡/茶馆的经典搭配", "适合拍照、约会和想要轻松节奏的人", "很适合做 2-3 天的精致型小旅行"],
    },
    "成都": {
        "image": DESTINATION_THEMES["成都"]["hero"],
        "title": "适合把吃喝、散步和城市松弛感排进同一天",
        "intro": "这里很适合先想今天想吃什么，再决定去哪里。茶馆、公园、商圈和夜景都能自然串到一起。",
        "highlights": ["文殊院 / 人民公园 / 宽窄巷子 / 太古里的多种组合", "家庭、朋友、情侣都容易排出顺路的计划", "餐饮选择多，预算也可以从经济型到轻奢型灵活调整"],
    },
    "上海": {
        "image": DESTINATION_THEMES["上海"]["hero"],
        "title": "适合把都市感、咖啡和夜景排成很顺的一天",
        "intro": "白天看展、逛街、喝咖啡，傍晚再去看夜景，是那种很容易出片、也很容易安排得高级的城市。",
        "highlights": ["外滩 / 武康路 / 博物馆 / 商圈的高适配组合", "适合第一次去和想做城市漫游的人", "节奏可以很松，也可以做得很满"],
    },
}


# ==============================================
# 工具函数
# ==============================================
def get_secret_or_env(key: str, default: str = "") -> str:
    # 本地开发时优先读 .env / 当前环境变量
    value = os.getenv(key)
    if value is not None and str(value).strip():
        return str(value).strip()

    # 只有本地没读到时，才回退到 st.secrets
    try:
        if key in st.secrets:
            value = st.secrets[key]
            return str(value).strip()
    except Exception:
        pass

    return str(default).strip() if default is not None else ""


def get_client() -> Optional[OpenAI]:
    api_key = get_secret_or_env("ARK_API_KEY")
    base_url = get_secret_or_env("ARK_BASE_URL", DEFAULT_BASE_URL)
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception:
        return None


def get_model_name() -> str:
    return get_secret_or_env("MODEL_NAME")


def resolve_theme(destination: str) -> Dict[str, str]:
    text = (destination or "").strip()
    for key, value in DESTINATION_THEMES.items():
        if key in text:
            return value
    return DEFAULT_THEME


def hex_to_rgba(value: str, alpha: float) -> str:
    value = value.lstrip("#")
    if len(value) != 6:
        return f"rgba(15,118,110,{alpha})"
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def style_card(theme: Dict[str, str], tone: str = "primary", alpha: float = 0.08) -> str:
    color = theme.get(tone, theme["primary"])
    bg = f"linear-gradient(135deg, {hex_to_rgba(color, alpha)}, rgba(255,255,255,0.96))"
    border = hex_to_rgba(color, 0.18)
    shadow = hex_to_rgba(color, 0.10)
    return f"background:{bg}; border:1px solid {border}; box-shadow: 0 10px 22px {shadow};"


def inject_css(theme: Dict[str, str]) -> None:
    hero_url = theme["hero"]
    page_bg = theme["page"]
    primary = theme["primary"]
    secondary = theme["secondary"]
    accent = theme["accent"]

    st.markdown(
        f"""
        <style>
            :root {{
                --card: rgba(255,255,255,0.90);
                --card-strong: rgba(255,255,255,0.96);
                --line: {hex_to_rgba(primary, 0.14)};
                --text: #0f172a;
                --muted: #546270;
                --primary: {primary};
                --secondary: {secondary};
                --accent: {accent};
                --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
                --hero-image: url('{hero_url}');
            }}
            .stApp {{
                background: {page_bg};
            }}
            .main .block-container {{
                max-width: 1400px;
                padding-top: 0.9rem;
                padding-bottom: 2rem;
            }}
            .hello-strip {{
                display:flex;
                align-items:center;
                gap:12px;
                padding: 0.8rem 1rem;
                border-radius: 18px;
                background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,255,255,0.82));
                border: 1px solid rgba(255,255,255,0.55);
                box-shadow: var(--shadow);
                margin-bottom: 0.9rem;
            }}
            .hello-avatar {{
                width: 40px;
                height: 40px;
                border-radius: 999px;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size: 1.1rem;
                background: linear-gradient(135deg, {hex_to_rgba(primary, 0.14)}, {hex_to_rgba(secondary, 0.14)});
            }}
            .hello-text {{
                color: var(--text);
                font-size: 0.95rem;
                line-height: 1.65;
            }}
            .hero {{
                position: relative;
                overflow: hidden;
                min-height: 320px;
                padding: 2.1rem 2.2rem 1.75rem 2.2rem;
                border-radius: 32px;
                color: white;
                background:
                    linear-gradient(120deg, rgba(6, 37, 44, 0.80), rgba(15, 118, 110, 0.42)),
                    var(--hero-image);
                background-size: cover;
                background-position: center;
                box-shadow: 0 24px 52px rgba(15, 23, 42, 0.18);
                border: 1px solid rgba(255,255,255,0.16);
                margin-bottom: 1rem;
            }}
            .hero-title {{
                font-size: 2.1rem;
                font-weight: 760;
                line-height: 1.06;
                margin-bottom: 0.5rem;
                letter-spacing: -0.02em;
            }}
            .hero-destination {{
                display:inline-block;
                margin-left: 0.2rem;
                font-size: 3.2rem;
                font-weight: 900;
                font-family: Georgia, "Times New Roman", serif;
                font-style: italic;
                letter-spacing: -0.04em;
                color: #fff6dc;
                text-shadow: 0 2px 10px rgba(0,0,0,0.16);
                vertical-align: baseline;
            }}
            .hero-subtitle {{
                font-size: 1.06rem;
                line-height: 1.78;
                max-width: 780px;
                opacity: 0.98;
                color: #f8fafc;
                text-shadow: 0 1px 2px rgba(0,0,0,0.12);
            }}
            .hero-badges {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 1rem;
            }}
            .hero-badge {{
                padding: 0.38rem 0.82rem;
                border-radius: 999px;
                background: rgba(255,255,255,0.16);
                border: 1px solid rgba(255,255,255,0.18);
                font-size: 0.86rem;
                font-weight: 650;
                backdrop-filter: blur(6px);
            }}
            .quote-frame {{
                width: 100%;
                display: flex;
                gap: 14px;
                align-items: center;
                padding: 16px 18px;
                border-radius: 22px;
                background: linear-gradient(135deg, rgba(255,255,255,0.26), rgba(255,255,255,0.10));
                border: 1px solid rgba(255,255,255,0.22);
                backdrop-filter: blur(10px);
                color: #ffffff;
                box-shadow: 0 10px 24px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.10);
            }}
            .quote-label {{
                font-size: 13px;
                font-weight: 900;
                letter-spacing: 0.08em;
                white-space: nowrap;
                color: #fff7ed;
                padding: 0.35rem 0.72rem;
                border-radius: 999px;
                background: rgba(255,255,255,0.14);
                border: 1px solid rgba(255,255,255,0.16);
            }}
            .quote-text {{
                font-size: 16px;
                font-weight: 720;
                line-height: 1.75;
                color: #ffffff;
                text-shadow: 0 1px 3px rgba(0,0,0,0.20);
            }}
            .glass-card {{
                background: var(--card);
                backdrop-filter: blur(14px);
                border: 1px solid rgba(255,255,255,0.56);
                box-shadow: var(--shadow);
                border-radius: 26px;
                padding: 1.15rem 1.2rem;
                margin-bottom: 1rem;
            }}
            .section-kicker {{
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                color: var(--primary);
                text-transform: uppercase;
                margin-bottom: 0.25rem;
            }}
            .section-title {{
                font-size: 1.2rem;
                font-weight: 820;
                color: var(--text);
                margin-bottom: 0.35rem;
                letter-spacing: -0.01em;
            }}
            .tiny-muted {{
                color: var(--muted);
                font-size: 0.94rem;
                line-height: 1.72;
            }}
            .bubble {{
                background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(240,253,250,0.90));
                border: 1px solid {hex_to_rgba(primary, 0.10)};
                border-radius: 20px;
                padding: 0.9rem 1rem;
                margin-top: 0.55rem;
            }}
            .destination-card {{
                background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,253,250,0.94));
                border: 1px solid {hex_to_rgba(primary, 0.10)};
                border-radius: 24px;
                padding: 1rem 1rem 0.85rem 1rem;
                box-shadow: 0 12px 24px rgba(15,23,42,0.05);
                margin-bottom: 0.95rem;
            }}
            .destination-title {{
                font-size: 1.24rem;
                font-weight: 840;
                color: var(--text);
                margin-bottom: 0.2rem;
                letter-spacing: -0.02em;
            }}
            .summary-panel {{
                background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(240,253,250,0.93));
                border: 1px solid {hex_to_rgba(primary, 0.10)};
                border-radius: 24px;
                padding: 1rem 1.05rem;
                margin-bottom: 1rem;
                box-shadow: 0 12px 24px rgba(15,23,42,0.05);
            }}
            .summary-title {{
                font-size: 1.22rem;
                font-weight: 820;
                color: var(--text);
                margin-bottom: 0.22rem;
            }}
            .pill {{
                display: inline-block;
                margin: 0.24rem 0.34rem 0 0;
                padding: 0.34rem 0.78rem;
                border-radius: 999px;
                background: {hex_to_rgba(primary, 0.08)};
                color: var(--primary);
                font-size: 0.84rem;
                font-weight: 680;
            }}
            .quick-city-note {{
                margin-top: 0.15rem;
                margin-bottom: 0.55rem;
                color: var(--muted);
                font-size: 0.92rem;
            }}
            .preview-modal {{
                background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(247,250,252,0.96));
                border: 1px solid {hex_to_rgba(primary, 0.12)};
                border-radius: 28px;
                box-shadow: 0 24px 44px rgba(15,23,42,0.10);
                padding: 1rem 1rem 0.9rem 1rem;
                margin-top: -0.2rem;
                margin-bottom: 1rem;
            }}
            .preview-img {{
                width: 100%;
                border-radius: 22px;
                height: 230px;
                object-fit: cover;
                border: 1px solid rgba(255,255,255,0.4);
            }}
            .friendly-empty {{
                background: linear-gradient(135deg, rgba(255,255,255,0.97), rgba(248,250,252,0.96));
                border: 1px solid var(--line);
                border-radius: 24px;
                padding: 1.3rem 1.2rem;
                box-shadow: 0 12px 24px rgba(15,23,42,0.05);
            }}
            .food-card, .hotel-card, .tip-card, .timeline-card, .place-card, .footer-card, .history-card {{
                border-radius: 22px;
                padding: 1rem 1.05rem;
                margin-bottom: 0.85rem;
            }}
            .card-title {{
                font-size: 1rem;
                font-weight: 790;
                color: var(--text);
                margin-bottom: 0.2rem;
            }}
            .card-meta {{
                color: var(--muted);
                font-size: 0.92rem;
                line-height: 1.68;
            }}
            .timeline-time {{
                font-size: 0.84rem;
                font-weight: 820;
                color: var(--primary);
                margin-bottom: 0.26rem;
            }}
            .budget-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px;
            }}
            .budget-item {{
                background: rgba(255,255,255,0.96);
                border: 1px solid var(--line);
                border-radius: 18px;
                padding: 0.95rem 1rem;
                box-shadow: 0 8px 18px rgba(15,23,42,0.04);
            }}
            .budget-label {{
                color: var(--muted);
                font-size: 0.82rem;
                margin-bottom: 0.16rem;
            }}
            .budget-value {{
                font-size: 1.08rem;
                font-weight: 820;
                color: var(--text);
            }}
            .loading-box {{
                background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(240,253,250,0.95));
                border: 1px solid {hex_to_rgba(primary, 0.12)};
                border-radius: 20px;
                padding: 1rem 1rem 0.85rem 1rem;
                box-shadow: 0 12px 22px rgba(15,23,42,0.05);
                margin-bottom: 1rem;
            }}
            .loading-title {{
                font-size: 1rem;
                font-weight: 780;
                color: var(--text);
                margin-bottom: 0.2rem;
            }}
            .loading-dots {{
                display: inline-flex;
                gap: 6px;
                margin-left: 8px;
                vertical-align: middle;
            }}
            .loading-dots span {{
                width: 7px;
                height: 7px;
                border-radius: 999px;
                background: var(--secondary);
                display: inline-block;
                animation: blink 1.2s infinite ease-in-out;
            }}
            .loading-dots span:nth-child(2) {{ animation-delay: 0.15s; }}
            .loading-dots span:nth-child(3) {{ animation-delay: 0.3s; }}
            @keyframes blink {{
                0%, 80%, 100% {{ opacity: 0.25; transform: translateY(0); }}
                40% {{ opacity: 1; transform: translateY(-2px); }}
            }}
            .stTabs [data-baseweb="tab-list"] {{
                gap: 10px;
                padding-bottom: 8px;
            }}
            .stTabs [data-baseweb="tab"] {{
                border-radius: 999px;
                background: rgba(255,255,255,0.82);
                padding: 0.58rem 1rem;
                border: 1px solid {hex_to_rgba(primary, 0.10)};
                height: auto;
                font-weight: 700;
            }}
            .stTabs [aria-selected="true"] {{
                background: {hex_to_rgba(primary, 0.12)} !important;
                color: var(--primary) !important;
            }}
            .stButton > button {{
                border-radius: 999px;
                border: none;
                background: linear-gradient(90deg, var(--primary), var(--secondary));
                color: white;
                font-weight: 780;
                min-height: 46px;
                box-shadow: 0 10px 22px {hex_to_rgba(secondary, 0.22)};
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }}
            .stButton > button:hover {{
                transform: translateY(-1px);
                box-shadow: 0 14px 28px {hex_to_rgba(secondary, 0.28)};
            }}
            .stDownloadButton > button {{
                border-radius: 999px;
                font-weight: 780;
                min-height: 42px;
                background: linear-gradient(90deg, var(--primary), var(--secondary));
                color: white;
                border: none;
            }}
            div[data-testid="stTextInputRootElement"] input,
            div[data-testid="stTextArea"] textarea,
            div[data-baseweb="select"] > div {{
                border-radius: 18px !important;
                font-size: 1rem !important;
            }}
            div[data-testid="stTextInputRootElement"] input {{
                min-height: 3rem;
            }}
            div[role="radiogroup"] {{
                gap: 10px;
                display: flex;
                flex-wrap: wrap;
                margin-bottom: 2px;
            }}
            div[role="radiogroup"] label {{
                background: rgba(255,255,255,0.88);
                border: 1px solid #b7e4c7;
                border-radius: 999px;
                padding: 8px 14px;
                box-shadow: 0 10px 22px rgba(22,101,52,0.05);
                transition: all .18s ease;
            }}
            div[role="radiogroup"] label:hover {{
                transform: translateY(-1px);
                border-color: #74c69d;
            }}
            div[role="radiogroup"] input[type="radio"] {{
                accent-color: #166534 !important;
            }}

            div[role="radiogroup"] label svg {{
                color: #166534 !important;
                fill: #166534 !important;
            }}
            div[data-baseweb="tag"] span {{
                color: #166534 !important;
                font-weight: 700 !important;
            }}
            div[data-baseweb="slider"] {{
                padding: 6px 4px 4px 4px;
            }}
            div[data-baseweb="slider"] [role="slider"] {{
                background:  #0f766e !important;
                border-color: #0f766e !important;
                box-shadow: 0 0 0 6px rgba(15,118,110,0.14) !important;
            }}
            div[data-baseweb="slider"] > div > div:first-child {{
                background: #2a9d8f !important;
                height: 8px !important;
                border-radius: 999px
            }}
            div[data-baseweb="slider"] > div > div:nth-child(2) {{
                background: rgba(42,157,143,0.18) !important;
                height: 8px !important;
                border-radius: 999px
            }}
            div[role="radiogroup"] label:has(input:checked) {{
                background: transparent !important;
                border-color: #74c69d !important;
                box-shadow: 0 8px 18px rgba(22,101,52,0.06) !important;
                color: #14532d !important;
            }}
            /* 多选标签：浅绿底 + 深绿字 + 深绿关闭按钮 */
            div[data-baseweb="tag"],
            span[data-baseweb="tag"],
            div[data-baseweb="select"] [data-baseweb="tag"] {{
                background: #ecfdf5 !important;
                background-color: #ecfdf5 !important;
                border: 1px solid #bbf7d0 !important;
                color: #166534 !important;
                border-radius: 14px !important;
                box-shadow: 0 6px 16px rgba(22,101,52,0.08) !important;
            }}
            div[data-baseweb="tag"] *,
            span[data-baseweb="tag"] *,
            div[data-baseweb="select"] [data-baseweb="tag"] * {{
                color: #166534 !important;
                fill: #166534 !important;
            }}
            div[data-baseweb="tag"] button,
            span[data-baseweb="tag"] button,
            div[data-baseweb="select"] [data-baseweb="tag"] button {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}
            .stProgress > div > div > div > div {{
                background: linear-gradient(90deg, var(--primary), var(--secondary));
            }}
            .stApp::before {{
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background:
                    radial-gradient(circle at 8% 12%, rgba(20,184,166,0.10), transparent 18%),
                    radial-gradient(circle at 88% 10%, rgba(59,130,246,0.08), transparent 18%),
                    radial-gradient(circle at 50% 92%, rgba(245,158,11,0.06), transparent 24%);
                z-index: 0;
            }}
            .impact-shell {{
                background: linear-gradient(145deg, rgba(255,255,255,0.97), rgba(240,253,250,0.95));
                border: 1px solid {hex_to_rgba(primary, 0.12)};
                border-radius: 26px;
                padding: 1.15rem 1.15rem 1rem 1.15rem;
                box-shadow: 0 16px 34px rgba(15,23,42,0.06);
                margin-top: 0.35rem;
                margin-bottom: 1rem;
            }}
            .impact-header {{
                display:flex;
                align-items:flex-start;
                justify-content:space-between;
                gap:16px;
                margin-bottom: 0.9rem;
            }}
            .impact-kicker {{
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                color: var(--primary);
                text-transform: uppercase;
                margin-bottom: 0.18rem;
            }}
            .impact-title {{
                font-size: 1.12rem;
                font-weight: 820;
                color: var(--text);
                line-height: 1.45;
                margin-bottom: 0.22rem;
            }}
            .impact-subtitle, .impact-footer {{
                color: var(--muted);
                font-size: 0.93rem;
                line-height: 1.72;
            }}
            .impact-badge {{
                flex: 0 0 auto;
                text-align: center;
                padding: 0.7rem 0.95rem;
                border-radius: 18px;
                background: linear-gradient(135deg, {hex_to_rgba(primary, 0.10)}, {hex_to_rgba(secondary, 0.12)});
                color: var(--primary);
                font-size: 0.82rem;
                font-weight: 780;
                line-height: 1.55;
                min-width: 108px;
            }}
            .impact-grid {{
                display:grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
            }}
            .impact-card {{
                background: rgba(255,255,255,0.96);
                border: 1px solid var(--line);
                border-radius: 20px;
                padding: 0.95rem 0.95rem 0.9rem 0.95rem;
                box-shadow: 0 10px 22px rgba(15,23,42,0.04);
            }}
            .impact-icon {{
                font-size: 1.25rem;
                margin-bottom: 0.45rem;
            }}
            .impact-card-title {{
                font-size: 0.98rem;
                font-weight: 790;
                color: var(--text);
                margin-bottom: 0.18rem;
            }}
            .impact-card-text {{
                color: var(--muted);
                font-size: 0.9rem;
                line-height: 1.7;
            }}
            .empty-kpis {{
                display:grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-top: 0.95rem;
            }}
            .empty-kpi {{
                background: rgba(255,255,255,0.96);
                border: 1px solid var(--line);
                border-radius: 18px;
                padding: 0.9rem 0.95rem;
                box-shadow: 0 8px 18px rgba(15,23,42,0.04);
            }}
            .empty-kpi-label {{
                color: var(--muted);
                font-size: 0.8rem;
                margin-bottom: 0.18rem;
            }}
            .empty-kpi-value {{
                color: var(--text);
                font-size: 0.96rem;
                font-weight: 760;
                line-height: 1.55;
            }}
            .loading-note {{
                color: var(--muted);
                font-size: 0.92rem;
                line-height: 1.7;
                margin-top: 0.5rem;
            }}
            @media (max-width: 900px) {{
                .impact-grid, .empty-kpis {{ grid-template-columns: 1fr; }}
                .impact-header {{ flex-direction: column; }}
            }}
            @media (max-width: 900px) {{
                .hero-title {{ font-size: 1.78rem; }}
                .hero-destination {{ font-size: 2.55rem; display:block; margin-left:0; margin-top:0.2rem; }}
                .budget-grid {{ grid-template-columns: repeat(2, 1fr); }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_quote_banner(quotes: List[str]) -> None:
    safe_quotes = json.dumps(quotes, ensure_ascii=False)
    components.html(
        f"""
        <div class="quote-frame">
            <div class="quote-label">✦ 旅行灵感</div>
            <div id="quote-text" class="quote-text"></div>
        </div>
        <script>
            const quotes = {safe_quotes};
            const el = document.getElementById('quote-text');
            let i = 0;
            function showQuote(index) {{
                el.innerText = quotes[index];
            }}
            showQuote(0);
            setInterval(() => {{
                i = (i + 1) % quotes.length;
                showQuote(i);
            }}, 3200);
        </script>
        """,
        height=78,
    )


def escape(v: Any) -> str:
    return html.escape(str(v) if v is not None else "")


def extract_json_block(text: str) -> str:
    if not text:
        return ""
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text)
    if fenced:
        return fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text.strip()


def safe_json_loads(text: str) -> Dict[str, Any]:
    return json.loads(extract_json_block(text))


def call_llm(messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 180) -> str:
    client = get_client()
    model_name = get_model_name()
    if client is None:
        raise RuntimeError("未检测到 ARK_API_KEY，无法连接模型。")
    if not model_name:
        raise RuntimeError("未检测到 MODEL_NAME，无法连接模型。")

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        timeout=timeout,
    )
    return (response.choices[0].message.content or "").strip()


def build_system_prompt() -> str:
    return """
你是一名严格、克制、以真实性优先，但不回避提供高置信具体名称的城市短途旅行规划师与JSON接口。
你的唯一任务是输出可解析的 JSON，不要输出 markdown，不要输出解释，不要输出额外文字。

你的目标不是“写得像旅游博主”，而是“在真实、可执行的前提下，尽量给出有参考价值的具体建议”。

必须遵守：

【总原则】
1. 真实性优先于丰富度，但不能因为过度保守把所有建议都写成泛称。
2. 优先给出“少而准”的具体名称，而不是“多但空”的泛化描述。
3. 如果用户约束与信息丰富度冲突，优先满足用户约束。

【预算约束规则】
4. 预算档位必须真实影响酒店和餐饮推荐：
   - 经济型：优先预算友好型酒店、连锁经济/中端酒店、本地小吃、家常餐馆、连锁平价品牌；避免高端酒店和高客单正餐。
   - 舒适型：优先中档酒店、口碑稳定餐厅和体验较平衡的用餐选择；不要明显过奢。
   - 轻奢型：可以推荐更高价格酒店、景观更好或服务更完整的住宿，并允许 1–2 餐品质更高的餐厅，但不要脱离目的地实际消费水平。
5. 如果推荐内容与预算档位明显不匹配，必须主动降级或升级，不允许“经济型却住得很贵”或“轻奢型却全部极低配”。

【名称精度规则】
6. 对以下内容，若你有高置信度，可以直接给出具体名称：
   - 博物馆、寺庙、景区、公园、文旅综合体、成熟商圈、历史街区
   - 全国或本地高频老字号
   - 全国高频连锁品牌
   - 知名酒店品牌
7. 对餐厅和酒店，使用以下三档策略：
   - 高置信：直接给具体名称
   - 中等置信：给“品牌名 + 区域/商圈附近”，不要硬补具体分店后缀
   - 低置信：给“区域级建议”
8. 只有在高置信时，才允许输出“XX店 / XX路店 / XX广场店”这类具体分店后缀。
9. 不要因为谨慎而把所有餐饮都写成“东北菜老字号”“连锁咖啡品牌”“本地烧烤品牌”这种泛称；主计划中应尽量保留 1–2 个高置信具体餐饮名。
10. 不允许编造任何景点、步道、商圈、地铁站、餐厅、酒店名称。

【细节约束】
11. 若某条信息不确定，宁可降级表达，也不要虚构。
12. 门票、餐饮、打车时间、预算只能输出“约 / 参考 / 区间”，不要伪装成精确核验值。
13. 对营业时间、预约规则、排队情况、免费服务、亲子设施、观光车、租赁服务等，若不能高置信确认，只能写“建议出发前核实”。
14. 对季节性活动、雪季项目、灯光展、节庆活动，若不能高置信确认正式名称，只能写成“冬季冰雪活动”“夜景散步”“室内文旅商业体”等稳妥表达，禁止创造看似官方的活动名。

【路线与体力规则】
15. 行程必须符合用户天数、预算、节奏与人群。
16. 如果用户输入包含“少走路 / 老人同行 / 家庭 / 亲子友好 / 夏季避暑 / 冬季保暖 / 下雨也能玩”任一条件：
   - 单日优先控制在 1–2 个核心片区
   - 餐饮优先与景点同片区或顺路
   - 宁可少安排一个点，也不要跨区折返
17. 如果“深度打卡”和“少走路”冲突，以“少走路”优先。

【输出要求】
18. 输出必须是单个 JSON 对象。
19. 所有文本都用中文。
20. 不要使用“滨江步道、天空之境、网红秘境、某某创意园”等泛化且可能虚假的名字。
21. 如果不够确定，可以减少数量，但不要把全部内容都退化成泛称。
22. 任何情况下都不得缺失顶层字段；如果拿不准，请用空字符串、空数组或空对象补齐。
23. 当天数 >= 4 时，优先输出更简洁版本：每天 3–4 个 blocks，reason / tips 尽量短，不追求铺满细节，以保证 JSON 稳定和生成速度。

JSON 顶层结构固定如下：
{{
  "meta": {{
    "destination": "",
    "days": 0,
    "budget": "",
    "style": "",
    "crowd": "",
    "season": "",
    "special": [],
    "summary": "",
    "positioning": "",
    "truth_notice": ""
  }},
  "overview": {{
    "route_logic": "",
    "stay_area_advice": "",
    "best_for": [],
    "avoid": []
  }},
  "day_plans": [
    {{
      "day": 1,
      "title": "",
      "theme": "",
      "blocks": [
        {{
          "time": "09:30",
          "type": "spot|food|hotel|night",
          "name": "",
          "area": "",
          "reason": "",
          "duration": "",
          "transport": "",
          "cost": "",
          "tips": ""
        }}
      ],
      "daily_budget": {{
        "tickets": "",
        "food": "",
        "transport": "",
        "subtotal": ""
      }}
    }}
  ],
  "hotels": [
    {{
      "name": "",
      "area": "",
      "price_range": "",
      "fit_for": "",
      "why": "",
      "room_tip": "",
      "booking_tip": ""
    }}
  ],
  "foods": [
    {{
      "name": "",
      "category": "",
      "signature": "",
      "area": "",
      "per_capita": "",
      "why": ""
    }}
  ],
  "budget": {{
    "range_total": "",
    "items": [
      {{"label": "住宿", "value": ""}},
      {{"label": "餐饮", "value": ""}},
      {{"label": "交通", "value": ""}},
      {{"label": "门票", "value": ""}}
    ],
    "note": ""
  }},
  "packing_list": {{
    "must_have": [],
    "optional": []
  }},
  "tips": {{
    "booking": [],
    "transport": [],
    "food": [],
    "weather": [],
    "pitfalls": []
  }}
}}
""".strip()


def build_user_prompt(
    destination: str,
    days: int,
    budget: str,
    style: str,
    crowd: str,
    season: str,
    special: List[str],
    stay_preference: str,
    extra: str,
    must_go: str,
    avoid: str,
) -> str:
    return f"""
请为以下用户生成真实、克制、可执行、但仍然有参考价值的短途旅行 JSON 计划。

用户输入：
- 目的地：{destination}
- 天数：{days} 天
- 预算：{budget}
- 节奏：{style}
- 人群：{crowd}
- 季节：{season}
- 偏好：{', '.join(special) if special else '无'}
- 住宿偏好：{stay_preference or '无'}
- 指定想去：{must_go or '无'}
- 明确避开：{avoid or '无'}
- 补充诉求：{extra or '无'}

额外要求：
1. 计划要像成熟旅游产品，而不是作文。
2. 每天行程块控制在 4–5 个以内（含餐饮），时间顺序要合理。
3. 如果你有高置信具体名称，请优先给具体名称，不要无差别泛化。
4. 如果你不能高置信确认具体分店，请改成“品牌名 + 某商圈/某区域附近”，不要硬写“XX店”。
5. 主计划里，餐饮部分尽量至少保留 1–2 个高置信具体名字；不要把所有餐饮都写成泛称。
6. 如果用户包含“少走路 / 家庭 / 老人同行 / 夏 / 冬 / 下雨也能玩”，请优先采用片区聚集策略，而不是多点串联。
7. 如果某个点存在真实性风险，请降级表达或删掉，不要保留可疑细节。
8. 门票、交通、预算、人均消费都用“参考/约/区间”表达。
9. 预算档位必须明显影响结果：经济型不能推荐明显过贵的酒店和高客单餐厅；轻奢型可以适当提高酒店和餐饮档位。
10. truth_notice 必须明确提醒用户：最终仍需自行核实营业时间、预约规则和价格。
11. 任何情况下都不要缺少顶层字段；拿不准就填空字符串、空数组。
12. 如果天数较多，请主动写得更简洁，优先保证结构完整和返回速度。
13. 只输出 JSON。
""".strip()


def normalize_plan_structure(
    plan: Dict[str, Any],
    destination: str = "",
    days: int = 0,
    budget: str = "",
    style: str = "",
    crowd: str = "",
    season: str = "",
    special: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if not isinstance(plan, dict):
        plan = {}

    plan.setdefault("meta", {})
    if not isinstance(plan["meta"], dict):
        plan["meta"] = {}
    plan["meta"].setdefault("destination", destination)
    plan["meta"].setdefault("days", days)
    plan["meta"].setdefault("budget", budget)
    plan["meta"].setdefault("style", style)
    plan["meta"].setdefault("crowd", crowd)
    plan["meta"].setdefault("season", season)
    plan["meta"].setdefault("special", special or [])
    plan["meta"].setdefault("summary", "")
    plan["meta"].setdefault("positioning", "")
    plan["meta"].setdefault("truth_notice", "出发前请再核实营业时间、预约规则与实时价格。")

    plan.setdefault("overview", {})
    if not isinstance(plan["overview"], dict):
        plan["overview"] = {}
    plan["overview"].setdefault("route_logic", "")
    plan["overview"].setdefault("stay_area_advice", "")
    plan["overview"].setdefault("best_for", [])
    plan["overview"].setdefault("avoid", [])

    plan.setdefault("day_plans", [])
    if not isinstance(plan["day_plans"], list):
        plan["day_plans"] = []

    target_days = max(int(days or 0), len(plan["day_plans"]) or 1)

    def empty_block():
        return {
            "time": "10:00",
            "type": "spot",
            "name": "自由安排",
            "area": "",
            "reason": "按你的偏好预留更灵活的活动时间。",
            "duration": "约2小时",
            "transport": "以实际为准",
            "cost": "弹性安排",
            "tips": "可以把这一段替换成你更想去的点。",
        }

    def empty_day(idx: int):
        return {
            "day": idx,
            "title": f"第{idx}天安排",
            "theme": "轻松顺路地走一走",
            "blocks": [empty_block()],
            "daily_budget": {
                "tickets": "参考0-100元/人",
                "food": "参考80-180元/人",
                "transport": "参考20-60元/人",
                "subtotal": "按实际安排调整",
            },
        }

    normalized_days = []
    for i in range(target_days):
        src = plan["day_plans"][i] if i < len(plan["day_plans"]) and isinstance(plan["day_plans"][i], dict) else empty_day(i + 1)
        day_obj = empty_day(i + 1)
        day_obj.update(src)
        if not isinstance(day_obj.get("blocks"), list) or not day_obj.get("blocks"):
            day_obj["blocks"] = [empty_block()]
        else:
            safe_blocks = []
            for block in day_obj["blocks"][:5]:
                if not isinstance(block, dict):
                    continue
                merged = empty_block()
                merged.update(block)
                safe_blocks.append(merged)
            day_obj["blocks"] = safe_blocks or [empty_block()]
        if not isinstance(day_obj.get("daily_budget"), dict):
            day_obj["daily_budget"] = empty_day(i + 1)["daily_budget"]
        else:
            db = empty_day(i + 1)["daily_budget"]
            db.update(day_obj["daily_budget"])
            day_obj["daily_budget"] = db
        normalized_days.append(day_obj)
    plan["day_plans"] = normalized_days

    plan.setdefault("hotels", [])
    if not isinstance(plan["hotels"], list):
        plan["hotels"] = []
    safe_hotels = []
    for hotel in plan["hotels"][:3]:
        if isinstance(hotel, dict):
            base = {"name": "", "area": "", "price_range": "", "fit_for": "", "why": "", "room_tip": "", "booking_tip": ""}
            base.update(hotel)
            safe_hotels.append(base)
    plan["hotels"] = safe_hotels

    plan.setdefault("foods", [])
    if not isinstance(plan["foods"], list):
        plan["foods"] = []
    safe_foods = []
    for food in plan["foods"][:6]:
        if isinstance(food, dict):
            base = {"name": "", "category": "", "signature": "", "area": "", "per_capita": "", "why": ""}
            base.update(food)
            safe_foods.append(base)
    plan["foods"] = safe_foods

    plan.setdefault("budget", {})
    if not isinstance(plan["budget"], dict):
        plan["budget"] = {}
    plan["budget"].setdefault("range_total", "按实际预订与用餐选择调整")
    items = plan["budget"].get("items") if isinstance(plan["budget"].get("items"), list) else []
    normalized_items = []
    for label in ["住宿", "餐饮", "交通", "门票"]:
        found = None
        for item in items:
            if isinstance(item, dict) and item.get("label") == label:
                found = {"label": label, "value": item.get("value", "")}
                break
        normalized_items.append(found or {"label": label, "value": "按实际安排调整"})
    plan["budget"]["items"] = normalized_items
    plan["budget"].setdefault("note", "")

    plan.setdefault("packing_list", {})
    if not isinstance(plan["packing_list"], dict):
        plan["packing_list"] = {}
    plan["packing_list"].setdefault("must_have", [])
    plan["packing_list"].setdefault("optional", [])

    plan.setdefault("tips", {})
    if not isinstance(plan["tips"], dict):
        plan["tips"] = {}
    for k in ["booking", "transport", "food", "weather", "pitfalls"]:
        if not isinstance(plan["tips"].get(k), list):
            plan["tips"][k] = []

    return plan


def validate_plan_shape(plan: Dict[str, Any]) -> None:
    normalize_plan_structure(plan)

    required_top_keys = [
        "meta",
        "overview",
        "day_plans",
        "hotels",
        "foods",
        "budget",
        "packing_list",
        "tips",
    ]

    for key in required_top_keys:
        if key not in plan:
            raise ValueError(f"缺少顶层字段: {key}")

    if not isinstance(plan.get("day_plans"), list) or not plan["day_plans"]:
        raise ValueError("day_plans 不能为空")

    if not isinstance(plan.get("hotels"), list):
        raise ValueError("hotels 必须为数组")

    if not isinstance(plan.get("foods"), list):
        raise ValueError("foods 必须为数组")


def repair_json_once(raw_text: str) -> Dict[str, Any]:
    cleaned = extract_json_block(raw_text)

    repair_messages = [
        {
            "role": "system",
            "content": (
                "你是 JSON 修复器。"
                "你的唯一任务是把用户给出的内容修复成合法 JSON。"
                "只输出单个 JSON 对象，不要解释，不要 markdown，不要代码块。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请把下面内容修复成严格合法的 JSON。\n"
                "要求：\n"
                "1. 只能输出 JSON\n"
                "2. 补齐缺失的逗号、引号、括号\n"
                "3. 不要新增解释文字\n\n"
                f"{cleaned}"
            ),
        },
    ]

    repaired = call_llm(repair_messages, temperature=0.0, timeout=120)

    try:
        return safe_json_loads(repaired)
    except Exception:
        second_messages = [
            {
                "role": "system",
                "content": (
                    "你是严格 JSON 修复器。"
                    "只输出一个可被 json.loads 成功解析的 JSON 对象。"
                    "不能输出任何解释。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "下面内容不是合法 JSON。请只输出修复后的合法 JSON：\n\n"
                    f"{repaired}"
                ),
            },
        ]
        repaired_again = call_llm(second_messages, temperature=0.0, timeout=120)
        return safe_json_loads(repaired_again)


def self_review_plan(
    plan: Dict[str, Any],
    destination: str,
    days: int,
    budget: str,
    style: str,
    crowd: str,
    season: str,
    special: List[str],
    stay_preference: str,
    extra: str,
    must_go: str,
    avoid: str,
) -> Dict[str, Any]:
    review_system_prompt = """
你现在不是旅行规划师，你是“真实性审稿人”。

你的任务不是把所有内容都改得很空，而是：
- 保留高置信具体名称
- 删除低置信具体名称
- 把不稳的细节降级表达
- 保留结果的参考价值

你必须重点检查以下风险：
1. 可疑的具体分店名
2. 可疑的当前活动名、季节项目名、雪季项目名
3. 过于精确但未核验的票价、打车时间、人均消费、排队时间
4. 未经核验的设施或服务细节，例如：
   - 母婴室
   - 休息区充足
   - 免费领香
   - 可租暖贴 / 雪地靴
   - 亲子设施完善
   - 可现场取号
5. 与“少走路 / 家庭 / 老人同行 / 夏 / 冬 / 雨天”相冲突的跨区折返安排

处理原则：
- 如果是高置信景点、博物馆、寺庙、成熟商圈、知名文旅综合体、老字号、知名品牌，请保留具体名称
- 如果只是“具体分店后缀”不稳，请降级成“品牌名 + 区域附近”，不要整条删成泛称
- 如果精确数字不稳，请改成“约 / 参考 / 区间”
- 如果路线过于分散，就删掉一个点，改成更集中
- 如果一个建议项真实性明显可疑，就删除
- 保持 JSON 结构不变
- 只输出新的完整 JSON
- 不要解释，不要注释
""".strip()

    review_user_prompt = (
        "下面是一个候选旅行 JSON，请做平衡式真实性审查。\n\n"
        "要求：不要过度删减，不要把所有餐饮和酒店都改成泛称；只处理低置信具体细节。\n\n"
        f"用户约束仍然是：\n{build_user_prompt(destination, days, budget, style, crowd, season, special, stay_preference, extra, must_go, avoid)}\n\n"
        f"候选 JSON：\n{json.dumps(plan, ensure_ascii=False)}"
    )

    review_messages = [
        {"role": "system", "content": review_system_prompt},
        {"role": "user", "content": review_user_prompt},
    ]

    reviewed = call_llm(review_messages, temperature=0.0, timeout=180)

    try:
        return safe_json_loads(reviewed)
    except Exception:
        return repair_json_once(reviewed)


def generate_plan_via_llm(
    destination: str,
    days: int,
    budget: str,
    style: str,
    crowd: str,
    season: str,
    special: List[str],
    stay_preference: str,
    extra: str,
    must_go: str,
    avoid: str,
) -> Dict[str, Any]:
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(destination, days, budget, style, crowd, season, special, stay_preference, extra, must_go, avoid)

    raw_text = call_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.08,
        timeout=180,
    )

    try:
        plan = safe_json_loads(raw_text)
    except Exception:
        plan = repair_json_once(raw_text)

    plan = normalize_plan_structure(plan, destination, days, budget, style, crowd, season, special)
    validate_plan_shape(plan)

    # 当天数较多时，优先稳定与速度，跳过二次审查，减少字段丢失概率
    if days >= 5:
        return plan

    reviewed = self_review_plan(plan, destination, days, budget, style, crowd, season, special, stay_preference, extra, must_go, avoid)
    reviewed = normalize_plan_structure(reviewed, destination, days, budget, style, crowd, season, special)
    validate_plan_shape(reviewed)
    return reviewed


def json_to_markdown(plan: Dict[str, Any]) -> str:
    meta = plan.get("meta", {})
    overview = plan.get("overview", {})
    lines: List[str] = []
    lines.append(f"# {meta.get('destination', '旅行')} {meta.get('days', '')}天旅行计划")
    lines.append("")
    lines.append(f"- 预算：{meta.get('budget', '')}")
    lines.append(f"- 节奏：{meta.get('style', '')}")
    lines.append(f"- 人群：{meta.get('crowd', '')}")
    lines.append(f"- 季节：{meta.get('season', '')}")
    if meta.get("special"):
        lines.append(f"- 偏好：{', '.join(meta.get('special', []))}")
    lines.append("")
    lines.append("## 总览")
    lines.append(meta.get("summary", ""))
    lines.append("")
    if overview.get("route_logic"):
        lines.append(f"- 路线逻辑：{overview.get('route_logic', '')}")
    if overview.get("stay_area_advice"):
        lines.append(f"- 住宿建议区域：{overview.get('stay_area_advice', '')}")
    lines.append("")

    lines.append("## 每日时间线")
    for day in plan.get("day_plans", []):
        lines.append(f"### Day {day.get('day', '')}｜{day.get('title', '')}")
        if day.get("theme"):
            lines.append(f"- 主题：{day.get('theme', '')}")
        for block in day.get("blocks", []):
            lines.append(
                f"- {block.get('time', '')} | {block.get('name', '')} | {block.get('reason', '')} | 时长 {block.get('duration', '')} | 交通 {block.get('transport', '')} | 费用 {block.get('cost', '')}"
            )
        daily_budget = day.get("daily_budget", {})
        if daily_budget:
            lines.append(
                f"- 当日预算：门票 {daily_budget.get('tickets', '')}；餐饮 {daily_budget.get('food', '')}；交通 {daily_budget.get('transport', '')}；小计 {daily_budget.get('subtotal', '')}"
            )
        lines.append("")

    lines.append("## 住宿")
    for hotel in plan.get("hotels", []):
        lines.append(f"- {hotel.get('name', '')}｜{hotel.get('area', '')}｜{hotel.get('price_range', '')}｜{hotel.get('why', '')}")
    lines.append("")

    lines.append("## 饮食")
    for food in plan.get("foods", []):
        lines.append(f"- {food.get('name', '')}｜{food.get('category', '')}｜{food.get('signature', '')}｜{food.get('per_capita', '')}｜{food.get('area', '')}")
    lines.append("")

    lines.append("## 预算")
    budget = plan.get("budget", {})
    lines.append(f"- 总预算：{budget.get('range_total', '')}")
    for item in budget.get("items", []):
        lines.append(f"- {item.get('label', '')}：{item.get('value', '')}")
    if budget.get("note"):
        lines.append(f"- 说明：{budget.get('note', '')}")
    lines.append("")

    lines.append("## 行李清单")
    for item in plan.get("packing_list", {}).get("must_have", []):
        lines.append(f"- [ ] {item}")
    for item in plan.get("packing_list", {}).get("optional", []):
        lines.append(f"- [ ] {item}（可选）")
    lines.append("")

    lines.append("## 实用提示")
    tips = plan.get("tips", {})
    for section, title in [("booking", "预订"), ("transport", "交通"), ("food", "饮食"), ("weather", "天气"), ("pitfalls", "避坑")]:
        values = tips.get(section, []) or []
        if values:
            lines.append(f"### {title}")
            for value in values:
                lines.append(f"- {value}")
            lines.append("")

    if meta.get("truth_notice"):
        lines.append("## 真实性提醒")
        lines.append(meta.get("truth_notice", ""))
        lines.append("")

    return "\n".join(lines).strip()


def copy_button(text: str, label: str, key: str) -> None:
    escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    if st.button(label, key=key, use_container_width=True):
        components.html(
            f"""
            <script>
            navigator.clipboard.writeText(`{escaped}`)
              .then(() => alert('这一部分已经复制到剪贴板'))
              .catch(() => alert('复制失败，请手动复制'));
            </script>
            """,
            height=0,
        )


def render_section_copy(text: str, key: str) -> None:
    spacer, btn = st.columns([6, 1.2])
    with spacer:
        st.write("")
    with btn:
        copy_button(text, "复制本段", key)


def section_overview_text(plan: Dict[str, Any]) -> str:
    lines = []
    for day in plan.get("day_plans", []):
        lines.append(f"Day {day.get('day', '')}｜{day.get('title', '')}")
        if day.get("theme"):
            lines.append(f"主题：{day.get('theme', '')}")
        for block in day.get("blocks", []):
            lines.append(f"- {block.get('time', '')} {block.get('name', '')}｜{block.get('reason', '')}")
        lines.append("")
    return "\n".join(lines).strip()


def section_timeline_text(plan: Dict[str, Any]) -> str:
    return section_overview_text(plan)


def section_food_text(plan: Dict[str, Any]) -> str:
    lines = []
    for food in plan.get("foods", []):
        lines.append(f"- {food.get('name', '')}｜{food.get('category', '')}｜{food.get('area', '')}｜{food.get('per_capita', '')}")
    return "\n".join(lines).strip()


def section_hotel_text(plan: Dict[str, Any]) -> str:
    lines = []
    for hotel in plan.get("hotels", []):
        lines.append(f"- {hotel.get('name', '')}｜{hotel.get('area', '')}｜{hotel.get('price_range', '')}")
    return "\n".join(lines).strip()


def section_budget_text(plan: Dict[str, Any]) -> str:
    budget = plan.get("budget", {})
    lines = [f"总预算：{budget.get('range_total', '')}"]
    for item in budget.get("items", []):
        lines.append(f"- {item.get('label', '')}：{item.get('value', '')}")
    for item in plan.get("packing_list", {}).get("must_have", []):
        lines.append(f"- {item}")
    return "\n".join(lines).strip()


def init_session_state() -> None:
    defaults = {
        "destination": "",
        "recent_history": [],
        "preview_city": "",
        "days": 2,
        "budget": "舒适型",
        "style": "平衡体验",
        "crowd": "情侣",
        "season": "春",
        "special": ["美食优先", "拍照出片"],
        "must_go": "",
        "avoid": "",
        "stay_preference": "",
        "extra": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def save_history(destination: str, days: int, budget: str, style: str) -> None:
    item = {
        "destination": destination,
        "days": days,
        "budget": budget,
        "style": style,
        "time": datetime.now().strftime("%m-%d %H:%M"),
    }
    history = st.session_state.get("recent_history", [])
    st.session_state["recent_history"] = [item] + history[:5]


def render_public_welfare_panel() -> None:
    cards_html = "".join(
        [
            f"<div class='impact-card'><div class='impact-icon'>{escape(item['icon'])}</div><div class='impact-card-title'>{escape(item['title'])}</div><div class='impact-card-text'>{escape(item['text'])}</div></div>"
            for item in PUBLIC_WELFARE_CONTENT
        ]
    )
    st.markdown(
        f"""
        <div class="impact-shell">
            <div class="impact-header">
                <div>
                    <div class="impact-kicker">旅途生成中</div>
                    <div class="impact-title">每一次出行都是心灵的洗礼，每一次旅行都是对未知的探索</div>
                    <div class="impact-subtitle">站在山巅与日月星辰对话，浅游水底与江河湖海晤谈，和每一棵树握手，与每一株草私语，方知宇宙浩瀚自然可谓！</div>
                </div>
                <div class="impact-badge">少一点打扰<br>多一点体面</div>
            </div>
            <div class="impact-grid">{cards_html}</div>
            <div class="impact-footer">保护环境，文明出行，旅途才能更愉快！</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="friendly-empty">
            <div class="section-kicker">准备好了就开始</div>
            <div class="section-title">先你的想法写下来吧</div>
            <div class="tiny-muted">
                目的地、天数、想怎么走、想避开什么，哪怕只是几句零散需求也没关系。<br><br>
                你一提交，我会把它们整理成：<br>
                • 一眼能看懂的总览<br>
                • 顺着时间走的日程安排<br>
                • 更容易落地的饮食与住宿建议<br>
                • 预算与随身清单
            </div>
            <div class="empty-kpis">
                <div class="empty-kpi">
                    <div class="empty-kpi-label">规划目标</div>
                    <div class="empty-kpi-value">路线顺、预算稳、体验不累</div>
                </div>
                <div class="empty-kpi">
                    <div class="empty-kpi-label">输出内容</div>
                    <div class="empty-kpi-value">总览、路线、住宿、美食、预算</div>
                </div>
                <div class="empty-kpi">
                    <div class="empty-kpi-label">输出结果</div>
                    <div class="empty-kpi-value">一份能直接下载的完整行程</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_generation_feedback() -> tuple:
    loading_placeholder = st.empty()
    welfare_placeholder = st.empty()
    progress_placeholder = st.empty()

    with loading_placeholder.container():
        st.markdown(
            """
            <div class="loading-box">
                <div class="loading-title">旅途计划生成中</div>
                <div class="tiny-muted">正在为你梳理更顺的路线组合……</div>
                <div class="loading-note">全程需2-3分钟，请耐心等待~</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with welfare_placeholder.container():
        render_public_welfare_panel()

    progress_bar = progress_placeholder.progress(12)
    return loading_placeholder, welfare_placeholder, progress_placeholder, progress_bar


def finish_generation_feedback(loading_placeholder, welfare_placeholder, progress_placeholder, progress_bar, success: bool = True, message: str = "") -> None:
    try:
        progress_bar.progress(100 if success else 0)
    except Exception:
        pass

    progress_placeholder.empty()
    welfare_placeholder.empty()

    if success:
        loading_placeholder.empty()
        return

    loading_placeholder.markdown(
        f"""
        <div class="loading-box">
            <div class="loading-title">这次没能顺利排好行程</div>
            <div class="tiny-muted">{escape(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================
# 渲染函数
# ==============================================
def render_greeting() -> None:
    st.markdown(
        """
        <div class="hello-strip">
            <div class="hello-avatar">✈️</div>
            <div class="hello-text">
                嗨，我是你的旅途小助手。你负责把想法告诉我，我负责把美丽风景打包送给你~
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(destination: str, theme: Dict[str, str]) -> None:
    current_destination = (destination or "").strip()
    if current_destination:
        title = f"<span>下一站去</span><span class='hero-destination'>{escape(current_destination)}</span>"
    else:
        title = "下一站我们去哪儿？"
    subtitle = (
        "把想去的地方、想和谁一起出发告诉我。"
        "我会把咱们的小想法整理成一份完美旅途计划。"
    )
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{escape(subtitle)}</div>
            <div class="hero-badges">
                <div class="hero-badge">快乐不必等完美时机，我们出发就现在！</div>
                <div class="hero-badge">{escape(theme.get('hint', ''))}</div>
                <div class="hero-badge">找不到答案的时候就去看看这个世界吧！</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_quote_banner(TRAVEL_QUOTES)


def render_preview_modal() -> None:
    city = st.session_state.get("preview_city", "")
    if not city:
        return
    data = PREVIEW_GUIDES.get(city)
    if not data:
        return

    st.markdown("<div class='preview-modal'>", unsafe_allow_html=True)
    cols = st.columns([1.1, 1.2])
    with cols[0]:
        st.markdown(f"<img class='preview-img' src='{escape(data['image'])}' />", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div class='section-kicker'>灵感预览</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-title'>{escape(city)} · {escape(data['title'])}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='tiny-muted'>{escape(data['intro'])}</div>", unsafe_allow_html=True)
        for item in data.get("highlights", []):
            st.markdown(f"- {item}")
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("就去这里", key=f"use_preview_{city}", use_container_width=True):
                st.session_state["destination"] = city
                st.session_state["preview_city"] = ""
                st.rerun()
        with btn2:
            if st.button("先关上", key=f"close_preview_{city}", use_container_width=True):
                st.session_state["preview_city"] = ""
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_intro_card() -> None:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-kicker">Let’s Start</div>
            <div class="section-title">来吧，让我们一起构思这场奇妙旅程~</div>
            <div class="bubble tiny-muted">
                不用一次就想得特别完整。先说目的地，再告诉我你更想轻松一点、热闹一点，还是把吃住安排得顺一点。剩下那些麻烦的组合和排序，我来帮你完成。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_destination_picker() -> None:
    st.markdown(
        """
        <div class="destination-card">
            <div class="section-kicker">目的地</div>
            <div class="destination-title">先把想去的地方告诉我</div>
            <div class="tiny-muted">城市、地名、片区都可以。输入我们人生的下一处风景吧。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text_input(
        "目的地",
        key="destination",
        placeholder="例如：厦门、长春、成都、杭州、莫干山、阿那亚",
        label_visibility="collapsed",
    )


def render_city_shortcuts() -> None:
    st.markdown("<div class='quick-city-note'>还没想好？先点一个灵感目的地试试看</div>", unsafe_allow_html=True)
    items = [("厦门 🌊", "厦门"), ("杭州 🍃", "杭州"), ("成都 🍜", "成都"), ("上海 🌃", "上海")]
    cols = st.columns(4)
    for idx, (label, city) in enumerate(items):
        with cols[idx]:
            if st.button(label, key=f"preview_{city}", use_container_width=True):
                st.session_state["preview_city"] = city
                st.rerun()


def render_input_panel() -> Dict[str, Any]:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-kicker">一起细化一下</div>
            <div class="section-title">接下来，让我们敲定一些细节</div>
            <div class="tiny-muted">回答得越具体，我们的出行计划就会越完美哦。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-kicker' style='margin-bottom:0.35rem;'>旅游时长</div>", unsafe_allow_html=True)
    days = st.select_slider("旅游时长", options=[1, 2, 3, 4, 5], key="days", label_visibility="collapsed")

    st.markdown("<div class='section-kicker' style='margin-top:0.8rem; margin-bottom:0.35rem;'>价格偏好</div>", unsafe_allow_html=True)
    budget = st.radio("价格偏好", ["经济型", "舒适型", "轻奢型"], horizontal=True, key="budget", label_visibility="collapsed")

    st.markdown("<div class='section-kicker' style='margin-top:0.8rem; margin-bottom:0.35rem;'>旅行节奏</div>", unsafe_allow_html=True)
    style = st.radio("旅行节奏", ["轻松休闲", "平衡体验", "深度打卡"], horizontal=True, key="style", label_visibility="collapsed")

    c1, c2 = st.columns(2)
    with c1:
        crowd = st.selectbox("这次会和谁一起出发？", ["独自", "情侣", "家庭", "朋友"], key="crowd")
    with c2:
        season = st.selectbox("大概会在什么季节去？", ["春", "夏", "秋", "冬"], key="season")

    special = st.multiselect(
        "这趟旅行更想要什么感觉？",
        SPECIAL_OPTIONS,
        key="special",
        placeholder="勾选几个你最在意的关键词",
    )
    must_go = st.text_input("有没有一定想去的地方？", key="must_go", placeholder="例如：鼓浪屿 / 宽窄巷子 / 伪满皇宫博物院")
    avoid = st.text_input("有没有想避开的安排？", key="avoid", placeholder="例如：别太赶、别排队太久、不去酒吧")
    stay_preference = st.text_input("住在哪一带会让你更安心？", key="stay_preference", placeholder="例如：靠近地铁 / 市中心 / 景区旁")
    extra = st.text_area(
        "再悄悄告诉我一点你的期待",
        key="extra",
        height=110,
        placeholder="例如：想看海、少走路、晚上能散步拍照，希望餐厅更稳妥，不要太网红。",
    )
    generate = st.button("开始旅程", use_container_width=True)

    return {
        "days": days,
        "budget": budget,
        "style": style,
        "crowd": crowd,
        "season": season,
        "special": special,
        "must_go": must_go,
        "avoid": avoid,
        "stay_preference": stay_preference,
        "extra": extra,
        "generate": generate,
    }


def render_history_card() -> None:
    history = st.session_state.get("recent_history", [])
    if not history:
        return
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-kicker">最近</div>
            <div class="section-title">最近我们一起构思过这些地方</div>
        """,
        unsafe_allow_html=True,
    )
    for item in history:
        st.markdown(
            f"""
            <div class="history-card" style="{style_card(resolve_theme(item['destination']), 'secondary', 0.07)}">
                <div class="card-title">{escape(item['destination'])} · {escape(item['days'])}天</div>
                <div class="card-meta">{escape(item['time'])} ｜ {escape(item['budget'])} ｜ {escape(item['style'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_plan_summary(plan: Dict[str, Any]) -> None:
    meta = plan.get("meta", {})
    overview = plan.get("overview", {})
    chips = [
        meta.get("destination", ""),
        f"{meta.get('days', '')}天",
        meta.get("budget", ""),
        meta.get("style", ""),
        meta.get("crowd", ""),
        meta.get("season", ""),
    ] + (meta.get("special", []) or [])
    chip_html = "".join([f"<span class='pill'>{escape(c)}</span>" for c in chips if c])
    summary_lines = []
    if overview.get("route_logic"):
        summary_lines.append(overview.get("route_logic", ""))
    if overview.get("stay_area_advice"):
        summary_lines.append("住宿更适合放在：" + overview.get("stay_area_advice", ""))
    summary_extra = "<br>".join([escape(x) for x in summary_lines])
    st.markdown(
        f"""
        <div class="summary-panel">
            <div class="section-kicker">总览</div>
            <div class="summary-title">先看一眼，我们的整体安排</div>
            <div class="tiny-muted">{escape(meta.get('summary', ''))}</div>
            <div style="margin-top: 0.55rem;">{chip_html}</div>
            <div class="tiny-muted" style="margin-top: 0.85rem;">{summary_extra}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview_tab(plan: Dict[str, Any], theme: Dict[str, str]) -> None:
    day_plans = plan.get("day_plans", [])
    for day_idx, day in enumerate(day_plans):
        st.markdown(f"### Day {escape(day.get('day', ''))}｜{escape(day.get('title', ''))}")
        if day.get("theme"):
            st.caption(day.get("theme", ""))
        blocks = day.get("blocks", [])
        cols = st.columns(2)
        for idx, block in enumerate(blocks):
            tone = "primary"
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="place-card" style="{style_card(theme, tone, 0.08)}">
                        <div class="card-title">{escape(block.get('time', ''))} · {escape(block.get('name', ''))}</div>
                        <div class="card-meta">
                            区域：{escape(block.get('area', ''))}<br>
                            为什么放在这里：{escape(block.get('reason', ''))}<br>
                            参考时长：{escape(block.get('duration', ''))} ｜ 交通：{escape(block.get('transport', ''))} ｜ 费用：{escape(block.get('cost', ''))}<br>
                            提醒：{escape(block.get('tips', ''))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_timeline_tab(plan: Dict[str, Any], theme: Dict[str, str]) -> None:
    for day_idx, day in enumerate(plan.get("day_plans", [])):
        st.markdown(f"### Day {escape(day.get('day', ''))}｜{escape(day.get('title', ''))}")
        for idx, block in enumerate(day.get("blocks", [])):
            tone = "primary"
            st.markdown(
                f"""
                <div class="timeline-card" style="{style_card(theme, tone, 0.08)}">
                    <div class="timeline-time">{escape(block.get('time', ''))}</div>
                    <div class="card-title">{escape(block.get('name', ''))}</div>
                    <div class="card-meta">
                        {escape(block.get('reason', ''))}<br>
                        区域：{escape(block.get('area', ''))} ｜ 类型：{escape(block.get('type', ''))}<br>
                        时长：{escape(block.get('duration', ''))} ｜ 交通：{escape(block.get('transport', ''))} ｜ 费用：{escape(block.get('cost', ''))}<br>
                        提示：{escape(block.get('tips', ''))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        daily_budget = day.get("daily_budget", {})
        if daily_budget:
            st.info(
                f"这一天大致会花：门票 {daily_budget.get('tickets', '')}｜餐饮 {daily_budget.get('food', '')}｜交通 {daily_budget.get('transport', '')}｜小计 {daily_budget.get('subtotal', '')}"
            )


def render_food_tab(plan: Dict[str, Any], theme: Dict[str, str]) -> None:
    st.markdown("### 饮食")
    for idx, food in enumerate(plan.get("foods", [])):
        tone = "primary"
        st.markdown(
            f"""
            <div class="food-card" style="{style_card(theme, tone, 0.09)}">
                <div class="card-title">{escape(food.get('name', ''))}</div>
                <div class="card-meta">
                    类型：{escape(food.get('category', ''))}<br>
                    推荐招牌：{escape(food.get('signature', ''))}<br>
                    区域：{escape(food.get('area', ''))}<br>
                    人均参考：{escape(food.get('per_capita', ''))}<br>
                    为什么推荐：{escape(food.get('why', ''))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_hotel_tab(plan: Dict[str, Any], theme: Dict[str, str]) -> None:
    st.markdown("### 住宿")
    for idx, hotel in enumerate(plan.get("hotels", [])):
        tone = "primary"
        st.markdown(
            f"""
            <div class="hotel-card" style="{style_card(theme, tone, 0.09)}">
                <div class="card-title">{escape(hotel.get('name', ''))}</div>
                <div class="card-meta">
                    区域：{escape(hotel.get('area', ''))}<br>
                    价格：{escape(hotel.get('price_range', ''))}<br>
                    更适合：{escape(hotel.get('fit_for', ''))}<br>
                    推荐理由：{escape(hotel.get('why', ''))}<br>
                    房型建议：{escape(hotel.get('room_tip', ''))}<br>
                    预订提醒：{escape(hotel.get('booking_tip', ''))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_budget_packing_tab(plan: Dict[str, Any]) -> None:
    budget = plan.get("budget", {})
    items = budget.get("items", [])
    padded = items[:4] + [{"label": "", "value": ""}] * max(0, 4 - len(items))
    st.markdown(
        "<div class='budget-grid'>"
        + "".join(
            [
                f"<div class='budget-item'><div class='budget-label'>{escape(item.get('label', ''))}</div><div class='budget-value'>{escape(item.get('value', ''))}</div></div>"
                for item in padded[:4]
            ]
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"### 这趟行程的大致预算：{escape(budget.get('range_total', ''))}")
    if budget.get("note"):
        st.caption(budget.get("note", ""))

    c1, c2 = st.columns([1.05, 1])
    with c1:
        st.markdown("#### 出发前顺手勾一下")
        for item in plan.get("packing_list", {}).get("must_have", []):
            st.checkbox(item, value=False, key=f"must_{item}")
        for item in plan.get("packing_list", {}).get("optional", []):
            st.checkbox(f"{item}（可选）", value=False, key=f"opt_{item}")
    with c2:
        st.markdown("#### 温馨提示：")
        tips = plan.get("tips", {})
        label_map = {
            "booking": "预订",
            "transport": "交通",
            "food": "饮食",
            "weather": "天气",
            "pitfalls": "避坑",
        }
        for idx, (key, title) in enumerate(label_map.items()):
            values = tips.get(key, []) or []
            if values:
                tone = "primary"
                st.markdown(
                    f"<div class='tip-card' style='{style_card(resolve_theme(st.session_state.get('destination', '')), tone, 0.08)}'><div class='card-title'>{escape(title)}</div><div class='card-meta'>"
                    + "<br>".join([f"• {escape(v)}" for v in values])
                    + "</div></div>",
                    unsafe_allow_html=True,
                )


def render_footer(plan: Dict[str, Any]) -> None:
    truth_notice = plan.get("meta", {}).get("truth_notice", "")
    footer_text = truth_notice or "出发前记得再核实营业时间、预约规则和实时价格。计划是起点，真正让旅途发光的还是你在路上的感受。"
    st.markdown(
        f"""
        <div class="footer-card" style="{style_card(resolve_theme(st.session_state.get('destination', '')), 'secondary', 0.08)}">
            <div class="section-kicker">出发前</div>
            <div class="section-title">AI旅行助手祝你旅途愉快！</div>
            <div class="tiny-muted">{escape(footer_text)}</div>
            <div class="tiny-muted" style="margin-top:0.6rem;">如果你想让结果更合心意，可以把“想避开什么”“住哪一带更方便”“有没有一定想去的点”写得更具体一点，我会重新排得更贴你。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================
# 主界面
# ==============================================
def main() -> None:
    init_session_state()
    current_theme = resolve_theme(st.session_state.get("destination", ""))
    inject_css(current_theme)

    render_greeting()
    render_hero(st.session_state.get("destination", ""), current_theme)
    render_preview_modal()

    left, right = st.columns([1.08, 1.92], gap="large")

    with left:
        render_intro_card()
        render_destination_picker()
        render_city_shortcuts()
        input_values = render_input_panel()
        render_history_card()

    with right:
        destination = st.session_state.get("destination", "").strip()
        if input_values["generate"]:
            if not destination:
                st.warning("先告诉我你想去哪儿，再开始排计划。")
            else:
                loading_placeholder, welfare_placeholder, progress_placeholder, progress_bar = show_generation_feedback()
                try:
                    plan = generate_plan_via_llm(
                        destination=destination,
                        days=input_values["days"],
                        budget=input_values["budget"],
                        style=input_values["style"],
                        crowd=input_values["crowd"],
                        season=input_values["season"],
                        special=input_values["special"],
                        stay_preference=input_values["stay_preference"],
                        extra=input_values["extra"],
                        must_go=input_values["must_go"],
                        avoid=input_values["avoid"],
                    )
                    st.session_state["plan_json"] = plan
                    st.session_state["plan_markdown"] = json_to_markdown(plan)
                    st.session_state.pop("plan_error", None)
                    save_history(destination, input_values["days"], input_values["budget"], input_values["style"])
                    finish_generation_feedback(loading_placeholder, welfare_placeholder, progress_placeholder, progress_bar, True, "")
                except Exception as e:
                    st.session_state["plan_error"] = str(e)
                    st.session_state.pop("plan_json", None)
                    st.session_state.pop("plan_markdown", None)
                    finish_generation_feedback(loading_placeholder, welfare_placeholder, progress_placeholder, progress_bar, False, f"这次没能顺利排好：{e}")

        if "plan_error" in st.session_state and "plan_json" not in st.session_state:
            st.error(f"生成失败：{st.session_state['plan_error']}")

        if "plan_json" not in st.session_state:
            render_empty_state()
            return

        plan = st.session_state["plan_json"]
        markdown_text = st.session_state["plan_markdown"]

        render_plan_summary(plan)

        _, dl_col = st.columns([5.2, 1.3])
        with dl_col:
            file_name = f"{plan.get('meta', {}).get('destination', '旅行计划')}_{plan.get('meta', {}).get('days', '')}天计划.md"
            st.download_button(
                "下载 Markdown",
                data=markdown_text.encode("utf-8"),
                file_name=file_name,
                mime="text/markdown",
                use_container_width=True,
            )

        tabs = st.tabs(["行程总览", "时间线", "饮食", "住宿", "预算与清单"])
        with tabs[0]:
            render_overview_tab(plan, current_theme)
        with tabs[1]:
            render_timeline_tab(plan, current_theme)
        with tabs[2]:
            render_food_tab(plan, current_theme)
        with tabs[3]:
            render_hotel_tab(plan, current_theme)
        with tabs[4]:
            render_budget_packing_tab(plan)

        render_footer(plan)


if __name__ == "__main__":
    main()