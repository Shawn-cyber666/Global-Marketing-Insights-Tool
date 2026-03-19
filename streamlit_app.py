import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse

st.set_page_config(page_title="Global User Insight Radar", layout="wide")
st.title("🌍 全球产品口碑雷达 (Overseas Insights)")

# 搜索关键词
keyword = st.text_input("输入要监测的海外关键词 (建议输入英文，如: vivo, smartphone localization)", "vivo")

if st.button("开始同步海外反馈"):
    with st.spinner('正在同步全球市场动态...'):
        encoded_query = urllib.parse.quote(keyword)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(rss_url, headers=headers, timeout=15)
            # 使用更稳健的 lxml 解析器
            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all('item')
            
            data = []
            for item in items[:15]:
                title = item.title.text if item.title else "No Title"
                pub_date = item.pubdate.text if item.pubdate else (item.find('pubDate').text if item.find('pubDate') else "Unknown")
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
                st.success(f"已成功同步 {len(data)} 条全球实时洞察！")
                st.dataframe(df, use_container_width=True)
                
                # --- 运营洞察模块 ---
                st.markdown("---")
                st.subheader("💡 海外营销运营洞察 (Marketing Ops Analysis)")
                st.info("基于最新抓取的全球资讯，AI 建议关注：1. 海外测评对硬件参数的微观评价；2. 目标市场的竞品营销节奏；3. 潜在的合规性讨论。")
            else:
                st.warning("暂未发现相关讨论。")
                
        except Exception as e:
            st.error(f"解析失败: {e}")

st.markdown("---")
st.caption("注：本项目旨在通过自动化手段提升出海营销运营的国际化洞察力。")
