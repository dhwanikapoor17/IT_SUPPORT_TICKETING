"use client";

import { FormEvent, useEffect, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Role = "user" | "admin";

type Ticket = {
  id: number;
  user_id: number;
  company: string;
  issue_type: string;
  location: string;
  issue: string;
  status: string;
  remarks: string | null;
  created_at?: string;
};

type CurrentUser = {
  id: number;
  name: string;
  email: string;
  role: Role;
};

const companies = ["Medfreshe", "CollarCheck", "Narula Exports"];

const issueTypes = [
  "Hardware",
  "Software",
  "Network",
  "Login / Access",
  "Printer",
  "Other",
];

const locations = [
  "1st Floor",
  "2nd Floor",
  "3rd Floor",
  "4th Floor",
];

function getErrorMessage(data: any, fallback: string): string {
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((item: any) => item?.msg || "Invalid request")
      .join(", ");
  }

  if (typeof data?.message === "string") {
    return data.message;
  }

  return fallback;
}

export default function Home() {
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);
  const [role, setRole] = useState<Role | null>(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccessMessage("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    setSubmitting(true);

    try {
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password,
        }),
      });

      const loginData = await loginResponse.json();

      if (!loginResponse.ok) {
        throw new Error(
          getErrorMessage(loginData, "Invalid email or password.")
        );
      }

      if (!loginData.access_token) {
        throw new Error("Access token was not received.");
      }

      const token = loginData.access_token;
      localStorage.setItem("access_token", token);

      const meResponse = await fetch(`${API_URL}/auth/me`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const meData = await meResponse.json();

      if (!meResponse.ok) {
        throw new Error(
          getErrorMessage(meData, "Unable to fetch account details.")
        );
      }

      const currentUser: CurrentUser = meData;

      if (
        currentUser.role !== "user" &&
        currentUser.role !== "admin"
      ) {
        throw new Error("Invalid account role.");
      }

      setRole(currentUser.role);
      setLoggedIn(true);
    } catch (err) {
      localStorage.removeItem("access_token");
      setError(
        err instanceof Error
          ? err.message
          : "Login failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccessMessage("");

    if (!name.trim()) {
      setError("Please enter your full name.");
      return;
    }

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setSubmitting(true);

    try {
      // 1. Create account via /auth/signup
      const signupResponse = await fetch(`${API_URL}/auth/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password: password,
        }),
      });

      const signupData = await signupResponse.json();

      if (!signupResponse.ok) {
        throw new Error(
          getErrorMessage(signupData, "Registration failed. Please try again.")
        );
      }

      // 2. Automatically log in after successful signup
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password,
        }),
      });

      const loginData = await loginResponse.json();

      if (!loginResponse.ok || !loginData.access_token) {
        setSuccessMessage("Account created successfully! Please sign in.");
        setAuthMode("login");
        return;
      }

      const token = loginData.access_token;
      localStorage.setItem("access_token", token);

      const meResponse = await fetch(`${API_URL}/auth/me`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const meData = await meResponse.json();

      if (!meResponse.ok) {
        setSuccessMessage("Account created successfully! Please sign in.");
        setAuthMode("login");
        return;
      }

      const currentUser: CurrentUser = meData;
      setRole(currentUser.role);
      setLoggedIn(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Registration failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setName("");
    setEmail("");
    setPassword("");
    setRole(null);
    setLoggedIn(false);
    setError("");
    setSuccessMessage("");
  };

  if (loggedIn && role === "admin") {
    return <AdminDashboard onLogout={handleLogout} />;
  }

  if (loggedIn && role === "user") {
    return <UserDashboard onLogout={handleLogout} />;
  }

  return (
    <main className="auth-page">
      <section className="login-card">
        <div className="brand-icon">IT</div>

        <h1>{authMode === "login" ? "IT Support Portal" : "Create an Account"}</h1>

        <p className="auth-subtitle">
          {authMode === "login"
            ? "Sign in to raise and manage your IT support tickets."
            : "Sign up to raise and track your IT support requests."}
        </p>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab-btn ${authMode === "login" ? "active" : ""}`}
            onClick={() => {
              setAuthMode("login");
              setError("");
              setSuccessMessage("");
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${authMode === "signup" ? "active" : ""}`}
            onClick={() => {
              setAuthMode("signup");
              setError("");
              setSuccessMessage("");
            }}
          >
            Sign Up
          </button>
        </div>

        {authMode === "login" ? (
          <form onSubmit={handleLogin} className="login-form">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            {error && <p className="error-text">{error}</p>}
            {successMessage && <p className="success-text">{successMessage}</p>}

            <button
              type="submit"
              className="primary-button"
              disabled={submitting}
            >
              {submitting ? "Signing In..." : "Sign In"}
            </button>

            <p className="auth-switch-prompt">
              Don't have an account?
              <button
                type="button"
                className="auth-switch-link"
                onClick={() => {
                  setAuthMode("signup");
                  setError("");
                  setSuccessMessage("");
                }}
              >
                Sign Up
              </button>
            </p>
          </form>
        ) : (
          <form onSubmit={handleSignup} className="login-form">
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              type="text"
              placeholder="Enter your full name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />

            <label htmlFor="signup-email">Email Address</label>
            <input
              id="signup-email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />

            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              type="password"
              placeholder="Create a password (min 6 characters)"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            {error && <p className="error-text">{error}</p>}
            {successMessage && <p className="success-text">{successMessage}</p>}

            <button
              type="submit"
              className="primary-button"
              disabled={submitting}
            >
              {submitting ? "Creating Account..." : "Create Account"}
            </button>

            <p className="auth-switch-prompt">
              Already have an account?
              <button
                type="button"
                className="auth-switch-link"
                onClick={() => {
                  setAuthMode("login");
                  setError("");
                  setSuccessMessage("");
                }}
              >
                Sign In
              </button>
            </p>
          </form>
        )}

        <p className="auth-footer">
          Your dashboard is automatically determined by your account access.
        </p>
      </section>
    </main>
  );
}

function UserDashboard({
  onLogout,
}: {
  onLogout: () => void;
}) {
  const [activeTab, setActiveTab] = useState<"create" | "tickets">(
    "create"
  );

  const [company, setCompany] = useState("");
  const [issueType, setIssueType] = useState("");
  const [location, setLocation] = useState("");
  const [issue, setIssue] = useState("");

  const [preview, setPreview] = useState(false);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function loadMyTickets() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Your session has expired. Please login again.");
      return;
    }

    setLoadingTickets(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/my-tickets`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Unable to load your tickets.")
        );
      }

      setTickets(data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to load your tickets."
      );
    } finally {
      setLoadingTickets(false);
    }
  }

  useEffect(() => {
    loadMyTickets();
  }, []);

  const submitTicket = async () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Your session has expired. Please login again.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/tickets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          company: company,
          issue_type: issueType,
          location: location,
          issue: issue,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Ticket submission failed.")
        );
      }

      await loadMyTickets();

      setCompany("");
      setIssueType("");
      setLocation("");
      setIssue("");
      setPreview(false);
      setActiveTab("tickets");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to submit ticket."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="dashboard-page">
      <Header
        title="IT Support Dashboard"
        subtitle="User Portal"
        onLogout={onLogout}
      />

      <section className="dashboard-wrapper">
        <div className="welcome-section">
          <div>
            <p className="small-label">WELCOME BACK</p>

            <h2>Raise an IT support ticket</h2>

            <p>
              Report your issue and track the progress of your support request.
            </p>
          </div>

          <div className="welcome-icon">🎫</div>
        </div>

        <div className="tabs">
          <button
            className={
              activeTab === "create" ? "tab active-tab" : "tab"
            }
            onClick={() => setActiveTab("create")}
          >
            Raise Ticket
          </button>

          <button
            className={
              activeTab === "tickets" ? "tab active-tab" : "tab"
            }
            onClick={() => setActiveTab("tickets")}
          >
            My Tickets
          </button>
        </div>

        {error && <p className="error-text">{error}</p>}

        {activeTab === "create" && (
          <section className="panel">
            <div className="panel-heading">
              <h3>Create New Ticket</h3>
              <p>Fill in the details of your IT-related issue.</p>
            </div>

            {!preview ? (
              <div className="ticket-form">
                <div className="form-grid">
                  <div>
                    <label>Company</label>

                    <select
                      value={company}
                      onChange={(event) => setCompany(event.target.value)}
                    >
                      <option value="">Select company</option>

                      {companies.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label>Issue Type</label>

                    <select
                      value={issueType}
                      onChange={(event) => setIssueType(event.target.value)}
                    >
                      <option value="">Select issue type</option>

                      {issueTypes.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label>Sitting Location</label>

                    <select
                      value={location}
                      onChange={(event) => setLocation(event.target.value)}
                    >
                      <option value="">Select floor</option>

                      {locations.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label>Describe Your Issue</label>

                  <textarea
                    placeholder="Explain your issue in detail..."
                    value={issue}
                    onChange={(event) => setIssue(event.target.value)}
                    rows={6}
                  />
                </div>

                <button
                  className="primary-button small-button"
                  onClick={() => setPreview(true)}
                  disabled={
                    !company ||
                    !issueType ||
                    !location ||
                    !issue.trim()
                  }
                >
                  Preview Ticket
                </button>
              </div>
            ) : (
              <div className="preview-box">
                <h3>Ticket Preview</h3>

                <div className="preview-row">
                  <span>Company</span>
                  <strong>{company}</strong>
                </div>

                <div className="preview-row">
                  <span>Issue Type</span>
                  <strong>{issueType}</strong>
                </div>

                <div className="preview-row">
                  <span>Location</span>
                  <strong>{location}</strong>
                </div>

                <div className="preview-description">
                  <span>Issue Description</span>
                  <p>{issue}</p>
                </div>

                <div className="preview-actions">
                  <button
                    className="secondary-button"
                    onClick={() => setPreview(false)}
                    disabled={submitting}
                  >
                    Edit
                  </button>

                  <button
                    className="primary-button"
                    onClick={submitTicket}
                    disabled={submitting}
                  >
                    {submitting ? "Submitting..." : "Confirm & Submit"}
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {activeTab === "tickets" && (
          <section className="panel">
            <div className="panel-heading">
              <h3>My Tickets</h3>
              <p>Track the status of your submitted tickets.</p>
            </div>

            {loadingTickets ? (
              <div className="empty-state">
                <h3>Loading tickets...</h3>
              </div>
            ) : tickets.length === 0 ? (
              <div className="empty-state">
                <div>📂</div>
                <h3>No tickets yet</h3>
                <p>Your submitted tickets will appear here.</p>
              </div>
            ) : (
              <div className="ticket-list">
                {tickets.map((ticket) => (
                  <div className="ticket-card" key={ticket.id}>
                    <div className="ticket-top">
                      <div>
                        <span className="ticket-number">
                          Ticket #{ticket.id}
                        </span>

                        <h3>{ticket.issue_type}</h3>
                      </div>

                      <span
                        className={`status ${ticket.status
                          .toLowerCase()
                          .replaceAll(" ", "-")}`}
                      >
                        {ticket.status}
                      </span>
                    </div>

                    <p>
                      <strong>Company:</strong> {ticket.company}
                    </p>

                    <p>
                      <strong>Location:</strong> {ticket.location}
                    </p>

                    <p>
                      <strong>Issue:</strong> {ticket.issue}
                    </p>

                    {ticket.remarks && (
                      <p>
                        <strong>Admin Remarks:</strong>{" "}
                        {ticket.remarks}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </section>
    </main>
  );
}

function AdminDashboard({
  onLogout,
}: {
  onLogout: () => void;
}) {
  const [filter, setFilter] = useState("All");
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [error, setError] = useState("");

  async function loadAllTickets() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Your session has expired. Please login again.");
      return;
    }

    setLoadingTickets(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/tickets`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Unable to load admin tickets.")
        );
      }

      setTickets(data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to load admin tickets."
      );
    } finally {
      setLoadingTickets(false);
    }
  }

  useEffect(() => {
    loadAllTickets();
  }, []);

  const updateTicket = async (
    id: number,
    field: "status" | "remarks",
    value: string
  ) => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Your session has expired. Please login again.");
      return;
    }

    setError("");

    try {
      const response = await fetch(`${API_URL}/tickets/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          [field]: value,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Ticket update failed.")
        );
      }

      const updatedTicket: Ticket = data;

      setTickets((currentTickets) =>
        currentTickets.map((ticket) =>
          ticket.id === id ? updatedTicket : ticket
        )
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to update ticket."
      );
    }
  };

  const filteredTickets =
    filter === "All"
      ? tickets
      : tickets.filter((ticket) => ticket.status === filter);

  const openCount = tickets.filter(
    (ticket) => ticket.status === "Open"
  ).length;

  const progressCount = tickets.filter(
    (ticket) => ticket.status === "In Progress"
  ).length;

  const resolvedCount = tickets.filter(
    (ticket) => ticket.status === "Resolved"
  ).length;

  return (
    <main className="dashboard-page">
      <Header
        title="IT Support Dashboard"
        subtitle="Admin Portal"
        onLogout={onLogout}
      />

      <section className="dashboard-wrapper">
        <div className="welcome-section">
          <div>
            <p className="small-label">ADMIN CONTROL CENTER</p>

            <h2>Manage support requests</h2>

            <p>
              Review tickets, assign updates, and track issue resolution.
            </p>
          </div>

          <div className="welcome-icon">🛠️</div>
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon blue-icon">🎫</div>

            <div>
              <p>Total Tickets</p>
              <h3>{tickets.length}</h3>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon orange-icon">⏳</div>

            <div>
              <p>Open Tickets</p>
              <h3>{openCount}</h3>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon purple-icon">🔧</div>

            <div>
              <p>In Progress</p>
              <h3>{progressCount}</h3>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon green-icon">✓</div>

            <div>
              <p>Resolved</p>
              <h3>{resolvedCount}</h3>
            </div>
          </div>
        </div>

        <section className="panel">
          <div className="admin-panel-header">
            <div className="panel-heading no-border">
              <h3>Support Tickets</h3>

              <p>Review and update all tickets raised by users.</p>
            </div>

            <div className="filter-wrapper">
              <label>Filter by Status</label>

              <select
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
              >
                <option value="All">All Tickets</option>
                <option value="Open">Open</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
                <option value="Closed">Closed</option>
              </select>
            </div>
          </div>

          {loadingTickets ? (
            <div className="empty-state">
              <h3>Loading tickets...</h3>
            </div>
          ) : filteredTickets.length === 0 ? (
            <div className="empty-state">
              <div>📂</div>

              <h3>No tickets found</h3>

              <p>No tickets match the selected status.</p>
            </div>
          ) : (
            <div className="admin-ticket-list">
              {filteredTickets.map((ticket) => (
                <div
                  className="admin-ticket-card"
                  key={ticket.id}
                >
                  <div className="admin-ticket-top">
                    <div>
                      <span className="ticket-number">
                        Ticket #{ticket.id}
                      </span>

                      <h3>{ticket.issue_type}</h3>
                    </div>

                    <span
                      className={`status ${ticket.status
                        .toLowerCase()
                        .replaceAll(" ", "-")}`}
                    >
                      {ticket.status}
                    </span>
                  </div>

                  <div className="ticket-information">
                    <p>
                      <strong>Company:</strong> {ticket.company}
                    </p>

                    <p>
                      <strong>Location:</strong> {ticket.location}
                    </p>

                    <p>
                      <strong>Issue:</strong> {ticket.issue}
                    </p>

                    {ticket.remarks && (
                      <p>
                        <strong>Current Remarks:</strong>{" "}
                        {ticket.remarks}
                      </p>
                    )}
                  </div>

                  <div className="admin-update-area">
                    <div>
                      <label>Update Status</label>

                      <select
                        value={ticket.status}
                        onChange={(event) =>
                          updateTicket(
                            ticket.id,
                            "status",
                            event.target.value
                          )
                        }
                      >
                        <option>Open</option>
                        <option>In Progress</option>
                        <option>Resolved</option>
                        <option>Closed</option>
                      </select>
                    </div>

                    <div>
                      <label>Admin Remarks</label>

                      <input
                        type="text"
                        defaultValue={ticket.remarks || ""}
                        placeholder="Enter remarks for the user"
                        onBlur={(event) => {
                          const newRemarks = event.target.value;

                          if (
                            newRemarks !== (ticket.remarks || "")
                          ) {
                            updateTicket(
                              ticket.id,
                              "remarks",
                              newRemarks
                            );
                          }
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

function Header({
  title,
  subtitle,
  onLogout,
}: {
  title: string;
  subtitle: string;
  onLogout: () => void;
}) {
  return (
    <header className="topbar">
      <div className="topbar-brand">
        <div className="mini-logo">IT</div>

        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>

      <button className="logout-button" onClick={onLogout}>
        Logout
      </button>
    </header>
  );
}