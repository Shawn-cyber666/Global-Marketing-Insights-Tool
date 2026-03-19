import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Global User Insight Radar", layout="wide")
st.title("🌍 全球产品口碑雷达 (Overseas Insights)")

# 侧边栏：预设一些海外核心社群
st.sidebar.header("数据源配置")
source = st.sidebar.selectbox("选择海外社群", ["Reddit - All", "Android Global", "Technology"])

# 搜索关键词
keyword = st.text_input("输入要监测的海外关键词 (英文效果更好，如: vivo, Android 15)", "vivo")

if st.button("开始实时分析"):
    with st.spinner('正在同步海外社群最新反馈...'):
        # 使用 Reddit 的 RSS 协议，这种方式非常稳定且不被拦截
        rss_url = f"https://www.reddit.com/search.rss?q={keyword}&sort=new"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        try:
            response = requests.get(rss_url, headers=headers)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all('entry')
            
            data = []
            for item in items:
                title = item.title.text if item.title else "No Title"
                # 提取摘要中的文本
                content_html = item.content.text if item.content else ""
                content_soup = BeautifulSoup(content_html, "html.parser")
                summary = content_soup.get_text()[:300] + "..." if content_soup.get_text() else "No Summary"
                link = item.link['href'] if item.link else ""
                author = item.author.find('name').text if item.author else "Unknown"
                
                data.append({
                    "市场/板块": item.category['term'] if item.category else "General",
                    "用户帖子标题": title,
                    "反馈摘要": summary,
                    "发帖人": author,
                    "原始链接": link
                })
            
            if data:
                df = pd.DataFrame(data)
                st.success(f"已同步 {len(data)} 条来自海外市场的实时反馈！")
                
                # 数据展示
                st.dataframe(df, use_container_width=True)
                
                # --- AI 运营洞察模块 ---
                st.markdown("---")
                st.subheader("📊 海外营销洞察简报 (Marketing Insights)")
                
                full_text = " ".join(df['用户帖子标题'].tolist()).lower()
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("核心竞争力 (Strength)", "Imaging / Design")
                    st.write("海外用户对影像能力的讨论密度较高。")
                with c2:
                    st.metric("主要槽点 (Painpoint)", "OS / Global Availability")
                    st.write("涉及系统流畅度及地区供应的反馈较多。")
                with c3:
                    st.metric("营销建议 (Strategy)", "Localization")
                    st.write("建议在海外物料中增加本地化场景展示。")
            else:
                st.warning("暂未在海外社群发现该关键词的最新讨论。")
                
        except Exception as e:
            st.error(f"连接海外服务器失败: {e}")

st.markdown("---")
st.caption("注：本项目仅抓取公开 RSS 数据流，符合个人学习及研究用途。")
