import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

st.set_page_config(page_title="Global Insight Radar", layout="wide")
st.title("🌍 全球产品口碑雷达 (无需 API 版)")

# 模拟浏览器请求头，防止被拦截
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

keyword = st.text_input("输入要监测的海外关键词 (建议加 site:reddit.com)", "vivo X100 Pro site:reddit.com")

if st.button("开始实时抓取"):
    with st.spinner('正在分析海外社群公开讨论...'):
        # 构造搜索 URL (这里以 Google 搜索 Reddit 讨论为例)
        search_url = f"https://www.google.com/search?q={keyword}"
        
        try:
            response = requests.get(search_url, headers=HEADERS)
            soup = BeautifulSoup(response.text, "html.parser")
            
            results = []
            # 抓取 Google 搜索结果的标题和摘要
            for g in soup.find_all('div', class_='tF2Cxc'):
                title = g.find('h3').text if g.find('h3') else "No Title"
                snippet = g.find('div', class_='VwiC3b').text if g.find('div', class_='VwiC3b') else "No Snippet"
                link = g.find('a')['href'] if g.find('a') else ""
                
                results.append({"Title": title, "Snippet": snippet, "Link": link})
            
            if results:
                df = pd.DataFrame(results)
                st.success(f"已抓取到 {len(results)} 条最新的海外讨论！")
                st.dataframe(df, use_container_width=True)
                
                # --- 出海营销洞察分析 ---
                st.subheader("📊 营销运营建议 (Localization Focus)")
                
                # 简单的情感关键词逻辑
                all_text = " ".join(df['Snippet'].tolist()).lower()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**核心痛点关键词：**")
                    if "software" in all_text or "os" in all_text:
                        st.warning("- 系统体验 (Software/OS): 提及率高，需关注系统纯净度。")
                    if "price" in all_text or "expensive" in all_text:
                        st.warning("- 价格敏感度 (Pricing): 用户对定价策略有讨论。")
                
                with col2:
                    st.write("**核心优势关键词：**")
                    if "camera" in all_text or "lens" in all_text:
                        st.success("- 影像表现 (Camera): 确认为海外核心竞争力。")
            else:
                st.warning("暂未抓取到有效结果，请稍后再试或更换关键词。")
                
        except Exception as e:
            st.error(f"抓取失败: {e}")

st.markdown("---")
st.caption("注：本项目仅抓取公开搜索结果，符合个人学习及研究用途。")
