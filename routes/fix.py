from fastapi import APIRouter, Body, HTTPException
import os
import pandas as pd

from services.metrics_service import calculate_fairness_metrics
from services.fix_service import apply_reweighing_and_resample

router = APIRouter()


@router.post("/")
async def apply_fix(
    file_id: str = Body(...),
    filepath: str = Body(...),
    sensitive_columns: list = Body(...),
    outcome_column: str = Body(...),
    favorable_outcome: str | int | float = Body(...)
):
    try:
        # ✅ Check file exists
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Dataset not found")

        # ✅ Load dataset
        df = pd.read_csv(filepath)

        if len(df) == 0:
            raise HTTPException(status_code=400, detail="Dataset is empty")

        # ✅ Ensure outcome column exists
        if outcome_column not in df.columns:
            raise HTTPException(status_code=400, detail="Invalid outcome column")

        # ✅ Convert favorable outcome type if needed
        if not pd.api.types.is_string_dtype(df[outcome_column]):
            try:
                favorable_outcome = int(favorable_outcome)
            except:
                try:
                    favorable_outcome = float(favorable_outcome)
                except:
                    pass  # keep as string if conversion fails

        # ✅ Apply fix (safe copy)
        df_fixed = df.copy()

        for sc in sensitive_columns:
            if sc not in df_fixed.columns:
                continue

            df_fixed = apply_reweighing_and_resample(
                df_fixed,
                sc,
                outcome_column,
                favorable_outcome
            )

        # ✅ Save fixed dataset
        os.makedirs("data/uploads", exist_ok=True)
        fixed_filepath = f"data/uploads/{file_id}_fixed.csv"
        df_fixed.to_csv(fixed_filepath, index=False)

        # ✅ Recalculate metrics (UPDATED FUNCTION)
        original_metrics = calculate_fairness_metrics(
            filepath,
            sensitive_columns,
            outcome_column,
            favorable_outcome
        )

        fixed_metrics = calculate_fairness_metrics(
            fixed_filepath,
            sensitive_columns,
            outcome_column,
            favorable_outcome
        )

        return {
            "original_metrics": original_metrics,
            "fixed_metrics": fixed_metrics,
            "fixed_filepath": fixed_filepath
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        print("Fix error:", e)
        raise HTTPException(
            status_code=500,
            detail="Error applying fairness fix"
        )