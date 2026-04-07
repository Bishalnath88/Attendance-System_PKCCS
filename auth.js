const API_BASE_URL = "https://attendance-systempkccs-production.up.railway.app";

function getToken() {
  return localStorage.getItem("token");
}

function getStoredEmail() {
  return localStorage.getItem("userEmail") || "";
}

function saveAuthSession(token, email) {
  localStorage.setItem("token", token);
  localStorage.setItem("userEmail", String(email || "").trim().toLowerCase());
}

function clearAuthSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("userEmail");
}

function requireAuth() {
  if (!getToken()) {
    window.location.replace("login.html");
  }
}

function redirectIfAuthenticated(targetPage = "dashboard.html") {
  if (getToken()) {
    window.location.replace(targetPage);
  }
}

function getAuthHeaders(extraHeaders = {}) {
  const token = getToken();
  return token
    ? { ...extraHeaders, Authorization: `Bearer ${token}` }
    : { ...extraHeaders };
}

function buildApiUrl(path, query = {}) {
  const url = new URL(path, `${API_BASE_URL}/`);

  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  return url.toString();
}

async function apiRequest(path, options = {}) {
  const {
    method = "GET",
    body,
    headers = {},
    auth = true,
    query = {},
  } = options;

  const finalHeaders = auth ? getAuthHeaders(headers) : { ...headers };
  const requestOptions = { method, headers: finalHeaders };

  if (body !== undefined) {
    if (body instanceof FormData) {
      requestOptions.body = body;
    } else {
      requestOptions.body = JSON.stringify(body);
      if (!requestOptions.headers["Content-Type"]) {
        requestOptions.headers["Content-Type"] = "application/json";
      }
    }
  }

  const response = await fetch(buildApiUrl(path, query), requestOptions);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (response.status === 401 && auth) {
    clearAuthSession();
    if (!window.location.pathname.endsWith("login.html")) {
      window.location.replace("login.html");
    }
  }

  if (!response.ok) {
    const message = typeof payload === "string"
      ? payload
      : payload.message || "Something went wrong.";
    const error = new Error(message);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

async function logout() {
  try {
    if (getToken()) {
      await apiRequest("/logout", { method: "POST" });
    }
  } catch (error) {
    // The local session should still be cleared even if the server is unavailable.
  } finally {
    clearAuthSession();
    window.location.replace("login.html");
  }
}

function getDisplayNameFromEmail(email) {
  const safeEmail = String(email || "").trim();
  if (!safeEmail.includes("@")) {
    return safeEmail || "Admin";
  }

  const name = safeEmail.split("@")[0].replace(/[._-]+/g, " ");
  return name
    .split(" ")
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || "Admin";
}

function populateUserInfo() {
  const email = getStoredEmail();
  const displayName = getDisplayNameFromEmail(email);
  const avatar = displayName.charAt(0).toUpperCase() || "A";

  const userName = document.getElementById("userName");
  const userAvatar = document.getElementById("userAvatar");

  if (userName) {
    userName.textContent = displayName;
    if (email) {
      userName.title = email;
    }
  }

  if (userAvatar) {
    userAvatar.textContent = avatar;
  }
}

function setupSidebar() {
  const menuToggle = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".sidebar");
  const mainContent = document.querySelector(".main-content");

  if (menuToggle && sidebar && mainContent) {
    menuToggle.addEventListener("click", () => {
      sidebar.classList.toggle("active");
      mainContent.classList.toggle("active");
    });
  }

  const menuLinks = document.querySelectorAll(".sidebar-menu a");
  const currentPath = window.location.pathname.split("/").pop();

  menuLinks.forEach(link => {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");
    }

    link.addEventListener("click", () => {
      if (window.innerWidth <= 768 && sidebar && mainContent) {
        sidebar.classList.remove("active");
        mainContent.classList.remove("active");
      }
    });
  });
}

function getTodayLocalDate() {
  const now = new Date();
  const timezoneOffset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - timezoneOffset).toISOString().split("T")[0];
}

function formatDate(dateString) {
  if (!dateString) {
    return "-";
  }

  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    const [year, month, day] = dateString.split("-").map(Number);
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(year, month - 1, day));
  }

  const parsedDate = new Date(dateString);
  if (Number.isNaN(parsedDate.getTime())) {
    return dateString;
  }

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(parsedDate);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, character => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[character]));
}

window.API_BASE_URL = API_BASE_URL;
window.apiRequest = apiRequest;
window.clearAuthSession = clearAuthSession;
window.escapeHtml = escapeHtml;
window.formatDate = formatDate;
window.getDisplayNameFromEmail = getDisplayNameFromEmail;
window.getStoredEmail = getStoredEmail;
window.getTodayLocalDate = getTodayLocalDate;
window.getToken = getToken;
window.logout = logout;
window.populateUserInfo = populateUserInfo;
window.redirectIfAuthenticated = redirectIfAuthenticated;
window.requireAuth = requireAuth;
window.saveAuthSession = saveAuthSession;
window.setupSidebar = setupSidebar;
