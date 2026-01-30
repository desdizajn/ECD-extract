#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECD Format Detector - Детектор за автоматско препознавање на типот на ЕЦД документ
"""

import fitz  # PyMuPDF
import re
from enum import Enum


class ECDFormat(Enum):
    """Типови на ЕЦД формати"""
    STANDARD = "standard"      # Стандарден ЕЦД формат (ECD.pdf, ECD341.pdf)
    CUSTOMS = "customs"        # Царински формат (ECDcarina.pdf)
    UNKNOWN = "unknown"


class ECDFormatDetector:
    """Детектор за автоматско препознавање на типот на ЕЦД документ"""
    
    def __init__(self, pdf_path: str, verbose: bool = False):
        self.pdf_path = pdf_path
        self.verbose = verbose
        self.text = ""
        
    def extract_text_sample(self) -> str:
        """Извлекува примерок текст од првата страница за анализа"""
        try:
            doc = fitz.open(self.pdf_path)
            if len(doc) > 0:
                # Земи ги првите 2 страници за анализа
                text = ""
                for i in range(min(2, len(doc))):
                    text += doc[i].get_text()
                self.text = text
                doc.close()
                return text
            doc.close()
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Грешка при извлекување на текст: {e}")
        return ""
    
    def detect_format(self) -> ECDFormat:
        """
        Детектира кој формат на ЕЦД документ е.
        
        Карактеристики за препознавање:
        
        STANDARD формат:
        - "Испраќач/Извозник" (кирилица)
        - "РДБ" е на специфично место
        - LRN на врвот со формат: "LRN : 24MK..."
        
        CUSTOMS формат:
        - "Consignor/Exporter" (латиница)
        - "РБД" наместо "РДБ"
        - "референтен број" е поле 7 со формат: "1/2026" или "BB/2026"
        """
        if not self.text:
            self.extract_text_sample()
        
        if not self.text:
            return ECDFormat.UNKNOWN
        
        # Проверки за CUSTOMS формат
        customs_indicators = 0
        
        # 1. Проверка за "Consignor/Exporter" (типично за царински формат)
        if "Consignor/Exporter" in self.text or "Consignor / Exporter" in self.text:
            customs_indicators += 2
            if self.verbose:
                print("   ✓ Детектиран 'Consignor/Exporter' (царински формат)")
        
        # 2. Проверка за "РБД" наместо "РДБ"
        if "РБД" in self.text and "РДБ" not in self.text:
            customs_indicators += 1
            if self.verbose:
                print("   ✓ Детектиран 'РБД' (царински формат)")
        
        # 3. Проверка за референтен број во формат "1/2026" или "BB/2026" на почеток
        ref_pattern = r'7\s+референтен број\s+[\w\d]+/\d{4}'
        if re.search(ref_pattern, self.text, re.IGNORECASE):
            customs_indicators += 2
            if self.verbose:
                print("   ✓ Детектиран референтен број со формат 'X/YYYY' (царински формат)")
        
        # 4. Проверка за "Ознаки и броеви" (типично за царински)
        if "Ознаки и броеви - Број на контејнер" in self.text:
            customs_indicators += 1
            if self.verbose:
                print("   ✓ Детектиран 'Ознаки и броеви' (царински формат)")
        
        # Проверки за STANDARD формат
        standard_indicators = 0
        
        # 1. Проверка за "Испраќач/Извозник" (кирилица)
        if "Испраќач/Извозник" in self.text or "Испраќач / Извозник" in self.text:
            standard_indicators += 2
            if self.verbose:
                print("   ✓ Детектиран 'Испраќач/Извозник' (стандарден формат)")
        
        # 2. Проверка за LRN на врвот
        if re.search(r'LRN\s*:\s*\d{2}MK', self.text):
            standard_indicators += 2
            if self.verbose:
                print("   ✓ Детектиран LRN формат (стандарден формат)")
        
        # 3. Проверка за "РДБ" на почеток
        if re.search(r'РДБ\s+\d', self.text):
            standard_indicators += 1
            if self.verbose:
                print("   ✓ Детектиран 'РДБ' формат (стандарден формат)")
        
        # 4. Проверка за "тов.лист" / "товарен лист"
        if "тов.лист" in self.text.lower() or "товарен лист" in self.text.lower():
            standard_indicators += 1
            if self.verbose:
                print("   ✓ Детектиран 'тов.лист' (стандарден формат)")
        
        # Одлучување врз основа на индикаторите
        if self.verbose:
            print(f"\n   Индикатори: Царински={customs_indicators}, Стандарден={standard_indicators}")
        
        if customs_indicators > standard_indicators and customs_indicators >= 2:
            if self.verbose:
                print("   🎯 Препознат: ЦАРИНСКИ формат")
            return ECDFormat.CUSTOMS
        elif standard_indicators > customs_indicators and standard_indicators >= 2:
            if self.verbose:
                print("   🎯 Препознат: СТАНДАРДЕН формат")
            return ECDFormat.STANDARD
        else:
            if self.verbose:
                print("   ⚠️  Не може да се детектира форматот")
            return ECDFormat.UNKNOWN


def detect_ecd_format(pdf_path: str, verbose: bool = False) -> ECDFormat:
    """
    Помошна функција за детекција на формат.
    
    Args:
        pdf_path: Патека до PDF фајлот
        verbose: Дали да прикажува детални информации
        
    Returns:
        ECDFormat enum вредност (STANDARD, CUSTOMS, или UNKNOWN)
    """
    detector = ECDFormatDetector(pdf_path, verbose)
    return detector.detect_format()


def main():
    """Тестирање на детекторот"""
    import sys
    
    if len(sys.argv) < 2:
        print("Употреба: python ecd_format_detector.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print("=" * 60)
    print("🔍 ECD Format Detector")
    print("=" * 60)
    print(f"📄 Документ: {pdf_path}")
    print("=" * 60)
    
    detector = ECDFormatDetector(pdf_path, verbose=True)
    format_type = detector.detect_format()
    
    print("\n" + "=" * 60)
    if format_type == ECDFormat.STANDARD:
        print("✅ Резултат: СТАНДАРДЕН ЕЦД формат")
    elif format_type == ECDFormat.CUSTOMS:
        print("✅ Резултат: ЦАРИНСКИ ЕЦД формат")
    else:
        print("⚠️  Резултат: НЕПОЗНАТ формат")
    print("=" * 60)


if __name__ == "__main__":
    main()
