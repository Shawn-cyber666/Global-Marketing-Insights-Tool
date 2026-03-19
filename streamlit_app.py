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

# 1. 页面基础配置：保持大厂专业审美
st.set_page_config(page_title="Global Insight v11.0", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 10px rgba(0,0,0,0.02); margin-bottom: 25px;}
    h1, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    .stDataFrame { border: 1px solid #e9ecef; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 侧边栏：多平台推送配置 (严谨版)
with st.sidebar:
    st.header("⚙️ 自动化推送配置")
    bot_platform = st.selectbox("选择目标群平台", ["飞书 (Feishu)", "v 消息 (vivo)", "企业微信", "钉钉"])
    webhook_url = st.text_input("机器人 Webhook 地址", 
                                value="https://open.feishu.cn/open-apis/bot/v2/hook/22b91725-268e-41f5-b647-5a33e2fc1188",
                                help="在群机器人设置中获取")
    
    st.divider()
    st.info("""
    **💡 推送成功指南：**
    1. **飞书**：后台安全设置请勾选**『自定义关键词』**，填入：**声量**。
    2. **v 消息**：直接粘贴 Webhook 即可。
    3. **签名校验**：请务必**取消勾选**后台的『签名校验』。
    """)

st.title("🛡️ 全球产品声量精准监测 & 自动化周报系统")
st.caption("版本：v11.0 究极版 | 集成飞书推送、全量可视化、专业报表导出")

# 3. 核心搜索模块
target = st.text_input("🔍 监测机型 (如: vivo X300 Ultra / OPPO Find X8)", "vivo X300 Ultra")
run_btn = st.button("开始挖掘并撰写报告", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在执行全球媒体索引，分析业务价值中...'):
        target_clean = target.strip().lower()
        target_search = target_clean.replace('u', ' ultra').replace('p', ' pro') if target_clean.endswith(('u', 'p')) else target_clean
        
        encoded_query = urllib.parse.quote(f'{target_search} review')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            # 强化版 XML 解析，确保不丢 URL
            response = requests.get(rss_url, timeout=12)
            soup = BeautifulSoup(response.content, "xml") 
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            
            for item in items[:40]:
                title = item.title.text if item.title else ""
                if target_search in title.lower() or target_clean in title.lower():
                    source = item.source.text if item.source else "Global Media"
                    
                    try:
                        date_obj = datetime.strptime(item.pubDate.text, '%a, %d %b %Y %H:%M:%S %Z')
                        f_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        f_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # 极严谨 URL 提取
                    link = item.link.text.strip() if item.link else ""
                    if not link or "http" not in link:
                        match = re.search(r'<link>(.*?)</link>', str(item))
                        link = match.group(1).strip() if match else "N/A"
                    
                    raw_data.append({"发布日期": f_date, "媒体来源": source, "核心标题内容": title, "原文URL": link})
                    all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data).sort_values(by="发布日期", ascending=False)
                
                # --- A. 撰写专业周报 (关键词“声量”置顶，适配飞书机器人) ---
                words = [w for w in re.findall(r'\w+', all_text) if len(w)>3 and w not in ['the','review','news','video','with','this']]
                top_tags = [k for k, v in Counter(words).most_common(5)]
                
                report_txt = f"【声量】{target_search.upper()} 海外声量洞察周报\n" \
                             f"━━━━━━━━━━━━━━\n" \
                             f"📊 捕获评测：{len(df)} 篇核心动态\n" \
                             f"📡 关键阵地：{df['媒体来源'].mode()[0]} 等主流媒体\n" \
                             f"🔥 关注焦点：# {' # '.join(top_tags)}\n\n" \
                             f"💡 业务建议：本周针对“{top_tags[0] if top_tags else '产品性能'}”讨论度高，建议 PR 侧强化素材传播。\n" \
                             f"━━━━━━━━━━━━━━\n" \
                             f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                st.markdown('<div class="report-card"><h3>📝 自动化洞察报告</h3></div>', unsafe_allow_html=True)
                st.code(report_txt, language="markdown")

                # --- B. 推送按钮 ---
                if st.button(f"🚀 推送报告至 {bot_platform} 群"):
                    if webhook_url:
                        try:
                            headers = {'Content-Type': 'application/json'}
                            if "飞书" in bot_platform:
                                payload = {"msg_type": "text", "content": {"text": report_txt}}
                            else:
                                payload = {"msgtype": "markdown", "markdown": {"content": report_txt}}
                            
                            res = requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=8)
                            res_json = res.json()
                            if res_json.get("code") == 0 or res_json.get("errcode") == 0:
                                st.success(f"✅ 成功推送到 {bot_platform} 群聊！")
                            else:
                                st.error(f"❌ 推送失败：{res_json.get('msg') or res_json.get('errmsg')}")
                        except Exception as e:
                            st.error(f"网络异常: {e}")
                    else:
                        st.warning("⚠️ 请先在侧边栏填写 Webhook 地址")

                # --- C. 完整报表导出 ---
                buffer = io.StringIO()
                buffer.write(f"--- 业务分析报告 ---\n{report_txt}\n\n--- 原始数据清单 ---\n")
                df.to_csv(buffer, index=False)
                st.download_button(
                    label="📂 点击下载：完整分析报表 (包含报告摘要及所有原文 URL)",
                    data=buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"{target_search}_周报_{f_date}.csv",
                    mime='text/csv',
                    use_container_width=True
                )

                # --- D. 可视化分析 ---
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(px.pie(df, names='媒体来源', hole=0.4, title="全球媒体声量占比"), use_container_width=True)
                with c2:
                    word_df = pd.DataFrame(Counter(words).most_common(10), columns=['维度','频次'])
                    st.plotly_chart(px.bar(word_df, x='频次', y='维度', orientation='h', title="Top 10 热议关键词"), use_container_width=True)

                # --- E. 全量数据清单 (修复 URL 隐藏问题) ---
                st.markdown('<div class="report-card"><h3>🔗 精准监测明细 (带原文原链)</h3></div>', unsafe_allow_html=True)
                st.dataframe(
                    df,
                    column_config={
                        "原文URL": st.column_config.LinkColumn("原文URL", width="large"),
                        "发布日期": st.column_config.TextColumn("发布日期", width="small")
                    },
                    hide_index=True,
                    use_container_width=True
                )

            else:
                st.warning("暂未发现匹配数据，请尝试更准确的机型名称。")
        except Exception as e:
            st.error(f"发生异常: {e}")

st.markdown("---")
st.caption("Global Marketing Insight System v11.0 | PA Data Platform")
