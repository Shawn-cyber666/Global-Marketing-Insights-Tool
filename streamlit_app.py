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

# 1. 页面配置与大厂风格
st.set_page_config(page_title="Global Insight v5.8", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; margin-bottom: 20px;}
    h1, h2, h3 { color: #0052d4; }
    /* 强制表格换行，确保长URL可见 */
    .stTable td { word-break: break-all !important; white-space: normal !important; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品声量精准监测看板")
st.caption("同步：Google News 实时索引 | 修复：精确日期、完整 URL 展示")

# 2. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 输入监测机型 (如 x300u / iPhone 16)", "vivo X100 Pro")
    with col_btn:
        st.write(" ")
        run_btn = st.button("开始精准挖掘", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在提取全球原始数据流...'):
        # 中式缩写转换逻辑
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
            
            for item in items[:40]:
                title = item.title.text if item.title else ""
                
                # 严格匹配
                if target_search not in title.lower() and target_clean not in title.lower():
                    continue
                
                source = item.source.text if item.source else "Media"
                
                # --- 精确日期处理 ---
                # 原始格式如: Sat, 14 Mar 2026 08:00:00 GMT
                raw_date = item.pubDate.text if item.pubDate else ""
                try:
                    # 转换为 2026-03-14 这种业务常用格式
                    date_obj = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z')
                    final_date = date_obj.strftime('%Y-%m-%d')
                except:
                    final_date = raw_date[:16] # 备选方案

                # --- 完整 URL 提取 ---
                link_val = item.link.next_sibling if item.link else ""
                if not link_val:
                    link_val = item.find('link').get_text() if item.find('link') else "N/A"
                
                raw_data.append({
                    "日期": final_date,
                    "渠道来源": source,
                    "评测标题": title,
                    "原始URL链接": str(link_val).strip()
                })
                all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data)

                # 3. 核心 KPI 展示
                m1, m2, m3 = st.columns(3)
                m1.metric("精准命中篇数", len(df))
                m2.metric("最新监测日期", df['日期'].max())
                m3.metric("搜索词补全", target_search)

                # 4. 词云回归
                st.markdown('<div class="report-card"><h3>📊 海外关注热点词云</h3></div>', unsafe_allow_html=True)
                words = re.findall(r'\w+', all_text)
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'this', 'that', 'review', 'news'}
                filtered_words = [w for w in words if len(w) > 3 and w not in stop_words and w not in target_search.split()]
                
                if filtered_words:
                    wc = WordCloud(background_color="white", width=1000, height=400, colormap='Blues').generate(" ".join(filtered_words))
                    plt.figure(figsize=(15, 6))
                    plt.imshow(wc, interpolation='bilinear'); plt.axis("off")
                    st.pyplot(plt)

                # 5. 精准数据表 (使用 st.table 确保 URL 不被隐藏)
                st.markdown('<div class="report-card"><h3>🔗 精准数据明细清单 (100% 透明展示)</h3></div>', unsafe_allow_html=True)
                # 使用 table 而不是 dataframe，因为它会完整显示每一行内容
                st.table(df)

            else:
                st.warning(f"未能匹配到关于 '{target}' 的精确结果。请尝试更完整的机型名称。")
                
        except Exception as e:
            st.error(f"连接异常: {e}")

st.markdown("---")
st.caption("Global Marketing Insight System v5.8 | Precise Date & URL Extraction Enabled")
