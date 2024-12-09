from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

# Load the image
image_path = "nutrition_image1.jpg"
image = Image.open(image_path)

# Preprocess the image
image = image.convert("L")  # Convert to grayscale
image = image.filter(ImageFilter.SHARPEN)  # Sharpen the image
image = ImageEnhance.Contrast(image).enhance(2)  # Increase contrast

# Perform OCR
extracted_text = pytesseract.image_to_string(image, config="--psm 6")
print("Extracted Text:", extracted_text)
