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
st.set_page_config(page_title="Global Insight BI v5.2", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #333333; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px;}
    h1, h2, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    div.stButton > button:first-child { background-color: #0052d4; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球深度评测与口碑 BI 看板")
st.caption("定位：产品营销辅助系统 | 已修复：缩进、链接、中式缩写逻辑")
st.markdown("---")

# 2. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 输入监测机型 (支持 x300u/x300p 自动转换)", "vivo X300 Ultra")
    with col_btn:
        st.write(" ")
        run_btn = st.button("开始挖掘海外原声", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在连接全球数据节点...'):
        # --- 业务逻辑：自动转换中式简写 (PM 视角优化) ---
        target_clean = target.strip().lower()
        if target_clean.endswith('u'):
            target_search = target_clean.replace('u', ' ultra')
        elif target_clean.endswith('p'):
            target_search = target_clean.replace('p', ' pro')
        else:
            target_search = target_clean

        # 构造搜索指令：机型 + 评测词
        search_query = f'{target_search} (review OR hands-on OR opinion)'
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
                
                # 严格过滤：标题必须包含用户搜的关键词（支持转换后的全称）
                if target_search not in title.lower() and target_clean not in title.lower():
                    continue
                
                source = item.source.text if item.source else "Global Media"
                
                # 链接提取补丁
                link_val = "#"
                if item.find('link'):
                    link_val = item.find('link').get_text()
                
                raw_data.append({
                    "时间": item.pubDate.text[:16] if item.pubDate else "Recent",
                    "媒体来源": source,
                    "核心标题": title,
                    "跳转原文": link_val
                })
                all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 3. 核心 KPI ---
                m1, m2, m3 = st.columns(3)
                m1.metric("精准匹配篇数", f"{len(df)} 篇", "已过滤干扰项")
                m2.metric("主要声音来源", df['媒体来源'].mode()[0] if not df.empty else "N/A")
                m3.metric("搜索词转换", f"'{target}' -> '{target_search}'")

                # --- 4. 词云与图表功能回归 ---
                st.markdown('<div class="report-card"><h3>📊 海外评测高频词分析</h3></div>', unsafe_allow_html=True)
                
                words = re.findall(r'\w+', all_text)
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'this', 'that', 'review', 'hands', 'opinion', 'video', 'news'}
                filtered_words = [w for w in words if len(w) > 3 and w not in stop_words and w not in target_search.split()]
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    word_counts = Counter(filtered_words).most_common(10)
                    word_df = pd.DataFrame(word_counts, columns=['特征词', '频次'])
                    fig_bar = px.bar(word_df, x='频次', y='特征词', orientation='h', color='频次', template="plotly_white")
                    st.plotly_chart(fig_bar, use_container_width=True)
                with c2:
                    if filtered_words:
                        wc = WordCloud(background_color="white", width=600, height=300).generate(" ".join(filtered_words))
                        plt.figure(figsize=(10, 5))
                        plt.imshow(wc, interpolation='bilinear'); plt.axis("off")
                        st.pyplot(plt)

                # --- 5. 数据明细与直达链接 ---
                st.markdown('<div class="report-card"><h3>🔗 精准数据清单 (可跳转)</h3></div>', unsafe_allow_html=True)
                # 使用 column_config 确保链接 100% 可点击
                st.dataframe(
                    df, 
                    use_container_width=True,
                    column_config={
                        "跳转原文": st.column_config.LinkColumn("🚀 直达原文", display_text="Open Link")
                    },
                    hide_index=True
                )

            else:
                st.warning(f"未找到关于 '{target}' 的精确结果。建议尝试输入全称，如 'vivo X300 Ultra'。")
                
        except Exception as e:
            st.error(f"引擎启动失败: {e}")

st.markdown("---")
st.caption("Global Marketing Insight BI System v5.2 | Final Indent & Logic Fixed")
