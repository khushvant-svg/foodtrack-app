import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { getMe, updateGoal, getTodaysMeals, logout } from "../api";

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [meals, setMeals] = useState([]);
  const [editingGoal, setEditingGoal] = useState(false);
  const [goalInput, setGoalInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [me, todaysMeals] = await Promise.all([getMe(), getTodaysMeals()]);
      setUser(me);
      setGoalInput(String(me.daily_calorie_goal));
      setMeals(todaysMeals);
    } catch (err) {
      setError(err.message || "Couldn't load your dashboard.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveGoal() {
    const parsed = parseInt(goalInput, 10);
    if (!parsed || parsed <= 0) return;
    try {
      const updated = await updateGoal(parsed);
      setUser(updated);
      setEditingGoal(false);
    } catch (err) {
      setError(err.message || "Couldn't update your goal.");
    }
  }

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  if (loading) {
    return (
      <div className="page">
        <p className="empty-state">Loading…</p>
      </div>
    );
  }

  const totalCalories = meals.reduce((sum, m) => sum + m.calories, 0);
  const goal = user?.daily_calorie_goal || 2000;
  const pct = Math.min(100, Math.round((totalCalories / goal) * 100));

  return (
    <div className="page">
      <div className="page-header">
        <h1>Today</h1>
        <button className="btn-text" onClick={handleLogout}>
          Log out
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="progress-card">
        <div className="progress-ring" style={{ "--pct": `${pct}%` }}>
          <span className="progress-number">{Math.round(totalCalories)}</span>
          <span className="progress-label">of {goal} kcal</span>
        </div>

        {editingGoal ? (
          <div className="goal-edit-row">
            <input
              type="number"
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
            />
            <button className="btn-text" onClick={handleSaveGoal}>
              Save
            </button>
          </div>
        ) : (
          <button className="btn-text" onClick={() => setEditingGoal(true)}>
            Edit goal
          </button>
        )}
      </div>

      <button className="btn-primary btn-large" onClick={() => navigate("/log")}>
        Log a meal
      </button>

      <div className="meal-list">
        <h2>Meals today</h2>
        {meals.length === 0 ? (
          <p className="empty-state">
            Nothing logged yet. <Link to="/log">Snap a photo</Link> to get started.
          </p>
        ) : (
          meals.map((meal) => (
            <div className="meal-row" key={meal.id}>
              <span>{(meal.confirmed_label || meal.food_label).replace(/_/g, " ")}</span>
              <span>{Math.round(meal.calories)} kcal</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
