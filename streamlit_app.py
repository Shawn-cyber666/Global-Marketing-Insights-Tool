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

# 1. 页面与商务白样式配置
st.set_page_config(page_title="Global KOL & Review Radar", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #333333; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px;}
    h1, h2, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    .stMetric { background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 10px; }
    div.stButton > button:first-child { background-color: #0052d4; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球深度评测与口碑 (Review) BI 看板")
st.caption("定位：产品营销辅助系统 - 依托高权重视角，精准锁定 KOL/媒体的深度吐槽与赞誉")
st.markdown("---")

# 2. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 输入精确机型 (如: vivo X100 Pro)", "vivo X100")
    with col_btn:
        st.write(" ")
        run_btn = st.button("挖掘海外深度评测", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在连接全球稳定节点，执行双重精确匹配...'):
        # 核心变动 1：Hack 搜索指令，强制要求包含评测或看法类关键词
        search_query = f'{target} (review OR hands-on OR opinion OR impressions OR tested)'
        encoded_query = urllib.parse.quote(search_query)
        
        # 回归最稳定的通道
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        try:
            response = requests.get(rss_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            target_clean = target.strip().lower() # 用户输入的纯净版小写
            
            for item in items[:60]: # 加大样本量以备过滤
                title = item.title.text if item.title else ""
                
                # 核心变动 2：Python 级终极拦截！如果不完全包含用户搜的词，直接丢弃！
                # 彻底解决搜 s 出来 Ultra 的问题
                if target_clean not in title.lower():
                    continue
                
                source = item.source.text if item.source else "Global Reviewer"
                link = item.find('link').text if item.find('link') else "#"
                pub_date = item.pubDate.text if item.pubDate else "Recent"
                
                raw_data.append({
                    "发布时间": pub_date,
                    "KOL/媒体来源": source,
                    "核心评测标题": title,
                    "跳转原文": link
                })
                all_text += " " + title.lower()
            
            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 3. 核心 KPI ---
                m1, m2, m3 = st.columns(3)
                m1.metric("精准匹配深度评测数", f"{len(df)} 篇", "过滤掉无关机型")
                m2.metric("主要观点阵地", df['KOL/媒体来源'].mode()[0] if not df.empty else "N/A")
                m3.metric("匹配策略", "严格级 (Strict Match)")

                # --- 4. 痛点与功能点挖掘 ---
                st.markdown('<div class="report-card"><h3>📊 海外评测高频关注点 (已剔除干扰词)</h3></div>', unsafe_allow_html=True)
                
                words = re.findall(r'\w+', all_text)
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'from', 'this', 'that', 'over', 'says', 'but', 'are', 'just', 'like', 'have', 'has', 'not', 'was', 'review', 'hands', 'opinion', 'impressions', 'tested'}
                search_terms = set(target.lower().split())
                final_stop_words = stop_words.union(search_terms)
                
                filtered_words = [w for w in words if len(w) > 3 and w not in final_stop_words]
                word_counts = Counter(filtered_words).most_common(12)
                word_df = pd.DataFrame(word_counts, columns=['功能/参数', '提及频次'])

                c1, c2 = st.columns([1, 1])
                with c1:
                    fig_bar = px.bar(word_df, x='提及频次', y='功能/参数', orientation='h',
                                   color='提及频次', color_continuous_scale='Blues', template="plotly_white")
                    st.plotly_chart(fig_bar, use_container_width=True)
                with c2:
                    if filtered_words:
                        wc = WordCloud(background_color="white", width=800, height=400, colormap="cool").generate(" ".join(filtered_words))
                        plt.figure(figsize=(10, 5))
                        plt.imshow(wc, interpolation='bilinear')
                        plt.axis("off")
                        st.pyplot(plt)

                # --- 5. 数据明细与可点击链接 ---
                st.markdown('<div class="report-card"><h3>🔗 评测源清单与追溯</h3></div>', unsafe_allow_html=True)
                
                c3, c4 = st.columns([1, 1.5])
                with c3:
                    sub_df = df['KOL/媒体来源'].value_counts().reset_index()
                    sub_df.columns = ['来源', '文章数']
                    fig_pie = px.pie(sub_df, values='文章数', names='来源', hole=0.4, template="plotly_white")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c4:
                    st.markdown("💬 **深度评测直达清单:**")
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        column_config={
                            "跳转原文": st.column_config.LinkColumn(
                                "🚀 直达链接",
                                help="点击跳转至原评测",
                                display_text="去看看"
                            )
                        },
                        hide_index=True
                    )

            else:
                st.warning(f"太严格了！系统成功拦截了所有不包含 '{target}' 的泛滥新闻，但目前尚未抓取到完全匹配的深度评测。")
                
        except Exception as e:
            st.error(f"网络通道异常: {e}")

st.markdown("---")
st.caption("Global Review Insight System v5.0 | 强校验防封杀版 | Data Driven by Google Index")
