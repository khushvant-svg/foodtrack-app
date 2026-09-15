import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { predictFood, logMeal } from "../api";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [selectedLabel, setSelectedLabel] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function handleFileChange(e) {
    const selected = e.target.files?.[0];
    if (!selected) return;

    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setResult(null);
    setSelectedLabel(null);
    setError("");
  }

  async function handleAnalyze() {
    if (!file) return;
    setAnalyzing(true);
    setError("");
    try {
      const prediction = await predictFood(file);
      setResult(prediction);
      setSelectedLabel(prediction.top_prediction);
    } catch (err) {
      setError(err.message || "Couldn't analyze that photo. Try another one.");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleConfirm() {
    if (!result) return;
    setSaving(true);
    setError("");
    try {
      await logMeal({
        food_label: result.top_prediction,
        confirmed_label:
          selectedLabel !== result.top_prediction ? selectedLabel : null,
        calories: result.calories,
        protein_g: result.protein_g,
        carbs_g: result.carbs_g,
        fat_g: result.fat_g,
      });
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message || "Couldn't log that meal. Try again.");
    } finally {
      setSaving(false);
    }
  }

  const allLabels = result
    ? [result.top_prediction, ...result.alternatives]
    : [];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Log a meal</h1>
      </div>

      <div className="upload-card">
        <label className="drop-zone" htmlFor="photo-input">
          {previewUrl ? (
            <img src={previewUrl} alt="Selected meal" className="preview-img" />
          ) : (
            <span>Tap to choose a photo of your meal</span>
          )}
        </label>
        <input
          id="photo-input"
          type="file"
          accept="image/jpeg,image/png"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />

        {error && <p className="error-text">{error}</p>}

        {!result && (
          <button
            className="btn-primary btn-large"
            onClick={handleAnalyze}
            disabled={!file || analyzing}
          >
            {analyzing ? "Analyzing…" : "Analyze photo"}
          </button>
        )}

        {result && (
          <div className="result-block">
            <h2 className="result-title">
              {selectedLabel.replace(/_/g, " ")}
              <span className="confidence-badge">
                {Math.round(result.confidence * 100)}% match
              </span>
            </h2>

            {allLabels.length > 1 && (
              <>
                <p className="result-note">Not quite right? Pick another guess:</p>
                <div className="chip-row">
                  {allLabels.map((label) => (
                    <button
                      key={label}
                      className={`chip ${
                        label === selectedLabel ? "chip-active" : ""
                      }`}
                      onClick={() => setSelectedLabel(label)}
                      type="button"
                    >
                      {label.replace(/_/g, " ")}
                    </button>
                  ))}
                </div>
              </>
            )}

            <div className="macro-grid">
              <div>
                <strong>{Math.round(result.calories)}</strong>
                <span>kcal</span>
              </div>
              <div>
                <strong>{Math.round(result.protein_g)}g</strong>
                <span>protein</span>
              </div>
              <div>
                <strong>{Math.round(result.carbs_g)}g</strong>
                <span>carbs</span>
              </div>
              <div>
                <strong>{Math.round(result.fat_g)}g</strong>
                <span>fat</span>
              </div>
            </div>

            <button
              className="btn-primary"
              onClick={handleConfirm}
              disabled={saving}
            >
              {saving ? "Logging…" : "Log this meal"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
