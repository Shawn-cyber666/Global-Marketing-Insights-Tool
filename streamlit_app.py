import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import plotly.express as px
from collections import Counter
import re
from datetime import datetime
import io
import json

# 1. 页面配置
st.set_page_config(page_title="Global Insight v12.0", layout="wide")

st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 10px rgba(0,0,0,0.02); margin-bottom: 25px;}
    h1, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 2. 情绪分析核心逻辑 (PA 业务引擎)
def analyze_sentiment(title):
    title = title.lower()
    pos_words = ['great', 'amazing', 'best', 'beast', 'king', 'excellent', 'impressive', 'pro', 'love', 'fantastic', 'top', 'worth']
    neg_words = ['bad', 'disappointing', 'issue', 'problem', 'fail', 'worst', 'expensive', 'not worth', 'poor', 'leak', 'hot', 'bug']
    
    score = 0
    for w in pos_words:
        if w in title: score += 1
    for w in neg_words:
        if w in title: score -= 1
        
    if score > 0: return "🟢 Positive (正面)"
    elif score < 0: return "🔴 Negative (负面)"
    else: return "🟡 Neutral (中立/客观)"

# 3. 侧边栏
with st.sidebar:
    st.header("⚙️ 系统配置")
    bot_platform = st.selectbox("推送平台 (备选)", ["飞书 (Feishu)", "v 消息 (vivo)", "企业微信", "钉钉"])
    webhook_url = st.text_input("Webhook 地址", value="https://open.feishu.cn/...")
    st.divider()
    st.info("💡 情绪分析基于标题关键词自动识别，建议作为口碑参考。")

st.title("🛡️ 全球产品声量精准监测 & 舆情情绪分析系统")
st.caption("版本：v12.0 | 核心：自动情绪定性 | 适配：vivo PA 全球业务")

# 4. 搜索模块
target = st.text_input("🔍 监测机型", "vivo X300 Ultra")
run_btn = st.button("开始挖掘并分析全球情绪", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在执行全球媒体索引，并进行 AI 情绪定性...'):
        target_clean = target.strip().lower()
        target_search = target_clean.replace('u', ' ultra').replace('p', ' pro') if target_clean.endswith(('u', 'p')) else target_clean
        
        encoded_query = urllib.parse.quote(f'{target_search} review')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(rss_url, timeout=12)
            soup = BeautifulSoup(response.content, "xml") 
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            
            for item in items[:40]:
                title = item.title.text if item.title else ""
                if target_search in title.lower() or target_clean in title.lower():
                    source = item.source.text if item.source else "Media"
                    f_date = datetime.now().strftime('%Y-%m-%d')
                    link = item.link.text.strip() if item.link else "N/A"
                    
                    # 注入情绪分析
                    sentiment = analyze_sentiment(title)
                    
                    raw_data.append({
                        "发布日期": f_date, 
                        "媒体来源": source, 
                        "核心标题内容": title, 
                        "舆情情绪": sentiment,
                        "原文URL": link
                    })
                    all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data).sort_values(by="发布日期", ascending=False)
                
                # --- A. 撰写专业周报 (加入情绪汇总) ---
                words = [w for w in re.findall(r'\w+', all_text) if len(w)>3 and w not in ['the','review','news','video','with']]
                top_tags = [k for k, v in Counter(words).most_common(5)]
                sentiment_counts = df['舆情情绪'].value_counts()
                top_sentiment = sentiment_counts.index[0]
                
                report_txt = f"【声量】{target_search.upper()} 全球舆情周报\n" \
                             f"━━━━━━━━━━━━━━\n" \
                             f"📊 动态规模：本周共监测到 {len(df)} 篇核心报道\n" \
                             f"🌈 情绪基调：主要以 {top_sentiment} 为主\n" \
                             f"📡 重点媒体：{df['媒体来源'].mode()[0]}\n" \
                             f"🔥 讨论热点：# {' # '.join(top_tags)}\n\n" \
                             f"💡 PA 建议：海外整体口碑趋于{top_sentiment[3:5]}。针对热词“{top_tags[0]}”，建议研发/传播侧保持关注。\n" \
                             f"━━━━━━━━━━━━━━\n" \
                             f"自动化洞察生成于：{datetime.now().strftime('%m-%d %H:%M')}"
                
                st.markdown('<div class="report-card"><h3>📝 自动化洞察报告 (含情绪定性)</h3></div>', unsafe_allow_html=True)
                st.code(report_txt)

                # --- B. 数据导出 ---
                buffer = io.StringIO()
                buffer.write(f"--- 业务分析报告 ---\n{report_txt}\n\n--- 原始数据明细 ---\n")
                df.to_csv(buffer, index=False)
                st.download_button("📂 下载完整洞察报表 (含情绪标签及URL)", buffer.getvalue().encode('utf-8-sig'), f"{target_search}_Report.csv", use_container_width=True)

                # --- C. 可视化模块 (新增情绪饼图) ---
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.plotly_chart(px.pie(df, names='舆情情绪', title="全球舆情色彩分布", color='舆情情绪', 
                                         color_discrete_map={"🟢 Positive (正面)":"#2ecc71", "🟡 Neutral (中立/客观)":"#f1c40f", "🔴 Negative (负面)":"#e74c3c"}), use_container_width=True)
                with col2:
                    st.plotly_chart(px.pie(df, names='媒体来源', hole=0.3, title="声量阵地分布"), use_container_width=True)
                with col3:
                    word_df = pd.DataFrame(Counter(words).most_common(10), columns=['关注点','频次'])
                    st.plotly_chart(px.bar(word_df, x='频次', y='关注点', orientation='h', title="核心关注点 Top 10"), use_container_width=True)

                # --- D. 全量明细表 ---
                st.markdown('<div class="report-card"><h3>🔗 精准监测清单 (已打情绪标签)</h3></div>', unsafe_allow_html=True)
                st.dataframe(
                    df,
                    column_config={
                        "原文URL": st.column_config.LinkColumn("原文URL", width="large"),
                        "舆情情绪": st.column_config.TextColumn("舆情倾向", width="medium")
                    },
                    hide_index=True,
                    use_container_width=True
                )

            else:
                st.warning("未匹配到相关动态。")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.caption("Global Insight System v12.0 | PA Analysis Hub")
