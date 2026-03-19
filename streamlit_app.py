import streamlit as st
import pandas as pd
import requests
import urllib.parse
import plotly.express as px
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime

# 1. 页面配置
st.set_page_config(page_title="Global Insight v7.8", layout="wide")

# 2. 侧边栏：灵活配置
with st.sidebar:
    st.header("⚙️ 自动化配置")
    bot_type = st.selectbox("选择沟通工具", ["飞书 (Lark)", "钉钉 (DingTalk)", "其他 (仅生成文本)"])
    webhook_url = st.text_input("机器人 Webhook 地址", type="password")
    st.divider()
    st.info("💡 提示：飞书/钉钉的机器人通常在群设置->机器人中添加。")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; margin-bottom: 20px;}
    h1, h3 { color: #0052d4; }
    .url-text { word-break: break-all; font-family: monospace; font-size: 11px; color: #888; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品声量精准监测 (多端适配版)")

# 3. 搜索模块
target = st.text_input("🔍 监测机型", "vivo X100 Pro")
run_btn = st.button("挖掘并生成报告", use_container_width=True)

# 统一推送函数
def send_to_bot(content, url, platform):
    if not url:
        st.warning("⚠️ 请先在侧边栏配置 Webhook 地址")
        return
    
    payload = {}
    if platform == "飞书 (Lark)":
        payload = {"msg_type": "text", "content": {"text": content}}
    elif platform == "钉钉 (DingTalk)":
        payload = {"msgtype": "text", "text": {"content": content}}
    
    try:
        res = requests.post(url, json=payload, timeout=5)
        st.success(f"✅ 已推送到 {platform}！")
    except Exception as e:
        st.error(f"推送失败: {e}")

if run_btn:
    with st.spinner('🚀 正在索引全球数据...'):
        # 转换逻辑
        target_clean = target.strip().lower()
        target_search = target_clean.replace('u', ' ultra').replace('p', ' pro') if target_clean.endswith(('u', 'p')) else target_clean
        
        # 抓取逻辑 (简化示意，保留核心)
        encoded_query = urllib.parse.quote(f'{target_search} review')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(rss_url, timeout=10)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            for item in items[:30]:
                title = item.title.text
                if target_search in title.lower():
                    source = item.source.text
                    date = item.pubDate.text[:16]
                    link = item.find('link').get_text()
                    raw_data.append({"日期": date, "来源": source, "标题": title, "URL": link})
                    all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data)
                
                # --- 生成周报文本 ---
                words = [w for w in re.findall(r'\w+', all_text) if len(w)>3 and w not in ['the','review','news']]
                top_tags = " # ".join([k for k, v in Counter(words).most_common(5)])
                
                report_txt = f"【产品声量速报 - {target_search.upper()}】\n" \
                             f"1. 本周新增深度评测: {len(df)} 篇\n" \
                             f"2. 核心关注点: # {top_tags}\n" \
                             f"3. 核心媒体: {df['来源'].mode()[0]}\n" \
                             f"4. 最新更新日期: {df['日期'].iloc[0]}\n" \
                             f"--- 数据由自动监测看板生成 ---"

                # 报告展示与一键推送
                st.markdown('<div class="report-card"><h3>📝 自动化报告内容</h3></div>', unsafe_allow_html=True)
                st.code(report_txt, language="markdown")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"🚀 推送到 {bot_type}"):
                        send_to_bot(report_txt, webhook_url, bot_type)
                with c2:
                    # 新增：导出 Excel 兼容格式
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📂 下载原始数据 (CSV)", csv, f"{target_search}_report.csv", "text/csv")

                # --- 仪表盘 ---
                st.plotly_chart(px.pie(df, names='来源', hole=0.4, title="渠道占比"), use_container_width=True)
                st.table(df)

            else:
                st.warning("无匹配数据。")
        except Exception as e:
            st.error(f"Error: {e}")
