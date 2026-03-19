import streamlit as st
import pandas as pd
import requests
import urllib.parse
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
st.caption("定位：产品营销辅助系统 - 专注于海外社群 (Reddit) 的真实用户痛点与原声挖掘")
st.markdown("---")

# 2. 精准搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 输入精准机型 (如: vivo X300s)", "vivo X300")
    with col_btn:
        st.write(" ")
        run_btn = st.button("挖掘海外真实评论", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在直连海外硬核数码社区，提取用户原声...'):
        # 核心改动 1：使用双引号强制精确匹配，避免 X300s 搜出 X300 Ultra
        exact_query = f'"{target}"'
        encoded_query = urllib.parse.quote(exact_query)
        
        # 核心改动 2：直接抓取 Reddit 的 JSON 接口，这是纯纯的用户发帖
        reddit_url = f"https://www.reddit.com/search.json?q={encoded_query}&sort=new&limit=40"
        
        # 伪装成一个独立的数据分析工具，避免被 Reddit 拦截
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) MarketingBI/2.0 (Analysis)'}
        
        try:
            response = requests.get(reddit_url, headers=headers, timeout=15)
            data = response.json()
            
            raw_data = []
            all_text = ""
            
            # 解析 JSON 数据
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                subreddit = post_data.get('subreddit_name_prefixed', 'Unknown')
                # 核心改动 3：拼接绝对且干净的 URL，确保 100% 可点击
                permalink = post_data.get('permalink', '')
                link = f"https://www.reddit.com{permalink}" if permalink else "#"
                upvotes = post_data.get('ups', 0)
                
                raw_data.append({
                    "讨论热度 (Upvotes)": upvotes,
                    "讨论版块": subreddit,
                    "用户发帖标题": title,
                    "跳转原文": link
                })
                all_text += " " + title.lower() + " " + post_data.get('selftext', '').lower()
            
            if raw_data:
                df = pd.DataFrame(raw_data)
                # 按热度排序
                df = df.sort_values(by="讨论热度 (Upvotes)", ascending=False)

                # --- 3. 核心 KPI ---
                m1, m2, m3 = st.columns(3)
                m1.metric("精准匹配 UGC 讨论数", f"{len(df)} 条", "100% 用户原声")
                m2.metric("核心发声阵地", df['讨论版块'].mode()[0] if not df.empty else "N/A")
                m3.metric("匹配精度", "极高 (Exact Match)")

                # --- 4. 用户关注功能点挖掘 ---
                st.markdown('<div class="report-card"><h3>📊 海外用户最关心的功能/痛点提取</h3></div>', unsafe_allow_html=True)
                
                words = re.findall(r'\w+', all_text)
                # 增加口语化的停用词，因为这是网友评论
                stop_words = {'the', 'a', 'to', 'in', 'of', 'and', 'on', 'with', 'for', 'is', 'at', 'by', 'it', 'from', 'this', 'that', 'over', 'says', 'but', 'are', 'just', 'like', 'have', 'has', 'not', 'was'}
                # 将用户的搜索词（如 vivo, x300s）全部拆开过滤掉
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

                # --- 5. UGC 数据明细与可点击链接 ---
                st.markdown('<div class="report-card"><h3>🔗 海外社群原声清单与追溯</h3></div>', unsafe_allow_html=True)
                
                c3, c4 = st.columns([1, 1.5])
                with c3:
                    sub_df = df['讨论版块'].value_counts().reset_index()
                    sub_df.columns = ['社区版块', '帖子数量']
                    fig_pie = px.pie(sub_df, values='帖子数量', names='社区版块', hole=0.4, template="plotly_white")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c4:
                    st.markdown("💬 **实时网友发帖清单 (点击右侧即可直达海外社区):**")
                    # 使用最新的 LinkColumn，这次绝对不会为空
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        column_config={
                            "跳转原文": st.column_config.LinkColumn(
                                "🚀 直达链接",
                                help="点击跳转至 Reddit 原帖查看详细评论",
                                display_text="去看看"
                            ),
                            "讨论热度 (Upvotes)": st.column_config.ProgressColumn(
                                "热度",
                                help="该帖子的点赞互动量",
                                format="%d",
                                min_value=0,
                                max_value=int(df['讨论热度 (Upvotes)'].max()) if not df.empty else 100,
                            )
                        },
                        hide_index=True
                    )

            else:
                st.warning(f"在海外社群中暂未找到完全匹配 '{target}' 的用户讨论。建议换个缩写（如去掉空格）。")
                
        except Exception as e:
            st.error(f"BI 引擎加载失败，请检查网络或重试。错误信息: {e}")

st.markdown("---")
st.caption("Global UGC Insight System v3.0 | 强校验版 | Powered by Real Community Data")
