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

# 1. 页面基础配置
st.set_page_config(page_title="Global Insight v10.0", layout="wide")

# 自定义 UI 样式：大厂商务蓝风格
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .report-card { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 25px;}
    h1, h3 { color: #0052d4; font-family: 'Segoe UI', sans-serif; }
    .url-text { word-break: break-all; font-family: monospace; font-size: 12px; color: #0052d4; }
    .stDataFrame { border: 1px solid #e9ecef; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 侧边栏：多平台推送配置
with st.sidebar:
    st.header("⚙️ 自动化推送配置")
    bot_platform = st.selectbox("选择目标群平台", ["飞书 (Feishu)", "v 消息 (vivo)", "企业微信", "钉钉"])
    webhook_url = st.text_input("机器人 Webhook 地址", type="password", placeholder="https://open.feishu.cn/...")
    
    st.divider()
    st.markdown("""
    **💡 飞书推送提示：**
    1. 在飞书群设置 -> 机器人 -> 添加**自定义机器人**。
    2. 在安全设置中勾选**“自定义关键词”**。
    3. 关键词填入：**`声量`** (代码已内置匹配)。
    """)

st.title("🛡️ 全球产品声量精准监测 & 自动化周报系统")
st.caption("版本：v10.0 稳定版 | 适配飞书、v 消息 | 强化 URL 溯源")

# 3. 搜索与挖掘模块
target = st.text_input("🔍 监测机型 (如: vivo X300 Ultra / OPPO Find X8)", "vivo X300 Ultra")
run_btn = st.button("开始挖掘全球原声并生成洞察", use_container_width=True)

if run_btn:
    with st.spinner('🚀 正在执行全球媒体穿透索引，请稍候...'):
        # 关键词转换：处理 u/p 缩写
        target_clean = target.strip().lower()
        target_search = target_clean.replace('u', ' ultra').replace('p', ' pro') if target_clean.endswith(('u', 'p')) else target_clean
        
        # 构造 Google News RSS 链接
        encoded_query = urllib.parse.quote(f'{target_search} review')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            # 修复：强行使用 xml 解析，防止 URL 丢失
            response = requests.get(rss_url, timeout=12)
            soup = BeautifulSoup(response.content, "xml") 
            items = soup.find_all('item')
            
            raw_data = []
            all_text = ""
            
            for item in items[:40]:
                title = item.title.text if item.title else ""
                # 过滤不相关内容
                if target_search in title.lower() or target_clean in title.lower():
                    source = item.source.text if item.source else "Global Media"
                    
                    # 格式化日期
                    try:
                        date_obj = datetime.strptime(item.pubDate.text, '%a, %d %b %Y %H:%M:%S %Z')
                        f_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        f_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # 严谨提取 URL：xml解析 + 正则兜底
                    link = item.link.text.strip() if item.link else ""
                    if not link or "http" not in link:
                        # 尝试从原始字符串中强行扣取
                        match = re.search(r'<link>(.*?)</link>', str(item))
                        link = match.group(1).strip() if match else "N/A"
                    
                    raw_data.append({
                        "发布日期": f_date,
                        "媒体来源": source,
                        "核心标题内容": title,
                        "原文URL": link
                    })
                    all_text += " " + title.lower()

            if raw_data:
                df = pd.DataFrame(raw_data).sort_values(by="发布日期", ascending=False)
                
                # --- A. 生成业务洞察报告 (去人机化) ---
                words = [w for w in re.findall(r'\w+', all_text) if len(w)>3 and w not in ['the','review','news','video','with','from','this']]
                top_tags = [k for k, v in Counter(words).most_common(5)]
                
                report_txt = f"""
📢 【{target_search.upper()} 海外声量洞察周报】
━━━━━━━━━━━━━━
📅 监测周期：本周实时数据
📊 捕获评测：共计 {len(df)} 篇核心动态
📡 关键阵地：{df['媒体来源'].mode()[0]} 等主流渠道
🔥 关注焦点：# {' # '.join(top_tags)}

💡 业务建议：
本周海外媒体对“{top_tags[0] if top_tags else '产品性能'}”的渗透度显著。建议 PR 侧在后续推文中强化相关卖点的素材支撑，并关注评论区反馈。
━━━━━━━━━━━━━━
[数据由 PA 自动化监测工具生成]
                """
                
                st.markdown('<div class="report-card"><h3>📝 自动化洞察报告</h3></div>', unsafe_allow_html=True)
                st.code(report_txt, language="markdown")

                # --- B. 数据导出功能：报告+表格一体化 ---
                buffer = io.StringIO()
                buffer.write(f"--- 业务分析报告 ---\n{report_txt}\n\n--- 原始数据清单 ---\n")
                df.to_csv(buffer, index=False)
                
                st.download_button(
                    label="📂 导出完整报表 (包含报告摘要及所有 URL)",
                    data=buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"{target_search}_GlobalMonitor_{f_date}.csv",
                    mime='text/csv',
                    use_container_width=True
                )

                # --- C. 推送模块 (适配飞书/v消息) ---
                if st.button(f"🚀 推送报告至 {bot_platform} 群"):
                    if webhook_url:
                        try:
                            # 飞书格式解析
                            if "飞书" in bot_platform:
                                payload = {
                                    "msg_type": "text", 
                                    "content": {"text": report_txt}
                                }
                            else:
                                # v消息/企微/钉钉 Markdown格式
                                payload = {
                                    "msgtype": "markdown", 
                                    "markdown": {"content": report_txt}
                                }
                            
                            res = requests.post(webhook_url, json=payload, timeout=8)
                            res_json = res.json()
                            
                            # 检查接口返回状态
                            if res.status_code == 200 and (res_json.get("code") == 0 or res_json.get("errcode") == 0):
                                st.success(f"✅ 推送成功！请前往 {bot_platform} 群内查看。")
                            else:
                                error_info = res_json.get("msg") or res_json.get("errmsg") or "未知错误"
                                st.error(f"❌ 推送失败：{error_info}")
                                st.info("💡 请确认：1. Webhook 地址正确；2. 飞书机器人安全设置已添加关键词『声量』。")
                        except Exception as e:
                            st.error(f"网络连接异常: {e}")
                    else:
                        st.warning("⚠️ 请先在侧边栏填写 Webhook 地址")

                # --- D. 可视化分析 ---
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(px.pie(df, names='媒体来源', hole=0.4, title="全球媒体声量占比"), use_container_width=True)
                with c2:
                    word_df = pd.DataFrame(Counter(words).most_common(10), columns=['维度','频次'])
                    st.plotly_chart(px.bar(word_df, x='频次', y='维度', orientation='h', title="Top 10 热议关键词"), use_container_width=True)

                # --- E. 原始数据表 (强制显示 URL) ---
                st.markdown('<div class="report-card"><h3>🔗 精准监测清单 (包含完整原文 URL)</h3></div>', unsafe_allow_html=True)
                st.dataframe(
                    df,
                    column_config={
                        "原文URL": st.column_config.LinkColumn(
                            "原文URL",
                            help="点击直接跳转海外媒体原网页",
                            width="large"
                        ),
                        "发布日期": st.column_config.TextColumn("发布日期", width="small")
                    },
                    hide_index=True,
                    use_container_width=True
                )

            else:
                st.warning(f"未能挖掘到关于 '{target}' 的有效全球动态，请尝试更准确的机型名称。")
        except Exception as e:
            st.error(f"运行出错: {e}")
            st.info("提示: 如果报错找不到 xml，请在终端执行: pip install lxml")

st.markdown("---")
st.caption("Global Marketing Insight Platform v10.0 | vivo PA Efficiency Tool")
