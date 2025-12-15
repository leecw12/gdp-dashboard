import streamlit as st
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="청담과 지역제한 설정", layout="wide")

st.title("📍 청담과 지역제한 설정")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # Google Maps API Key 입력
    api_key = st.text_input(
        "Google Maps API Key",
        value="AIzaSyAXXch5LHkdwrHGXP_LIBdyfIZW0b9ffI8",
        type="password",
        help="Google Cloud Console에서 발급받은 API Key를 입력하세요"
    )
    
    st.markdown("---")
    
    # 검색 기능
    st.subheader("🔍 장소 검색")
    search_query = st.text_input(
        "가게/장소 이름 또는 주소",
        placeholder="예: 스타벅스 강남점, 서울시청",
        help="가게 이름, 주소, 랜드마크 등을 검색하세요"
    )
    
    if st.button("🔍 검색", use_container_width=True, type="primary"):
        if search_query:
            st.session_state['search_query'] = search_query
            st.session_state['do_search'] = True
            st.rerun()
    
    st.markdown("---")
    
    # 중심 좌표 설정
    st.subheader("📌 중심 좌표 (또는 검색 사용)")
    latitude = st.number_input("위도 (Latitude)", value=37.5174448, format="%.6f", key="lat")
    longitude = st.number_input("경도 (Longitude)", value=127.0467984, format="%.6f", key="lng")
    
    if st.button("📍 현재 좌표로 이동", use_container_width=True):
        st.session_state['manual_center'] = True
        st.rerun()
    
    st.markdown("---")
    
    # 반경 설정
    st.subheader("📏 반경 설정")
    
    # 세션 스테이트에 반경 저장
    if 'radius_km' not in st.session_state:
        st.session_state['radius_km'] = 1.0
    
    # 반경 선택 옵션 생성 (0.1 ~ 4.0, 0.1 단위)
    radius_options = [round(x * 0.1, 1) for x in range(1, 41)]

    # 기본 선택값 인덱스
    default_index = radius_options.index(
        st.session_state.get('radius_km', 1.0)
    )

    radius_km = st.selectbox(
        "반경 (km)",
        options=radius_options,
        index=default_index,
        key="radius_input"
    )
        
    # 반경 값이 변경되었는지 확인
    if radius_km != st.session_state.get('radius_km'):
        st.session_state['radius_km'] = radius_km
        st.session_state['radius_changed'] = True
    
    radius_m = radius_km * 1000
    st.info(f"반경: {radius_km}km ({radius_m:,.0f}m)")
    
    # 반경 업데이트 버튼
    if st.button("🔄 반경 적용", use_container_width=True):
        st.session_state['radius_changed'] = True
        st.rerun()
    
    st.markdown("---")
    
    # 원 스타일 설정
    st.subheader("🎨 스타일 설정")
    circle_color = st.color_picker("원 색상", "#FF0000")
    circle_opacity = st.slider("투명도", 0.0, 1.0, 0.3, 0.1)
    stroke_opacity = st.slider("테두리 투명도", 0.0, 1.0, 0.8, 0.1)

# 세션 스테이트 초기화
if 'search_query' not in st.session_state:
    st.session_state['search_query'] = ""
if 'do_search' not in st.session_state:
    st.session_state['do_search'] = False
if 'manual_center' not in st.session_state:
    st.session_state['manual_center'] = False
if 'radius_changed' not in st.session_state:
    st.session_state['radius_changed'] = False
if 'radius_km' not in st.session_state:
    st.session_state['radius_km'] = 1.0

# 메인 화면 안내
col1, col2 = st.columns([3, 1])
with col1:
    st.info("💡 사이드바에서 가게/장소를 검색하거나 좌표를 직접 입력하세요. 반경 변경 후 '🔄 반경 적용' 버튼을 클릭하세요.")
with col2:
    if st.button("🔄 초기화"):
        st.session_state['search_query'] = ""
        st.session_state['do_search'] = False
        st.session_state['manual_center'] = False
        st.session_state['radius_changed'] = False
        st.session_state['radius_km'] = 1.0
        st.rerun()

if api_key == "YOUR_API_KEY_HERE" or not api_key:
    st.warning("""
    ⚠️ **Google Maps API Key를 입력하세요!**
    
    API Key 발급 방법은 아래 '📖 Google Maps API Key 발급 방법'을 펼쳐서 확인하세요.
    """)

# HTML/JavaScript 코드
map_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Maps</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
        #map {{
            width: 100%;
            height: 600px;
        }}
        .info-window {{
            font-family: Arial, sans-serif;
            font-size: 14px;
            padding: 10px;
            max-width: 300px;
        }}
        .info-window strong {{
            display: block;
            margin-bottom: 5px;
            font-size: 16px;
            color: #1a73e8;
        }}
        .info-window .address {{
            color: #666;
            margin-top: 5px;
            font-size: 12px;
        }}
        .info-window .phone {{
            color: #1a73e8;
            margin-top: 5px;
        }}
        #search-status {{
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            padding: 10px 20px;
            border-radius: 5px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            z-index: 1000;
            display: none;
            font-family: Arial, sans-serif;
        }}
        .status-success {{
            border-left: 4px solid #4CAF50;
        }}
        .status-error {{
            border-left: 4px solid #f44336;
        }}
    </style>
</head>
<body>
    <div id="search-status"></div>
    <div id="map"></div>
    
    <script>
        let map;
        let marker;
        let circle;
        let infoWindow;
        let placesService;
        let searchMarkers = [];
        let searchCircles = [];
        
        function initMap() {{
            // 지도 생성
            const center = {{ lat: {latitude}, lng: {longitude} }};
            
            map = new google.maps.Map(document.getElementById('map'), {{
                center: center,
                zoom: 13,
                mapTypeControl: true,
                streetViewControl: true,
                fullscreenControl: true
            }});
            
            // Places Service 초기화
            placesService = new google.maps.places.PlacesService(map);
            
            // 마커 생성
            marker = new google.maps.Marker({{
                position: center,
                map: map,
                title: '중심점',
                draggable: true,
                animation: google.maps.Animation.DROP,
                icon: {{
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 10,
                    fillColor: '{circle_color}',
                    fillOpacity: 1,
                    strokeColor: 'white',
                    strokeWeight: 2
                }}
            }});
            
            // 원형 반경 생성
            circle = new google.maps.Circle({{
                map: map,
                center: center,
                radius: {radius_m},
                strokeColor: '{circle_color}',
                strokeOpacity: {stroke_opacity},
                strokeWeight: 2,
                fillColor: '{circle_color}',
                fillOpacity: {circle_opacity},
                editable: false
            }});
            
            // 정보창 생성
            infoWindow = new google.maps.InfoWindow();
            
            // 마커 클릭 이벤트
            marker.addListener('click', function() {{
                infoWindow.setContent(`
                    <div class="info-window">
                        <strong>중심점</strong>
                        <div>위도: {latitude}</div>
                        <div>경도: {longitude}</div>
                        <div>반경: {radius_km}km</div>
                    </div>
                `);
                infoWindow.open(map, marker);
            }});
            
            // 지도 클릭 이벤트
            map.addListener('click', function(e) {{
                updateCenter(e.latLng);
            }});
            
            // 마커 드래그 이벤트
            marker.addListener('dragend', function(e) {{
                updateCenter(e.latLng);
            }});
            
            // 검색 실행
            const searchQuery = "{st.session_state.get('search_query', '')}";
            const doSearch = {'true' if st.session_state.get('do_search', False) else 'false'};
            const manualCenter = {'true' if st.session_state.get('manual_center', False) else 'false'};
            const radiusChanged = {'true' if st.session_state.get('radius_changed', False) else 'false'};
            
            if (doSearch && searchQuery) {{
                searchPlace(searchQuery);
            }} else if (manualCenter) {{
                updateCenter(new google.maps.LatLng({latitude}, {longitude}));
            }} else if (radiusChanged) {{
                // 반경만 변경된 경우 - 모든 원의 반경 업데이트
                circle.setRadius({radius_m});
                searchCircles.forEach(c => c.setRadius({radius_m}));
                console.log('반경 업데이트:', {radius_km}, 'km');
            }}
            
            console.log('✅ 지도 로드 성공!');
        }}
        
        function updateCenter(position, placeName = null) {{
            marker.setPosition(position);
            circle.setCenter(position);
            map.panTo(position);
            
            const title = placeName || '중심점';
            
            infoWindow.setContent(`
                <div class="info-window">
                    <strong>${{title}}</strong>
                    <div>위도: ${{position.lat().toFixed(6)}}</div>
                    <div>경도: ${{position.lng().toFixed(6)}}</div>
                    <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee;">
                        🔵 반경: {radius_km}km
                    </div>
                </div>
            `);
        }}
        
        function searchPlace(query) {{
            showStatus('검색 중...', 'status-success');
            
            // 기존 검색 마커 및 원 제거
            searchMarkers.forEach(m => m.setMap(null));
            searchMarkers = [];
            searchCircles.forEach(c => c.setMap(null));
            searchCircles = [];
            
            const request = {{
                query: query,
                fields: ['name', 'geometry', 'formatted_address', 'formatted_phone_number', 'rating', 'user_ratings_total']
            }};
            
            placesService.findPlaceFromQuery(request, function(results, status) {{
                if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length > 0) {{
                    const place = results[0];
                    const location = place.geometry.location;
                    
                    // 중심점 및 원 업데이트
                    updateCenter(location, place.name);
                    
                    // 상세 정보 가져오기
                    const detailRequest = {{
                        placeId: place.place_id,
                        fields: ['name', 'formatted_address', 'formatted_phone_number', 'rating', 'user_ratings_total', 'opening_hours', 'website']
                    }};
                    
                    placesService.getDetails(detailRequest, function(placeDetails, status) {{
                        if (status === google.maps.places.PlacesServiceStatus.OK) {{
                            let content = `
                                <div class="info-window">
                                    <strong>${{placeDetails.name}}</strong>
                            `;
                            
                            if (placeDetails.rating) {{
                                content += `<div>⭐ ${{placeDetails.rating}} (${{placeDetails.user_ratings_total || 0}} 리뷰)</div>`;
                            }}
                            
                            if (placeDetails.formatted_address) {{
                                content += `<div class="address">📍 ${{placeDetails.formatted_address}}</div>`;
                            }}
                            
                            if (placeDetails.formatted_phone_number) {{
                                content += `<div class="phone">📞 ${{placeDetails.formatted_phone_number}}</div>`;
                            }}
                            
                            if (placeDetails.opening_hours) {{
                                const isOpen = placeDetails.opening_hours.isOpen();
                                content += `<div style="margin-top: 5px; color: ${{isOpen ? 'green' : 'red'}};">
                                    ${{isOpen ? '🟢 영업 중' : '🔴 영업 종료'}}
                                </div>`;
                            }}
                            
                            if (placeDetails.website) {{
                                content += `<div style="margin-top: 5px;">
                                    <a href="${{placeDetails.website}}" target="_blank">🌐 웹사이트</a>
                                </div>`;
                            }}
                            
                            content += `<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                                <div style="font-size: 14px; color: #1a73e8; font-weight: bold;">🔵 반경: {radius_km}km</div>
                                <div style="font-size: 12px; color: #666; margin-top: 3px;">반경 내 영역이 표시됩니다</div>
                            </div></div>`;
                            
                            infoWindow.setContent(content);
                            infoWindow.open(map, marker);
                        }}
                    }});
                    
                    map.setZoom(15);
                    showStatus(`✅ "${{place.name}}" 검색 완료!`, 'status-success');
                    
                }} else {{
                    showStatus('❌ 검색 결과를 찾을 수 없습니다.', 'status-error');
                    
                    // Text Search로 재시도
                    textSearch(query);
                }}
            }});
        }}
        
        function textSearch(query) {{
            const request = {{
                query: query,
                location: map.getCenter(),
                radius: 5000
            }};
            
            placesService.textSearch(request, function(results, status) {{
                if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length > 0) {{
                    showStatus(`${{results.length}}개의 결과를 찾았습니다.`, 'status-success');
                    
                    // 첫 번째 결과로 중심 원 이동
                    const firstPlace = results[0];
                    updateCenter(firstPlace.geometry.location, firstPlace.name);
                    map.setZoom(14);
                    
                    // 여러 결과 마커 및 반경 표시 (최대 5개)
                    results.slice(0, 5).forEach((place, index) => {{
                        // 검색 마커
                        const searchMarker = new google.maps.Marker({{
                            position: place.geometry.location,
                            map: map,
                            label: {{
                                text: String(index + 1),
                                color: 'white',
                                fontSize: '12px',
                                fontWeight: 'bold'
                            }},
                            icon: {{
                                path: google.maps.SymbolPath.CIRCLE,
                                scale: 12,
                                fillColor: '#4285F4',
                                fillOpacity: 1,
                                strokeColor: 'white',
                                strokeWeight: 2
                            }}
                        }});
                        
                        // 각 검색 결과마다 반경 원 생성
                        const searchCircle = new google.maps.Circle({{
                            map: map,
                            center: place.geometry.location,
                            radius: {radius_m},
                            strokeColor: index === 0 ? '{circle_color}' : '#4285F4',
                            strokeOpacity: {stroke_opacity} * 0.6,
                            strokeWeight: index === 0 ? 2 : 1,
                            fillColor: index === 0 ? '{circle_color}' : '#4285F4',
                            fillOpacity: {circle_opacity} * 0.5,
                            editable: false
                        }});
                        
                        searchCircles.push(searchCircle);
                        
                        searchMarker.addListener('click', function() {{
                            // 클릭한 위치를 메인 중심으로 설정
                            updateCenter(place.geometry.location, place.name);
                            
                            // 메인 원을 해당 위치로 이동
                            circle.setCenter(place.geometry.location);
                            marker.setPosition(place.geometry.location);
                            
                            infoWindow.setContent(`
                                <div class="info-window">
                                    <strong>${{place.name}}</strong>
                                    <div class="address">📍 ${{place.formatted_address || '주소 정보 없음'}}</div>
                                    ${{place.rating ? `<div>⭐ ${{place.rating}}</div>` : ''}}
                                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                                        🔵 반경: {radius_km}km
                                    </div>
                                    <div style="margin-top: 5px; font-size: 12px; color: #666;">
                                        총 ${{results.length}}개 결과 중 ${{index + 1}}번
                                    </div>
                                </div>
                            `);
                            infoWindow.open(map, marker);
                        }});
                        
                        searchMarkers.push(searchMarker);
                    }});
                    
                    // 첫 번째 결과 정보 표시
                    infoWindow.setContent(`
                        <div class="info-window">
                            <strong>${{results[0].name}}</strong>
                            <div class="address">📍 ${{results[0].formatted_address || '주소 정보 없음'}}</div>
                            ${{results[0].rating ? `<div>⭐ ${{results[0].rating}}</div>` : ''}}
                            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                                🔵 반경: {radius_km}km
                            </div>
                            <div style="margin-top: 5px; font-size: 12px; color: #666;">
                                총 ${{results.length}}개 결과 (각 위치마다 반경 표시)
                            </div>
                        </div>
                    `);
                    infoWindow.open(map, marker);
                    
                }} else {{
                    showStatus('❌ 검색 결과를 찾을 수 없습니다.', 'status-error');
                }}
            }});
        }}
        
        function showStatus(message, className) {{
            const statusDiv = document.getElementById('search-status');
            statusDiv.textContent = message;
            statusDiv.className = className;
            statusDiv.style.display = 'block';
            
            setTimeout(function() {{
                statusDiv.style.display = 'none';
            }}, 3000);
        }}
        
        window.initMap = initMap;
    </script>
    
    <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap&libraries=places&language=ko" async defer></script>
</body>
</html>
"""

# 검색 후 세션 스테이트 리셋
if st.session_state.get('do_search', False):
    st.session_state['do_search'] = False
if st.session_state.get('manual_center', False):
    st.session_state['manual_center'] = False
if st.session_state.get('radius_changed', False):
    st.session_state['radius_changed'] = False

# HTML 렌더링
components.html(map_html, height=650)

# 하단 정보 표시
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("중심 위도", f"{latitude:.6f}")
with col2:
    st.metric("중심 경도", f"{longitude:.6f}")
with col3:
    st.metric("반경", f"{radius_km} km")
with col4:
    st.metric("면적", f"{3.14159 * radius_km * radius_km:.2f} km²")

# 검색 예시
if st.session_state.get('search_query'):
    st.info(f"🔍 마지막 검색: **{st.session_state['search_query']}**")

# 사용 가이드
st.markdown("---")
with st.expander("📖 Google Maps API Key 발급 방법"):
    st.markdown("""
    ### Google Maps API Key 발급하기
    
    #### 1. Google Cloud Console 접속
    - https://console.cloud.google.com/ 접속
    - Google 계정으로 로그인
    
    #### 2. 프로젝트 생성
    - 상단의 프로젝트 선택 → "새 프로젝트" 클릭
    - 프로젝트 이름 입력 (예: "지도 앱")
    - "만들기" 클릭
    
    #### 3. 필요한 API 활성화 (중요!)
    
    **반드시 2개 API 모두 활성화:**
    
    a) **Maps JavaScript API**
    - 좌측 메뉴 → "API 및 서비스" → "라이브러리"
    - "Maps JavaScript API" 검색 → 선택
    - "사용 설정" 클릭
    
    b) **Places API** (가게 검색용)
    - 같은 방법으로 "Places API" 검색 → 선택
    - "사용 설정" 클릭
    
    #### 4. API Key 생성
    - 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
    - 상단 "+ 사용자 인증 정보 만들기" → "API 키" 선택
    - API Key가 생성됨 → 복사
    
    #### 💰 비용 정보
    - **월 $200 무료 크레딧** 제공
    - Maps JavaScript API: 월 28,000회 로드 무료
    - Places API: 월 약 17,000회 검색 무료
    - 일반적인 개인 사용은 무료 범위 내
    - 신용카드 등록 필요 (과금 방지 설정 가능)
    
    #### 🔗 자세한 가이드
    - https://developers.google.com/maps/documentation/javascript/get-api-key
    - https://developers.google.com/maps/documentation/places/web-service/overview
    """)

with st.expander("📖 사용 가이드"):
    st.markdown("""
    ### 🔍 가게/장소 검색 기능
    
    **검색 방법:**
    1. 사이드바의 "🔍 장소 검색" 입력창에 검색어 입력
    2. "🔍 검색" 버튼 클릭
    3. 지도에서 자동으로 해당 위치로 이동
    4. **검색한 위치를 중심으로 설정한 반경이 자동으로 표시됩니다** ✨
    
    **검색 가능한 것들:**
    - 가게 이름: "스타벅스 강남점", "맥도날드 홍대점"
    - 브랜드명: "이디야", "CU편의점"
    - 장소/건물: "서울시청", "코엑스", "롯데타워"
    - 주소: "서울시 강남구 테헤란로 123"
    - 랜드마크: "남산타워", "광화문"
    
    **검색 결과 표시:**
    - **정확한 1개 결과**: 해당 위치로 이동 + 반경 표시 + 상세 정보
    - **여러 개 결과**: 최대 5개 위치에 각각 반경 원 표시 (번호 1-5)
      - 각 검색 결과마다 개별 반경 원이 표시됩니다
      - 첫 번째 결과는 빨간색, 나머지는 파란색으로 구분
      - 마커 클릭 시 해당 위치가 메인 중심이 되고 빨간 원으로 변경
    
    **상세 정보 포함:**
    - 📍 주소
    - ⭐ 평점 및 리뷰 수
    - 📞 전화번호
    - 🟢/🔴 영업 중 여부
    - 🌐 웹사이트 (있는 경우)
    - 🔵 설정된 반경 거리
    
    ### 📏 반경 기능
    
    1. **사이드바에서 반경 설정**
       - 0.1 ~ 50km 범위 설정
       - 검색 전/후 언제든 변경 가능
    
    2. **검색 시 반경 자동 표시**
       - 검색한 위치를 중심으로 설정한 반경이 즉시 표시됩니다
       - 여러 검색 결과가 있으면 각 위치마다 반경 표시
    
    3. **반경 활용 예시**
       - "스타벅스 강남역점" 검색 + 반경 1km → 해당 매장 1km 반경 표시
       - "편의점" 검색 + 반경 500m → 검색된 여러 편의점 각각에 500m 반경 표시
    
    ### 📌 기본 기능
    
    1. **좌표 직접 입력**
       - 위도/경도를 직접 입력
       - "📍 현재 좌표로 이동" 버튼 클릭
    
    2. **지도 인터랙션**
       - 지도 클릭: 중심점 이동
       - 마커 드래그: 중심점 이동
       - 검색 마커 클릭: 해당 위치를 메인 중심으로 설정
    
    ### 💡 검색 팁
    
    - **구체적으로 검색**: "스타벅스" 보다 "스타벅스 강남역점"
    - **지역명 추가**: "맥도날드 서울" 처럼 지역 포함
    - **정확한 이름**: 정식 명칭 사용 시 정확도 ↑
    - **반경 먼저 설정**: 검색 전에 원하는 반경을 먼저 설정하면 검색 후 바로 반영
    
    ### 주요 도시 좌표
    
    - **서울시청**: 37.5665, 126.9780
    - **부산시청**: 35.1796, 129.0756
    - **강남역**: 37.4979, 127.0276
    - **홍대입구역**: 37.5572, 126.9239
    """)

with st.expander("🆕 새로운 기능 (v2.0)"):
    st.markdown("""
    ### ✨ 주요 업데이트
    
    #### 🔍 검색 위치 반경 표시 (NEW!)
    - **검색한 장소를 중심으로 자동 반경 표시**
    - 여러 검색 결과가 있으면 각 위치마다 반경 원 표시
    - 첫 번째 결과는 빨간색, 나머지는 파란색으로 구분
    - 검색 마커 클릭 시 해당 위치가 메인 중심으로 변경
    
    #### 📏 동적 반경 조정
    - 사이드바에서 반경 변경 시 실시간 반영
    - 검색 전/후 언제든 반경 조정 가능
    - 검색된 모든 위치에 동일한 반경 적용
    
    #### 🎨 시각적 개선
    - 메인 중심점: 빨간색 원
    - 검색 결과: 파란색 원 (투명도 조정)
    - 번호 매긴 검색 결과 마커 (1-5)
    - 클릭 시 색상 변경으로 현재 중심 표시
    
    #### 💡 활용 예시
    
    1. **매장 상권 분석**
       - "스타벅스 강남역점" 검색
       - 반경 1km 설정
       - → 해당 매장 1km 상권 범위 확인
    
    2. **여러 지점 비교**
       - "편의점" 검색
       - 반경 500m 설정
       - → 각 편의점의 500m 반경 비교
    
    3. **배달 가능 범위**
       - 원하는 식당 검색
       - 배달 가능 거리(예: 2km) 설정
       - → 배달 가능 영역 시각화
    """)

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>"
    "💻 구글 지도 반경 표시 & 가게 검색 앱 | Powered by Google Maps & Places API<br/>"
    "⚠️ Places API 활성화 필수"
    "</div>",
    unsafe_allow_html=True
)
