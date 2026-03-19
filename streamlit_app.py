import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import plotly.express as px
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime
import json

# 1. 页面配置
st.set_page_config(page_title="Global Insight v7.5", layout="wide")

# 2. 侧边栏配置：机器人 Webhook (保护隐私)
with st.sidebar:
    st.header("⚙️ 自动化配置")
    webhook_url = st.text_input("群机器人 Webhook 地址", help="支持企业微信/钉钉/飞书机器人 URL", type="password")
    st.info("💡 配置后可一键将分析摘要推送到项目群。")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.01); margin-bottom: 20px;}
    h1, h2, h3 { color: #0052d4; }
    .url-text { word-break: break-all; font-family: monospace; font-size: 11px; color: #888; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品声量监测与自动化助手")
st.markdown("---")

# 3. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 输入监测机型", "vivo X100 Pro")
    with col_btn:
        st.write(" ")
        run_btn = st.button("挖掘并分析", use_container_width=True)

# 定义推送函数
def push_to_bot(content, url):
    if not url:
        st.error("❌ 请先在侧边栏填写 Webhook 地址")
        return
    # 通用 Markdown 格式 (兼容企微/钉钉)
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content, # 企微格式
            "text": content,    # 钉钉格式
            "title": "产品声量周报"
        }
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            st.success("✅ 已成功推送至群聊！")
        else:
            st.error(f"推送失败: {res.text}")
    except Exception as e:
        st.error(f"连接异常: {e}")

if run_btn:
    with st.spinner('🚀 正在执行深度索引...'):
        # 业务逻辑：自动转换
        target_clean = target.strip().lower()
        target_search = target_clean.replace('u', ' ultra').replace('p', ' pro') if target_clean.endswith(('u', 'p')) else target_clean

        search_query = f'{target_search} review'
        encoded_query = urllib.parse.quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(rss_url, timeout=15)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            
            for item in items[:40]:
                title = item.title.text if item.title else ""
                if target_search not in title.lower(): continue
                
                source = item.source.text if item.source else "Global Media"
                date_str = item.pubDate.text[:16] if item.pubDate else ""
                link_val = item.find('link').get_text() if item.find('link') else "#"
                
                raw_data.append({"日期": date_str, "渠道": source, "标题": title, "URL": link_val})
                all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data)
                
                # --- 生成周报文本 ---
                words = re.findall(r'\w+', all_text)
                top_keywords = [k for k, v in Counter([w for w in words if len(w)>3 and w not in ['the','review','news']]).most_common(5)]
                
                report_md = f"### 📊 {target_search.upper()} 海外声量速报\n" \
                            f"> **监测周期**: 本周实时数据\n\n" \
                            f"- **声量概况**: 精准命中评测 **{len(df)}** 篇\n" \
                            f"- **核心媒体**: {df['渠道'].mode()[0]} 等权威渠道\n" \
                            f"- **舆情热词**: # {' # '.join(top_keywords)}\n" \
                            f"- **最新动态**: {df['日期'].iloc[0]}\n\n" \
                            f"[查看完整看板]({st.get_option('browser.serverAddress') if 'browser.serverAddress' in st._config.get_config_options() else '本地环境'})"

                # --- 报告区域 ---
                st.markdown('<div class="report-card"><h3>📝 自动化报告摘要</h3></div>', unsafe_allow_html=True)
                st.markdown(report_md)
                
                if st.button("🚀 一键推送到项目群", use_container_width=True):
                    push_to_bot(report_md, webhook_url)

                # --- 原有图表 ---
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(px.pie(df, names='渠道', hole=0.4, title="媒体来源分布"), use_container_width=True)
                with c2:
                    st.plotly_chart(px.bar(pd.DataFrame(Counter(top_keywords).most_common(), columns=['热词','频次']), x='频次', y='热词', orientation='h'), use_container_width=True)

                st.markdown('<div class="report-card"><h3>🔗 数据明细</h3></div>', unsafe_allow_html=True)
                st.table(df)

            else:
                st.warning("未找到匹配数据。")
        except Exception as e:
            st.error(f"Error: {e}")
