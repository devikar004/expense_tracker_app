const API = "/api";
const form = document.getElementById("expense-form");
const formTitle = document.getElementById("form-title");
const formError = document.getElementById("form-error");
const listError = document.getElementById("list-error");
const expenseList = document.getElementById("expense-list");
const summaryBox = document.getElementById("summary");
const submitButton = document.getElementById("submit-button");
const cancelButton = document.getElementById("cancel-edit");
const expenseIdInput = document.getElementById("expense-id");

function showElement(element) {
  element.classList.remove("hidden");
}

function hideElement(element) {
  element.classList.add("hidden");
}

function todayISO() {
  const now = new Date();
  const offset = now.getTimezoneOffset();
  return new Date(now.getTime() - offset * 60 * 1000)
    .toISOString()
    .slice(0, 10);
}

function currentMonth() {
  return todayISO().slice(0, 7);
}

function formatMoney(value) {
  return Number(value).toLocaleString(undefined, {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  });
}

function escapeHTML(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : String(value);
  return div.innerHTML;
}

async function requestJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }

  if (!response.ok) {
    const message =
      payload.error ||
      (payload.errors && Object.values(payload.errors).join(" ")) ||
      `Request failed (${response.status}).`;
    throw new Error(message);
  }

  return payload;
}

function getFilters() {
  return {
    q: document.getElementById("filter-title").value.trim(),
    category: document.getElementById("filter-category").value,
    from: document.getElementById("filter-from").value,
    to: document.getElementById("filter-to").value,
  };
}

function buildQueryString(filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

async function loadExpenses() {
  hideElement(listError);
  expenseList.innerHTML = `<p class="muted">Loading expenses…</p>`;

  try {
    const filters = getFilters();
    const data = await requestJSON(`${API}/expenses${buildQueryString(filters)}`);
    renderExpenses(data.expenses);
  } catch (error) {
    expenseList.innerHTML = "";
    listError.textContent = error.message;
    showElement(listError);
  }
}

function renderExpenses(expenses) {
  if (!expenses.length) {
    expenseList.innerHTML = `<p class="muted">No expenses match the current filters.</p>`;
    return;
  }

  expenseList.innerHTML = expenses
    .map(
      (expense) => `
      <article class="expense">
        <div>
          <h3>${escapeHTML(expense.title)}</h3>
          <p class="muted">
            ${escapeHTML(expense.date)} • ${escapeHTML(expense.category)}
          </p>
          ${expense.note ? `<p>${escapeHTML(expense.note)}</p>` : ""}
        </div>
        <div class="expense-actions">
          <strong>${formatMoney(expense.amount)}</strong>
          <button data-action="edit" data-id="${expense.id}">Edit</button>
          <button data-action="delete" data-id="${expense.id}" class="danger">
            Delete
          </button>
        </div>
      </article>
    `
    )
    .join("");
}

async function loadSummary() {
  summaryBox.innerHTML = `<p class="muted">Loading summary…</p>`;

  try {
    const data = await requestJSON(`${API}/summary?month=${currentMonth()}`);
    renderSummary(data);
  } catch (error) {
    summaryBox.innerHTML = `<p class="error">${escapeHTML(error.message)}</p>`;
  }
}

function renderSummary(data) {
  const categoryRows = data.by_category.length
    ? data.by_category
        .map(
          (item) => `
          <li>
            <span>${escapeHTML(item.category)}</span>
            <span>${formatMoney(item.total)} (${item.count})</span>
          </li>
        `
        )
        .join("")
    : `<li class="muted">No expenses this month.</li>`;

  summaryBox.innerHTML = `
    <p class="total">Total spent: <strong>${formatMoney(data.total)}</strong></p>
    <p class="muted">${data.expense_count} expense(s) in ${escapeHTML(data.month)}</p>
    <ul class="category-summary">${categoryRows}</ul>
  `;
}

function resetForm() {
  form.reset();
  expenseIdInput.value = "";
  document.getElementById("date").value = todayISO();
  formTitle.textContent = "Add expense";
  submitButton.textContent = "Add expense";
  hideElement(cancelButton);
  hideElement(formError);
}

function fillForm(expense) {
  expenseIdInput.value = expense.id;
  document.getElementById("title").value = expense.title;
  document.getElementById("amount").value = expense.amount;
  document.getElementById("category").value = expense.category;
  document.getElementById("date").value = expense.date;
  document.getElementById("note").value = expense.note;

  formTitle.textContent = "Edit expense";
  submitButton.textContent = "Save changes";
  showElement(cancelButton);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadExpenseForEdit(id) {
  try {
    const data = await requestJSON(`${API}/expenses${buildQueryString(getFilters())}`);
    const expense = data.expenses.find((item) => item.id === Number(id));
    if (!expense) throw new Error("Expense not found.");
    fillForm(expense);
  } catch (error) {
    formError.textContent = error.message;
    showElement(formError);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideElement(formError);

  const id = expenseIdInput.value;
  const payload = {
    title: document.getElementById("title").value,
    amount: document.getElementById("amount").value,
    category: document.getElementById("category").value,
    date: document.getElementById("date").value,
    note: document.getElementById("note").value,
  };

  try {
    if (id) {
      await requestJSON(`${API}/expenses/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      await requestJSON(`${API}/expenses`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }

    resetForm();
    await Promise.all([loadExpenses(), loadSummary()]);
  } catch (error) {
    formError.textContent = error.message;
    showElement(formError);
  }
});

cancelButton.addEventListener("click", resetForm);

expenseList.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button) return;

  const id = button.dataset.id;
  const action = button.dataset.action;

  if (action === "edit") {
    await loadExpenseForEdit(id);
  }

  if (action === "delete") {
    if (!confirm("Delete this expense?")) return;

    try {
      await requestJSON(`${API}/expenses/${id}`, { method: "DELETE" });
      await Promise.all([loadExpenses(), loadSummary()]);
    } catch (error) {
      listError.textContent = error.message;
      showElement(listError);
    }
  }
});

document.getElementById("apply-filters").addEventListener("click", loadExpenses);

document.getElementById("clear-filters").addEventListener("click", () => {
  document.getElementById("filter-title").value = "";
  document.getElementById("filter-category").value = "";
  document.getElementById("filter-from").value = "";
  document.getElementById("filter-to").value = "";
  loadExpenses();
});

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("date").value = todayISO();
  loadExpenses();
  loadSummary();
});