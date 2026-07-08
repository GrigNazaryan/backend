from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.db_models import Service, User
from app.models.schemas import SendCodeRequest, TokenResponse, UserOut, VerifyCodeRequest
from app.services.otp_service import OtpError, send_verification_code, verify_code_and_sign_in

router = APIRouter(prefix="/auth", tags=["auth"])


# @router.post("/send-code", status_code=status.HTTP_204_NO_CONTENT)
# def send_code(payload: SendCodeRequest, db: Session = Depends(get_db)):
#     try:
#         send_verification_code(db, payload.email)
#     except OtpError as e:
#         raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

@router.post("/send-code", status_code=status.HTTP_204_NO_CONTENT)
def send_code(payload: SendCodeRequest, db: Session = Depends(get_db)):
    print(f"DEBUG: Payload received: {payload.dict()}") # <-- ЭТА СТРОКА ПОКАЖЕТ, ЧТО ПРИШЛО
    try:
        send_verification_code(db, payload.email)
    except OtpError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))



@router.post("/verify-code", response_model=TokenResponse)
def verify_code(payload: VerifyCodeRequest, db: Session = Depends(get_db)):
    try:
        user, token = verify_code_and_sign_in(
            db, payload.email, payload.code, payload.display_name, payload.phone_number
        )
    except OtpError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return TokenResponse(access_token=token, user=UserOut.model_validate(user, from_attributes=True))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently deletes the signed-in user's account and every
    listing they posted. Required by Google Play policy (apps with
    accounts must offer in-app account deletion, not just sign-out) —
    and just the right thing to do regardless."""
    db.execute(delete(Service).where(Service.owner_id == current_user.id))
    db.delete(current_user)
    db.commit()
