import streamlit as st
import pandas as pd
import plotly.express as px

# --- Streamlit 앱 설정 ---
# 페이지 레이아웃을 'wide'로 설정하여 더 넓은 화면을 사용합니다.
st.set_page_config(layout="wide", page_title="상권 분석 앱")

st.title('🍗 상권별 길단위인구수 및 치킨전문점 비교 및 분석 시각화')
st.markdown("""
이 앱은 사용자가 직접 업로드한 데이터를 기반으로 대한민국 주요 상권의 **길단위인구수 (유동인구)** 와 **치킨전문점 수**를 시각화하고 비교, 분석합니다.
이를 통해 특정 상권의 특성을 파악하고, 유동인구와 특정 업종 간의 관계를 직관적으로 이해할 수 있습니다.

**데이터 업로드**: `상권명`, `길단위인구수`, `치킨전문점수` 컬럼을 포함하는 CSV 파일을 업로드해주세요. 여러 파일을 동시에 업로드할 수 있습니다.
""")

# --- 데이터 업로드 섹션 ---
st.header('📤 데이터 업로드')
# 여러 파일 업로드 가능하도록 변경
uploaded_files = st.file_uploader("여기에 CSV 파일을 업로드해주세요.", type=['csv'], accept_multiple_files=True)

# 인코딩 선택 옵션 추가
encoding_option = st.selectbox(
    "CSV 파일의 인코딩을 선택해주세요:",
    ('utf-8', 'cp949', 'euc-kr'),
    index=1 # 기본값으로 cp949 선택 (한국어 CSV 파일에 흔히 사용됨)
)

all_dfs = [] # 모든 유효한 DataFrame을 저장할 리스트

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            # 파일 이름으로 데이터셋 출처를 기록
            source_name = uploaded_file.name
            
            # 업로드된 CSV 파일을 DataFrame으로 읽어옵니다. 선택된 인코딩 사용
            current_df = pd.read_csv(uploaded_file, encoding=encoding_option)

            # 필요한 컬럼이 있는지 확인합니다.
            required_columns = ['상권명', '길단위인구수', '치킨전문점수']
            if not all(col in current_df.columns for col in required_columns):
                st.error(f"'{source_name}' 파일에 필요한 컬럼이 부족합니다. 다음 컬럼들이 포함되어야 합니다: {', '.join(required_columns)}")
                continue # 다음 파일로 넘어감
            else:
                # 길단위인구수와 치킨전문점수가 숫자인지 확인하고, 아니라면 오류 메시지를 표시합니다.
                numeric_check_failed = False
                for col in ['길단위인구수', '치킨전문점수']:
                    if not pd.api.types.is_numeric_dtype(current_df[col]):
                        st.error(f"'{source_name}' 파일의 '{col}' 컬럼은 숫자 형식이어야 합니다. 데이터를 확인해주세요.")
                        numeric_check_failed = True
                        break
                if numeric_check_failed:
                    continue # 다음 파일로 넘어감

                # 컬럼 이름이 정확하도록 설정 (대소문자 구분 없이 매칭하도록 개선 가능하지만 여기서는 정확한 이름 요구)
                current_df = current_df[required_columns] # 순서도 맞춤
                current_df.columns = ['상권명', '길단위인구수', '치킨전문점수']

                # 데이터셋 출처 컬럼 추가
                current_df['데이터셋 출처'] = source_name
                all_dfs.append(current_df)

        except UnicodeDecodeError:
            st.error(f"'{uploaded_file.name}' 파일은 선택하신 인코딩 '{encoding_option}'으로는 읽을 수 없습니다. 다른 인코딩을 시도해보세요 (예: 'euc-kr', 'cp949').")
        except Exception as e:
            st.error(f"'{uploaded_file.name}' 파일을 읽는 도중 오류가 발생했습니다: {e}")

    if all_dfs:
        df = pd.concat(all_dfs, ignore_index=True)
    else:
        df = None # 유효한 파일이 없으면 df는 None
        st.warning("업로드된 모든 파일에 문제가 있어 데이터를 로드할 수 없습니다. 파일을 확인해주세요.")
else:
    st.info("시각화를 위해 CSV 파일을 업로드해주세요.")

# --- 데이터가 성공적으로 로드된 경우에만 시각화 및 분석 수행 ---
if df is not None:
    st.header('📊 데이터 미리보기')
    # 데이터셋 출처 컬럼도 함께 표시
    st.dataframe(df)

    # --- 분석 섹션 ---
    st.header('🔍 데이터 분석')

    # 상관관계 분석
    st.subheader('상관관계 분석: 길단위인구수 vs. 치킨전문점 수')
    # 여러 데이터셋이 합쳐졌으므로 전체 데이터에 대한 상관관계를 계산
    correlation = df['길단위인구수'].corr(df['치킨전문점수'])
    st.info(f"**전체 데이터셋에서 길단위인구수와 치킨전문점 수 간의 상관계수: {correlation:.2f}**")
    if correlation > 0.7:
        st.success("매우 강한 양의 상관관계가 있습니다. 유동인구가 많을수록 치킨전문점 수도 많아지는 경향이 뚜렷합니다.")
    elif correlation > 0.3:
        st.success("어느 정도 양의 상관관계가 있습니다. 유동인구가 많을수록 치킨전문점 수도 많아지는 경향이 있습니다.")
    elif correlation < -0.7:
        st.warning("매우 강한 음의 상관관계가 있습니다. 유동인구가 많을수록 치킨전문점 수가 적어지는 경향이 뚜렷합니다.")
    elif correlation < -0.3:
        st.warning("어느 정도 음의 상관관계가 있습니다. 유동인구가 많을수록 치킨전문점 수가 적어지는 경향이 있습니다.")
    else:
        st.info("상관관계가 약하거나 거의 없습니다. 유동인구와 치킨전문점 수 사이에 뚜렷한 선형 관계를 찾기 어렵습니다.")

    st.markdown("---")

    # 상위 N개 상권 선택 기능
    st.subheader('상위 N개 상권 필터링')
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox("정렬 기준", ['길단위인구수', '치킨전문점수'])
    with col2:
        top_n = st.slider("상위 N개 상권 선택", min_value=1, max_value=len(df), value=min(5, len(df)))

    # 선택된 기준으로 데이터 정렬 및 상위 N개 추출
    filtered_df = df.sort_values(by=sort_by, ascending=False).head(top_n)

    st.write(f"**상위 {top_n}개 상권 (기준: {sort_by})**")
    # 필터링된 데이터프레임에 데이터셋 출처도 포함하여 표시
    st.dataframe(filtered_df)

    # --- 시각화 ---
    # 각 시각화에서 '데이터셋 출처'를 color로 사용하거나, facet_col로 분리하여 볼 수 있도록 옵션을 제공하면 더 유연해짐.
    # 일단은 '상권명'에 데이터셋 출처를 결합하여 x축에 표시
    df_plot = df.copy()
    # 상권명이 중복될 경우를 대비하여 상권명과 데이터셋 출처를 합쳐 고유한 레이블 생성
    df_plot['상권명_출처'] = df_plot['상권명'] + ' (' + df_plot['데이터셋 출처'].str.replace('.csv', '', regex=False) + ')'


    st.header('📈 상권별 길단위인구수')
    fig_population = px.bar(
        df_plot.sort_values('길단위인구수', ascending=False),
        x='상권명_출처', # 결합된 상권명_출처 사용
        y='길단위인구수',
        title='상권별 길단위인구수 분포',
        labels={'상권명_출처': '상권명 (데이터셋 출처)', '길단위인구수': '길단위인구수'},
        color='길단위인구수',
        color_continuous_scale=px.colors.sequential.Plasma,
        hover_name='상권명' # 원래 상권명은 hover_name으로
    )
    fig_population.update_layout(xaxis_title="상권명 (데이터셋 출처)", yaxis_title="길단위인구수")
    st.plotly_chart(fig_population, use_container_width=True)

    st.header('🐔 상권별 치킨전문점 수')
    fig_chicken = px.bar(
        df_plot.sort_values('치킨전문점수', ascending=False),
        x='상권명_출처', # 결합된 상권명_출처 사용
        y='치킨전문점수',
        title='상권별 치킨전문점 수 분포',
        labels={'상권명_출처': '상권명 (데이터셋 출처)', '치킨전문점수': '치킨전문점수'},
        color='치킨전문점수',
        color_continuous_scale=px.colors.sequential.Viridis,
        hover_name='상권명'
    )
    fig_chicken.update_layout(xaxis_title="상권명 (데이터셋 출처)", yaxis_title="치킨전문점수")
    st.plotly_chart(fig_chicken, use_container_width=True)

    st.header('👥🐔 길단위인구수와 치킨전문점 수 비교 (산점도)')
    fig_scatter = px.scatter(
        df_plot, # df_plot 사용
        x='길단위인구수',
        y='치킨전문점수',
        size='길단위인구수',
        color='데이터셋 출처', # 데이터셋 출처별로 색상 구분
        hover_name='상권명_출처', # 상권명_출처를 hover_name으로
        title='길단위인구수와 치킨전문점 수의 관계',
        labels={'길단위인구수': '길단위인구수', '치킨전문점수': '치킨전문점수'},
        log_x=False,
        size_max=60
    )
    fig_scatter.update_layout(xaxis_title="길단위인구수", yaxis_title="치킨전문점수")
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("""
    ### 💡 분석 가이드 및 인사이트
    * **상관관계 계수**: 길단위인구수와 치킨전문점 수 사이의 선형적인 관계 강도와 방향을 나타냅니다.
        * 1에 가까울수록 양의 선형 관계 (하나가 증가하면 다른 하나도 증가)
        * -1에 가까울수록 음의 선형 관계 (하나가 증가하면 다른 하나는 감소)
        * 0에 가까울수록 선형 관계 없음
    * **상위 N개 상권 필터링**: 특정 기준(유동인구 또는 치킨전문점 수)으로 가장 활발하거나 특정 업종이 많은 상권을 빠르게 식별할 수 있습니다.
    * **산점도**: 유동인구 대비 치킨전문점 수가 예상보다 많거나 적은 '이상치' 상권을 찾아내는 데 유용합니다. 이는 새로운 시장 기회나 경쟁 과열 지역을 시사할 수 있습니다.
    * **여러 데이터셋 분석**: 여러 CSV 파일을 업로드하여 통합된 데이터셋에서 분석을 수행할 수 있습니다. 산점도에서는 각 데이터셋의 출처별로 색상이 구분되어 시각적으로 비교하기 용이합니다.
    """)

st.markdown("""
### 📝 코드 사용법
1.  위 코드를 `app.py`와 같은 이름의 Python 파일로 저장합니다.
2.  터미널 또는 명령 프롬프트에서 다음 명령어를 실행하여 필요한 라이브러리를 설치합니다:
    ```bash
    pip install streamlit pandas plotly
    ```
3.  저장한 파일이 있는 디렉토리에서 다음 명령어를 실행하여 스트림릿 앱을 시작합니다:
    ```bash
    streamlit run app.py
    ```
    명령어 실행 후 웹 브라우저에서 자동으로 앱이 열릴 것입니다.

**데이터 형식**: 업로드할 CSV 파일은 반드시 `상권명`, `길단위인구수`, `치킨전문점수`라는 컬럼 이름을 포함해야 하며, `길단위인구수`와 `치킨전문점수`는 숫자 형식이어야 합니다.
""")
