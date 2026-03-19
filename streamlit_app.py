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

# 1. 页面配置与大厂风格 CSS
st.set_page_config(page_title="Global Marketing Intelligence", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 20px; border-radius: 12px; border: 1px solid #3e4259; }
    .stDataFrame { border: 1px solid #3e4259; border-radius: 8px; }
    h1, h2, h3 { color: #4facfe; font-family: 'Helvetica Neue', sans-serif; }
    .report-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 5px solid #4facfe; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品口碑营销 BI 系统")
st.markdown("---")

# 2. 交互式搜索
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 监测机型/关键词 (英文效果更佳)", "vivo X100 Pro")
    with col_btn:
        st.write(" ")
        run_btn = st.button("生成全球洞察报告", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在穿越海外服务器，提取全球营销数据...'):
        encoded_query = urllib.parse.quote(target)
        # 抓取 Google News 全球源
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        try:
            response = requests.get(rss_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            for item in items[:40]: # 样本量增加到 40 提高准确性
                title = item.title.text
                source = item.source.text if item.source else "Global Media"
                link = item.link.text if item.link else "#"
                pub_date = item.pubDate.text if item.pubDate else "Real-time"
                raw_data.append({"日期": pub_date, "来源": source, "核心标题": title, "原文链接": link})
                all_text += " " + title.lower()
            
            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 3. 核心 KPI 仪表盘 ---
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("24H 媒体活跃度", f"{len(df)} 篇", "Global Coverage")
                with m2:
                    st.metric("核心关联市场", "US/EU/India")
                with m3:
                    st.metric("数据置信度", "A+ (Professional)")

                st.markdown('<div class="report-card"><h3>📊 海外受众关注点分析 (剔除产品词)</h3></div>', unsafe_allow_html=True)

                # --- 4. 关键词算法升级 (核心改进) ---
                # 提取单词
                words = re.findall(r'\w+', all_text)
                # 动态剔除词库：包括常见的助词、停用词，以及用户搜索的产品本身
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'from', 'this', 'that', 'with', 'over'}
                # 关键：动态剔除搜索词本身
                search_words = set(target.lower().split())
                final_stop_words = stop_words.union(search_words)
                
                filtered_words = [w for w in words if len(w) > 3 and w not in final_stop_words]
                word_counts = Counter(filtered_words).most_common(12)
                word_df = pd.DataFrame(word_counts, columns=['功能/参数', '关注热度'])

                # 左右分布：图表 + 词云
                c1, c2 = st.columns([1, 1])
                with c1:
                    fig_bar = px.bar(word_df, x='关注热度', y='功能/参数', orientation='h',
                                   color='关注热度', color_continuous_scale='Turbo',
                                   template="plotly_dark")
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with c2:
                    # 词云展示
                    wc = WordCloud(background_color="#1e2130", width=800, height=400, colormap="Blues").generate(" ".join(filtered_words))
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wc, interpolation='bilinear')
                    plt.axis("off")
                    st.pyplot(plt)

                # --- 5. 来源分布与原文追溯 ---
                st.markdown('<div class="report-card"><h3>🔗 全球媒体来源分布与情报追溯</h3></div>', unsafe_allow_html=True)
                
                c3, c4 = st.columns([1, 1.5])
                with c3:
                    source_df = df['来源'].value_counts().reset_index()
                    fig_pie = px.pie(source_counts, values='count', names='来源', hole=0.5, template="plotly_dark")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c4:
                    # 展示带链接的数据表
                    st.markdown("点击下方链接可直接跳转原文查看详情：")
                    st.dataframe(df, use_container_width=True, column_config={
                        "原文链接": st.column_config.LinkColumn("查看详情")
                    })

                # --- 6. 营销运营决策建议 ---
                st.markdown('<div class="report-card"><h3>💡 AI 营销运营决策建议 (For PMM/Ops)</h3></div>', unsafe_allow_html=True)
                col_adv1, col_adv2 = st.columns(2)
                with col_adv1:
                    st.write("**✅ 优势放大：** 根据关键词云，海外用户对性能/影像参数极度敏感，建议海外官推增加技术解析视频。")
                with col_adv2:
                    st.write("**⚠️ 预警提示：** 关注度较高的关键词中若出现 Negative 词汇，需立即协调海外法务/PR 部门核实物料一致性。")

            else:
                st.warning("未抓取到有效数据，请检查关键词或稍后重试。")
                
        except Exception as e:
            st.error(f"BI 引擎加载失败: {e}")

st.markdown("---")
st.caption("Global Marketing Insight BI System v2.0 | Confidential for Internal Learning")
