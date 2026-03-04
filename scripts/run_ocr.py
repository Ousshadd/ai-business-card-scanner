import cv2, sys
from app.preprocessor import ImagePreprocessor
from app.ocr import OCREngine

if len(sys.argv) < 2:
    print("Usage: python run_ocr.py <image_path>")
    sys.exit(1)

path = sys.argv[1]
img = cv2.imread(path)
if img is None:
    print('Image not found')
    sys.exit(1)

_, buf = cv2.imencode('.jpg', img)
bytes_data = buf.tobytes()

proc = ImagePreprocessor()
ocr = OCREngine()
pre = proc.preprocess(bytes_data)
text = ocr.extract_text(pre)

print('---- OCR RESULT ----')
print(text)
