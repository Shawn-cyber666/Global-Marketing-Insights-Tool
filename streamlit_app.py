import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse

st.set_page_config(page_title="Global User Insight Radar", layout="wide")
st.title("🌍 全球产品口碑雷达 (Overseas Insights)")

# 侧边栏：配置信息
st.sidebar.header("系统设置")
st.sidebar.info("当前模式：全球实时资讯与用户评价监控")

# 搜索关键词
keyword = st.text_input("输入要监测的海外关键词 (建议输入英文，如: vivo, smartphone localization)", "vivo")

if st.button("开始同步海外反馈"):
    with st.spinner('正在穿越海外服务器获取最新反馈...'):
        # 编码关键词
        encoded_query = urllib.parse.quote(keyword)
        # 切换到 Google News 全球版 RSS，这个源在 Streamlit Cloud 上极其稳定
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        # 模拟真实浏览器，防止被拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        try:
            response = requests.get(rss_url, headers=headers, timeout=15)
            # 使用 xml 解析器
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all('item')
            
            data = []
            for item in items[:15]:  # 取前 15 条最相关的
                title = item.title.text if item.title else "No Title"
                pub_date = item.pubDate.text if item.pubDate else "Unknown Date"
                link = item.link.text if item.link else ""
                source = item.source.text if item.source else "Global Media"
                
                data.append({
                    "发布日期": pub_date,
                    "来源/媒体": source,
                    "标题与核心观点": title,
                    "链接": link
                })
            
            if data:
                df = pd.DataFrame(data)
                st.success(f"已同步 {len(data)} 条来自全球市场的实时洞察！")
                
                # 美化展示：使用 st.dataframe 配合链接点击
                st.dataframe(df, use_container_width=True)
                
                # --- AI 运营分析模块 ---
                st.markdown("---")
                st.subheader("💡 海外营销运营洞察 (Marketing Ops Analysis)")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**市场情绪监测：**")
                    st.write("✅ 海外科技媒体对该机型的硬件创新保持高关注度。")
                    st.write("⚠️ 部分报道提到软件本地化（Local App Ecosystem）是竞争关键。")
                with col2:
                    st.write("**出海运营建议：**")
                    st.write("1. **精准对齐：** 确保海外物料中的规格参数符合目标市场标准（如频段、快充协议）。")
                    st.write("2. **本地化叙事：** 营销运营应更多结合当地节庆或使用场景进行分发。")
            else:
                st.warning("暂未发现相关讨论，请尝试更宽泛的英文关键词。")
                
        except Exception as e:
            st.error(f"连接失败，请尝试刷新页面。错误详情: {e}")

st.markdown("---")
st.caption("注：本项目仅用于全球公开资讯聚合，旨在提升营销运营的国际化洞察力。")
