# event_type
EVENT_TYPE_CANDIDATES = [
    {
        "key": "meeting",
        "name": "회의",
        "description": "여러 사람이 모여 논의, 정보 공유, 의사결정, 업무 조율을 하는 일정",
        "examples": ["정기 팀위클리", "프로젝트 미팅", "회의 안건 논의", "weekly sync"],
    },
    {
        "key": "presentation",
        "name": "발표",
        "description": "청중 앞에서 자료, 결과물, 프로젝트 내용을 설명하거나 공유하는 일정",
        "examples": ["캡스톤 최종 발표", "수업 발표", "프로젝트 PT", "데모데이 발표"],
    },
    {
        "key": "hospital",
        "name": "병원",
        "description": "진료, 검사, 건강검진, 치료, 병원 예약과 관련된 일정",
        "examples": ["건강검진 예약", "치과 진료", "병원 방문", "검사 예약"],
    },
    {
        "key": "birthday",
        "name": "생일",
        "description": "가족, 친구, 지인의 생일이나 생신을 챙기는 일정",
        "examples": ["아버지 생신", "친구 생일", "생일 파티"],
    },
    {
        "key": "travel_departure",
        "name": "여행 출발",
        "description": "국내외 여행, 출장, 이동이 포함된 일정",
        "examples": ["제주도 일정", "부산 여행", "해외여행", "출장"],
    },
    {
        "key": "exam",
        "name": "시험",
        "description": "학교, 자격증, 평가 시험을 치르는 일정",
        "examples": ["중간고사", "기말고사", "토익 시험", "자격증 시험"],
    },
]

# context
CONTEXT_CANDIDATES = [
    {
        "key": "school",
        "name": "학교",
        "description": "학교, 수업, 학과, 과제, 시험, 캠퍼스 활동과 관련된 맥락",
        "examples": ["학교 캡스톤 발표", "중간고사", "수업 발표", "과제 제출"],
    },
    {
        "key": "work",
        "name": "업무",
        "description": "회사, 업무, 거래처, 직장, 회의, 프로젝트와 관련된 맥락",
        "examples": ["업무 회의", "거래처 미팅", "회사 프로젝트", "팀 위클리"],
    },
    {
        "key": "family",
        "name": "가족",
        "description": "부모님, 형제자매, 친척 등 가족 관계와 관련된 맥락",
        "examples": ["아버지 생신", "가족 모임", "부모님 병원 동행"],
    },
    {
        "key": "health",
        "name": "건강",
        "description": "진료, 검사, 건강검진, 치료, 약 처방 등 건강관리와 관련된 맥락",
        "examples": ["건강검진", "병원 예약", "치과 진료", "검사 결과 상담"],
    },
    {
        "key": "social",
        "name": "사적 약속",
        "description": "친구, 지인, 모임, 식사, 약속 등 사적인 만남과 관련된 맥락",
        "examples": ["친구 약속", "저녁 모임", "생일 파티", "카페 약속"],
    },
    {
        "key": "team_project",
        "name": "팀 프로젝트",
        "description": "팀플, 조별과제, 캡스톤, 협업 프로젝트처럼 여러 사람이 함께 수행하는 맥락",
        "examples": ["캡스톤 최종 발표", "팀플 회의", "프로젝트 위클리", "조별과제"],
    },
]

# place_type
PLACE_TYPE_CANDIDATES = [
    {
        "key": "school",
        "name": "학교",
        "description": "학교, 캠퍼스, 강의실, 대학교, 교실과 같은 장소 유형",
        "examples": ["학교", "강의실", "캠퍼스", "대학교"],
    },
    {
        "key": "office",
        "name": "사무실",
        "description": "회사, 사무실, 회의실, 업무 공간과 같은 장소 유형",
        "examples": ["회사", "사무실", "회의실", "오피스"],
    },
    {
        "key": "hospital",
        "name": "병원",
        "description": "병원, 의원, 치과, 검진센터, 보건소와 같은 의료 장소 유형",
        "examples": ["병원", "치과", "검진센터", "의원"],
    },
    {
        "key": "restaurant",
        "name": "음식점",
        "description": "식당, 카페, 음식점, 술집 등 식사나 만남을 위한 장소 유형",
        "examples": ["식당", "카페", "레스토랑", "술집"],
    },
    {
        "key": "transit",
        "name": "교통시설",
        "description": "역, 터미널, 공항, 정류장 등 이동과 관련된 장소 유형",
        "examples": ["서울역", "공항", "버스터미널", "지하철역"],
    },
    {
        "key": "home",
        "name": "집",
        "description": "집, 자택, 본가, 자취방 등 거주 공간과 관련된 장소 유형",
        "examples": ["집", "자택", "본가", "자취방"],
    },
    {
        "key": "online",
        "name": "온라인",
        "description": "Zoom, Google Meet, Discord 등 온라인으로 진행되는 공간 유형",
        "examples": ["Zoom", "Google Meet", "디스코드", "온라인 회의"],
    },
]