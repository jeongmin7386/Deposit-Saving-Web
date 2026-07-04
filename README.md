# 예금/적금 웹 계산기

기존 콘솔 기반 `deposit savings.py`를 FastAPI 백엔드와 React/Vite 프론트엔드로 분리한 웹 계산기입니다. 원본 콘솔 버전은 `legacy/console_app.py`에 보관했습니다.

## 주요 기능

- 예금 계산
- 적금 계산
- 청년도약계좌 계산
- 청년미래적금 일반형/우대형 계산
- 청년미래적금 일반형/우대형 비교표
- 총 납입 원금, 은행 이자, 정부기여금, 만기 예상 수령액 표시

## 프로젝트 구조

```text
backend/
  app/
    api/
    calculators/
    schemas/
  tests/
frontend/
  src/
legacy/
  console_app.py
render.yaml
```

## 로컬 백엔드 실행

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

기본 주소는 `http://127.0.0.1:8000`입니다.

## 로컬 프론트엔드 실행

```bash
cd frontend
pnpm install
pnpm run dev
```

기본 주소는 `http://127.0.0.1:5173`입니다. 백엔드 주소를 바꾸려면 `frontend/.env`에 아래 값을 설정합니다.

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Render 배포

이 저장소는 루트의 `render.yaml`을 사용해 Render Blueprint로 배포할 수 있습니다.

1. GitHub에 아래 파일과 폴더를 push합니다.

```text
backend/
frontend/
legacy/
README.md
.gitignore
render.yaml
```

2. Render Dashboard에서 `New +` → `Blueprint`를 선택합니다.
3. GitHub 저장소를 연결합니다.
4. Render가 루트의 `render.yaml`을 인식하면 적용합니다.
5. 배포가 끝나면 두 서비스가 생성됩니다.

```text
deposit-saving-web-api  # FastAPI 백엔드
deposit-saving-web      # React 정적 사이트
```

`render.yaml`의 핵심 설정은 아래와 같습니다.

- 백엔드: `backend` 폴더를 Python Web Service로 배포
- 백엔드 시작 명령: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- 프론트엔드: `frontend` 폴더를 Static Site로 배포
- 프론트엔드 빌드 명령: `pnpm install --frozen-lockfile && pnpm run build`
- 프론트엔드 배포 폴더: `dist`
- 프론트엔드의 `VITE_API_BASE_URL`은 백엔드 Render URL을 자동 참조

React 라우팅을 위해 `/*` 요청은 `/index.html`로 rewrite됩니다.

## 수동 배포 방식

Blueprint를 쓰지 않는다면 Render에서 서비스를 두 개 직접 만듭니다.

### 백엔드 Web Service

- Root Directory: `backend`
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

### 프론트엔드 Static Site

- Root Directory: `frontend`
- Build Command: `pnpm install --frozen-lockfile && pnpm run build`
- Publish Directory: `dist`
- Environment Variable:

```text
VITE_API_BASE_URL=https://백엔드서비스이름.onrender.com
```

## 테스트

```bash
cd backend
pytest
```

청년미래적금 테스트는 월 500,000원, 연 5%, 36개월 기준의 일반형/우대형 계산, 월 납입 한도 검증, 정부기여금 차이를 확인합니다.

## API 예시

### 청년미래적금

`POST /api/calculate/youth-future`

```json
{
  "monthly_amount": 500000,
  "annual_rate": 5.0,
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

## 청년미래적금 계산 기준

- 가입기간: 36개월
- 월 납입 한도: 최대 500,000원
- 일반형 정부기여금: 총 납입 원금의 6%
- 우대형 정부기여금: 총 납입 원금의 12%
- 이자소득: 비과세
- 은행 이자: `monthly_amount * (annual_rate / 12) * (months * (months + 1) / 2)`
- 만기 예상 수령액: `principal + bank_interest + government_contribution`

정부기여금은 `1.12 * (원금 + 이자)` 방식이 아니라 원금 기준으로 별도 계산합니다.
