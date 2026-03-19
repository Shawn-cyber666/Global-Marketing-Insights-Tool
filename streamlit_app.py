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

# 1. 页面配置
st.set_page_config(page_title="Global Marketing Intelligence", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #333333; }
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
    div.stButton > button:first-child {
        background-color: #0052d4;
        color: white;
        border-radius: 8px;
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
        target = st.text_input("🔍 监测机型/关键词 (英文效果更佳)", "vivo")
    with col_btn:
        st.write(" ")
        run_btn = st.button("生成全球数据报表", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在提取全球营销数据...'):
        encoded_query = urllib.parse.quote(target)
        # 强制使用 Google News 全球源
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
                # 核心修复：确保获取的是 link 标签内的文本链接
                link = item.find('link').text if item.find('link') else "#"
                pub_date = item.pubDate.text if item.pubDate else "Real-time"
                
                raw_data.append({
                    "日期": pub_date, 
                    "来源": source, 
                    "核心标题": title, 
                    "原文链接": link  # 这里存的是完整的 URL 字符串
                })
                all_text += " " + title.lower()
            
            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 3. 核心 KPI ---
                m1, m2, m3 = st.columns(3)
                m1.metric("全球媒体活跃度", f"{len(df)} 篇", "24H 采样")
                m2.metric("监测范围", "Global News Feed")
                m3.metric("解析引擎", "LXML / BS4")

                # --- 4. 关键词与词云 ---
                st.markdown('<div class="report-card"><h3>📊 海外受众功能关注度 (已过滤产品词)</h3></div>', unsafe_allow_html=True)
                
                words = re.findall(r'\w+', all_text)
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'from', 'this', 'that', 'with', 'over', 'says', 'best', 'review', 'vs'}
                search_terms = set(target.lower().split())
                final_stop_words = stop_words.union(search_terms)
                
                filtered_words = [w for w in words if len(w) > 3 and w not in final_stop_words]
                word_counts = Counter(filtered_words).most_common(12)
                word_df = pd.DataFrame(word_counts, columns=['功能/参数', '关注热度'])

                c1, c2 = st.columns([1, 1])
                with c1:
                    fig_bar = px.bar(word_df, x='关注热度', y='功能/参数', orientation='h',
                                   color='关注热度', color_continuous_scale='Blues', template="plotly_white")
                    st.plotly_chart(fig_bar, use_container_width=True)
                with c2:
                    if filtered_words:
                        wc = WordCloud(background_color="white", width=800, height=400, colormap="cool").generate(" ".join(filtered_words))
                        plt.figure(figsize=(10, 5))
                        plt.imshow(wc, interpolation='bilinear')
                        plt.axis("off")
                        st.pyplot(plt)

                # --- 5. 数据明细 (修复链接显示) ---
                st.markdown('<div class="report-card"><h3>🔗 媒体分布与原文情报溯源</h3></div>', unsafe_allow_html=True)
                
                c3, c4 = st.columns([1, 1.5])
                with c3:
                    source_df = df['来源'].value_counts().reset_index()
                    source_df.columns = ['来源', '数量']
                    fig_pie = px.pie(source_df, values='数量', names='来源', hole=0.4, template="plotly_white")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c4:
                    st.markdown("🔍 **实时数据清单 (点击链接图标跳转):**")
                    # 使用最新的 LinkColumn 配置，确保 URL 被渲染成可点击状态
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        column_config={
                            "原文链接": st.column_config.LinkColumn(
                                "跳转原文",
                                help="点击直接访问海外媒体原始报道",
                                validate="^http",
                                display_text="Open Link" # 这样会显示为 "Open Link" 字样，而不是空框
                            )
                        },
                        hide_index=True
                    )

            else:
                st.warning("暂未发现有效数据。")
                
        except Exception as e:
            st.error(f"BI 引擎加载失败: {e}")

st.markdown("---")
st.caption("Global Marketing Insight BI System v2.2 | Data Logic & Link Fix Updated")
