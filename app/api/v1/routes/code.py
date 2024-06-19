from fastapi import APIRouter, Body


router = APIRouter()

@router.post("/run", description="Run code from code block (string)")
async def run_code(code: str = Body(...)):
    return {"message": "Code run successfully."}


@router.post("/submit", description="Submit code to a problem")
async def submit_code():
    return {"message": "Code submitted successfully."}