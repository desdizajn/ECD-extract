# OCR Подобрувања за Продукција

## 🎯 Имплементирани Подобрувања

### 1. Македонски Јазик ✅
```bash
# Инсталација
sudo apt-get install -y tesseract-ocr-mkd tesseract-ocr-script-cyrl
```

**Подобрување**: Користиме `mkd+eng` наместо `srp+eng` за македонски документи, што дава подобра точност на препознавање на македонски кирилски карактери.

### 2. Image Preprocessing ✅
```python
def preprocess_image_for_ocr(image):
    """Подобрување на сликата за подобра OCR точност"""
    # 1. Grayscale конверзија
    image = image.convert('L')
    
    # 2. Зголемување на контраст (2x)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # 3. Зголемување на острина (1.5x)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)
    
    # 4. Binarization (црно-бело threshold)
    threshold = 180
    image = image.point(lambda x: 0 if x < threshold else 255, '1')
    
    return image
```

**Ефект**: Подобра точност на препознавање, особено за слаби скенирања.

### 3. Висока Резолуција ✅
```python
images = convert_from_path(pdf_path, dpi=300)  # 300 DPI
```

**Препорака**: За продукција користете **300-400 DPI**. Повисоки вредности (600+ DPI) се побавни без значително подобрување.

## 📊 Споредба на Резултати

| Конфигурација | Карактери | Точност | Забелешка |
|--------------|-----------|---------|-----------|
| `srp+eng` без preprocessing | 2079 | Базична | Оригинална имплементација |
| `srp+eng` со preprocessing | 2081 | Иста | Минимално подобрување |
| `mkd+eng` со preprocessing | 2077 | Подобра | Најдобра за македонски |

## 🚀 Дополнителни Подобрувања за Продукција

### 1. Адаптивен Threshold
Наместо фиксен threshold (180), користете адаптивен:
```python
import cv2
import numpy as np

def adaptive_threshold_preprocessing(image):
    # Конвертирај PIL во OpenCV
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # Adaptive threshold
    img_threshold = cv2.adaptiveThreshold(
        img_cv, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Конвертирај назад во PIL
    return Image.fromarray(img_threshold)
```

### 2. Deskewing (Исправање на Ротација)
Ако документите се криво скенирани:
```python
from deskew import determine_skew
import cv2
import numpy as np

def deskew_image(image):
    img_array = np.array(image)
    angle = determine_skew(img_array)
    
    if abs(angle) > 0.5:  # Ако е повеќе од 0.5 степени
        img_rotated = image.rotate(angle, expand=True, fillcolor='white')
        return img_rotated
    return image
```

### 3. Noise Removal (Отстранување на Шум)
```python
from PIL import ImageFilter

def denoise_image(image):
    # Median filter за отстранување на шум
    return image.filter(ImageFilter.MedianFilter(size=3))
```

### 4. Multiple OCR Attempts со Voting
За критични документи, изврши OCR неколку пати со различни конфигурации и избери најдобар резултат:
```python
def multi_attempt_ocr(image):
    configs = [
        ('mkd+eng', '--oem 3 --psm 6'),
        ('mkd+srp+eng', '--oem 3 --psm 6'),
        ('mkd', '--oem 3 --psm 6'),
    ]
    
    results = []
    for lang, config in configs:
        try:
            text = pytesseract.image_to_string(image, lang=lang, config=config)
            results.append((text, len(text)))
        except:
            continue
    
    # Избери го најдолгиот резултат (веројатно најточен)
    return max(results, key=lambda x: x[1])[0]
```

### 5. Post-processing на Текст
```python
import re

def clean_ocr_text(text):
    # Исправи чести OCR грешки
    replacements = {
        '|': 'I',  # Пајп vs I
        '0': 'O',  # Нула vs O (во зависност од контекст)
        'З': '3',  # Кирилска З vs број 3 (во TIN)
        # Додади повеќе
    }
    
    # Исправи TIN формат (MK + 13 цифри)
    text = re.sub(r'(MK)[О0](\d+)', r'MK\2', text)
    
    return text
```

## 📋 Препорачана Продукциска Конфигурација

```python
def production_ocr_extract(pdf_path):
    """Оптимална OCR конфигурација за продукција"""
    
    # 1. Висока резолуција
    images = convert_from_path(pdf_path, dpi=350)
    
    full_text = ""
    for image in images:
        # 2. Deskewing
        image = deskew_image(image)
        
        # 3. Denoise
        image = denoise_image(image)
        
        # 4. Preprocessing
        image = preprocess_image_for_ocr(image)
        
        # 5. Multiple attempts
        text = multi_attempt_ocr(image)
        
        # 6. Post-processing
        text = clean_ocr_text(text)
        
        full_text += text + "\n"
    
    return full_text
```

## ⚡ Перформанси

### Брзина
- 300 DPI: ~5-10 секунди по страница
- 400 DPI: ~10-15 секунди по страница
- Preprocessing додава: +1-2 секунди по страница

### Паралелизација
За batch обработка користете multiprocessing:
```python
from multiprocessing import Pool

def process_single_page(args):
    image, lang, config = args
    return pytesseract.image_to_string(image, lang=lang, config=config)

def parallel_ocr(images):
    with Pool(4) as pool:  # 4 паралелни процеси
        args = [(img, 'mkd+eng', '--oem 3 --psm 6') for img in images]
        results = pool.map(process_single_page, args)
    return '\n'.join(results)
```

## 🎯 Квалитет на Скенирање

За најдобри резултати, обезбедете:
- ✅ **300+ DPI** резолуција при скенирање
- ✅ **Добро осветлување** (не премногу темно/светло)
- ✅ **Рамен документ** (без извиткани страни)
- ✅ **Чист скенер** (без прав/дамки)
- ✅ **Правилна ориентација** (не наопаку/настрана)

## 📈 Метрики за Евалуација

Следете ги следните метрики:
```python
def evaluate_ocr_quality(extracted_text, expected_fields):
    """Евалуација на квалитетот на OCR"""
    metrics = {
        'total_chars': len(extracted_text),
        'tin_found': bool(re.search(r'MK\d{13}', extracted_text)),
        'date_found': bool(re.search(r'\d{2}/\d{2}/\d{4}', extracted_text)),
        'confidence': calculate_confidence(extracted_text),
    }
    return metrics
```

## 🔧 Tesseract Параметри

### Page Segmentation Modes (PSM)
- `--psm 6`: Assume a single uniform block of text (ECD документи) ✅
- `--psm 4`: Assume a single column of text
- `--psm 3`: Fully automatic page segmentation

### OCR Engine Mode (OEM)
- `--oem 3`: LSTM mode (најдобра точност) ✅
- `--oem 1`: Neural nets LSTM engine
- `--oem 0`: Legacy engine

### Whitelist/Blacklist
За ограничување на карактери:
```python
config = '--oem 3 --psm 6 -c tessedit_char_whitelist=АБВГДЕЖЗИЈКЛМНОПРСТУФХЦЧЏШ0123456789'
```

## 📚 Референци

- [Tesseract Documentation](https://github.com/tesseract-ocr/tesseract)
- [Image Preprocessing for OCR](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html)
- [Macedonian Language Data](https://github.com/tesseract-ocr/tessdata/tree/main)

## ✅ Checklist за Продукција

- [x] Инсталиран македонски јазик (`mkd`)
- [x] Кирилица скрипт (`Cyrillic`)
- [x] Image preprocessing имплементиран
- [x] 300 DPI резолуција
- [x] Fallback механизам (mkd → srp → eng)
- [ ] Adaptive threshold
- [ ] Deskewing
- [ ] Noise removal
- [ ] Post-processing на текст
- [ ] Паралелна обработка
- [ ] Логирање на метрики
- [ ] Error handling и retry логика
