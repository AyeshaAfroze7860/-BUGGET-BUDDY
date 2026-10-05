import pytesseract
import re
from PIL import Image


# Windows Tesseract location
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text(image_path):
    """
    Extract text from receipt image.
    """

    image = Image.open(image_path)

    text = pytesseract.image_to_string(image)

    return text


def extract_amount(text):
    """
    Try to find the total amount from OCR text.
    """

    patterns = [

        r"(?:grand\s*total|total\s*amount|net\s*amount|total)"
        r"\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)",

        r"₹\s*([0-9]+(?:\.[0-9]{1,2})?)",

        r"rs\.?\s*([0-9]+(?:\.[0-9]{1,2})?)",

        r"inr\s*([0-9]+(?:\.[0-9]{1,2})?)"

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        if matches:

            try:
                values = [
                    float(value)
                    for value in matches
                ]

                return max(values)

            except ValueError:
                pass

    # Fallback:
    # Find numbers and take the largest amount
    numbers = re.findall(
        r"\b\d+(?:\.\d{1,2})?\b",
        text
    )

    if numbers:

        values = []

        for number in numbers:

            try:
                values.append(float(number))
            except ValueError:
                pass

        if values:
            return max(values)

    return None


def detect_category(text):
    """
    Detect expense category based on receipt text.
    """

    text = text.lower()

    food = [
        "restaurant",
        "food",
        "grocery",
        "supermarket",
        "rice",
        "milk",
        "bread",
        "vegetable",
        "fruit",
        "snack",
        "chicken",
        "meat",
        "pizza"
    ]

    travel = [
        "uber",
        "ola",
        "petrol",
        "fuel",
        "bus",
        "metro",
        "train",
        "taxi"
    ]

    shopping = [
        "amazon",
        "mall",
        "clothing",
        "shirt",
        "dress",
        "shoe",
        "fashion",
        "shopping"
    ]

    healthcare = [
        "hospital",
        "pharmacy",
        "medicine",
        "medical",
        "clinic"
    ]

    education = [
        "college",
        "school",
        "book",
        "course",
        "education"
    ]

    if any(word in text for word in food):
        return "Food"

    if any(word in text for word in travel):
        return "Travel"

    if any(word in text for word in shopping):
        return "Shopping"

    if any(word in text for word in healthcare):
        return "Healthcare"

    if any(word in text for word in education):
        return "Education"

    return "Other"


def process_receipt(image_path):
    """
    Complete OCR processing.
    """

    text = extract_text(image_path)

    amount = extract_amount(text)

    category = detect_category(text)

    return {
        "text": text,
        "amount": amount,
        "category": category
    }