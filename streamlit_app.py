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
import io

# 1. 页面配置
st.set_page_config(page_title="Global Insight v9.0", layout="wide")

# 自定义 CSS 确保 URL 强制显示不被截断
st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; margin-bottom: 20px;}
    .url-cell { word-break: break-all !important; white-space: normal !important; font-size: 11px; color: #0052d4; font-family: monospace; }
    h1, h3 { color: #0052d4; }
    </style>
    """, unsafe_allow_html=True)

# 2. 侧边栏：推送配置 (针对 v 消息/微信)
with st.sidebar:
    st.header("📲 内部推送配置")
    bot_platform = st.selectbox("推送平台", ["v 消息 (vivo)", "企业微信", "钉钉"])
    webhook_url = st.text_input("机器人 Webhook 地址", type="password", help="在群机器人设置中获取")
    st.divider()
    st.info("💡 配置后，点击下方生成的『推送到群』即可。")

st.title("🛡️ 全球产品声量精准监测 & 自动化周报系统")
st.caption("版本：v9.0 | 核心：报告+数据一体化导出 | 适配：v 消息推送")

# 3. 搜索与挖掘
target = st.text_input("🔍 监测机型 (如 x300u / vivo X100 Pro)", "vivo X300 Ultra")
run_btn = st.button("开始挖掘并撰写报告", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在索引全球节点并生成分析报告...'):
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
                    # 精确日期
                    try:
                        date_obj = datetime.strptime(item.pubDate.text, '%a, %d %b %Y %H:%M:%S %Z')
                        f_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        f_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # 彻底提取 URL
                    link = item.find('link').get_text() if item.find('link') else "N/A"
                    raw_data.append({"发布日期": f_date, "媒体来源": source, "核心标题内容": title, "原文URL": link})
                    all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data).sort_values(by="发布日期", ascending=False)
                
                # --- A. 撰写专业 PM 报告摘要 ---
                words = [w for w in re.findall(r'\w+', all_text) if len(w)>3 and w not in ['the','review','news','video','with']]
                top_tags = [k for k, v in Counter(words).most_common(5)]
                
                report_txt = f"""
📢 【{target_search.upper()} 海外声量洞察周报】
━━━━━━━━━━━━━━
1. 监测概览：本周共捕获全球精准评测/动态 {len(df)} 篇；
2. 核心阵地：声量主要集中于 {df['媒体来源'].mode()[0]} 等主流媒体；
3. 关键关注点：# {' # '.join(top_tags)}；
4. 业务建议：本周针对“{top_tags[0] if top_tags else '产品'}”的讨论较多，建议运营侧跟进相关卖点素材。
━━━━━━━━━━━━━━
数据生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
                """
                
                st.markdown('<div class="report-card"><h3>📝 自动化分析报告</h3></div>', unsafe_allow_html=True)
                st.code(report_txt, language="markdown")

                # --- B. 增强版导出：报告 + 完整数据 (包含 URL) ---
                # 将报告文本和表格合并为一个文件
                buffer = io.StringIO()
                buffer.write(f"--- 业务分析报告 ---\n{report_txt}\n\n--- 原始数据明细 ---\n")
                df.to_csv(buffer, index=False)
                
                st.download_button(
                    label="📂 点击下载：完整分析报表 (含报告及 URL 链接)",
                    data=buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"{target_search}_周报_{f_date}.csv",
                    mime='text/csv',
                    use_container_width=True
                )

                # --- C. 推送模块 ---
                if st.button(f"🚀 一键推送到 {bot_platform} 群"):
                    if webhook_url:
                        # 兼容 v 消息/微信/钉钉的 Markdown 推送
                        payload = {"msgtype": "markdown", "markdown": {"content": report_txt}}
                        try:
                            requests.post(webhook_url, json=payload, timeout=5)
                            st.success("✅ 推送成功！请在群内查收。")
                        except Exception as e:
                            st.error(f"推送失败: {e}")
                    else:
                        st.warning("请在侧边栏填写机器人 Webhook 地址")

                # --- D. 数据可视化 ---
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(px.pie(df, names='媒体来源', hole=0.4, title="媒体来源分布"), use_container_width=True)
                with c2:
                    st.plotly_chart(px.bar(pd.DataFrame(Counter(words).most_common(10), columns=['维度','频次']), x='频次', y='维度', orientation='h', title="热点维度排行"), use_container_width=True)

                # --- E. 原始数据清单 (使用 Markdown 确保 URL 绝对可见) ---
                st.markdown('<div class="report-card"><h3>🔗 原始监测明细 (带 URL 原链)</h3></div>', unsafe_allow_html=True)
                # 构造 HTML 表格以获得极致展示效果
                html_table = "<table style='width:100%; border-collapse: collapse; font-size:13px;'>"
                html_table += "<tr><th>日期</th><th>来源</th><th>标题</th><th>URL</th></tr>"
                for _, row in df.iterrows():
                    html_table += f"<tr><td>{row['发布日期']}</td><td>{row['媒体来源']}</td><td>{row['核心标题内容']}</td><td class='url-cell'>{row['原文URL']}</td></tr>"
                html_table += "</table>"
                st.markdown(html_table, unsafe_allow_html=True)

            else:
                st.warning("暂未发现匹配数据，请尝试更精确的名称。")
        except Exception as e:
            st.error(f"连接异常: {e}")

st.markdown("---")
st.caption("Global Marketing Insight System v9.0 | vivo PA Edition")
