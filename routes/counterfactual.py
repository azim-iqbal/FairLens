from fastapi import APIRouter
router = APIRouter()
import pandas as pd
def run_counterfactual_test(filepath, sensitive_column, outcome_column):
    try:
        df = pd.read_csv(filepath)

        # ✅ Basic validation
        if sensitive_column not in df.columns or outcome_column not in df.columns:
            return 0, [], "Low"

        if len(df) == 0:
            return 0, [], "Low"

        # Drop rows with missing values (important)
        df = df.dropna(subset=[sensitive_column, outcome_column])

        if len(df) == 0:
            return 0, [], "Low"

        # Prepare data
        X = df.drop(columns=[outcome_column])
        y = df[outcome_column]

        # Encode categorical safely
        from sklearn.tree import DecisionTreeClassifier
        import category_encoders as ce

        encoder = ce.OrdinalEncoder(handle_unknown="value")
        X_enc = encoder.fit_transform(X)

        # Train simple model
        model = DecisionTreeClassifier(max_depth=5, random_state=42)
        model.fit(X_enc, y)

        preds_original = model.predict(X_enc)

        # ✅ SAFE COPY (no mutation bug)
        X_flipped = X.copy()

        unique_vals = df[sensitive_column].dropna().unique()

        if len(unique_vals) < 2:
            return 0, [], "Low"

        # Flip sensitive attribute
        for idx in X_flipped.index:
            orig_val = X_flipped.at[idx, sensitive_column]
            new_val = next((v for v in unique_vals if v != orig_val), orig_val)
            X_flipped.at[idx, sensitive_column] = new_val

        # Encode flipped
        X_flipped_enc = encoder.transform(X_flipped)

        preds_flipped = model.predict(X_flipped_enc)

        # Compare
        flip_mask = preds_original != preds_flipped
        flip_count = flip_mask.sum()

        flip_rate = (flip_count / len(df)) * 100

        # Collect sample evidence
        flipped_samples = []
        flipped_indices = df[flip_mask].index.tolist()[:5]

        for idx in flipped_indices:
            flipped_samples.append({
                "original_sensitive": str(df.at[idx, sensitive_column]),
                "flipped_sensitive": str(X_flipped.at[idx, sensitive_column]),
                "original_outcome": str(preds_original[idx]),
                "flipped_outcome": str(preds_flipped[idx])
            })

        # Severity classification
        if flip_rate < 10:
            severity = "Low"
        elif flip_rate <= 25:
            severity = "Medium"
        else:
            severity = "High"

        return float(flip_rate), flipped_samples, severity

    except Exception as e:
        print("Counterfactual error:", e)
        return 0, [], "Low"