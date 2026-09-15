// Set VITE_API_URL on your hosting platform to your deployed backend's URL,
// e.g. https://foodtrack-api.onrender.com — falls back to local dev.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function signup(email, password) {
  return request("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email, password) {
  // FastAPI's OAuth2PasswordRequestForm expects form-encoded data, not JSON.
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const data = await request("/auth/login", { method: "POST", body: form });
  localStorage.setItem("token", data.access_token);
  return data;
}

export function logout() {
  localStorage.removeItem("token");
}

export function isLoggedIn() {
  return !!getToken();
}

export async function getMe() {
  return request("/auth/me");
}

export async function updateGoal(daily_calorie_goal) {
  return request("/auth/me/goal", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ daily_calorie_goal }),
  });
}

export async function predictFood(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/predict", { method: "POST", body: formData });
}

export async function logMeal(meal) {
  return request("/meals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(meal),
  });
}

export async function getTodaysMeals() {
  return request("/meals/today");
}
