from fastapi import APIRouter, Body, HTTPException
from services.report_service import generate_report_data, create_pdf_report

router = APIRouter(prefix="/report", tags=["Report"])


@router.post("/")
async def generate_report(file_id: str = Body(...)):
    try:
        # ✅ Generate report data
        report_data = generate_report_data(file_id)

        if not report_data:
            raise HTTPException(status_code=404, detail="Report data not found")

        # ✅ Generate PDF
        pdf_path = create_pdf_report(file_id, report_data)

        return {
            "report": report_data,
            "pdf_path": pdf_path
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        print("Report route error:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report"
        )