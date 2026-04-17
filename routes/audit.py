from fastapi import APIRouter, Body, HTTPException
import json
import os
import pandas as pd

from services.metrics_service import calculate_fairness_metrics
from services.gemini_service import get_gemini_findings  #make sure this exists

router = APIRouter()


@router.post("/")
async def run_audit(
    file_id: str = Body(...),
    filename: str = Body(default=""),
    filepath: str = Body(...),
    sensitive_columns: list = Body(default=[]),
    outcome_column: str = Body(default=""),
    favorable_value: str = Body(default="")
):
    try:
        # ✅ Check file exists
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Dataset not found")

        # ✅ Load dataset
        df = pd.read_csv(filepath)

        if df.empty:
            raise HTTPException(status_code=400, detail="Dataset is empty")

        # =========================================================
        # 🔥 STEP 1: AI SCAN (NO CONFIG PROVIDED)
        # =========================================================
        if not outcome_column or not favorable_value:
            samples = df.head(10).to_dict(orient="records")

            gemini_findings = get_gemini_findings(
                columns=df.columns.tolist(),
                samples=samples
            )

            return {
                "mode": "scan_only",
                "findings": gemini_findings
            }

        # =========================================================
        # 🔥 STEP 2: FULL AUDIT
        # =========================================================

        # fallback if frontend didn't send sensitive columns
        if not sensitive_columns:
            sensitive_columns = []

        # default favorable value
        if not favorable_value:
            favorable_value = "Yes"

        metrics = calculate_fairness_metrics(
            filepath,
            sensitive_columns,
            outcome_column,
            favorable_value
        )

        # ✅ Save metrics for report
        os.makedirs("data/uploads", exist_ok=True)
        with open(f"data/uploads/{file_id}_metrics.json", "w") as f:
            json.dump(metrics, f)

        return {
            "mode": "full_audit",
            "metrics": metrics
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        print("Audit error:", e)
        raise HTTPException(
            status_code=500,
            detail="Audit failed"
        )
    print("Metrics:", metrics)