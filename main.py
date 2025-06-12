import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit 페이지 설정을 넓은 레이아웃으로 변경
st.set_page_config(layout="wide")

# --- 1. 데이터 로드 함수 (GitHub URL에서 로드) ---
# @st.cache_data 데코레이터를 사용하여 데이터를 캐시하여 앱 성능을 최적화합니다.
@st.cache_data
def load_data_from_url(file_url):
    """
    지정된 GitHub Raw URL에서 데이터를 로드합니다. CSV 또는 Excel 파일을 지원하며,
    CSV의 경우 한글 인코딩 문제(UnicodeDecodeError)를 처리합니다.
    """
    if not file_url:
        return None

    st.info(f"데이터를 로드 중입니다: {file_url}")
    try:
        if file_url.endswith('.csv'):
            try:
                # UTF-8 인코딩으로 먼저 시도합니다.
                return pd.read_csv(file_url, encoding='utf-8')
            except UnicodeDecodeError:
                # UTF-8로 실패하면 CP949(Windows 한글 기본 인코딩)로 다시 시도합니다.
                return pd.read_csv(file_url, encoding='cp949')
        elif file_url.endswith('.xlsx') or file_url.endswith('.xls'):
            # Excel 파일은 pd.read_excel로 로드합니다.
            return pd.read_excel(file_url)
        else:
            # 지원하지 않는 파일 형식인 경우 오류 메시지를 표시합니다.
            st.error("지원하지 않는 파일 형식입니다. CSV 또는 Excel URL을 입력해주세요.")
            return None
    except Exception as e:
        st.error(f"파일을 로드하는 중 오류가 발생했습니다. URL이 올바른지 확인하거나 GitHub Raw 파일 링크인지 확인해주세요: {e}")
        return None

# --- 2. 데이터 전처리 함수 ---
def preprocess_data(chicken_df, population_df):
    """
    치킨 점포 데이터와 길단위 인구 데이터를 전처리하고 병합합니다.
    시간대별 인구당 점포수 비율을 계산합니다.
    """
    # 디버깅을 위해 업로드된 데이터프레임의 컬럼명을 출력합니다.
    st.write("---")
    st.write("**업로드된 '점포-행정동' 데이터의 컬럼명:**", chicken_df.columns.tolist())
    st.write("**업로드된 '길단위인구-행정동' 데이터의 컬럼명:**", population_df.columns.tolist())
    st.write("---")

    # 필요한 컬럼이 존재하는지 확인합니다.
    required_chicken_cols = ['기준_년분기', '행정동_코', '행정동_코_명', '서비스_업종_코드_명', '점포수']
    missing_chicken_cols = [col for col in required_chicken_cols if col not in chicken_df.columns]
    if missing_chicken_cols:
        st.error(f"'점포-행정동' 데이터에 다음 필수 컬럼이 누락되었습니다: {', '.join(missing_chicken_cols)}")
        st.warning("데이터 파일의 컬럼명이 코드에서 예상하는 컬럼명과 일치하는지 확인해주세요.")
        return None

    required_population_cols = ['기준_년분기', '행정동_코', '행정동_코_명']
    time_cols_prefix = '시간대_' # 시간대별 인구 컬럼 접두사
    
    missing_population_cols = [col for col in required_population_cols if col not in population_df.columns]
    if missing_population_cols:
        st.error(f"'길단위인구-행정동' 데이터에 다음 필수 컬럼이 누락되었습니다: {', '.join(missing_population_cols)}")
        st.warning("데이터 파일의 컬럼명이 코드에서 예상하는 컬럼명과 일치하는지 확인해주세요.")
        return None
    
    # 시간대 컬럼이 하나라도 있는지 확인
    actual_time_cols = [col for col in population_df.columns if time_cols_prefix in col and '_생활인구_수' in col]
    if not actual_time_cols:
        st.error(f"'길단위인구-행정동' 데이터에 '시간대_'로 시작하고 '_생활인구_수'로 끝나는 시간대별 인구 컬럼이 없습니다.")
        st.warning("데이터 파일의 시간대별 인구 컬럼명 형식이 올바른지 확인해주세요 (예: '시간대_00_06_생활인구_수').")
        return None

    # 치킨 점포 데이터 전처리
    # '치킨' 또는 '닭강정' 등이 포함된 서비스 업종만 필터링합니다.
    # 실제 데이터의 '서비스_업종_코드_명' 컬럼 값에 따라 조정이 필요할 수 있습니다.
    chicken_df_filtered = chicken_df[chicken_df['서비스_업종_코드_명'].str.contains('치킨|닭강정|후라이드', na=False)]
    
    # 행정동별 치킨 점포수 합계를 계산합니다.
    chicken_agg = chicken_df_filtered.groupby(['기준_년분기', '행정동_코', '행정동_코_명'])['점포수'].sum().reset_index()
    chicken_agg.rename(columns={'점포수': '치킨_점포수'}, inplace=True)

    # 길단위인구 데이터 전처리
    # 시간대별 인구 컬럼들을 식별합니다.
    time_cols = [col for col in population_df.columns if '시간대_' in col and '_생활인구_수' in col]
    
    # melt 함수를 사용하여 시간대별 인구 데이터를 긴 형식으로 변환합니다.
    # 이는 시각화에 용이하도록 데이터를 재구성하는 과정입니다.
    population_melted = population_df.melt(
        id_vars=['기준_년분기', '행정동_코', '행정동_코_명'],
        value_vars=time_cols,
        var_name='시간대',
        value_name='생활인구수'
    )
    
    # '시간대' 컬럼의 값을 보기 좋게 정리합니다 (예: '시간대_00_06_생활인구_수' -> '00-06시').
    population_melted['시간대'] = population_melted['시간대'].str.replace('시간대_', '').str.replace('_생활인구_수', '시')
    population_melted['시간대'] = population_melted['시간대'].replace({
        '00_06시': '00-06시', '06_11시': '06-11시', '11_14시': '11-14시',
        '14_17시': '14-17시', '17_21시': '17-21시', '21_24시': '21-24시'
    })

    # 치킨 점포수 데이터와 길단위인구 데이터를 행정동, 년분기를 기준으로 병합합니다.
    merged_df = pd.merge(
        chicken_agg,
        population_melted,
        on=['기준_년분기', '행정동_코', '행정동_코_명'],
        how='inner' # 두 데이터셋에 모두 존재하는 행정동만 포함합니다.
    )
    
    # 인구당 점포수 비율을 계산합니다 (인구 10만명당 점포수).
    # 생활인구수가 0인 경우 0으로 처리하여 DivideByZero 오류를 방지합니다.
    merged_df['인구당_점포수_비율'] = merged_df.apply(
        lambda row: (row['치킨_점포수'] / row['생활인구수']) * 100000 if row['생활인구수'] > 0 else 0, axis=1
    )

    return merged_df

# --- Streamlit 앱 UI 시작 ---
st.title('🍗 행정동별 치킨 점포수 분석')

st.markdown("""
이 앱은 사용자가 GitHub Raw URL로 제공하는 **행정동별 치킨 점포수 데이터**와 
**시간대별 길단위 생활인구 데이터**를 결합하여, 
**시간대별 길단위 인구 10만명당 치킨 점포수 비율**을 분석하고 시각화합니다.
분석 결과를 통해 특정 행정동의 치킨 점포 밀집도를 인구 대비로 파악할 수 있습니다.
""")

# 사이드바에 데이터 로드 섹션 생성
st.sidebar.header('데이터 로드 (GitHub URL)')
st.sidebar.markdown("GitHub Raw 파일 URL을 입력해주세요. (예: `https://raw.githubusercontent.com/사용자명/저장소명/브랜치명/파일경로/파일이름.csv`)")


# 1. 점포-행정동 데이터 URL 입력 섹션
st.sidebar.subheader('1. 점포-행정동 데이터 URL')
# 사용자가 제공한 파일명으로 예시 URL을 변경했습니다.
# 실제 사용자 GitHub Raw URL로 변경해야 합니다.
chicken_url_default = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPOSITORY/YOUR_BRANCH/서울시 상권분석서비스(점포-행정동).csv" 
chicken_url = st.sidebar.text_input("점포-행정동 GitHub Raw URL 입력:", chicken_url_default, key='chicken_url')
chicken_df = None # 초기 데이터프레임 변수 선언

if chicken_url: # URL이 입력되었을 때만 로드 시도
    chicken_df = load_data_from_url(chicken_url)
    if chicken_df is not None:
        st.sidebar.success('점포-행정동 데이터 로드 완료!')
        st.sidebar.dataframe(chicken_df.head()) # 데이터 미리보기

# 2. 길단위인구-행정동 데이터 URL 입력 섹션
st.sidebar.subheader('2. 길단위인구-행정동 데이터 URL')
# 사용자가 제공한 파일명으로 예시 URL을 변경했습니다.
# 실제 사용자 GitHub Raw URL로 변경해야 합니다.
population_url_default = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPOSITORY/YOUR_BRANCH/서울시 상권분석서비스(길단위인구-행정동).csv" 
population_url = st.sidebar.text_input("길단위인구-행정동 GitHub Raw URL 입력:", population_url_default, key='population_url')
population_df = None # 초기 데이터프레임 변수 선언

if population_url: # URL이 입력되었을 때만 로드 시도
    population_df = load_data_from_url(population_url)
    if population_df is not None:
        st.sidebar.success('길단위인구-행정동 데이터 로드 완료!')
        st.sidebar.dataframe(population_df.head()) # 데이터 미리보기

# 두 데이터 파일이 모두 성공적으로 로드되었을 경우 분석을 시작합니다.
if chicken_df is not None and population_df is not None:
    st.header('데이터 분석 결과')
    # 데이터 전처리 진행 중임을 사용자에게 알립니다.
    with st.spinner('데이터를 전처리하고 있습니다... 잠시만 기다려 주세요.'):
        analyzed_df = preprocess_data(chicken_df, population_df)
    
    if analyzed_df is not None:
        st.success('데이터 전처리 및 병합 완료!')
        st.dataframe(analyzed_df.head()) # 전처리된 데이터의 일부를 보여줍니다.

        # 사용자 입력 위젯 (분석 설정)
        st.sidebar.header('분석 설정')
        
        # 사용 가능한 '기준_년분기'를 드롭다운으로 표시하고 선택하도록 합니다.
        # 데이터프레임이 비어있지 않은지 확인 후 unique() 호출
        if not analyzed_df.empty:
            quarters = sorted(analyzed_df['기준_년분기'].unique())
            selected_quarter = st.sidebar.selectbox('기준 년분기 선택:', quarters)

            # 사용 가능한 '시간대'를 드롭다운으로 표시하고 선택하도록 합니다.
            time_bands = sorted(analyzed_df['시간대'].unique())
            selected_time_band = st.sidebar.selectbox('시간대 선택:', time_bands)

            # 행정동 필터링 (선택 사항)
            # '전체' 옵션을 추가하여 모든 행정동을 볼 수 있도록 합니다.
            all_dong_names = ['전체'] + sorted(analyzed_df['행정동_코_명'].unique())
            selected_dong_name = st.sidebar.selectbox('행정동 선택:', all_dong_names)

            # 선택된 기준에 따라 데이터를 필터링합니다.
            filtered_df = analyzed_df[
                (analyzed_df['기준_년분기'] == selected_quarter) & 
                (analyzed_df['시간대'] == selected_time_band)
            ]
            if selected_dong_name != '전체':
                filtered_df = filtered_df[filtered_df['행정동_코_명'] == selected_dong_name]
            
            st.subheader(f"📊 {selected_quarter} - {selected_time_band} 기준 인구 10만명당 치킨 점포수 비율")
            
            if not filtered_df.empty:
                # 1. 막대 그래프: 행정동별 인구당 점포수 비율 (상위 20개)
                st.markdown("#### 행정동별 인구 10만명당 치킨 점포수 비율 (상위/하위 20개)")
                
                # 그래프를 나란히 배치하기 위해 두 개의 컬럼을 생성합니다.
                col1, col2 = st.columns(2)
                with col1:
                    st.write("##### 상위 20개 행정동")
                    # 인구당 점포수 비율이 높은 순으로 상위 20개 행정동을 선택합니다.
                    top_20_dong = filtered_df.sort_values(by='인구당_점포수_비율', ascending=False).head(20)
                    fig_bar_top = px.bar(
                        top_20_dong, 
                        x='행정동_코_명', 
                        y='인구당_점포수_비율',
                        title='상위 20개 행정동',
                        labels={'행정동_코_명': '행정동명', '인구당_점포수_비율': '인구 10만명당 점포수 비율'},
                        hover_data=['치킨_점포수', '생활인구수'] # 마우스 오버 시 추가 정보 표시
                    )
                    st.plotly_chart(fig_bar_top, use_container_width=True) # 컨테이너 너비에 맞게 그래프 조정

                with col2:
                    st.write("##### 하위 20개 행정동")
                    # 인구당 점포수 비율이 낮은 순으로 하위 20개 행정동을 선택합니다.
                    bottom_20_dong = filtered_df.sort_values(by='인구당_점포수_비율', ascending=True).head(20)
                    fig_bar_bottom = px.bar(
                        bottom_20_dong, 
                        x='행정동_코_명', 
                        y='인구당_점포수_비율',
                        title='하위 20개 행정동',
                        labels={'행정동_코_명': '행정동명', '인구당_점포수_비율': '인구 10만명당 점포수 비율'},
                        hover_data=['치킨_점포수', '생활인구수'] # 마우스 오버 시 추가 정보 표시
                    )
                    st.plotly_chart(fig_bar_bottom, use_container_width=True) # 컨테이너 너비에 맞게 그래프 조정

                # 2. 박스 플롯: 시간대별 인구당 점포수 비율 분포
                st.markdown("#### 시간대별 인구 10만명당 치킨 점포수 비율 분포")
                # 선택된 년분기의 모든 시간대 데이터를 사용하여 분포를 시각화합니다.
                fig_box = px.box(
                    analyzed_df[analyzed_df['기준_년분기'] == selected_quarter], 
                    x='시간대', 
                    y='인구당_점포수_비율',
                    title=f'{selected_quarter} 시간대별 인구 10만명당 치킨 점포수 비율 분포',
                    labels={'시간대': '시간대', '인구당_점포수_비율': '인구 10만명당 점포수 비율'},
                    category_orders={"시간대": time_bands} # 시간대 순서를 올바르게 지정합니다.
                )
                st.plotly_chart(fig_box, use_container_width=True) # 컨테이너 너비에 맞게 그래프 조정

                # 3. 상세 데이터 테이블
                st.markdown("#### 상세 데이터 테이블")
                st.dataframe(filtered_df.sort_values(by='인구당_점포수_비율', ascending=False))
                
                # 분석 결과를 CSV 파일로 다운로드할 수 있는 버튼을 제공합니다.
                csv = filtered_df.to_csv(index=False).encode('utf-8-sig') # 한글 깨짐 방지를 위해 'utf-8-sig' 인코딩 사용
                st.download_button(
                    label="분석 결과 데이터 다운로드 (CSV)",
                    data=csv,
                    file_name=f'치킨_점포수_분석_결과_{selected_quarter}_{selected_time_band}.csv',
                    mime='text/csv',
                )

            else:
                # 필터링된 데이터가 없는 경우 경고 메시지를 표시합니다.
                st.warning("⚠️ 선택된 필터에 해당하는 데이터가 없습니다. 다른 조건을 선택해주세요.")
        else:
            st.warning("분석할 데이터가 비어 있습니다. 데이터 전처리 단계에서 문제가 발생했을 수 있습니다.")
    else:
        # 데이터 전처리 중 오류가 발생한 경우 오류 메시지를 표시합니다.
        st.error("데이터 전처리 중 오류가 발생했습니다. 데이터 형식을 확인해주세요.")
else:
    # 데이터 파일이 모두 업로드되지 않은 경우 안내 메시지를 표시합니다.
    st.info("👈 왼쪽 사이드바에서 '점포-행정동' 및 '길단위인구-행정동' 데이터의 GitHub Raw URL을 입력해주세요.")

# 앱 하단에 데이터 컬럼 설명을 추가합니다.
st.markdown("""
---
### 데이터 컬럼 설명
* **기준_년분기**: 데이터의 기준 년도와 분기 (예: 2023_1, 2023_2)
* **행정동_코**: 행정동을 구분하는 고유 코드
* **행정동_코_명**: 행정동의 한글 이름
* **치킨_점포수**: 해당 행정동의 치킨 점포수 합계
* **생활인구수**: 특정 시간대의 길단위 생활 인구수 (총 유동 인구)
* **시간대**: 생활 인구가 측정된 시간대 (예: 00-06시, 06-11시 등)
* **인구당_점포수_비율**: 생활인구 10만명당 치킨 점포수 비율 (밀집도 지표)
""")
