import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 데이터 로드 (가상의 데이터 생성 또는 실제 파일 로드) ---

@st.cache_data
def load_data():
    # 실제 파일 경로로 변경해주세요.
    # df_store = pd.read_csv('점포-상권.csv')
    # df_population = pd.read_csv('길단위인구-상권.csv')

    # 데이터셋 구조를 바탕으로 가상의 데이터 생성
    # 점포-상권 데이터 (image_8a0c4f.png 기반)
    data_store = {
        '기준년분기명': ['2023_1', '2023_1', '2023_1', '2023_1', '2023_2', '2023_2'],
        '상권구분코드': ['A', 'A', 'B', 'B', 'A', 'B'],
        '상권구분코드명': ['골목상권', '골목상권', '발달상권', '발달상권', '골목상권', '발달상권'],
        '상권코드': [1001, 1001, 2001, 2001, 1001, 2001],
        '상권코드명': ['강남역', '강남역', '홍대입구', '홍대입구', '강남역', '홍대입구'],
        '서비스업종코드': ['F01', 'F02', 'F01', 'F03', 'F01', 'F01'],
        '서비스업종코드명': ['치킨', '한식', '치킨', '카페', '치킨', '치킨'],
        '점포수': [10, 50, 15, 30, 12, 18],
        '유사_업종_점포_수': [15, 60, 20, 35, 18, 22],
        '개업_율': [0.05, 0.03, 0.07, 0.02, 0.06, 0.04],
        '개업_점포_수': [1, 2, 1, 1, 1, 1],
        '폐업_율': [0.02, 0.01, 0.03, 0.01, 0.01, 0.02],
        '폐업_점포_수': [0, 0, 0, 0, 0, 0],
        '프랜차이즈_점포_수': [7, 20, 10, 15, 8, 12]
    }
    df_store = pd.DataFrame(data_store)

    # 길단위인구-상권 데이터 (image_8a0c32.png 기반)
    data_population = {
        '기준년분기명': ['2023_1', '2023_1', '2023_2', '2023_2'],
        '상권구분코드': ['A', 'B', 'A', 'B'],
        '상권구분코드명': ['골목상권', '발달상권', '골목상권', '발달상권'],
        '상권코드': [1001, 2001, 1001, 2001],
        '상권코드명': ['강남역', '홍대입구', '강남역', '홍대입구'],
        '총_유동인구_수': [10000, 15000, 11000, 16000],
        '시간대_1_유동인구_수': [500, 800, 550, 850], # 가정: 00-06시
        '시간대_2_유동인구_수': [1000, 1500, 1100, 1600], # 가정: 06-12시
        '시간대_3_유동인구_수': [2000, 3000, 2200, 3300], # 가정: 12-18시
        '시간대_4_유동인구_수': [3000, 4500, 3300, 4800], # 가정: 18-24시
        '시간대_5_유동인구_수': [1500, 2000, 1600, 2100],
        '시간대_6_유동인구_수': [1000, 1200, 1100, 1300],
        '시간대_7_유동인구_수': [500, 700, 550, 750],
        '시간대_8_유동인구_수': [300, 400, 330, 440],
        '시간대_9_유동인구_수': [100, 200, 110, 220],
        '시간대_10_유동인구_수': [50, 100, 55, 110],
        '남성_유동인구_수': [5000, 8000, 5500, 8500],
        '여성_유동인구_수': [5000, 7000, 5500, 7500],
        '연령대_10_유동인구_수': [500, 1000, 550, 1100],
        '연령대_20_유동인구_수': [2000, 3000, 2200, 3300],
        '연령대_30_유동인구_수': [3000, 4000, 3300, 4400],
        '연령대_40_유동인구_수': [2500, 3500, 2700, 3700],
        '연령대_50_유동인구_수': [1000, 2000, 1100, 2200],
        '연령대_60_유동인구_수': [500, 1000, 550, 1100],
        '연령대_70_이상_유동인구_수': [500, 500, 500, 500],
        '월요일_유동인구_수': [1500, 2000, 1600, 2100],
        '화요일_유동인구_수': [1600, 2100, 1700, 2200],
        '수요일_유동인구_수': [1700, 2200, 1800, 2300],
        '목요일_유동인구_수': [1800, 2300, 1900, 2400],
        '금요일_유동인구_수': [2000, 3000, 2100, 3100],
        '토요일_유동인구_수': [1000, 1500, 1100, 1600],
        '일요일_유동인구_수': [400, 700, 440, 770],
        '봄_유동인구_수': [2500, 3000, 2700, 3300],
        '여름_유동인구_수': [3000, 4000, 3300, 4400],
        '가을_유동인구_수': [2500, 3500, 2700, 3700],
        '겨울_유동인구_수': [2000, 2500, 2200, 2700]
    }
    df_population = pd.DataFrame(data_population)

    return df_store, df_population

df_store, df_population = load_data()

# --- 2. 데이터 전처리 ---

# 치킨 점포 데이터 필터링
df_chicken_stores = df_store[df_store['서비스업종코드명'] == '치킨'].copy()

# 상권 정보 기준으로 두 데이터셋 조인
# 기준년분기명, 상권구분코드, 상권코드 기준으로 조인
df_merged = pd.merge(
    df_chicken_stores,
    df_population,
    on=['기준년분기명', '상권구분코드', '상권코드', '상권구분코드명', '상권코드명'],
    how='inner'
)

# 시간대별 유동인구 컬럼 식별
time_columns = [col for col in df_merged.columns if '시간대_' in col and '_유동인구_수' in col]

# 시간대별 유동인구 당 점포수 비율 계산
# 0으로 나누는 오류 방지를 위해 작은 값(epsilon) 추가
epsilon = 1e-6
for col in time_columns:
    df_merged[f'점포수_대비_{col}_비율'] = df_merged['점포수'] / (df_merged[col] + epsilon)

# --- 3. 스트림릿 UI 구성 ---

st.set_page_config(layout="wide")
st.title('🍗 상권별 치킨 점포수 및 유동인구 분석')

# 사이드바 설정
st.sidebar.header('상권 선택')

# 고유한 상권 구분을 가져옵니다.
unique_quarters = df_merged['기준년분기명'].unique()
selected_quarter = st.sidebar.selectbox('기준 년분기 선택', unique_quarters)

# 선택된 년분기에 해당하는 상권 구분 코드명만 필터링
filtered_by_quarter = df_merged[df_merged['기준년분기명'] == selected_quarter]
unique_trade_areas = filtered_by_quarter['상권구분코드명'].unique()
selected_trade_area = st.sidebar.selectbox('상권 구분 코드명 선택', unique_trade_areas)

# 선택된 상권 코드명만 필터링
filtered_by_trade_area = filtered_by_quarter[filtered_by_quarter['상권구분코드명'] == selected_trade_area]
unique_market_names = filtered_by_trade_area['상권코드명'].unique()
selected_market_name = st.sidebar.selectbox('상권 코드명 선택', unique_market_names)

# 최종 필터링된 데이터
final_filtered_df = df_merged[
    (df_merged['기준년분기명'] == selected_quarter) &
    (df_merged['상권구분코드명'] == selected_trade_area) &
    (df_merged['상권코드명'] == selected_market_name)
]

if not final_filtered_df.empty:
    st.subheader(f'{selected_quarter} - {selected_trade_area} - {selected_market_name} 상권 분석 결과')

    # 치킨 점포수 정보
    total_chicken_stores = final_filtered_df['점포수'].sum()
    st.write(f"해당 상권의 치킨 점포수: **{int(total_chicken_stores)}개**")

    # 시간대별 유동인구 당 점포수 비율 시각화
    st.subheader('시간대별 길단위인구 당 치킨 점포수 비율')

    # 시각화를 위한 데이터 준비
    plot_data = pd.DataFrame(columns=['시간대', '비율'])
    for col in time_columns:
        ratio_col_name = f'점포수_대비_{col}_비율'
        if ratio_col_name in final_filtered_df.columns:
            # 해당 시간대 컬럼의 '시간대_X_' 부분을 제거하고 '시간대 X'로 변환
            time_label = col.replace('_유동인구_수', '').replace('_', ' ')
            plot_data = pd.concat([plot_data, pd.DataFrame({'시간대': [time_label], '비율': [final_filtered_df[ratio_col_name].iloc[0]]})], ignore_index=True)


    if not plot_data.empty:
        fig = px.line(
            plot_data,
            x='시간대',
            y='비율',
            title=f'{selected_market_name} 상권 시간대별 유동인구 당 치킨 점포수 비율',
            labels={'비율': '점포수 / 유동인구 수', '시간대': '시간대 구분'},
            markers=True # 마커 추가
        )
        fig.update_xaxes(categoryorder='array', categoryarray=plot_data['시간대'].tolist()) # 시간대 순서 정렬
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("선택된 상권의 시간대별 유동인구 데이터가 부족하여 비율을 시각화할 수 없습니다.")

    st.subheader('데이터 미리보기 (치킨 점포수 및 시간대별 유동인구)')
    display_cols = ['기준년분기명', '상권구분코드명', '상권코드명', '점포수'] + time_columns
    st.dataframe(final_filtered_df[display_cols].iloc[:1]) # 첫 번째 행만 보여줌
    st.markdown("*(위 데이터는 선택된 상권의 치킨 점포수와 시간대별 유동인구를 보여줍니다)*")

else:
    st.warning("선택된 상권에 해당하는 치킨 점포수 데이터가 없습니다. 다른 상권을 선택해주세요.")


st.markdown("""
---
### 분석 개요
이 애플리케이션은 사용자가 선택한 상권의 치킨 점포수와 시간대별 유동인구 데이터를 분석하여,
유동인구 대비 치킨 점포수의 비율을 시각화합니다.
이를 통해 특정 시간대에 유동인구가 많은 상권에서 치킨 점포의 밀집도를 파악할 수 있습니다.

**데이터 컬럼 설명 (가정):**
* `기준년분기명`: 데이터의 기준이 되는 년도와 분기 (예: 2023_1)
* `상권구분코드명`: 상권의 종류 (예: 골목상권, 발달상권)
* `상권코드명`: 상권의 구체적인 이름 (예: 강남역, 홍대입구)
* `점포수`: 해당 상권의 치킨 점포수
* `시간대_X_유동인구_수`: 각 시간대별 유동인구 수 (예: 시간대_1_유동인구_수, 시간대_2_유동인구_수 등. 실제 데이터의 시간대 의미를 확인해주세요.)
""")
