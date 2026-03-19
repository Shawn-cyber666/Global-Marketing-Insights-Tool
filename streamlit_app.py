import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
import plotly.express as px
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 1. 页面与大厂商务白样式配置
st.set_page_config(page_title="Global UGC Insight Radar", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #333333; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px;}
    h1, h2, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    .stMetric { background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 10px; }
    div.stButton > button:first-child { background-color: #0052d4; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球海外用户真实口碑 (UGC) BI 看板")
st.caption("定位：产品营销辅助系统 - 穿透媒体通稿，直击海外社群真实痛点")
st.markdown("---")

# 2. 搜索模块优化
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        # 修改了提示语，引导输入全称
        target = st.text_input("🔍 输入监测机型 (💡出海提示：海外用户多用全称，请搜 'vivo X300 Ultra' 而非 'X300u')", "vivo X300 Ultra")
    with col_btn:
        st.write(" ")
        run_btn = st.button("挖掘海外真实评论", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在突破海外防火墙，提取真实 UGC...'):
        try:
            # 核心变动：去掉了严格的双引号，允许搜索引擎利用 NLP 模糊匹配，但依然死死限制在 Reddit 站内
            query = f'site:reddit.com {target}'
            
            # 使用 DDGS 库获取数据
            results = DDGS().text(query, max_results=40)
            
            raw_data = []
            all_text = ""
            
            for r in results:
                title = r.get('title', '')
                link = r.get('href', '#')
                body = r.get('body', '')
                
                # 提取 Reddit 版块
                sub_match = re.search(r'reddit\.com/r/([^/]+)', link)
                subreddit = f"r/{sub_match.group(1)}" if sub_match else "Reddit General"
                
                raw_data.append({
                    "社区版块": subreddit,
                    "讨论摘要": body[:150] + "..." if len(body) > 150 else body,
                    "跳转原文": link
                })
                all_text += " " + title.lower() + " " + body.lower()
            
            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 3. 核心 KPI ---
                m1, m2, m3 = st.columns(3)
                m1.metric("挖掘到 UGC 讨论数", f"{len(df)} 条", "来自真实海外论坛")
                m2.metric("核心发声阵地", df['社区版块'].mode()[0] if not df.empty else "N/A")
                m3.metric("爬虫状态", "成功直连 (Bypassed)")

                # --- 4. 痛点挖掘 ---
                st.markdown('<div class="report-card"><h3>📊 海外用户最关心的功能/情绪点</h3></div>', unsafe_allow_html=True)
                
                words = re.findall(r'\w+', all_text)
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'from', 'this', 'that', 'over', 'says', 'but', 'are', 'just', 'like', 'have', 'has', 'not', 'was', 'reddit', 'comments', 'you', 'can', 'will', 'about', 'they', 'what'}
                search_terms = set(target.lower().split())
                final_stop_words = stop_words.union(search_terms)
                
                filtered_words = [w for w in words if len(w) > 3 and w not in final_stop_words]
                word_counts = Counter(filtered_words).most_common(12)
                word_df = pd.DataFrame(word_counts, columns=['功能/参数/情绪', '提及频次'])

                c1, c2 = st.columns([1, 1])
                with c1:
                    fig_bar = px.bar(word_df, x='提及频次', y='功能/参数/情绪', orientation='h',
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
                st.markdown('<div class="report-card"><h3>🔗 海外社群原声清单与追溯</h3></div>', unsafe_allow_html=True)
                
                c3, c4 = st.columns([1, 1.5])
                with c3:
                    sub_df = df['社区版块'].value_counts().reset_index()
                    sub_df.columns = ['社区版块', '帖子数量']
                    fig_pie = px.pie(sub_df, values='帖子数量', names='社区版块', hole=0.4, template="plotly_white")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c4:
                    st.markdown("💬 **实时网友发帖清单 (点击直达海外社区):**")
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        column_config={
                            "跳转原文": st.column_config.LinkColumn(
                                "🚀 直达链接",
                                help="点击跳转至 Reddit 原帖",
                                display_text="去看看"
                            )
                        },
                        hide_index=True
                    )

            else:
                st.warning(f"暂未抓取到关于 '{target}' 的有效数据。请检查拼写，或尝试使用更完整的国际版产品名称。")
                
        except Exception as e:
            st.error(f"引擎提取失败，可能是当前网络请求过频，请稍等片刻后重试。错误信息: {e}")

st.markdown("---")
st.caption("Global UGC Insight System v4.1 | 搜索逻辑优化版 | Powered by Real Community Data")
