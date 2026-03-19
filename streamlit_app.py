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

# 1. 页面样式与大厂商务白配置
st.set_page_config(page_title="Global Insight Pro v6.0", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px;}
    h1, h2, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    .stMetric { background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 10px; }
    div.stButton > button:first-child { background-color: #0052d4; color: white; border-radius: 8px; }
    /* 强制表格链接换行显示 */
    .url-text { word-break: break-all; font-family: monospace; font-size: 12px; color: #666; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品声量精准监测 BI 看板")
st.caption("同步：Google News 实时索引 | 修复：精确日期 (YYYY-MM-DD) | 修复：完整 URL 原链")
st.markdown("---")

# 2. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 监测机型 (自动识别 u/p 缩写)", "vivo X300 Ultra")
    with col_btn:
        st.write(" ")
        run_btn = st.button("开始深度挖掘", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在同步全球媒体节点，执行高精度匹配...'):
        # 业务逻辑：自动转换中式缩写
        target_clean = target.strip().lower()
        if target_clean.endswith('u'):
            target_search = target_clean.replace('u', ' ultra')
        elif target_clean.endswith('p'):
            target_search = target_clean.replace('p', ' pro')
        else:
            target_search = target_clean

        search_query = f'{target_search} review'
        encoded_query = urllib.parse.quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(rss_url, timeout=15)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            
            for item in items[:50]:
                title = item.title.text if item.title else ""
                
                # 严格匹配校验
                if target_search not in title.lower() and target_clean not in title.lower():
                    continue
                
                source = item.source.text if item.source else "Overseas Media"
                
                # --- 精确日期处理 (YYYY-MM-DD) ---
                raw_date = item.pubDate.text if item.pubDate else ""
                try:
                    date_obj = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z')
                    final_date = date_obj.strftime('%Y-%m-%d')
                except:
                    final_date = "2026-03-19" # 兜底今日日期

                # --- 完整链接提取 ---
                link_val = item.link.next_sibling if item.link else ""
                if not link_val:
                    link_val = item.find('link').get_text() if item.find('link') else "N/A"
                
                raw_data.append({
                    "日期": final_date,
                    "来源渠道": source,
                    "评测标题": title,
                    "原文URL": str(link_val).strip()
                })
                all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 3. 核心 KPI ---
                m1, m2, m3 = st.columns(3)
                m1.metric("精准命中篇数", f"{len(df)} 篇")
                m2.metric("最新监测日期", df['日期'].max())
                m3.metric("搜索转换逻辑", f"'{target}' -> '{target_search}'")

                # --- 4. 图表功能回归 ---
                st.markdown('<div class="report-card"><h3>📊 渠道声量与热点分析</h3></div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    # 渠道占比饼图
                    source_counts = df['来源渠道'].value_counts().reset_index()
                    fig_pie = px.pie(source_counts, values='count', names='来源渠道', hole=0.4, title="媒体来源分布", color_discrete_sequence=px.colors.sequential.Blues_r)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c2:
                    # 热词柱状图
                    words = re.findall(r'\w+', all_text)
                    stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'this', 'that', 'review', 'news'}
                    filtered_words = [w for w in words if len(w) > 3 and w not in stop_words and w not in target_search.split()]
                    word_counts = Counter(filtered_words).most_common(10)
                    word_df = pd.DataFrame(word_counts, columns=['热词', '频次'])
                    fig_bar = px.bar(word_df, x='频次', y='热词', orientation='h', title="核心关注点 Top 10", color='频次', color_continuous_scale='Blues')
                    st.plotly_chart(fig_bar, use_container_width=True)

                # --- 5. 词云展示 ---
                if filtered_words:
                    st.markdown('<div class="report-card"><h3>☁️ 全球评价关键词云</h3></div>', unsafe_allow_html=True)
                    wc = WordCloud(background_color="white", width=1200, height=400, colormap='Blues').generate(" ".join(filtered_words))
                    plt.figure(figsize=(15, 5))
                    plt.imshow(wc, interpolation='bilinear'); plt.axis("off")
                    st.pyplot(plt)

                # --- 6. 原始数据清单 (使用 Markdown 确保 URL 100% 完整且可复制) ---
                st.markdown('<div class="report-card"><h3>🔗 精准监测明细 (带完整日期与 URL)</h3></div>', unsafe_allow_html=True)
                
                # 构造 Markdown 表格字符串以实现 100% 透明度
                md_table = "| 日期 | 来源渠道 | 评测标题 | 原始 URL 链接 |\n| :--- | :--- | :--- | :--- |\n"
                for index, row in df.iterrows():
                    md_table += f"| {row['日期']} | {row['来源渠道']} | {row['评测标题']} | <span class='url-text'>{row['原文URL']}</span> |\n"
                
                st.markdown(md_table, unsafe_allow_html=True)

            else:
                st.warning(f"未能匹配到关于 '{target}' 的精确结果。")
                
        except Exception as e:
            st.error(f"连接异常: {e}")

st.markdown("---")
st.caption("Global Marketing Insight System v6.0 | Precise Date & Full URL Extraction")
