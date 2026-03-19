import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup  # <--- 刚才漏掉的“救命稻草”
import urllib.parse
import plotly.express as px
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime

# 1. 页面配置：商务深蓝风格
st.set_page_config(page_title="Global Insight v8.1", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.01); margin-bottom: 20px;}
    h1, h3 { color: #0052d4; }
    .v-msg-box { background-color: #e8f0fe; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; border-left: 5px solid #0052d4; white-space: pre-wrap; }
    .url-text { word-break: break-all; font-size: 11px; color: #0052d4; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品声量精准监测 (v8.1 稳定修复版)")

# 2. 侧边栏：v 消息机器人配置
with st.sidebar:
    st.header("⚙️ v 消息自动化配置")
    v_webhook = st.text_input("v 消息机器人 Webhook", type="password", help="在群设置-群机器人中获取")
    st.divider()
    st.info("💡 提示：若暂时没有 Webhook，可直接手动复制生成的报告。")

# 3. 核心业务逻辑
target = st.text_input("🔍 监测机型 (自动识别 u/p)", "vivo X300 Ultra")
run_btn = st.button("开始挖掘并生成 v 消息摘要", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在执行全球媒体穿透索引...'):
        # 补全转换逻辑
        target_clean = target.strip().lower()
        target_search = target_clean.replace('u', ' ultra').replace('p', ' pro') if target_clean.endswith(('u', 'p')) else target_clean
        
        encoded_query = urllib.parse.quote(f'{target_search} review')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(rss_url, timeout=10)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            for item in items[:40]:
                title = item.title.text
                if target_search in title.lower() or target_clean in title.lower():
                    source = item.source.text
                    # 格式化日期
                    try:
                        date_obj = datetime.strptime(item.pubDate.text, '%a, %d %b %Y %H:%M:%S %Z')
                        f_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        f_date = datetime.now().strftime('%Y-%m-%d')
                    
                    link = item.find('link').get_text() if item.find('link') else "#"
                    raw_data.append({"日期": f_date, "来源": source, "标题": title, "URL": link})
                    all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data).sort_values(by="日期", ascending=False)
                
                # --- 生成 v 消息专用报告文本 ---
                words = [w for w in re.findall(r'\w+', all_text) if len(w)>3 and w not in ['the','review','news','video','phone','with']]
                top_tags_list = [k for k, v in Counter(words).most_common(5)]
                top_tags = " # ".join(top_tags_list)
                
                v_report = f"📢 【{target_search.upper()} 海外声量速报】\n" \
                           f"━━━━━━━━━━━━━━\n" \
                           f"📅 监测日期：{datetime.now().strftime('%Y-%m-%d')}\n" \
                           f"📊 本周新增动态：{len(df)} 篇\n" \
                           f"📡 核心来源：{df['来源'].mode()[0]}\n" \
                           f"🔥 舆情热点：# {top_tags}\n" \
                           f"🔗 数据详表：已在看板更新\n" \
                           f"━━━━━━━━━━━━━━\n" \
                           f"💡 简评：媒体对【{top_tags_list[0] if top_tags_list else '产品表现'}】关注度显著。"

                # 展示报告
                st.markdown('<div class="report-card"><h3>📝 v 消息预推摘要</h3></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="v-msg-box">{v_report}</div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🚀 尝试推送到 v 消息群"):
                        if v_webhook:
                            payload = {"msgtype": "markdown", "markdown": {"content": v_report}}
                            try:
                                requests.post(v_webhook, json=payload, timeout=5)
                                st.success("✅ 已尝试推送到 v 消息！")
                            except:
                                st.error("推送失败，请检查网络或 Webhook 地址。")
                        else:
                            st.warning("请先在左侧侧边栏填写 v 消息 Webhook 地址。")
                with c2:
                    st.download_button("📂 导出 CSV 原始数据", df.to_csv(index=False).encode('utf-8-sig'), f"{target_search}_data.csv")

                # --- 可视化图表 ---
                st.markdown("---")
                col_l, col_r = st.columns(2)
                with col_l:
                    st.plotly_chart(px.pie(df, names='来源', hole=0.4, title="主流媒体分布"), use_container_width=True)
                with col_r:
                    word_df = pd.DataFrame(Counter(words).most_common(10), columns=['热词','频次'])
                    st.plotly_chart(px.bar(word_df, x='频次', y='热词', orientation='h', title="核心关注点 Top 10"), use_container_width=True)

                # --- 原始数据展示 ---
                st.markdown('<div class="report-card"><h3>🔗 精准监测清单 (100% 透明原链)</h3></div>', unsafe_allow_html=True)
                md_table = "| 日期 | 来源渠道 | 评测标题 | 原始 URL 链接 |\n| :--- | :--- | :--- | :--- |\n"
                for _, row in df.iterrows():
                    md_table += f"| {row['日期']} | {row['来源']} | {row['标题']} | <span class='url-text'>{row['URL']}</span> |\n"
                st.markdown(md_table, unsafe_allow_html=True)

            else:
                st.warning(f"未能找到关于 '{target}' 的精确匹配数据。")
        except Exception as e:
            st.error(f"运行出错: {e}")

st.markdown("---")
st.caption("Global Insight System v8.1 | Stable Fix")
