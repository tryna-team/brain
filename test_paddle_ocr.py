from paddleocr import PaddleOCR

ocr = PaddleOCR(
    lang="korean",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

results = ocr.predict("test_image.png")

for result in results:
    print(result.get("rec_texts", []))