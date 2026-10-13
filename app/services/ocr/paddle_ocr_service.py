import os
import tempfile
from functools import lru_cache

from paddleocr import PaddleOCR


@lru_cache(maxsize=1)
def get_paddle_ocr() -> PaddleOCR:
    return PaddleOCR(
        lang="korean",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )


class PaddleOcrService:
    def extract_text(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        suffix = ".png" if content_type == "image/png" else ".jpg"
        path = None

        try:
            # 업로드된 이미지를 임시 파일로 저장
            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False,
            ) as temp_file:
                temp_file.write(image_bytes)
                path = temp_file.name

            # PaddleOCR 실행
            results = get_paddle_ocr().predict(path)

            # 인식된 텍스트 추출
            lines = []

            for result in results:
                lines.extend(result.get("rec_texts", []))

            return "\n".join(lines)

        finally:
            # OCR 처리 후 임시 파일 삭제
            if path is not None:
                os.unlink(path)


paddle_ocr_service = PaddleOcrService()