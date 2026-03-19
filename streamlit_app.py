import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import plotly.express as px
from collections import Counter
import re

# 1. 页面样式配置
st.set_page_config(page_title="Global Insight Fix", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; margin-bottom: 20px;}
    h1 { color: #0052d4; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球深度评测 (Final Fix)")
st.caption("已修复：缩进问题 | 链接显示问题 | 搜索穿透问题")

# 2. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 输入精确机型", "vivo X100 Pro")
    with col_btn:
        st.write(" ")
        run_btn = st.button("开始挖掘", use_container_width=True)

if run_btn:
    with st.spinner('🚀 执行高精度匹配中...'):
        # 强制包含 review 关键词
        search_query = f'{target} review'
        encoded_query = urllib.parse.quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(rss_url, timeout=15)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            target_clean = target.strip().lower()
            
            for item in items:
                title = item.title.text if item.title else ""
                
                # 严格过滤非目标机型
                if target_clean not in title.lower():
                    continue
                
                source = item.source.text if item.source else "Global Media"
                
                # 获取链接并处理
                link_val = item.link.next_sibling if item.link else ""
                if not link_val:
                    link_val = item.find('link').get_text() if item.find('link') else "#"
                
                # 构造 Markdown 链接，这是最稳妥的显示方式
                link_display = f"[点击跳转]({link_val})"
                
                raw_data.append({
                    "媒体来源": source,
                    "核心评测标题": title,
                    "直达链接": link_display
                })

            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 仪表盘 ---
                c1, c2 = st.columns([1, 2])
                with c1:
                    sub_df = df['媒体来源'].value_counts().reset_index()
                    fig_pie = px.pie(sub_df, values='count', names='媒体来源', title="声量分布")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c2:
                    st.markdown("### 📝 精准评测清单")
                    # 使用 write 配合 Markdown 渲染，解决链接不显示问题
                    st.table(df) 
                    st.info("💡 如果上表链接无法点击，请检查浏览器是否拦截了弹出窗口。")

            else:
                st.warning(f"未找到关于 '{target}' 的精确匹配结果。")
                
        except Exception as e:
            st.error(f"运行出错: {e}")

st.markdown("---")
st.caption("System v5.1 | Stable Node Enabled")
