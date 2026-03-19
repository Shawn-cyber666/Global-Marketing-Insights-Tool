# --- 核心数据抓取逻辑 (针对链接显示进行了暴力修复) ---
            for item in items[:60]:
                title = item.title.text if item.title else ""
                
                # 严格匹配逻辑
                if target_clean not in title.lower():
                    continue
                
                source = item.source.text if item.source else "Global Reviewer"
                
                # 【关键修复点】：强制获取 link 标签的内容，并确保它是干净的字符串
                # 兼容不同版本的 RSS 结构
                raw_link = ""
                if item.find('link'):
                    raw_link = item.find('link').get_text()
                elif item.link:
                    raw_link = item.link
                
                link_str = str(raw_link).strip()
                
                # 如果链接还是抓不到，尝试从 description 中提取（兜底方案）
                if not link_str.startswith("http"):
                    link_str = "#"

                pub_date = item.pubDate.text if item.pubDate else "Recent"
                
                raw_data.append({
                    "发布时间": pub_date,
                    "KOL/媒体来源": source,
                    "核心评测标题": title,
                    "跳转原文": link_str # 确保这里存入的是 100% 的 URL 字符串
                })
                all_text += " " + title.lower()
            
            if raw_data:
                df = pd.DataFrame(raw_data)

                # --- 数据显示部分 (LinkColumn 优化) ---
                st.markdown("💬 **深度评测直达清单 (点击 '去看看' 即可跳转):**")
                st.dataframe(
                    df, 
                    use_container_width=True,
                    column_config={
                        "跳转原文": st.column_config.LinkColumn(
                            "🚀 直达链接",
                            help="点击跳转至原评测网页",
                            display_text="去看看" # 这里会把 URL 隐藏，显示为按钮文字
                        )
                    },
                    hide_index=True
                )
