# 예금/적금 만기 예상조회 웹서비스

기존 콘솔 기반 `deposit savings.py`를 FastAPI 백엔드와 React/Vite 프론트엔드로 분리한 웹앱입니다. 원본 콘솔 버전은 `legacy/console_app.py`에 보관했습니다.

## 주요 기능

- 직접 입력 계산기: 예금, 적금, 청년도약계좌, 청년미래적금
- 청년미래적금 일반형/우대형 계산 및 비교표
- 금융감독원 FINLIFE Open API 기반 예금/적금 상품 동기화
- 상품 검색, 즐겨찾기, 비교함, 상품별 만기 예상조회 연결
- 관리자 화면의 FINLIFE 동기화와 수동 상품 등록
- SQLite 기반 로컬 상품 DB와 동기화 로그

금융상품 검색 정보는 FINLIFE API와 수동 등록 데이터를 기반으로 하며, 모든 금융회사와 모든 상품을 보장하지 않습니다. 실제 가입 가능 여부와 우대 조건 적용 여부는 금융기관 심사 기준에 따라 달라질 수 있습니다.

## 프로젝트 구조

```text
backend/
  app/
    api/
    calculators/
    repositories/
    schemas/
    services/
  tests/
frontend/
  src/
legacy/
  console_app.py
render.yaml
.env.example
```

## 환경변수

루트의 `.env.example`을 참고하세요.

```text
FINLIFE_API_KEY=금융감독원_오픈API_키
DATABASE_URL=sqlite:///./financial_products.db
SYNC_ON_STARTUP=false
ADMIN_TOKEN=
ALLOWED_ORIGINS=
ALLOWED_ORIGIN_REGEX=https://.*\.onrender\.com
```

프론트엔드 로컬 실행 시 `frontend/.env`에 백엔드 주소를 넣을 수 있습니다.

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 백엔드 실행

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

기본 주소는 `http://127.0.0.1:8000`입니다. API 문서는 `http://127.0.0.1:8000/docs`에서 확인할 수 있습니다.

## 프론트엔드 실행

```bash
cd frontend
pnpm install
pnpm run dev
```

기본 주소는 `http://127.0.0.1:5173`입니다.

## 테스트

```bash
cd backend
pytest
```

테스트에는 청년미래적금 일반형/우대형 계산, 월 납입 한도 검증, 정부기여금 차이, 상품 저장소 검색/비교 검증이 포함되어 있습니다.

## API 예시

### 청년미래적금 계산

`POST /api/calculate/youth-future`

```json
{
  "monthly_amount": 500000,
  "annual_rate": 5,
  "benefit_type": "general"
}
```

응답 예시:

```json
{
  "product_type": "youth-future-general",
  "product_name": "청년미래적금 일반형",
  "months": 36,
  "principal": 18000000,
  "bank_interest": 1387500,
  "government_contribution": 1080000,
  "maturity_amount": 20467500
}
```

### 상품 검색

`GET /api/products?product_type=deposit&term_months=12&min_rate=3.5`

응답 예시:

```json
{
  "items": [
    {
      "id": 1,
      "product_type": "deposit",
      "product_name": "정기예금",
      "company_name": "샘플은행",
      "data_source": "finlife",
      "best_rate": 4.1,
      "best_term_months": 12,
      "options": []
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### 상품 비교

`POST /api/products/compare`

```json
{
  "product_ids": [1, 2]
}
```

### FINLIFE 동기화

`POST /api/admin/sync/finlife`

```json
{
  "product_types": ["deposit", "saving"],
  "sector_codes": ["020000", "030300"]
}
```

`ADMIN_TOKEN`을 설정한 경우 요청 헤더에 `X-Admin-Token`을 함께 보내야 합니다.

### 수동 상품 등록

`POST /api/admin/products`

```json
{
  "company_name": "샘플은행",
  "product_type": "deposit",
  "product_name": "샘플 정기예금",
  "join_method": "인터넷, 스마트폰",
  "option": {
    "saving_term_months": 12,
    "base_rate": 3.5,
    "maximum_rate": 4.1
  }
}
```

## 청년미래적금 계산 기준

- 가입기간: 36개월
- 월 납입 한도: 최대 500,000원
- 일반형 정부기여금: 총 납입 원금의 6%
- 우대형 정부기여금: 총 납입 원금의 12%
- 이자소득: 비과세
- 은행 이자: `monthly_amount * (annual_rate / 12) * (months * (months + 1) / 2)`
- 만기 예상 수령액: `principal + bank_interest + government_contribution`

정부기여금은 `1.12 * (원금 + 이자)` 방식이 아니라 원금 기준으로 별도 계산합니다.

## Render 배포

루트의 `render.yaml`을 사용해 Blueprint로 배포할 수 있습니다.

1. GitHub에 `backend/`, `frontend/`, `legacy/`, `README.md`, `.env.example`, `.gitignore`, `render.yaml`을 push합니다.
2. Render Dashboard에서 `New +` → `Blueprint`를 선택합니다.
3. GitHub 저장소를 연결하고 `render.yaml`을 적용합니다.
4. 백엔드 서비스 환경변수에 `FINLIFE_API_KEY`를 등록합니다.
5. 필요하면 `ADMIN_TOKEN`을 등록해 관리자 API를 보호합니다.

생성되는 서비스:

```text
deposit-saving-web-api  # FastAPI 백엔드
deposit-saving-web      # React 정적 사이트
```

프론트엔드의 `VITE_API_BASE_URL`은 `render.yaml`에서 백엔드 Render URL을 참조하도록 설정되어 있습니다.
