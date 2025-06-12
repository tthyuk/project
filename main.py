import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import json

# --- 파일 로드 ---
@st.cache_data
def load_data():
    shop_df = pd.read_csv("서울시_점포.csv", encoding='euc-kr')
    pop_df = pd.read_csv("서울시_인구.csv", encoding='euc-kr')
    with open("서울시_행정동_중심좌표.json", encoding='utf-8') as f:
        geo_data = json.load(f)
    return shop_df, pop_df, geo_data

shop_df, pop_df, geo_data = load_data()

# --- JSON -> DataFrame ---
geo_df = pd.DataFrame(geo_data["DATA"])
geo_df["위도"] = geo_df["ydnts_value"] / 10000
geo_df["경도"] = geo_df["xcnts_value"] / 10000
geo_df["행정동명"] = geo_df["adstrd_nm"]

# --- 치킨 필터: '상호명'에 '치킨' 포함하는 점포 ---
if "상호명" in shop_df.columns:
    chicken_df = shop_df[shop_df["상호명"].str.contains("치킨", na=False)]
else:
    st.error("⚠ '상호명' 컬럼이 존재하지 않습니다.")
    st.stop()

# --- Streamlit UI ---
st.title("서울시 행정동별 치킨집 수 vs 길단위 인구수 비교")

# 지도 생성
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 마커 추가
for _, row in geo_df.iterrows():
    folium.Marker(
        [row["위도"], row["경도"]],
        tooltip=row["행정동명"],
        popup=row["행정동명"]
    ).add_to(m)

# 지도 출력
map_data = st_folium(m, width=700, height=500)
selected_dong = map_data.get("last_object_clicked_tooltip")

# 선택된 행정동 처리
if selected_dong:
    st.subheader(f"📍 선택한 행정동: {selected_dong}")

    chicken_count = chicken_df[chicken_df["행정동명"] == selected_dong].shape[0]
    pop_total = pop_df[pop_df["행정동명"] == selected_dong]["총생활인구수"].sum()

    st.markdown(f"- 치킨집 수: **{chicken_count} 개**")
    st.markdown(f"- 총 인구 수: **{pop_total:,} 명**")

    # 시각화
    fig, ax = plt.subplots()
    ax.bar(["치킨집 수", "인구 수"], [chicken_count, pop_total], color=["orange", "skyblue"])
    ax.set_ylabel("수")
    st.pyplot(fig)
else:
    st.info("🗺 지도에서 행정동 마커를 클릭하세요.")
