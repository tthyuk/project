import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")

# --- 1. 데이터 로드 함수 ---
@st.cache_data
def load_data(file_path, file_type):
    if file_type == 'csv':
        return pd.read_csv(file_path)
    elif file_type == 'excel':
        return pd.read_excel(file_path)
    else:
        st.error("지원하지 않는 파일 형식입니다. CSV 또는 Excel 파일을 업로드해주세요.")
        return None

# --- 2. 데이터 전처리 함수 ---
def preprocess_data(chicken_df, population_df):
    # 치킨 점포 데이터 전처리
    # '치킨'이 포함된 서비스 업종만 필터링 (실제 데이터에 맞게 조정 필요)
    chicken_df_filtered = chicken_df[chicken_df['서비스_업종_코드_명'].str.contains('치킨|닭강정|후라이드', na=False)]
    
    # 행정동별 치킨 점포수 합계
    chicken_agg = chicken_df_filtered.groupby(['기준_년분기', '행정동_코', '행정동_코_명'])['점포수'].sum().reset_index()
    chicken_agg.rename(columns={'점포수': '치킨_점포수'}, inplace=True)

    # 길단위인구 데이터 전처리
    # 시간대별 인구 컬럼 선택 및 재구성
    time_cols = [col for col in population_df.columns if '시간대_' in col and '_생활인구_수' in col]
    population_melted = population_df.melt(
        id_vars=['기준_년분기', '행정동_코', '행정동_코_명'],
        value_vars=time_cols,
        var_name='시간대',
        value_name='생활인구수'
    )
    
    # 시간대 컬럼을 깔끔하게 정리 (예: '시간대_00_06_생활인구_수' -> '00-06시')
    population_melted['시간대'] = population_melted['시간대'].str.replace('시간대_', '').str.replace('_생활인구_수', '시')
    population_melted['시간대'] = population_melted['시간대'].replace({
        '00_06시': '00-06시', '06_11시': '06-11시', '11_14시': '11-14시',
        '14_17시': '14-17시', '17_21시': '17-21시', '21_24시': '21-24시'
    })

    # 데이터 병합
    merged_df = pd.merge(
        chicken_agg,
        population_melted,
        on=['기준_년분기', '행정동_코', '행정동_코_명'],
        how='inner'
    )
    
    # 인구당 점포수 비율 계산 (0으로 나누는 경우 방지)
    merged_df['인구당_점포수_비율'] = merged_df.apply(
        lambda row: (row['치킨_점포수'] / row['생활인구수']) * 100000 if row['생활인구수'] > 0 else 0, axis=1
    ) # 인구 10만명당 점포수 비율로 계산

    return merged_df

# --- Streamlit 앱 UI ---
st.title('🍗 행정동별 치킨 점포수 분석')

st.markdown("""
이 앱은 행정동별 치킨 점포수와 시간대별 길단위 생활인구 데이터를 결합하여, 
**시간대별 길단위 인구 10만명당 치킨 점포수 비율**을 분석하고 시각화합니다.
""")

st.sidebar.header('데이터 업로드')

# 점포-행정동 데이터 업로드
st.sidebar.subheader('1. 점포-행정동 데이터 (chicken_stores.csv / .xlsx)')
uploaded_chicken_file = st.sidebar.file_uploader("점포-행정동 파일을 선택하세요", type=['csv', 'xlsx'], key='chicken_upload')
chicken_df = None
if uploaded_chicken_file is not None:
    file_type = 'csv' if uploaded_chicken_file.name.endswith('.csv') else 'excel'
    chicken_df = load_data(uploaded_chicken_file, file_type)
    if chicken_df is not None:
        st.sidebar.success('점포-행정동 데이터 로드 완료!')
        st.sidebar.dataframe(chicken_df.head())

# 길단위인구-행정동 데이터 업로드
st.sidebar.subheader('2. 길단위인구-행정동 데이터 (population_by_time.csv / .xlsx)')
uploaded_population_file = st.sidebar.file_uploader("길단위인구-행정동 파일을 선택하세요", type=['csv', 'xlsx'], key='population_upload')
population_df = None
if uploaded_population_file is not None:
    file_type = 'csv' if uploaded_population_file.name.endswith('.csv') else 'excel'
    population_df = load_data(uploaded_population_file, file_type)
    if population_df is not None:
        st.sidebar.success('길단위인구-행정동 데이터 로드 완료!')
        st.sidebar.dataframe(population_df.head())

# 데이터 전처리 및 분석 실행
if chicken_df is not None and population_df is not None:
    st.header('데이터 분석 결과')
    with st.spinner('데이터를 전처리하고 있습니다...'):
        analyzed_df = preprocess_data(chicken_df, population_df)
    
    if analyzed_df is not None:
        st.success('데이터 전처리 및 병합 완료!')
        st.dataframe(analyzed_df.head())

        # 사용자 입력 위젯
        st.sidebar.header('분석 설정')
        
        # 년분기 선택
        quarters = sorted(analyzed_df['기준_년분기'].unique())
        selected_quarter = st.sidebar.selectbox('기준 년분기 선택:', quarters)

        # 시간대 선택
        time_bands = sorted(analyzed_df['시간대'].unique())
        selected_time_band = st.sidebar.selectbox('시간대 선택:', time_bands)

        # 행정동 필터링 (선택 사항)
        all_dong_names = ['전체'] + sorted(analyzed_df['행정동_코_명'].unique())
        selected_dong_name = st.sidebar.selectbox('행정동 선택:', all_dong_names)

        # 필터링된 데이터
        filtered_df = analyzed_df[
            (analyzed_df['기준_년분기'] == selected_quarter) & 
            (analyzed_df['시간대'] == selected_time_band)
        ]
        if selected_dong_name != '전체':
            filtered_df = filtered_df[filtered_df['행정동_코_명'] == selected_dong_name]
        
        st.subheader(f"{selected_quarter} - {selected_time_band} 기준 인구 10만명당 치킨 점포수 비율")
        
        if not filtered_df.empty:
            # 1. 막대 그래프: 행정동별 인구당 점포수 비율 (상위 20개)
            st.markdown("#### 행정동별 인구 10만명당 치킨 점포수 비율 (상위/하위 20개)")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("##### 상위 20개 행정동")
                top_20_dong = filtered_df.sort_values(by='인구당_점포수_비율', ascending=False).head(20)
                fig_bar_top = px.bar(
                    top_20_dong, 
                    x='행정동_코_명', 
                    y='인구당_점포수_비율',
                    title='상위 20개 행정동',
                    labels={'행정동_코_명': '행정동명', '인구당_점포수_비율': '인구 10만명당 점포수 비율'},
                    hover_data=['치킨_점포수', '생활인구수']
                )
                st.plotly_chart(fig_bar_top, use_container_width=True)

            with col2:
                st.write("##### 하위 20개 행정동")
                bottom_20_dong = filtered_df.sort_values(by='인구당_점포수_비율', ascending=True).head(20)
                fig_bar_bottom = px.bar(
                    bottom_20_dong, 
                    x='행정동_코_명', 
                    y='인구당_점포수_비율',
                    title='하위 20개 행정동',
                    labels={'행정동_코_명': '행정동명', '인구당_점포수_비율': '인구 10만명당 점포수 비율'},
                    hover_data=['치킨_점포수', '생활인구수']
                )
                st.plotly_chart(fig_bar_bottom, use_container_width=True)

            # 2. 박스 플롯: 시간대별 인구당 점포수 비율 분포
            st.markdown("#### 시간대별 인구 10만명당 치킨 점포수 비율 분포")
            fig_box = px.box(
                analyzed_df[analyzed_df['기준_년분기'] == selected_quarter], # 선택된 년분기의 모든 시간대 데이터
                x='시간대', 
                y='인구당_점포수_비율',
                title=f'{selected_quarter} 시간대별 인구 10만명당 치킨 점포수 비율 분포',
                labels={'시간대': '시간대', '인구당_점포수_비율': '인구 10만명당 점포수 비율'},
                category_orders={"시간대": time_bands} # 시간대 순서 지정
            )
            st.plotly_chart(fig_box, use_container_width=True)

            # 3. 데이터 테이블
            st.markdown("#### 상세 데이터 테이블")
            st.dataframe(filtered_df.sort_values(by='인구당_점포수_비율', ascending=False))
            
            # 데이터 다운로드 버튼
            csv = filtered_df.to_csv(index=False).encode('utf-8-sig') # 한글 깨짐 방지
            st.download_button(
                label="분석 결과 데이터 다운로드 (CSV)",
                data=csv,
                file_name=f'치킨_점포수_분석_결과_{selected_quarter}_{selected_time_band}.csv',
                mime='text/csv',
            )

        else:
            st.warning("선택된 필터에 해당하는 데이터가 없습니다. 다른 조건을 선택해주세요.")
    else:
        st.error("데이터 전처리 중 오류가 발생했습니다. 데이터 형식을 확인해주세요.")
else:
    st.info("왼쪽 사이드바에서 '점포-행정동' 및 '길단위인구-행정동' 데이터 파일을 업로드해주세요.")

st.markdown("""
---
### 데이터 컬럼 설명
* **기준_년분기**: 데이터의 기준 년도와 분기
* **행정동_코**: 행정동을 구분하는 코드
* **행정동_코_명**: 행정동의 이름
* **치킨_점포수**: 해당 행정동의 치킨 점포수 합계
* **생활인구수**: 특정 시간대의 길단위 생활 인구수
* **시간대**: 생활 인구가 측정된 시간대 (예: 00-06시)
* **인구당_점포수_비율**: 생활인구 10만명당 치킨 점포수 비율
""")
