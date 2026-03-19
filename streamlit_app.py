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

# 1. 页面配置与大厂商务白样式
st.set_page_config(page_title="Global Insight Pro v7.0", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px;}
    h1, h2, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    .stMetric { background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 10px; }
    div.stButton > button:first-child { background-color: #0052d4; color: white; border-radius: 8px; }
    .url-text { word-break: break-all; font-family: monospace; font-size: 12px; color: #666; }
    .report-box { background-color: #f1f3f9; padding: 15px; border-left: 5px solid #0052d4; font-family: 'PingFang SC', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品声量精准监测与周报助手")
st.caption("同步：Google News 实时索引 | 核心：自动生成 PM 周报摘要")
st.markdown("---")

# 2. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 输入监测机型 (支持 x300u/x300p 自动补全)", "vivo X100 Pro")
    with col_btn:
        st.write(" ")
        run_btn = st.button("挖掘并生成报告", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在同步全球节点并撰写报告摘要...'):
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
                if target_search not in title.lower() and target_clean not in title.lower():
                    continue
                
                source = item.source.text if item.source else "Overseas Media"
                
                # 精确日期处理
                raw_date = item.pubDate.text if item.pubDate else ""
                try:
                    date_obj = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z')
                    final_date = date_obj.strftime('%Y-%m-%d')
                except:
                    final_date = datetime.now().strftime('%Y-%m-%d')

                link_val = item.link.next_sibling if item.link else ""
                if not link_val:
                    link_val = item.find('link').get_text() if item.find('link') else "N/A"
                
                raw_data.append({"日期": final_date, "渠道": source, "标题": title, "URL": str(link_val).strip()})
                all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data)
                
                # --- 3. 【新增】一键周报草稿生成 ---
                st.markdown('<div class="report-card"><h3>📝 PM 周报摘要自拟 (可直接复制)</h3></div>', unsafe_allow_html=True)
                
                # 自动提炼关键词
                words = re.findall(r'\w+', all_text)
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'review', 'news'}
                filtered_words = [w for w in words if len(w) > 3 and w not in stop_words and w not in target_search.split()]
                top_keywords = [k for k, v in Counter(filtered_words).most_common(5)]
                
                report_text = f"""
【{target_search.upper()} 海外声量周报摘要】
1. 监测概况：本周精准监测到海外深度评测/动态共计 {len(df)} 篇；
2. 核心阵地：主要声量集中在 {df['渠道'].mode()[0]} 等权威媒体；
3. 关键日期：最新动态更新至 {df['日期'].max()}；
4. 用户/媒体关注点：重点集中在“{', '.join(top_keywords)}”等核心维度；
5. 风险/机会点：通过对关键词挖掘，发现媒体对【{top_keywords[0] if top_keywords else '产品细节'}】讨论频次最高，建议后续运营重点关注。
                """
                st.info("💡 鼠标选中下方文本框即可快速复制：")
                st.text_area(label="Weekly Report Draft", value=report_text.strip(), height=180)

                # --- 4. 仪表盘与可视化 ---
                st.markdown('<div class="report-card"><h3>📊 渠道分布与趋势图表</h3></div>', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 1])
                with c1:
                    fig_pie = px.pie(df['渠道'].value_counts().reset_index(), values='count', names='渠道', hole=0.4, title="媒体来源占比")
                    st.plotly_chart(fig_pie, use_container_width=True)
                with c2:
                    word_df = pd.DataFrame(Counter(filtered_words).most_common(10), columns=['热词', '频次'])
                    fig_bar = px.bar(word_df, x='频次', y='热词', orientation='h', title="核心关注点 Top 10", color='频次')
                    st.plotly_chart(fig_bar, use_container_width=True)

                # --- 5. 词云与数据清单 ---
                if filtered_words:
                    wc = WordCloud(background_color="white", width=1200, height=300).generate(" ".join(filtered_words))
                    plt.figure(figsize=(15, 4)); plt.imshow(wc); plt.axis("off")
                    st.pyplot(plt)

                st.markdown('<div class="report-card"><h3>🔗 精准数据明细 (带日期与 URL)</h3></div>', unsafe_allow_html=True)
                # 使用 Markdown 表格确保 URL 可复制
                md_table = "| 日期 | 渠道 | 标题 | 原始 URL |\n| :--- | :--- | :--- | :--- |\n"
                for _, row in df.iterrows():
                    md_table += f"| {row['日期']} | {row['渠道']} | {row['标题']} | <span class='url-text'>{row['URL']}</span> |\n"
                st.markdown(md_table, unsafe_allow_html=True)

            else:
                st.warning(f"未找到关于 '{target}' 的精确结果。")
        except Exception as e:
            st.error(f"运行出错: {e}")

st.markdown("---")
st.caption("Global Insight System v7.0 | Integrated Report Generator")
