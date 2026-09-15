import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { signup, login } from "../api";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signup(email, password);
      // Sign up doesn't return a token, so log in right after.
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message || "Couldn't create your account. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Create account</h1>
        <p className="subtext">Track what you eat, one photo at a time.</p>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>

        {error && <p className="error-text">{error}</p>}

        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? "Creating account…" : "Sign up"}
        </button>

        <p className="switch-link">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
