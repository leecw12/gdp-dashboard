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

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>"
    "💻 구글 지도 반경 표시 & 가게 검색 앱 | Powered by Google Maps & Places API<br/>"
    "⚠️ Places API 활성화 필수"
    "</div>",
    unsafe_allow_html=True
)
