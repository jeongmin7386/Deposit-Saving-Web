import React, { useEffect, useMemo, useState } from "react";
import {
  BadgePercent,
  Calculator,
  Coins,
  Database,
  GitCompare,
  Landmark,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Star,
  WalletCards,
} from "lucide-react";

function normalizeApiBaseUrl(value) {
  const baseUrl = value || "http://127.0.0.1:8000";
  const withProtocol = /^https?:\/\//.test(baseUrl) ? baseUrl : `https://${baseUrl}`;
  return withProtocol.replace(/\/$/, "");
}

const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

const calculatorProducts = [
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
    maxAmount: 700000,
    fixedMonths: 60,
  },
  {
    id: "youth-future",
    label: "청년미래적금",
    endpoint: "/api/calculate/youth-future",
    icon: Coins,
    amountLabel: "월 납입액",
    maxAmount: 500000,
    fixedMonths: 36,
  },
];

const productMap = Object.fromEntries(
  calculatorProducts.map((product) => [product.id, product]),
);

const viewTabs = [
  { id: "finder", label: "상품 찾기", icon: Search },
  { id: "calculator", label: "직접 계산", icon: Calculator },
  { id: "compare", label: "비교함", icon: GitCompare },
  { id: "favorites", label: "즐겨찾기", icon: Star },
  { id: "admin", label: "관리", icon: Database },
];

function isAdminRoute() {
  return window.location.pathname.replace(/\/$/, "") === "/admin";
}

function readStoredIds(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "[]");
  } catch {
    return [];
  }
}

function formatKrw(value) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(Number(value ?? 0));
}

function formatRate(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return `${Number(value).toFixed(2).replace(/\.00$/, "")}%`;
}

function productTypeLabel(type) {
  return type === "saving" ? "적금" : "예금";
}

function getOptionRate(option) {
  return Number(option?.maximum_rate ?? option?.base_rate ?? 0);
}

function getBestOption(product) {
  const options = product?.options ?? [];
  if (options.length === 0) {
    return null;
  }
  return [...options].sort((a, b) => getOptionRate(b) - getOptionRate(a))[0];
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message = Array.isArray(data?.detail)
      ? data.detail.map((item) => item.msg).join(" ")
      : data?.detail || "요청을 처리하지 못했습니다.";
    throw new Error(message);
  }

  return data;
}

function App() {
  const [activeView, setActiveView] = useState(() => (isAdminRoute() ? "admin" : "finder"));
  const showAdminTab = isAdminRoute();

  const [productId, setProductId] = useState("youth-future");
  const [amount, setAmount] = useState("500000");
  const [annualRate, setAnnualRate] = useState("5");
  const [months, setMonths] = useState("12");
  const [benefitType, setBenefitType] = useState("general");
  const [annualIncome, setAnnualIncome] = useState("");
  const [result, setResult] = useState(null);
  const [calculatorError, setCalculatorError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [filters, setFilters] = useState({
    product_type: "deposit",
    keyword: "",
    term_months: "",
    min_rate: "",
    sort: "rate_desc",
  });
  const [catalog, setCatalog] = useState({ items: [], total: 0, limit: 20, offset: 0 });
  const [isLoadingProducts, setIsLoadingProducts] = useState(false);
  const [productError, setProductError] = useState("");

  const [compareIds, setCompareIds] = useState(() => readStoredIds("compareProductIds"));
  const [favoriteIds, setFavoriteIds] = useState(() => readStoredIds("favoriteProductIds"));
  const [compareProducts, setCompareProducts] = useState([]);
  const [favoriteProducts, setFavoriteProducts] = useState([]);

  const [adminToken, setAdminToken] = useState(() => localStorage.getItem("adminToken") || "");
  const [adminMessage, setAdminMessage] = useState("");
  const [adminError, setAdminError] = useState("");
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncLogs, setSyncLogs] = useState([]);
  const [adminForm, setAdminForm] = useState({
    company_name: "",
    company_code: "",
    product_type: "deposit",
    product_name: "",
    saving_term_months: "12",
    base_rate: "3.5",
    maximum_rate: "4.0",
    join_method: "영업점, 인터넷, 스마트폰",
    special_conditions: "",
  });

  const selectedProduct = productMap[productId];
  const visibleTabs = useMemo(
    () => viewTabs.filter((tab) => showAdminTab || tab.id !== "admin"),
    [showAdminTab],
  );

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

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    if (!showAdminTab && activeView === "admin") {
      setActiveView("finder");
    }
  }, [activeView, showAdminTab]);

  useEffect(() => {
    localStorage.setItem("compareProductIds", JSON.stringify(compareIds));
  }, [compareIds]);

  useEffect(() => {
    localStorage.setItem("favoriteProductIds", JSON.stringify(favoriteIds));
  }, [favoriteIds]);

  useEffect(() => {
    localStorage.setItem("adminToken", adminToken);
  }, [adminToken]);

  useEffect(() => {
    if (activeView !== "compare" || compareIds.length === 0) {
      setCompareProducts([]);
      return;
    }
    loadProductsByIds(compareIds, setCompareProducts);
  }, [activeView, compareIds]);

  useEffect(() => {
    if (activeView !== "favorites" || favoriteIds.length === 0) {
      setFavoriteProducts([]);
      return;
    }
    loadProductsByIds(favoriteIds, setFavoriteProducts);
  }, [activeView, favoriteIds]);

  useEffect(() => {
    if (activeView === "admin") {
      loadSyncLogs();
    }
  }, [activeView]);

  async function loadProducts(event) {
    event?.preventDefault();
    setIsLoadingProducts(true);
    setProductError("");

    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== "") {
          params.set(key, value);
        }
      });
      const data = await requestJson(`/api/products?${params.toString()}`);
      setCatalog(data);
    } catch (error) {
      setProductError(error.message);
      setCatalog({ items: [], total: 0, limit: 20, offset: 0 });
    } finally {
      setIsLoadingProducts(false);
    }
  }

  async function loadProductsByIds(ids, setter) {
    const loaded = await Promise.all(
      ids.map(async (id) => {
        try {
          return await requestJson(`/api/products/${id}`);
        } catch {
          return null;
        }
      }),
    );
    setter(loaded.filter(Boolean));
  }

  async function loadSyncLogs() {
    try {
      const headers = adminToken ? { "X-Admin-Token": adminToken } : {};
      const data = await requestJson("/api/admin/sync/logs", { headers });
      setSyncLogs(data);
    } catch {
      setSyncLogs([]);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setCalculatorError("");
    setIsSubmitting(true);

    try {
      const data = await requestJson(selectedProduct.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setResult(data);
    } catch (requestError) {
      setResult(null);
      setCalculatorError(requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleProductChange(nextProductId) {
    setProductId(nextProductId);
    setResult(null);
    setCalculatorError("");
    const nextProduct = productMap[nextProductId];
    if (nextProduct.defaultMonths) {
      setMonths(String(nextProduct.defaultMonths));
    }
    if (nextProductId === "youth-future") {
      setAmount("500000");
    }
  }

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function toggleCompare(id) {
    setProductError("");
    setCompareIds((current) => {
      if (current.includes(id)) {
        return current.filter((item) => item !== id);
      }
      if (current.length >= 5) {
        setProductError("비교함에는 최대 5개 상품까지만 담을 수 있습니다.");
        return current;
      }
      return [...current, id];
    });
  }

  function toggleFavorite(id) {
    setFavoriteIds((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  function useProductForCalculation(product) {
    const option = getBestOption(product);
    setActiveView("calculator");
    setProductId(product.product_type);
    setAnnualRate(String(option?.maximum_rate ?? option?.base_rate ?? product.best_rate ?? "0"));
    if (option?.saving_term_months) {
      setMonths(String(option.saving_term_months));
    }
    setResult(null);
    setCalculatorError("");
  }

  async function handleSyncFinlife() {
    setAdminMessage("");
    setAdminError("");
    setIsSyncing(true);

    try {
      const headers = { "Content-Type": "application/json" };
      if (adminToken) {
        headers["X-Admin-Token"] = adminToken;
      }
      const data = await requestJson("/api/admin/sync/finlife", {
        method: "POST",
        headers,
        body: JSON.stringify({ product_types: ["deposit", "saving"] }),
      });
      setAdminMessage(
        `FINLIFE 동기화 완료: 상품 ${data.products_upserted}개, 옵션 ${data.options_upserted}개`,
      );
      await loadProducts();
      await loadSyncLogs();
    } catch (error) {
      setAdminError(error.message);
    } finally {
      setIsSyncing(false);
    }
  }

  async function handleCreateManualProduct(event) {
    event.preventDefault();
    setAdminMessage("");
    setAdminError("");

    try {
      const headers = { "Content-Type": "application/json" };
      if (adminToken) {
        headers["X-Admin-Token"] = adminToken;
      }
      const body = {
        company_name: adminForm.company_name,
        company_code: adminForm.company_code || null,
        product_type: adminForm.product_type,
        product_name: adminForm.product_name,
        join_method: adminForm.join_method || null,
        special_conditions: adminForm.special_conditions || null,
        option: {
          saving_term_months: Number(adminForm.saving_term_months),
          base_rate: adminForm.base_rate || null,
          maximum_rate: adminForm.maximum_rate || null,
        },
      };
      const created = await requestJson("/api/admin/products", {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
      setAdminMessage(`${created.company_name} ${created.product_name} 상품을 등록했습니다.`);
      setAdminForm((current) => ({
        ...current,
        product_name: "",
        special_conditions: "",
      }));
      await loadProducts();
    } catch (error) {
      setAdminError(error.message);
    }
  }

  function renderControls() {
    if (activeView === "calculator") {
      return (
        <CalculatorForm
          productId={productId}
          selectedProduct={selectedProduct}
          benefitType={benefitType}
          amount={amount}
          annualRate={annualRate}
          months={months}
          annualIncome={annualIncome}
          calculatorError={calculatorError}
          isSubmitting={isSubmitting}
          onProductChange={handleProductChange}
          onBenefitTypeChange={setBenefitType}
          onAmountChange={setAmount}
          onAnnualRateChange={setAnnualRate}
          onMonthsChange={setMonths}
          onAnnualIncomeChange={setAnnualIncome}
          onSubmit={handleSubmit}
        />
      );
    }

    if (activeView === "admin") {
      return (
        <AdminControls
          adminToken={adminToken}
          adminForm={adminForm}
          adminMessage={adminMessage}
          adminError={adminError}
          isSyncing={isSyncing}
          onAdminTokenChange={setAdminToken}
          onAdminFormChange={(key, value) =>
            setAdminForm((current) => ({ ...current, [key]: value }))
          }
          onSync={handleSyncFinlife}
          onCreate={handleCreateManualProduct}
        />
      );
    }

    return (
      <SearchControls
        filters={filters}
        isLoading={isLoadingProducts}
        compareCount={compareIds.length}
        favoriteCount={favoriteIds.length}
        onFilterChange={updateFilter}
        onSubmit={loadProducts}
      />
    );
  }

  function renderMainPanel() {
    if (activeView === "calculator") {
      return (
        <>
          <ResultSummary result={result} productId={productId} />
          {productId === "youth-future" && <YouthFutureComparison result={result} />}
          <NoticePanel />
        </>
      );
    }

    if (activeView === "compare") {
      return (
        <>
          <ProductComparison
            products={compareProducts}
            onRemove={(id) =>
              setCompareIds((current) => current.filter((item) => item !== id))
            }
            onEstimate={useProductForCalculation}
          />
          <NoticePanel />
        </>
      );
    }

    if (activeView === "favorites") {
      return (
        <>
          <ProductCatalog
            title="즐겨찾기"
            products={favoriteProducts}
            total={favoriteProducts.length}
            isLoading={false}
            error=""
            compareIds={compareIds}
            favoriteIds={favoriteIds}
            onCompare={toggleCompare}
            onFavorite={toggleFavorite}
            onEstimate={useProductForCalculation}
            emptyMessage="즐겨찾기한 상품이 아직 없습니다."
          />
          <NoticePanel />
        </>
      );
    }

    if (activeView === "admin") {
      return (
        <>
          <AdminStatus syncLogs={syncLogs} />
          <NoticePanel />
        </>
      );
    }

    return (
      <>
        <ProductCatalog
          title="금융상품 검색 결과"
          products={catalog.items}
          total={catalog.total}
          isLoading={isLoadingProducts}
          error={productError}
          compareIds={compareIds}
          favoriteIds={favoriteIds}
          onCompare={toggleCompare}
          onFavorite={toggleFavorite}
          onEstimate={useProductForCalculation}
          emptyMessage="동기화된 상품이 없습니다. 관리자 화면에서 FINLIFE 동기화를 실행하거나 수동 상품을 등록해 주세요."
        />
        <NoticePanel />
      </>
    );
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <div className="panel form-panel">
          <div className="title-row">
            <div>
              <p className="eyebrow">Deposit Savings Service</p>
              <h1>예·적금 만기 예상조회</h1>
            </div>
            <Calculator aria-hidden="true" />
          </div>

          <nav className="view-tabs" aria-label="서비스 메뉴">
            {visibleTabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  type="button"
                  className={activeView === tab.id ? "active" : ""}
                  onClick={() => setActiveView(tab.id)}
                >
                  <Icon size={17} aria-hidden="true" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {renderControls()}
        </div>

        <div className="result-column">{renderMainPanel()}</div>
      </section>
    </main>
  );
}

function SearchControls({
  filters,
  isLoading,
  compareCount,
  favoriteCount,
  onFilterChange,
  onSubmit,
}) {
  return (
    <form className="stacked-form" onSubmit={onSubmit} noValidate>
      <div className="segmented" aria-label="상품 유형">
        <button
          type="button"
          className={filters.product_type === "deposit" ? "active" : ""}
          onClick={() => onFilterChange("product_type", "deposit")}
        >
          예금
        </button>
        <button
          type="button"
          className={filters.product_type === "saving" ? "active" : ""}
          onClick={() => onFilterChange("product_type", "saving")}
        >
          적금
        </button>
      </div>

      <div className="field-grid">
        <label>
          <span>은행명 또는 상품명</span>
          <input
            value={filters.keyword}
            onChange={(event) => onFilterChange("keyword", event.target.value)}
            placeholder="예: 국민, 자유적금"
          />
        </label>
        <label>
          <span>가입 기간</span>
          <select
            value={filters.term_months}
            onChange={(event) => onFilterChange("term_months", event.target.value)}
          >
            <option value="">전체</option>
            <option value="6">6개월</option>
            <option value="12">12개월</option>
            <option value="24">24개월</option>
            <option value="36">36개월</option>
          </select>
        </label>
        <label>
          <span>최저 최고금리(%)</span>
          <input
            inputMode="decimal"
            min="0"
            max="100"
            step="0.01"
            type="number"
            value={filters.min_rate}
            onChange={(event) => onFilterChange("min_rate", event.target.value)}
            placeholder="예: 3.5"
          />
        </label>
        <label>
          <span>정렬</span>
          <select
            value={filters.sort}
            onChange={(event) => onFilterChange("sort", event.target.value)}
          >
            <option value="rate_desc">최고금리 높은순</option>
            <option value="rate_asc">최고금리 낮은순</option>
            <option value="name">금융회사명순</option>
            <option value="term">기간순</option>
          </select>
        </label>
      </div>

      <div className="small-stats">
        <span>비교함 {compareCount}개</span>
        <span>즐겨찾기 {favoriteCount}개</span>
      </div>

      <button className="submit-button" type="submit" disabled={isLoading}>
        {isLoading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
        <span>상품 검색</span>
      </button>
    </form>
  );
}

function CalculatorForm({
  productId,
  selectedProduct,
  benefitType,
  amount,
  annualRate,
  months,
  annualIncome,
  calculatorError,
  isSubmitting,
  onProductChange,
  onBenefitTypeChange,
  onAmountChange,
  onAnnualRateChange,
  onMonthsChange,
  onAnnualIncomeChange,
  onSubmit,
}) {
  return (
    <form className="stacked-form" onSubmit={onSubmit} noValidate>
      <div className="product-grid" role="tablist" aria-label="계산 상품 유형">
        {calculatorProducts.map((product) => {
          const Icon = product.icon;
          const isSelected = product.id === productId;
          return (
            <button
              className={`product-button ${isSelected ? "selected" : ""}`}
              key={product.id}
              type="button"
              onClick={() => onProductChange(product.id)}
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
            onClick={() => onBenefitTypeChange("general")}
          >
            일반형
          </button>
          <button
            type="button"
            className={benefitType === "preferred" ? "active" : ""}
            onClick={() => onBenefitTypeChange("preferred")}
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
            max={selectedProduct.maxAmount}
            step="1"
            type="number"
            value={amount}
            onChange={(event) => onAmountChange(event.target.value)}
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
            onChange={(event) => onAnnualRateChange(event.target.value)}
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
              step="1"
              type="number"
              value={months}
              onChange={(event) => onMonthsChange(event.target.value)}
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
              step="1"
              type="number"
              placeholder="선택 입력"
              value={annualIncome}
              onChange={(event) => onAnnualIncomeChange(event.target.value)}
            />
          </label>
        )}
      </div>

      {calculatorError && <p className="error-message">{calculatorError}</p>}

      <button className="submit-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? <Loader2 className="spin" size={18} /> : <Calculator size={18} />}
        <span>계산하기</span>
      </button>
    </form>
  );
}

function AdminControls({
  adminToken,
  adminForm,
  adminMessage,
  adminError,
  isSyncing,
  onAdminTokenChange,
  onAdminFormChange,
  onSync,
  onCreate,
}) {
  return (
    <div className="admin-stack">
      <div className="admin-actions">
        <label>
          <span>관리자 토큰</span>
          <input
            value={adminToken}
            onChange={(event) => onAdminTokenChange(event.target.value)}
            placeholder="ADMIN_TOKEN 설정 시 입력"
            type="password"
          />
        </label>
        <button className="submit-button" type="button" onClick={onSync} disabled={isSyncing}>
          {isSyncing ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
          <span>FINLIFE 동기화</span>
        </button>
      </div>

      <form className="stacked-form compact-form" onSubmit={onCreate} noValidate>
        <div className="section-heading">
          <h2>수동 상품 등록</h2>
        </div>
        <div className="field-grid">
          <label>
            <span>금융회사명</span>
            <input
              value={adminForm.company_name}
              onChange={(event) => onAdminFormChange("company_name", event.target.value)}
              required
            />
          </label>
          <label>
            <span>회사 코드</span>
            <input
              value={adminForm.company_code}
              onChange={(event) => onAdminFormChange("company_code", event.target.value)}
              placeholder="선택 입력"
            />
          </label>
          <label>
            <span>상품 유형</span>
            <select
              value={adminForm.product_type}
              onChange={(event) => onAdminFormChange("product_type", event.target.value)}
            >
              <option value="deposit">예금</option>
              <option value="saving">적금</option>
            </select>
          </label>
          <label>
            <span>상품명</span>
            <input
              value={adminForm.product_name}
              onChange={(event) => onAdminFormChange("product_name", event.target.value)}
              required
            />
          </label>
          <label>
            <span>기간</span>
            <input
              inputMode="numeric"
              min="1"
              max="120"
              step="1"
              type="number"
              value={adminForm.saving_term_months}
              onChange={(event) => onAdminFormChange("saving_term_months", event.target.value)}
            />
          </label>
          <label>
            <span>기본금리(%)</span>
            <input
              inputMode="decimal"
              min="0"
              max="100"
              step="0.01"
              type="number"
              value={adminForm.base_rate}
              onChange={(event) => onAdminFormChange("base_rate", event.target.value)}
            />
          </label>
          <label>
            <span>최고금리(%)</span>
            <input
              inputMode="decimal"
              min="0"
              max="100"
              step="0.01"
              type="number"
              value={adminForm.maximum_rate}
              onChange={(event) => onAdminFormChange("maximum_rate", event.target.value)}
            />
          </label>
          <label>
            <span>가입 방법</span>
            <input
              value={adminForm.join_method}
              onChange={(event) => onAdminFormChange("join_method", event.target.value)}
            />
          </label>
          <label className="wide-field">
            <span>우대 조건</span>
            <textarea
              value={adminForm.special_conditions}
              onChange={(event) => onAdminFormChange("special_conditions", event.target.value)}
              rows="3"
            />
          </label>
        </div>
        <button className="submit-button" type="submit">
          <Plus size={18} />
          <span>수동 상품 저장</span>
        </button>
      </form>

      {adminMessage && <p className="success-message">{adminMessage}</p>}
      {adminError && <p className="error-message">{adminError}</p>}
    </div>
  );
}

function ProductCatalog({
  title,
  products,
  total,
  isLoading,
  error,
  compareIds,
  favoriteIds,
  onCompare,
  onFavorite,
  onEstimate,
  emptyMessage,
}) {
  return (
    <section className="panel product-list-panel">
      <div className="result-header">
        <div>
          <p className="eyebrow">Financial Products</p>
          <h2>{title}</h2>
        </div>
        <span className="status-pill">{total}개</span>
      </div>

      {error && <p className="error-message">{error}</p>}
      {isLoading && (
        <div className="loading-row">
          <Loader2 className="spin" size={18} />
          <span>상품을 불러오는 중입니다.</span>
        </div>
      )}
      {!isLoading && products.length === 0 && <p className="empty-copy">{emptyMessage}</p>}

      <div className="product-list">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            isCompared={compareIds.includes(product.id)}
            isFavorite={favoriteIds.includes(product.id)}
            onCompare={() => onCompare(product.id)}
            onFavorite={() => onFavorite(product.id)}
            onEstimate={() => onEstimate(product)}
          />
        ))}
      </div>
    </section>
  );
}

function ProductCard({ product, isCompared, isFavorite, onCompare, onFavorite, onEstimate }) {
  const bestOption = getBestOption(product);

  return (
    <article className="product-card">
      <div className="product-card-top">
        <div>
          <p className="company-name">{product.company_name}</p>
          <h3>{product.product_name}</h3>
        </div>
        <div className="badge-group">
          <span className="type-badge">{productTypeLabel(product.product_type)}</span>
          <span className="source-badge">{product.data_source === "finlife" ? "FINLIFE" : "수동"}</span>
        </div>
      </div>

      <div className="metric-strip">
        <div>
          <span>최고금리</span>
          <strong>{formatRate(bestOption?.maximum_rate ?? product.best_rate)}</strong>
        </div>
        <div>
          <span>기본금리</span>
          <strong>{formatRate(bestOption?.base_rate)}</strong>
        </div>
        <div>
          <span>기간</span>
          <strong>{bestOption?.saving_term_months ?? product.best_term_months ?? "-"}개월</strong>
        </div>
      </div>

      <dl className="product-meta">
        <div>
          <dt>가입 방법</dt>
          <dd>{product.join_method || "정보 없음"}</dd>
        </div>
        <div>
          <dt>우대 조건</dt>
          <dd>{product.special_conditions || "정보 없음"}</dd>
        </div>
      </dl>

      <div className="card-actions">
        <button type="button" onClick={onEstimate}>
          <Calculator size={16} />
          <span>예상조회</span>
        </button>
        <button type="button" className={isCompared ? "selected" : ""} onClick={onCompare}>
          <GitCompare size={16} />
          <span>{isCompared ? "비교 해제" : "비교 담기"}</span>
        </button>
        <button type="button" className={isFavorite ? "selected" : ""} onClick={onFavorite}>
          <Star size={16} />
          <span>{isFavorite ? "저장됨" : "즐겨찾기"}</span>
        </button>
      </div>
    </article>
  );
}

function ProductComparison({ products, onRemove, onEstimate }) {
  return (
    <section className="panel comparison-panel">
      <div className="result-header">
        <div>
          <p className="eyebrow">Comparison</p>
          <h2>상품 비교표</h2>
        </div>
        <span className="status-pill">{products.length}개</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>상품</th>
              <th>금융회사</th>
              <th>유형</th>
              <th>기간</th>
              <th>기본금리</th>
              <th>최고금리</th>
              <th>작업</th>
            </tr>
          </thead>
          <tbody>
            {products.length === 0 ? (
              <tr>
                <td colSpan="7">상품 찾기에서 비교할 상품을 2개 이상 담아 주세요.</td>
              </tr>
            ) : (
              products.map((product) => {
                const option = getBestOption(product);
                return (
                  <tr key={product.id}>
                    <td>{product.product_name}</td>
                    <td>{product.company_name}</td>
                    <td>{productTypeLabel(product.product_type)}</td>
                    <td>{option?.saving_term_months ?? product.best_term_months ?? "-"}개월</td>
                    <td>{formatRate(option?.base_rate)}</td>
                    <td>{formatRate(option?.maximum_rate ?? product.best_rate)}</td>
                    <td>
                      <div className="table-actions">
                        <button type="button" onClick={() => onEstimate(product)}>
                          계산
                        </button>
                        <button type="button" onClick={() => onRemove(product.id)}>
                          제거
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
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

function AdminStatus({ syncLogs }) {
  return (
    <section className="panel comparison-panel">
      <div className="result-header">
        <div>
          <p className="eyebrow">Data Management</p>
          <h2>동기화 기록</h2>
        </div>
        <span className="status-pill">{syncLogs.length}건</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>상태</th>
              <th>소스</th>
              <th>상품 유형</th>
              <th>상품</th>
              <th>옵션</th>
              <th>완료 시각</th>
            </tr>
          </thead>
          <tbody>
            {syncLogs.length === 0 ? (
              <tr>
                <td colSpan="6">아직 동기화 기록이 없습니다.</td>
              </tr>
            ) : (
              syncLogs.map((log) => (
                <tr key={log.id}>
                  <td>{log.status}</td>
                  <td>{log.source}</td>
                  <td>{log.product_type || "-"}</td>
                  <td>{log.products_upserted}</td>
                  <td>{log.options_upserted}</td>
                  <td>{log.completed_at || log.requested_at}</td>
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
      <h2>안내</h2>
      <p>
        금융상품 검색 정보는 금융감독원 FINLIFE Open API와 관리자가 수동 등록한 데이터를
        바탕으로 표시합니다. 모든 금융회사와 모든 상품을 보장하지는 않습니다.
      </p>
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
