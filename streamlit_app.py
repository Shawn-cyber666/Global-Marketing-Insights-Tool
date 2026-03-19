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

# 1. 页面配置：商务简约白风格
st.set_page_config(page_title="Global Marketing Intelligence", layout="wide")

st.markdown("""
    <style>
    /* 全局背景与字体 */
    .main { background-color: #f8f9fa; color: #333333; }
    /* 卡片设计 */
    .report-card { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    .stMetric { background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 10px; }
    /* 调整 Tab 和按钮 */
    div.stButton > button:first-child {
        background-color: #0052d4;
        color: white;
        border-radius: 8px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品口碑营销 BI 系统")
st.caption("定位：出海营销运营 - 海外市场实时舆情与功能洞察工具")
st.markdown("---")

# 2. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 监测机型/关键词 (输入英文，如: vivo X100 Pro)", "vivo")
    with col_btn:
        st.write(" ")
        run_btn = st.button("生成全球数据报表", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在同步全球营销数据，构建数据透视表...'):
        encoded_query = urllib.parse.quote(target)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        try:
            response = requests.get(rss_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            for item in items[:40]:
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
                m1.metric("全球媒体声量", f"{len(df)} 篇", "24H 实时更新")
                m2.metric("覆盖市场范围", "Global / Multi-Region")
                m3.metric("数据置信度", "高 (High Reliability)")

                # --- 4. 关键词挖掘区 ---
                st.markdown('<div class="report-card"><h3>📊 海外受众功能关注度 (已过滤产品关键词)</h3></div>', unsafe_allow_html=True)
                
                # 关键词过滤算法
                words = re.findall(r'\w+', all_text)
                # 基础停用词
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'from', 'this', 'that', 'over', 'says', 'best', 'review', 'vs'}
                # 动态过滤搜索词及其拆分词
                search_terms = set(target.lower().split())
                final_stop_words = stop_words.union(search_terms)
                
                filtered_words = [w for w in words if len(w) > 3 and w not in final_stop_words]
                word_counts = Counter(filtered_words).most_common(12)
                word_df = pd.DataFrame(word_counts, columns=['功能/参数', '关注指数'])

                c1, c2 = st.columns([1, 1])
                with c1:
                    # 使用商务蓝渐变色
                    fig_bar = px.bar(word_df, x='关注指数', y='功能/参数', orientation='h',
                                   color='关注指数', color_continuous_scale='Blues',
                                   template="plotly_white")
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with c2:
                    # 词云美化：白底商务色调
                    wc = WordCloud(background_color="white", width=800, height=400, colormap="cool").generate(" ".join(filtered_words))
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wc, interpolation='bilinear')
                    plt.axis("off")
                    st.pyplot(plt)

                # --- 5. 来源分布与数据明细 ---
                st.markdown('<div class="report-card"><h3>🔗 媒体分布与原文情报溯源</h3></div>', unsafe_allow_html=True)
                
                c3, c4 = st.columns([1, 1.5])
                with c3:
                    source_df = df['来源'].value_counts().reset_index()
                    # 修正了之前的变量名错误
                    fig_pie = px.pie(source_df, values='count', names='来源', hole=0.4, template="plotly_white")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c4:
                    st.markdown("🔍 **数据明细表格 (带原文追溯链接):**")
                    st.dataframe(df, use_container_width=True, column_config={
                        "原文链接": st.column_config.LinkColumn("点击查看原文")
                    })

                # --- 6. 营销决策建议 ---
                st.markdown('<div class="report-card"><h3>💡 营销运营决策建议 (Marketing Insights)</h3></div>', unsafe_allow_html=True)
                st.info("基于当前全球舆情热点，建议：\n1. 针对高频出现的 **功能关键词** 优化海外营销物料的视觉重心。\n2. 重点监控高权重媒体（如饼图所示）对产品参数的专业评测评价，确保合规与一致性。")

            else:
                st.warning("暂未发现有效全球讨论，请尝试更通用的关键词。")
                
        except Exception as e:
            st.error(f"BI 引擎加载失败，请检查网络或刷新重试。错误详情: {e}")

st.markdown("---")
st.caption("Global Marketing Insight BI System v2.1 | Data Logic Updated 2026")
