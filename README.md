# 예금/적금 웹 계산기

기존 콘솔 기반 `deposit savings.py`를 프론트엔드와 백엔드가 분리된 웹앱 구조로 리팩토링한 프로젝트입니다. 원본 콘솔 버전은 `legacy/console_app.py`에 보관했습니다.

## 구조

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
```

## 백엔드 실행

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

기본 주소는 `http://127.0.0.1:8000`입니다.

## 프론트엔드 실행

```bash
cd frontend
pnpm install
pnpm run dev
```

기본 주소는 `http://127.0.0.1:5173`입니다. 백엔드 주소를 바꾸려면 `frontend/.env`에 아래 값을 설정합니다.

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 테스트

```bash
cd backend
pytest
```

청년미래적금 테스트는 월 500,000원, 연 5%, 36개월 기준의 일반형/우대형 계산, 월 납입 한도 검증, 정부기여금 차이를 확인합니다.

## API

### 예금

`POST /api/calculate/deposit`

```json
{
  "monthly_amount": 10000000,
  "annual_rate": 4.2,
  "months": 12
}
```

### 적금

`POST /api/calculate/saving`

```json
{
  "monthly_amount": 300000,
  "annual_rate": 4.5,
  "months": 24
}
```

### 청년도약계좌

`POST /api/calculate/youth-leap`

```json
{
  "monthly_amount": 700000,
  "annual_rate": 5.0,
  "annual_income": 36000000
}
```

`annual_income`을 생략하면 정부기여금은 0원으로 계산합니다.

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
  "maturity_amount": 20467500,
  "notices": [
    "청년미래적금은 36개월, 월 최대 500,000원 납입 기준입니다.",
    "정부기여금은 원금 기준으로 별도 계산되며 이자소득은 비과세로 처리했습니다.",
    "중소기업 우대형 요건을 충족하지 못하면 일반형 혜택으로 지급될 수 있습니다.",
    "실제 가입 가능 여부는 금융기관 심사 기준에 따라 달라질 수 있습니다."
  ],
  "comparison": [
    {
      "product_type": "youth-future-general",
      "product_name": "청년미래적금 일반형",
      "months": 36,
      "principal": 18000000,
      "bank_interest": 1387500,
      "government_contribution": 1080000,
      "maturity_amount": 20467500,
      "notices": [
        "청년미래적금은 36개월, 월 최대 500,000원 납입 기준입니다.",
        "정부기여금은 원금 기준으로 별도 계산되며 이자소득은 비과세로 처리했습니다."
      ]
    },
    {
      "product_type": "youth-future-preferred",
      "product_name": "청년미래적금 우대형",
      "months": 36,
      "principal": 18000000,
      "bank_interest": 1387500,
      "government_contribution": 2160000,
      "maturity_amount": 21547500,
      "notices": [
        "청년미래적금은 36개월, 월 최대 500,000원 납입 기준입니다.",
        "정부기여금은 원금 기준으로 별도 계산되며 이자소득은 비과세로 처리했습니다."
      ]
    }
  ]
}
```

## 계산 기준

청년미래적금은 아래 기준으로 계산합니다.

- 가입기간: 36개월
- 월 납입 한도: 최대 500,000원
- 일반형 정부기여금: 총 납입 원금의 6%
- 우대형 정부기여금: 총 납입 원금의 12%
- 이자소득: 비과세
- 은행 이자: `monthly_amount * (annual_rate / 12) * (months * (months + 1) / 2)`
- 만기 예상 수령액: `principal + bank_interest + government_contribution`

정부기여금은 `1.12 * (원금 + 이자)` 방식이 아니라 원금 기준으로 별도 계산합니다.

