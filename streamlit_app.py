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
st.set_page_config(page_title="Global Insight v9.1", layout="wide")

st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; margin-bottom: 20px;}
    h1, h3 { color: #0052d4; }
    </style>
    """, unsafe_allow_html=True)

# 2. 侧边栏：推送配置 (新增飞书)
with st.sidebar:
    st.header("📲 内部推送配置")
    bot_platform = st.selectbox("推送平台", ["v 消息 (vivo)", "企业微信", "钉钉", "飞书"])
    webhook_url = st.text_input("机器人 Webhook 地址", type="password", help="在群机器人设置中获取")
    st.divider()
    st.info("💡 提示：飞书机器人需在群设置添加，支持纯文本一键推送。")

st.title("🛡️ 全球产品声量精准监测 & 自动化周报系统")
st.caption("版本：v9.1 | 核心：URL 严谨提取 | 适配：飞书 / v 消息全平台")

# 3. 搜索模块
with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        target = st.text_input("🔍 监测机型 (如 x300u / vivo X100 Pro)", "vivo X300 Ultra")
    with col_btn:
        st.write(" ")
        run_btn = st.button("开始挖掘并撰写报告", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在索引全球节点并生成分析报告...'):
        target_clean = target.strip().lower()
        target_search = target_clean.replace('u', ' ultra').replace('p', ' pro') if target_clean.endswith(('u', 'p')) else target_clean
        
        encoded_query = urllib.parse.quote(f'{target_search} review')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            # 修复点 1：明确使用 xml 解析引擎，防止标签丢失
            response = requests.get(rss_url, timeout=12)
            soup = BeautifulSoup(response.content, "xml") 
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            for item in items[:40]:
                title = item.title.text if item.title else ""
                if target_search in title.lower() or target_clean in title.lower():
                    source = item.source.text if item.source else "媒体节点"
                    
                    try:
                        date_obj = datetime.strptime(item.pubDate.text, '%a, %d %b %Y %H:%M:%S %Z')
                        f_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        f_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # 修复点 2：极其严谨的 URL 提取逻辑 (含正则兜底)
                    link = item.link.text.strip() if item.link else ""
                    if not link or "http" not in link:
                        match = re.search(r'<link>(.*?)</link>', str(item))
                        link = match.group(1).strip() if match else "N/A"
                    
                    raw_data.append({"发布日期": f_date, "媒体来源": source, "核心标题内容": title, "原文URL": link})
                    all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data).sort_values(by="发布日期", ascending=False)
                
                # --- A. 撰写专业 PM 报告摘要 ---
                words = [w for w in re.findall(r'\w+', all_text) if len(w)>3 and w not in ['the','review','news','video','with','this']]
                top_tags = [k for k, v in Counter(words).most_common(5)]
                
                report_txt = f"""
📢 【{target_search.upper()} 海外声量洞察周报】
━━━━━━━━━━━━━━
1. 监测概览：本周共捕获全球精准评测/动态 {len(df)} 篇；
2. 核心阵地：声量主要集中于 {df['媒体来源'].mode()[0]} 等主流媒体；
3. 关键关注点：# {' # '.join(top_tags)}；
4. 业务建议：本周针对“{top_tags[0] if top_tags else '产品细节'}”的讨论较多，建议运营侧跟进相关卖点素材。
━━━━━━━━━━━━━━
数据生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
                """
                
                st.markdown('<div class="report-card"><h3>📝 自动化分析报告</h3></div>', unsafe_allow_html=True)
                st.text_area(label="报告文本 (可直接复制)", value=report_txt.strip(), height=220)

                # --- B. 增强版导出：报告 + 完整数据 ---
                buffer = io.StringIO()
                buffer.write(f"--- 业务分析报告 ---\n{report_txt}\n\n--- 原始数据明细 ---\n")
                df.to_csv(buffer, index=False)
                
                st.download_button(
                    label="📂 点击下载：完整分析报表 (含报告及带 URL 的完整数据)",
                    data=buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"{target_search}_全景洞察报表_{f_date}.csv",
                    mime='text/csv',
                    use_container_width=True
                )

                # --- C. 推送模块 (新增飞书支持) ---
                if st.button(f"🚀 一键推送到 {bot_platform} 群"):
                    if webhook_url:
                        try:
                            if bot_platform == "飞书":
                                payload = {"msg_type": "text", "content": {"text": report_txt}}
                            else:
                                # v 消息 / 企微 / 钉钉 通用 markdown
                                payload = {"msgtype": "markdown", "markdown": {"content": report_txt}}
                            
                            res = requests.post(webhook_url, json=payload, timeout=5)
                            if res.status_code == 200:
                                st.success(f"✅ 成功推送到 {bot_platform}！")
                            else:
                                st.error(f"推送返回异常状态码: {res.status_code}")
                        except Exception as e:
                            st.error(f"推送失败，请检查 Webhook 链接是否正确: {e}")
                    else:
                        st.warning("⚠️ 请先在左侧栏填写 Webhook 地址")

                # --- D. 数据可视化 ---
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(px.pie(df, names='媒体来源', hole=0.4, title="媒体来源分布"), use_container_width=True)
                with c2:
                    st.plotly_chart(px.bar(pd.DataFrame(Counter(words).most_common(10), columns=['维度','频次']), x='频次', y='维度', orientation='h', title="热点维度排行"), use_container_width=True)

                # --- E. 原始数据清单 (使用 Streamlit 原生 LinkColumn 组件修复 URL 隐藏问题) ---
                st.markdown('<div class="report-card"><h3>🔗 全量数据清单 (精准溯源)</h3></div>', unsafe_allow_html=True)
                
                # 修复点 3：利用 st.dataframe 强行规定原文 URL 的显示格式为“原样展示链接”
                st.dataframe(
                    df,
                    column_config={
                        "原文URL": st.column_config.LinkColumn(
                            "原文URL",
                            help="点击直接访问海外原报道",
                            max_chars=300,  # 允许展示超长 URL
                            display_text=None # 设定为 None 强制显示完整 URL，而不是显示图标
                        ),
                        "发布日期": st.column_config.TextColumn("发布日期", width="small")
                    },
                    hide_index=True,
                    use_container_width=True
                )

            else:
                st.warning("暂未发现匹配数据，请尝试更精确的名称。")
        except Exception as e:
            st.error(f"解析异常，请检查网络或依赖库: {e}\n提示: 确保已安装 lxml 库 (pip install lxml)")

st.markdown("---")
st.caption("Global Marketing Insight System v9.1 | PA Data Platform")
