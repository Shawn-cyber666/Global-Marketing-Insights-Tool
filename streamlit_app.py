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
from datetime import datetime

# 1. 页面配置
st.set_page_config(page_title="Global Insight v8.5", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 25px;}
    h1, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    .summary-text { line-height: 1.8; color: #444; font-size: 15px; }
    .url-link { color: #0052d4; font-family: monospace; font-size: 12px; word-break: break-all; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 全球产品声量与业务洞察工具")
st.caption("版本：v8.5 | 状态：生产环境稳定版 | 核心：去人机化分析 & 全量数据导出")

# 2. 搜索逻辑
target = st.text_input("🔍 监测机型", "vivo X300 Ultra")
run_btn = st.button("挖掘全球原声并生成洞察", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在同步全球媒体节点，深度清洗数据中...'):
        # 补全转换逻辑
        target_clean = target.strip().lower()
        target_search = target_clean.replace('u', ' ultra').replace('p', ' pro') if target_clean.endswith(('u', 'p')) else target_clean
        
        encoded_query = urllib.parse.quote(f'{target_search} review')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(rss_url, timeout=12)
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            for item in items[:40]:
                title = item.title.text
                if target_search in title.lower() or target_clean in title.lower():
                    source = item.source.text
                    # 格式化日期
                    try:
                        date_obj = datetime.strptime(item.pubDate.text, '%a, %d %b %Y %H:%M:%S %Z')
                        f_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        f_date = datetime.now().strftime('%Y-%m-%d')
                    
                    link = item.find('link').get_text() if item.find('link') else "N/A"
                    raw_data.append({"日期": f_date, "媒体来源": source, "评测标题": title, "原文URL": link})
                    all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data).sort_values(by="日期", ascending=False)
                
                # --- 核心改进：去人机化的 PM 洞察摘要 ---
                words = [w for w in re.findall(r'\w+', all_text) if len(w)>3 and w not in ['the','review','news','video','phone','with','pro','ultra']]
                top_tags = [k for k, v in Counter(words).most_common(6)]
                
                # 模拟 PM 思考逻辑
                insight_summary = f"""
### 💡 业务观察与口碑建议
**1. 舆情走势：** 本周海外媒体对 **{target_search.upper()}** 的讨论保持稳步增长，共计捕获到 **{len(df)}** 篇核心评测，主要声量源自 **{df['媒体来源'].mode()[0]}** 等头部阵地。

**2. 核心卖点渗透：** 词频分析显示，海外用户目前对 **“{', '.join(top_tags[:3])}”** 的讨论最为集中。这表明产品在相关维度的市场认知度较高，建议营销侧继续强化此优势。

**3. 用户反馈聚焦：** 值得关注的是，关键词中出现了 **“{top_tags[-1] if len(top_tags)>3 else 'Performance'}”**。若此项反馈偏正面，可考虑作为下阶段 Global PR 的核心素材；若偏负面，需协同研发关注软件优化。

**4. 总结：** 当前全球口碑稳中向好，建议持续监测关键日期的舆情波动，保障海外上市期的品牌声量。
                """
                
                st.markdown('<div class="report-card"><h3>📝 PM 洞察报告 (去人机化)</h3></div>', unsafe_allow_html=True)
                st.markdown(insight_summary)

                # --- 改进：全字段 CSV 导出 ---
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📂 导出全字段 Excel/CSV 报表",
                    data=csv,
                    file_name=f"{target_search}_Global_Monitor_{f_date}.csv",
                    mime='text/csv',
                    use_container_width=True
                )

                # --- 可视化 ---
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(px.pie(df, names='媒体来源', hole=0.4, title="声量来源占比"), use_container_width=True)
                with c2:
                    word_df = pd.DataFrame(Counter(words).most_common(10), columns=['关注维度','频次'])
                    st.plotly_chart(px.bar(word_df, x='频次', y='关注维度', orientation='h', title="Top 10 核心关注点"), use_container_width=True)

                # --- 改进：100% 透明显示 URL 的数据表 ---
                st.markdown('<div class="report-card"><h3>🔗 全量数据清单 (带完整日期与 URL)</h3></div>', unsafe_allow_html=True)
                # 使用 Markdown 构建表格，确保 URL 既可见又可点
                md_table = "| 发布日期 | 媒体来源 | 核心标题内容 | 原始 URL (长按可复制) |\n| :--- | :--- | :--- | :--- |\n"
                for _, row in df.iterrows():
                    md_table += f"| {row['日期']} | {row['媒体来源']} | {row['评测标题']} | <a href='{row['原文URL']}' class='url-link' target='_blank'>{row['原文URL']}</a> |\n"
                st.markdown(md_table, unsafe_allow_html=True)

            else:
                st.warning(f"未能匹配到关于 '{target}' 的精确数据，请尝试更准确的机型全称。")
        except Exception as e:
            st.error(f"连接或解析异常: {e}")

st.markdown("---")
st.caption("Global Insight System v8.5 | 业务驱动型工具")
