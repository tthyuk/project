import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import json

# 데이터 로딩
shop_df = pd.read_csv("서울시 상권분석서비스(점포-행정동).csv", encoding='euc-kr')
pop_df = pd.read_csv("서울시 상권분석서비스(길단위인구-행정동).csv", encoding='euc-kr')

with open("서울시 상권분석서비스(영역-행정동).json", encoding="utf-8") as f:
    geo_data = json.load(f)

geo_df = pd.DataFrame(geo_data["DATA"])
geo_df["lat"] = geo_df["ydnts_value"] / 10000  # 좌표 변환
geo_df["lon"] = geo_df["xcnts_value"] / 10000

# 치킨 전문점만 필터
chicken_df = shop_df[shop_df["상권업종중분류명"].str.contains("치킨", na=False)]

# Streamlit UI
st.title("서울시 행정동별 치킨집 수 vs 인구 비교")

# 지도 생성
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 지도에 행정동 마커 추가
for _, row in geo_df.iterrows():
    dong_name = row["adstrd_nm"]
    lat = row["lat"]
    lon = row["lon"]
    folium.Marker(
        [lat, lon],
        popup=dong_name,
        tooltip=dong_name
    ).add_to(m)

# 지도 표시
map_data = st_folium(m, width=700, height=500)

# 지도에서 선택된 행정동 이름 가져오기
selected_dong = None
if map_data and map_data.get("last_object_clicked_tooltip"):
    selected_dong = map_data["last_object_clicked_tooltip"]

if selected_dong:
    st.subheader(f"선택된 행정동: {selected_dong}")

    # 치킨집 수 계산
    chicken_count = chicken_df[chicken_df["행정동명"] == selected_dong].shape[0]

    # 인구 수 계산
    pop_count = pop_df[pop_df["행정동명"] == selected_dong]["총생활인구수"].sum()

    # 시각화
    st.write(f"치킨집 수: {chicken_count}")
    st.write(f"총 생활인구수: {pop_count}")
    fig, ax = plt.subplots()
    ax.bar(["치킨집 수", "인구 수"], [chicken_count, pop_count], color=["orange", "skyblue"])
    st.pyplot(fig)
else:
    st.info("지도의 마커를 클릭하여 행정동을 선택하세요.")
