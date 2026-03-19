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

# 1. 页面样式与商务白主题配置
st.set_page_config(page_title="Global Insight BI v5.5", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #333333; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px;}
    h1, h2, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    div.stButton > button:first-child { background-color: #0052d4; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品声量与渠道实时看板")
st.caption("功能：实时口碑挖掘 | 渠道时效追踪 | 链接深度修复")
st.markdown("---")

# 2. 交互模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 监测机型 (自动识别 u/p 缩写)", "vivo X300 Ultra")
    with col_btn:
        st.write(" ")
        run_btn = st.button("挖掘全球实时数据", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在同步全球媒体节点，请稍后...'):
        # 中式缩写转换逻辑
        target_clean = target.strip().lower()
        if target_clean.endswith('u'):
            target_search = target_clean.replace('u', ' ultra')
        elif target_clean.endswith('p'):
            target_search = target_clean.replace('p', ' pro')
        else:
            target_search = target_clean

        # 搜索增强：机型 + 评测关键词
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
                
                # 关键词匹配校验
                if target_search not in title.lower() and target_clean not in title.lower():
                    continue
                
                source = item.source.text if item.source else "Overseas Media"
                
                # 时间格式化
                raw_date = item.pubDate.text if item.pubDate else "Recently"
                formatted_date = raw_date[:16] # 截取到分钟
                
                # 核心：链接提取与清理
                link_node = item.find('link')
                link_val = link_node.get_text() if link_node else "#"
                
                raw_data.append({
                    "发布时间": formatted_date,
                    "来源渠道": source,
                    "核心标题内容": title,
                    "原文链接": link_val
                })
                all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 3. 实时看板 KPI ---
                m1, m2, m3 = st.columns(3)
                m1.metric("监测到相关评测", f"{len(df)} 篇")
                m2.metric("最活跃渠道", df['来源渠道'].mode()[0])
                m3.metric("数据时效", "实时同步")

                # --- 4. 词云与趋势可视化 ---
                st.markdown('<div class="report-card"><h3>📊 海外用户关注度点阵</h3></div>', unsafe_allow_html=True)
                
                words = re.findall(r'\w+', all_text)
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'this', 'that', 'review', 'news', 'video'}
                filtered_words = [w for w in words if len(w) > 3 and w not in stop_words and w not in target_search.split()]
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    word_counts = Counter(filtered_words).most_common(10)
                    word_df = pd.DataFrame(word_counts, columns=['热词', '频次'])
                    fig_bar = px.bar(word_df, x='频次', y='热词', orientation='h', color='频次', color_continuous_scale='Blues')
                    st.plotly_chart(fig_bar, use_container_width=True)
                with c2:
                    if filtered_words:
                        wc = WordCloud(background_color="white", width=600, height=300, colormap='Blues').generate(" ".join(filtered_words))
                        plt.figure(figsize=(10, 5))
                        plt.imshow(wc, interpolation='bilinear'); plt.axis("off")
                        st.pyplot(plt)

                # --- 5. 实时数据明细 (带链接修复) ---
                st.markdown('<div class="report-card"><h3>🔗 实时监测清单 (点击 "Open" 直达原文)</h3></div>', unsafe_allow_html=True)
                
                st.dataframe(
                    df, 
                    use_container_width=True,
                    column_config={
                        "原文链接": st.column_config.LinkColumn(
                            "原文链接",
                            help="点击直接跳转至来源网页",
                            display_text="Open Link 🔗"
                        ),
                        "发布时间": st.column_config.TextColumn("📅 发布时间"),
                        "来源渠道": st.column_config.TextColumn("📡 来源渠道")
                    },
                    hide_index=True
                )

            else:
                st.warning(f"暂未在海外主流渠道发现关于 '{target}' 的精确讨论，建议检查机型全称。")
                
        except Exception as e:
            st.error(f"连接中断: {e}")

st.markdown("---")
st.caption("Marketing Insight System v5.5 | Developer Edition")
