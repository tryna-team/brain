from io import BytesIO
from PIL import Image, UnidentifiedImageError

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.services.ocr.image_ocr_service import image_ocr_service
from app.services.ocr.paddle_ocr_service import paddle_ocr_service


router = APIRouter(prefix="/images")


@router.post("/ocr")
async def extract_image_text(
    image: UploadFile = File(...),
):
    allowed_types = {
        "image/jpeg",
        "image/png",
    }

    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="JPG 또는 PNG 이미지만 업로드할 수 있습니다.",
        )

    # 최대 10MB
    max_size = 10 * 1024 * 1024

    image_bytes = await image.read(max_size + 1)

    if len(image_bytes) > max_size:
        raise HTTPException(
            status_code=413,
            detail="이미지 크기는 10MB를 초과할 수 없습니다.",
        )

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="이미지 파일이 비어 있습니다.",
        )

    # 실제 이미지 형식 및 크기 검증
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            if img.format not in {"JPEG", "PNG"}:
                raise HTTPException(
                    status_code=400,
                    detail="유효한 JPG 또는 PNG 이미지가 아닙니다.",
                )

            width, height = img.size

            if width > 5000 or height > 5000 or width * height > 20_000_000:
                raise HTTPException(
                    status_code=400,
                    detail="이미지 크기가 너무 큽니다.",
                )

            img.verify()

    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="이미지 파일을 읽을 수 없습니다.",
        )

    try:
        text = await run_in_threadpool(
            # upstage OCR
            # image_ocr_service.extract_text,
            # paddle OCR
            paddle_ocr_service.extract_text,
            image_bytes,
            image.filename or "image.png",
            image.content_type,
        )

        return {
            "success": True,
            "result": {
                "text": text,
            },
        }

    except Exception as e:
        import traceback

        print("OCR ERROR:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail="OCR 처리 중 오류가 발생했습니다.",
        )