/**
 * ========================================
 * AUTHENTICATION UTILITIES MODULE
 * ========================================
 * Handles client-side authentication, token management,
 * and API communication with authorization headers.
 * ========================================
 */

// API endpoint base URL (Railway deployment)
const API_BASE_URL = "https://attendance-systempkccs-production.up.railway.app";

/**
 * Get stored authentication token from localStorage
 * @returns {string|null} JWT token or null if not found
 */
function getToken() {
  return localStorage.getItem("token");
}

/**
 * Get stored user email from localStorage
 * @returns {string} User email or empty string if not found
 */
function getStoredEmail() {
  return localStorage.getItem("userEmail") || "";
}

/**
 * Save authentication session to localStorage
 * @param {string} token - JWT/session token from server
 * @param {string} email - User email address
 */
function saveAuthSession(token, email) {
  localStorage.setItem("token", token);
  localStorage.setItem("userEmail", String(email || "").trim().toLowerCase());
}

/**
 * Clear authentication session from localStorage (logout)
 */
function clearAuthSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("userEmail");
}

/**
 * Require authentication - redirect to login if no token
 * Used on protected pages (dashboard, students, etc.)
 */
function requireAuth() {
  if (!getToken()) {
    window.location.replace("login.html");
  }
}

/**
 * Redirect to dashboard if already authenticated
 * Used on login page to prevent showing it to authenticated users
 * @param {string} targetPage - Where to redirect if authenticated
 */
function redirectIfAuthenticated(targetPage = "dashboard.html") {
  if (getToken()) {
    window.location.replace(targetPage);
  }
}

/**
 * Get request headers with Bearer token authorization
 * @param {object} extraHeaders - Additional headers to merge
 * @returns {object} Headers object with Authorization if token exists
 */
function getAuthHeaders(extraHeaders = {}) {
  const token = getToken();
  return token
    ? { ...extraHeaders, Authorization: `Bearer ${token}` }
    : { ...extraHeaders };
}

/**
 * Build complete API URL with query parameters
 * @param {string} path - API endpoint path
 * @param {object} query - Query parameters object
 * @returns {string} Complete API URL with query string
 */
function buildApiUrl(path, query = {}) {
  const url = new URL(path, `${API_BASE_URL}/`);

  // Add query parameters, skipping empty/null values
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  return url.toString();
}

/**
 * Make authenticated API request with automatic error handling
 * Automatically includes Bearer token in Authorization header
 * Handles JSON and text responses
 * Redirects to login on 401 Unauthorized
 * 
 * @param {string} path - API endpoint path (e.g., "/students")
 * @param {object} options - Request options
 *   - method: HTTP method (default: GET)
 *   - body: Request body (object or FormData)
 *   - headers: Additional headers to include
 *   - auth: Include auth token (default: true)
 *   - query: Query parameters object
 * @returns {Promise} API response data
 * @throws {Error} On API error with message and status properties
 * 
 * @example
 * // GET request
 * const students = await apiRequest("/students");
 * 
 * // POST request
 * const result = await apiRequest("/students", {
 *   method: "POST",
 *   body: { name: "John", roll: "001", class: "10A" }
 * });
 */
async function apiRequest(path, options = {}) {
  const {
    method = "GET",
    body,
    headers = {},
    auth = true,
    query = {},
  } = options;

  // Prepare headers with authentication if needed
  const finalHeaders = auth ? getAuthHeaders(headers) : { ...headers };
  const requestOptions = { method, headers: finalHeaders };

  // Handle request body (JSON or FormData)
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

  // Make the request
  const response = await fetch(buildApiUrl(path, query), requestOptions);
  
  // Parse response based on content type
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  // Handle 401 Unauthorized - clear session and redirect to login
  if (response.status === 401 && auth) {
    clearAuthSession();
    if (!window.location.pathname.endsWith("login.html")) {
      window.location.replace("login.html");
    }
  }

  // Handle error responses
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
