import { useMemo, useState } from "react";
import {
  BadgePercent,
  Calculator,
  Coins,
  Landmark,
  Loader2,
  WalletCards,
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const products = [
  {
    id: "deposit",
    label: "예금",
    endpoint: "/api/calculate/deposit",
    icon: Landmark,
    amountLabel: "예치 금액",
    monthsLabel: "예치 기간",
    defaultMonths: 12,
  },
  {
    id: "saving",
    label: "적금",
    endpoint: "/api/calculate/saving",
    icon: WalletCards,
    amountLabel: "월 납입액",
    monthsLabel: "납입 기간",
    defaultMonths: 12,
  },
  {
    id: "youth-leap",
    label: "청년도약계좌",
    endpoint: "/api/calculate/youth-leap",
    icon: BadgePercent,
    amountLabel: "월 납입액",
    fixedMonths: 60,
  },
  {
    id: "youth-future",
    label: "청년미래적금",
    endpoint: "/api/calculate/youth-future",
    icon: Coins,
    amountLabel: "월 납입액",
    fixedMonths: 36,
  },
];

const productMap = Object.fromEntries(products.map((product) => [product.id, product]));

function formatKrw(value) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(Number(value ?? 0));
}

function App() {
  const [productId, setProductId] = useState("youth-future");
  const [amount, setAmount] = useState("500000");
  const [annualRate, setAnnualRate] = useState("5");
  const [months, setMonths] = useState("12");
  const [benefitType, setBenefitType] = useState("general");
  const [annualIncome, setAnnualIncome] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const selectedProduct = productMap[productId];

  const payload = useMemo(() => {
    const basePayload = {
      monthly_amount: amount,
      annual_rate: annualRate,
    };

    if (productId === "deposit" || productId === "saving") {
      return { ...basePayload, months };
    }

    if (productId === "youth-leap") {
      return annualIncome
        ? { ...basePayload, annual_income: annualIncome }
        : basePayload;
    }

    return { ...basePayload, benefit_type: benefitType };
  }, [amount, annualIncome, annualRate, benefitType, months, productId]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_BASE_URL}${selectedProduct.endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        const message = Array.isArray(data.detail)
          ? data.detail.map((item) => item.msg).join(" ")
          : data.detail || "계산 요청을 처리하지 못했습니다.";
        throw new Error(message);
      }

      setResult(data);
    } catch (requestError) {
      setResult(null);
      setError(requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleProductChange(nextProductId) {
    setProductId(nextProductId);
    setResult(null);
    setError("");
    const nextProduct = productMap[nextProductId];
    if (nextProduct.defaultMonths) {
      setMonths(String(nextProduct.defaultMonths));
    }
    if (nextProductId === "youth-future") {
      setAmount("500000");
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <div className="panel form-panel">
          <div className="title-row">
            <div>
              <p className="eyebrow">Deposit Savings Calculator</p>
              <h1>예금/적금 계산기</h1>
            </div>
            <Calculator aria-hidden="true" />
          </div>

          <form onSubmit={handleSubmit}>
            <div className="product-grid" role="tablist" aria-label="상품 유형">
              {products.map((product) => {
                const Icon = product.icon;
                const isSelected = product.id === productId;
                return (
                  <button
                    className={`product-button ${isSelected ? "selected" : ""}`}
                    key={product.id}
                    type="button"
                    onClick={() => handleProductChange(product.id)}
                    aria-pressed={isSelected}
                  >
                    <Icon size={18} aria-hidden="true" />
                    <span>{product.label}</span>
                  </button>
                );
              })}
            </div>

            {productId === "youth-future" && (
              <div className="segmented" aria-label="청년미래적금 상품 유형">
                <button
                  type="button"
                  className={benefitType === "general" ? "active" : ""}
                  onClick={() => setBenefitType("general")}
                >
                  일반형
                </button>
                <button
                  type="button"
                  className={benefitType === "preferred" ? "active" : ""}
                  onClick={() => setBenefitType("preferred")}
                >
                  우대형
                </button>
              </div>
            )}

            <div className="field-grid">
              <label>
                <span>{selectedProduct.amountLabel}</span>
                <input
                  inputMode="numeric"
                  min="1"
                  step="10000"
                  type="number"
                  value={amount}
                  onChange={(event) => setAmount(event.target.value)}
                  required
                />
              </label>

              <label>
                <span>연 금리(%)</span>
                <input
                  inputMode="decimal"
                  min="0"
                  max="100"
                  step="0.01"
                  type="number"
                  value={annualRate}
                  onChange={(event) => setAnnualRate(event.target.value)}
                  required
                />
              </label>

              {selectedProduct.fixedMonths ? (
                <label>
                  <span>가입 기간</span>
                  <input value={`${selectedProduct.fixedMonths}개월`} disabled />
                </label>
              ) : (
                <label>
                  <span>{selectedProduct.monthsLabel}</span>
                  <input
                    inputMode="numeric"
                    min="1"
                    max="120"
                    type="number"
                    value={months}
                    onChange={(event) => setMonths(event.target.value)}
                    required
                  />
                </label>
              )}

              {productId === "youth-leap" && (
                <label>
                  <span>개인 연소득</span>
                  <input
                    inputMode="numeric"
                    min="0"
                    step="1000000"
                    type="number"
                    placeholder="선택 입력"
                    value={annualIncome}
                    onChange={(event) => setAnnualIncome(event.target.value)}
                  />
                </label>
              )}
            </div>

            {error && <p className="error-message">{error}</p>}

            <button className="submit-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="spin" size={18} /> : <Calculator size={18} />}
              <span>계산하기</span>
            </button>
          </form>
        </div>

        <div className="result-column">
          <ResultSummary result={result} productId={productId} />
          {productId === "youth-future" && <YouthFutureComparison result={result} />}
          <NoticePanel />
        </div>
      </section>
    </main>
  );
}

function ResultSummary({ result, productId }) {
  if (!result) {
    return (
      <section className="panel empty-state">
        <h2>계산 결과</h2>
        <p>값을 입력하면 총 납입 원금, 은행 이자, 정부기여금, 만기 예상 수령액이 표시됩니다.</p>
      </section>
    );
  }

  const items = [
    ["총 납입 원금", result.principal],
    ["은행 이자", result.bank_interest],
    ["정부기여금", result.government_contribution],
    ["만기 예상 수령액", result.maturity_amount],
  ];

  return (
    <section className="panel result-panel">
      <div className="result-header">
        <div>
          <p className="eyebrow">{result.months}개월 기준</p>
          <h2>{result.product_name}</h2>
        </div>
        <span className="status-pill">{productId === "youth-future" ? "비과세" : "계산 완료"}</span>
      </div>

      <div className="result-cards">
        {items.map(([label, value]) => (
          <article className="result-card" key={label}>
            <span>{label}</span>
            <strong>{formatKrw(value)}</strong>
          </article>
        ))}
      </div>

      {result.notices?.length > 0 && (
        <ul className="notice-list">
          {result.notices.map((notice) => (
            <li key={notice}>{notice}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function YouthFutureComparison({ result }) {
  const comparison = result?.comparison ?? [];

  return (
    <section className="panel comparison-panel">
      <div className="section-heading">
        <h2>일반형/우대형 비교</h2>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>유형</th>
              <th>원금</th>
              <th>은행 이자</th>
              <th>정부기여금</th>
              <th>만기 수령액</th>
            </tr>
          </thead>
          <tbody>
            {comparison.length === 0 ? (
              <tr>
                <td colSpan="5">계산 후 비교표가 표시됩니다.</td>
              </tr>
            ) : (
              comparison.map((item) => (
                <tr key={item.product_type}>
                  <td>{item.product_name.replace("청년미래적금 ", "")}</td>
                  <td>{formatKrw(item.principal)}</td>
                  <td>{formatKrw(item.bank_interest)}</td>
                  <td>{formatKrw(item.government_contribution)}</td>
                  <td>{formatKrw(item.maturity_amount)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function NoticePanel() {
  return (
    <section className="panel guide-panel">
      <h2>가입 안내</h2>
      <p>
        청년도약계좌와 청년미래적금의 중복가입 또는 갈아타기 가능 여부는 상품 출시 시점,
        금융기관 접수 기준, 정부 정책 세부 지침에 따라 달라질 수 있습니다.
      </p>
      <p>
        중소기업 우대형 요건을 충족하지 못하면 일반형 혜택으로 지급될 수 있으며, 실제 가입
        가능 여부는 금융기관 심사 기준에 따라 달라질 수 있습니다.
      </p>
    </section>
  );
}

export default App;

