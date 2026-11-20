/**
 * Credit Card Transaction Analytics Dashboard
 * Vanilla JavaScript + Chart.js 4.4.1
 */

// State Management
const state = {
  filters: {
    tier: "All",
    region: "All",
    startDate: "2024-01-01",
    endDate: "2025-12-31"
  },
  pagination: {
    limit: 10,
    offset: 0,
    total: 0
  },
  charts: {
    category: null,
    region: null,
    tier: null,
    emi: null,
    monthly: null
  },
  theme: localStorage.getItem("cc_theme") || "light"
};

// Formatting Utilities
function formatINR(val, compact = false) {
  if (val === null || val === undefined || isNaN(val)) return "₹0.00";
  const num = Number(val);
  
  if (compact && num >= 10000000) {
    return `₹${(num / 10000000).toFixed(2)} Cr`;
  }
  if (compact && num >= 100000) {
    return `₹${(num / 100000).toFixed(2)} L`;
  }

  return "₹" + num.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function formatNumber(val) {
  if (val === null || val === undefined || isNaN(val)) return "0";
  return Number(val).toLocaleString("en-IN");
}

function formatPercent(val) {
  if (val === null || val === undefined || isNaN(val)) return "0.0%";
  return Number(val).toFixed(2) + "%";
}

// Color Palettes
function getThemeColors() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  return {
    isDark,
    textColor: isDark ? "#94A3B8" : "#64748B",
    headingColor: isDark ? "#F8FAFC" : "#0F172A",
    gridColor: isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(15, 23, 42, 0.06)",
    navy: "#1F4E79",
    accent: "#0284C7",
    teal: "#0D9488",
    green: "#10B981",
    amber: "#F59E0B",
    coral: "#F97316",
    purple: "#8B5CF6",
    categoryPalette: [
      "#1F4E79", "#0284C7", "#0D9488", "#10B981", "#8B5CF6",
      "#EC4899", "#F59E0B", "#F97316", "#64748B", "#3B82F6"
    ],
    regionPalette: [
      "#1F4E79", "#0284C7", "#0D9488", "#10B981", "#F59E0B"
    ]
  };
}

// Chart.js Global Default Tweaks
function configureChartDefaults() {
  const colors = getThemeColors();
  Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
  Chart.defaults.color = colors.textColor;
  Chart.defaults.scale.grid.color = colors.gridColor;
}

// Build Query String from Filters
function getFilterQueryParams(includePagination = false) {
  const params = new URLSearchParams();
  if (state.filters.tier && state.filters.tier !== "All") {
    params.append("tier", state.filters.tier);
  }
  if (state.filters.region && state.filters.region !== "All") {
    params.append("region", state.filters.region);
  }
  if (state.filters.startDate) {
    params.append("start_date", state.filters.startDate);
  }
  if (state.filters.endDate) {
    params.append("end_date", state.filters.endDate);
  }
  if (includePagination) {
    params.append("limit", state.pagination.limit);
    params.append("offset", state.pagination.offset);
  }
  const str = params.toString();
  return str ? `?${str}` : "";
}

// Initialize and Fetch All Dashboard Components
async function loadDashboard() {
  const loadingIndicator = document.getElementById("loadingIndicator");
  const emptyState = document.getElementById("emptyState");
  const analyticsContent = document.getElementById("analyticsContent");

  try {
    loadingIndicator.classList.remove("hidden");
    const query = getFilterQueryParams();

    // Parallel fetch of endpoints
    const [
      kpisRes,
      categoryRes,
      regionRes,
      tierRes,
      emiRes,
      monthlyRes,
      testsRes
    ] = await Promise.all([
      fetch(`/api/kpis${query}`).then(r => r.json()),
      fetch(`/api/category-spend${query}`).then(r => r.json()),
      fetch(`/api/region-share${query}`).then(r => r.json()),
      fetch(`/api/tier-stats${query}`).then(r => r.json()),
      fetch(`/api/emi${query}`).then(r => r.json()),
      fetch(`/api/monthly${query}`).then(r => r.json()),
      fetch(`/api/hypothesis-tests${query}`).then(r => r.json())
    ]);

    // Handle Empty Dataset
    if (!kpisRes || kpisRes.total_transactions === 0) {
      emptyState.classList.remove("hidden");
      analyticsContent.classList.add("hidden");
      updateFilterBadge(0);
      await loadTransactions();
      return;
    }

    emptyState.classList.add("hidden");
    analyticsContent.classList.remove("hidden");

    // Render Data
    renderKPIs(kpisRes);
    updateFilterBadge(kpisRes.total_transactions);
    renderCategoryChart(categoryRes);
    renderRegionChart(regionRes);
    renderTierChart(tierRes);
    renderEmiChart(emiRes);
    renderMonthlyChart(monthlyRes);
    renderHypothesisTable(testsRes);

    // Refresh Transactions
    await loadTransactions();
  } catch (err) {
    console.error("Failed to load dashboard metrics:", err);
  } finally {
    loadingIndicator.classList.add("hidden");
  }
}

// Render KPI Cards
function renderKPIs(kpis) {
  document.getElementById("kpiTotalValue").textContent = formatINR(kpis.total_value);
  document.getElementById("kpiTotalValueSub").textContent = `Full Portfolio: ${formatINR(kpis.total_value, true)}`;

  document.getElementById("kpiTransactions").textContent = formatNumber(kpis.total_transactions);
  document.getElementById("kpiTransactionsSub").textContent = `${formatNumber(kpis.distinct_customers)} Distinct Customers`;

  document.getElementById("kpiMeanAmount").textContent = formatINR(kpis.mean_amount);
  document.getElementById("kpiMeanAmountSub").textContent = `Median Ticket: ${formatINR(kpis.median_amount)}`;

  document.getElementById("kpiSuccessRate").textContent = formatPercent(kpis.success_rate);
  const failRefundRate = (100 - kpis.success_rate).toFixed(2);
  document.getElementById("kpiSuccessRateSub").textContent = `${failRefundRate}% Failed/Refunded`;

  document.getElementById("kpiEmiShare").textContent = `${kpis.emi_count_share}%`;
  document.getElementById("kpiEmiShareSub").textContent = `${kpis.emi_spend_share}% of total spend`;
}

// Update Active Filter Badge
function updateFilterBadge(count) {
  const badge = document.getElementById("activeFilterBadge");
  const filtersApplied = (
    state.filters.tier !== "All" ||
    state.filters.region !== "All" ||
    state.filters.startDate !== "2024-01-01" ||
    state.filters.endDate !== "2025-12-31"
  );

  if (filtersApplied) {
    badge.textContent = `Filtered: ${formatNumber(count)} transactions matching criteria`;
    badge.style.color = "var(--color-accent)";
  } else {
    badge.textContent = `Showing all 10,059 transactions`;
    badge.style.color = "var(--text-muted)";
  }
}

// 1. Horizontal Bar: Top 10 Categories by Spend
function renderCategoryChart(data) {
  const colors = getThemeColors();
  const ctx = document.getElementById("categoryChart").getContext("2d");

  const labels = data.map(d => d.category);
  const values = data.map(d => d.total_value);

  if (state.charts.category) {
    state.charts.category.destroy();
  }

  state.charts.category = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Total Spend (INR)",
        data: values,
        backgroundColor: colors.categoryPalette,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              const item = data[context.dataIndex];
              return ` ${formatINR(item.total_value)} (${item.share_pct}% of spend, ${formatNumber(item.count)} txns)`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: {
            callback: value => formatINR(value, true),
            color: colors.textColor
          },
          grid: { color: colors.gridColor }
        },
        y: {
          ticks: { color: colors.textColor, font: { size: 11 } },
          grid: { display: false }
        }
      }
    }
  });
}

// 2. Doughnut: Spend Share by Region
function renderRegionChart(data) {
  const colors = getThemeColors();
  const ctx = document.getElementById("regionChart").getContext("2d");

  const labels = data.map(d => d.region);
  const values = data.map(d => d.total_value);

  if (state.charts.region) {
    state.charts.region.destroy();
  }

  state.charts.region = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors.regionPalette,
        borderWidth: 2,
        borderColor: colors.isDark ? "#1E293B" : "#FFFFFF"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "60%",
      plugins: {
        legend: {
          position: "right",
          labels: {
            boxWidth: 14,
            color: colors.textColor,
            padding: 12
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const item = data[context.dataIndex];
              return ` ${item.region}: ${formatINR(item.total_value)} (${item.share_pct}%) • Mean ticket: ${formatINR(item.mean_amount)}`;
            }
          }
        }
      }
    }
  });
}

// 3. Bar: Mean Amount by Card Tier
function renderTierChart(data) {
  const colors = getThemeColors();
  const ctx = document.getElementById("tierChart").getContext("2d");

  const tiers = data.tiers || [];
  const labels = tiers.map(t => t.tier);
  const values = tiers.map(t => t.mean_amount);

  // Highlight Classic tier since it has highest mean ticket
  const backgroundColors = tiers.map(t =>
    t.tier === "Classic" ? colors.navy : colors.accent
  );

  if (data.anova && data.anova.f_statistic !== null) {
    document.getElementById("tierAnovaBadge").textContent = `ANOVA F: ${data.anova.f_statistic} (${data.anova.decision})`;
  }

  if (state.charts.tier) {
    state.charts.tier.destroy();
  }

  state.charts.tier = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Mean Ticket (INR)",
        data: values,
        backgroundColor: backgroundColors,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              const item = tiers[context.dataIndex];
              return ` Mean: ${formatINR(item.mean_amount)} | Median: ${formatINR(item.median_amount)} (${formatNumber(item.count)} txns)`;
            }
          }
        }
      },
      scales: {
        y: {
          ticks: {
            callback: value => formatINR(value, true),
            color: colors.textColor
          },
          grid: { color: colors.gridColor }
        },
        x: {
          ticks: { color: colors.textColor },
          grid: { display: false }
        }
      }
    }
  });
}

// 4. Bar: EMI vs Non-EMI Mean Amount
function renderEmiChart(data) {
  const colors = getThemeColors();
  const ctx = document.getElementById("emiChart").getContext("2d");

  const emiMean = data.emi ? data.emi.mean_amount : 0;
  const nonEmiMean = data.non_emi ? data.non_emi.mean_amount : 0;

  if (state.charts.emi) {
    state.charts.emi.destroy();
  }

  state.charts.emi = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Non-EMI Transactions", "EMI Transactions"],
      datasets: [{
        data: [nonEmiMean, emiMean],
        backgroundColor: ["#64748B", "#1F4E79"],
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw;
              const isEmi = context.dataIndex === 1;
              const details = isEmi ? data.emi : data.non_emi;
              return ` Mean: ${formatINR(val)} (Total: ${formatINR(details.total_value, true)}, ${formatNumber(details.count)} txns)`;
            }
          }
        }
      },
      scales: {
        y: {
          ticks: {
            callback: value => formatINR(value, true),
            color: colors.textColor
          },
          grid: { color: colors.gridColor }
        },
        x: {
          ticks: { color: colors.textColor, font: { weight: "600" } },
          grid: { display: false }
        }
      }
    }
  });
}

// 5. Line: Monthly Spend Across 24 Months
function renderMonthlyChart(data) {
  const colors = getThemeColors();
  const ctx = document.getElementById("monthlyChart").getContext("2d");

  const labels = data.map(d => d.month);
  const values = data.map(d => d.total_spend);

  // Gradient fill for area
  const gradient = ctx.createLinearGradient(0, 0, 0, 320);
  gradient.addColorStop(0, "rgba(2, 132, 199, 0.35)");
  gradient.addColorStop(1, "rgba(2, 132, 199, 0.0)");

  if (state.charts.monthly) {
    state.charts.monthly.destroy();
  }

  state.charts.monthly = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Monthly Spend (INR)",
        data: values,
        borderColor: colors.accent,
        backgroundColor: gradient,
        borderWidth: 2.5,
        tension: 0.3,
        fill: true,
        pointBackgroundColor: colors.navy,
        pointBorderColor: "#FFFFFF",
        pointHoverRadius: 6,
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              const item = data[context.dataIndex];
              return ` Spend: ${formatINR(item.total_spend)} (${formatNumber(item.count)} txns, Avg: ${formatINR(item.mean_amount)})`;
            }
          }
        }
      },
      scales: {
        y: {
          ticks: {
            callback: value => formatINR(value, true),
            color: colors.textColor
          },
          grid: { color: colors.gridColor }
        },
        x: {
          ticks: {
            color: colors.textColor,
            maxRotation: 45,
            minRotation: 45,
            font: { size: 10 }
          },
          grid: { display: false }
        }
      }
    }
  });
}

// Render Inferential Hypothesis Testing Table
function renderHypothesisTable(tests) {
  const tbody = document.getElementById("hypothesisTableBody");
  tbody.innerHTML = "";

  tests.forEach(t => {
    const tr = document.createElement("tr");

    const badgeClass = t.decision === "Reject H0" ? "badge-reject" : "badge-fail";
    const statFormatted = t.statistic !== null ? `${t.statistic_name}: ${t.statistic}` : "N/A";
    const pValFormatted = t.p_value_formatted ? `p = ${t.p_value_formatted}` : "N/A";

    tr.innerHTML = `
      <td>
        <strong>${escapeHtml(t.name)}</strong>
        <div style="font-size: 0.76rem; color: var(--text-muted); margin-top: 2px;">
          <em>H0:</em> ${escapeHtml(t.null_hypothesis)}
        </div>
      </td>
      <td><span class="badge badge-pill">${escapeHtml(t.test_type)}</span></td>
      <td><strong>${escapeHtml(statFormatted)}</strong></td>
      <td><strong>${escapeHtml(pValFormatted)}</strong></td>
      <td><span class="badge ${badgeClass}">${escapeHtml(t.decision)}</span></td>
      <td style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(t.conclusion)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Fetch and Render Transactions Table
async function loadTransactions() {
  const query = getFilterQueryParams(true);
  try {
    const res = await fetch(`/api/transactions${query}`);
    const data = await res.json();

    state.pagination.total = data.total;
    const tbody = document.getElementById("transactionsTableBody");
    tbody.innerHTML = "";

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; padding: 24px; color: var(--text-muted);">No transactions found.</td></tr>`;
      updatePaginationControls(0);
      return;
    }

    data.items.forEach(row => {
      const tr = document.createElement("tr");
      
      let statusClass = "badge-status-success";
      if (row.TransactionStatus === "Failed") statusClass = "badge-status-failed";
      if (row.TransactionStatus === "Refunded") statusClass = "badge-status-refunded";

      tr.innerHTML = `
        <td><strong>${escapeHtml(row.TransactionID || "-")}</strong></td>
        <td>${escapeHtml(row.TransactionDate || "-")}</td>
        <td>
          <div style="font-weight:600;">${escapeHtml(row.CustomerName || "-")}</div>
          <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(row.CustomerID || "-")}</div>
        </td>
        <td>${escapeHtml(row.Category || "-")}</td>
        <td>${escapeHtml(row.Merchant || "-")}</td>
        <td><span class="badge badge-pill">${escapeHtml(row.CardTier || "-")}</span></td>
        <td>${escapeHtml(row.Region || "-")}</td>
        <td class="text-right"><strong>${formatINR(row.Amount_INR)}</strong></td>
        <td><span style="font-size:0.78rem;">${escapeHtml(row.PaymentMode || "-")}</span></td>
        <td><span class="badge ${statusClass}">${escapeHtml(row.TransactionStatus || "-")}</span></td>
        <td>${row.IsEMI ? '<span class="badge badge-info">EMI</span>' : '<span style="color:var(--text-muted);">-</span>'}</td>
      `;
      tbody.appendChild(tr);
    });

    updatePaginationControls(data.items.length);
  } catch (err) {
    console.error("Failed to load transactions list:", err);
  }
}

// Update Pagination Controls
function updatePaginationControls(currentItemsCount) {
  const { limit, offset, total } = state.pagination;
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + limit, total);
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;

  document.getElementById("paginationInfo").textContent =
    `Showing ${formatNumber(start)} to ${formatNumber(end)} of ${formatNumber(total)} entries`;
  
  document.getElementById("pageIndicator").textContent = `Page ${currentPage} of ${totalPages}`;

  document.getElementById("btnPrevPage").disabled = offset <= 0;
  document.getElementById("btnNextPage").disabled = offset + limit >= total;
}

// Escape HTML utility for XSS safety
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Reset Filters Function
window.resetFilters = function() {
  state.filters.tier = "All";
  state.filters.region = "All";
  state.filters.startDate = "2024-01-01";
  state.filters.endDate = "2025-12-31";
  state.pagination.offset = 0;

  document.getElementById("filterTier").value = "All";
  document.getElementById("filterRegion").value = "All";
  document.getElementById("filterStartDate").value = "2024-01-01";
  document.getElementById("filterEndDate").value = "2025-12-31";

  loadDashboard();
};

// Event Listeners Setup
function setupEventListeners() {
  // Filter Inputs Change
  const triggerFilter = () => {
    state.filters.tier = document.getElementById("filterTier").value;
    state.filters.region = document.getElementById("filterRegion").value;
    state.filters.startDate = document.getElementById("filterStartDate").value;
    state.filters.endDate = document.getElementById("filterEndDate").value;
    state.pagination.offset = 0;
    loadDashboard();
  };

  document.getElementById("filterTier").addEventListener("change", triggerFilter);
  document.getElementById("filterRegion").addEventListener("change", triggerFilter);
  document.getElementById("filterStartDate").addEventListener("change", triggerFilter);
  document.getElementById("filterEndDate").addEventListener("change", triggerFilter);
  document.getElementById("resetFiltersBtn").addEventListener("click", window.resetFilters);

  // Pagination Handlers
  document.getElementById("pageSizeSelect").addEventListener("change", (e) => {
    state.pagination.limit = parseInt(e.target.value, 10);
    state.pagination.offset = 0;
    loadTransactions();
  });

  document.getElementById("btnPrevPage").addEventListener("click", () => {
    if (state.pagination.offset >= state.pagination.limit) {
      state.pagination.offset -= state.pagination.limit;
      loadTransactions();
    }
  });

  document.getElementById("btnNextPage").addEventListener("click", () => {
    if (state.pagination.offset + state.pagination.limit < state.pagination.total) {
      state.pagination.offset += state.pagination.limit;
      loadTransactions();
    }
  });

  // Modal Controls
  const modal = document.getElementById("addModal");
  const openModalBtn = document.getElementById("openAddModalBtn");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const cancelModalBtn = document.getElementById("cancelModalBtn");
  const addForm = document.getElementById("addTransactionForm");
  const formAlert = document.getElementById("formAlert");

  const openModal = () => {
    modal.classList.remove("hidden");
    formAlert.classList.add("hidden");
    // Set default date to today
    document.getElementById("addDate").value = new Date().toISOString().split("T")[0];
  };

  const closeModal = () => {
    modal.classList.add("hidden");
    addForm.reset();
  };

  openModalBtn.addEventListener("click", openModal);
  closeModalBtn.addEventListener("click", closeModal);
  cancelModalBtn.addEventListener("click", closeModal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  // Add Transaction Form Submission
  addForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    formAlert.classList.add("hidden");

    const amount = parseFloat(document.getElementById("addAmount").value);
    const tier = document.getElementById("addTier").value;
    const region = document.getElementById("addRegion").value;

    if (isNaN(amount) || amount <= 0) {
      formAlert.className = "alert alert-danger";
      formAlert.textContent = "Amount must be strictly greater than 0.";
      formAlert.classList.remove("hidden");
      return;
    }

    const payload = {
      Amount_INR: amount,
      CardTier: tier,
      Region: region,
      Category: document.getElementById("addCategory").value,
      Merchant: document.getElementById("addMerchant").value || "Store",
      PaymentMode: document.getElementById("addPaymentMode").value,
      CardType: document.getElementById("addCardType").value,
      TransactionDate: document.getElementById("addDate").value || new Date().toISOString().split("T")[0],
      TransactionStatus: document.getElementById("addStatus").value,
      IsEMI: document.getElementById("addIsEMI").checked
    };

    try {
      const res = await fetch("/api/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Validation or submission error");
      }

      const created = await res.json();
      formAlert.className = "alert alert-success";
      formAlert.textContent = `Transaction ${created.TransactionID} successfully recorded!`;
      formAlert.classList.remove("hidden");

      setTimeout(() => {
        closeModal();
        loadDashboard();
      }, 1000);
    } catch (err) {
      formAlert.className = "alert alert-danger";
      formAlert.textContent = `Failed: ${err.message}`;
      formAlert.classList.remove("hidden");
    }
  });

  // Dark/Light Mode Theme Toggle
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const themeIcon = document.getElementById("themeIcon");
  const themeText = document.querySelector(".theme-text");

  const applyTheme = (theme) => {
    document.documentElement.setAttribute("data-theme", theme);
    state.theme = theme;
    localStorage.setItem("cc_theme", theme);

    if (theme === "dark") {
      themeIcon.textContent = "☀️";
      themeText.textContent = "Light Mode";
    } else {
      themeIcon.textContent = "🌙";
      themeText.textContent = "Dark Mode";
    }

    // Refresh charts colors
    configureChartDefaults();
    if (state.charts.category) {
      loadDashboard();
    }
  };

  // Initialize theme
  applyTheme(state.theme);

  themeToggleBtn.addEventListener("click", () => {
    const nextTheme = state.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
  });
}

// Initial Bootstrapping
document.addEventListener("DOMContentLoaded", () => {
  configureChartDefaults();
  setupEventListeners();
  loadDashboard();
});
