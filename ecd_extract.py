#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECD PDF Extractor - Универзална скрипта за извлекување на податоци од ЕЦД
Поддршка за различни формати на електронски царински декларации
"""

import sys
import argparse
from extract_ecd_generic import ECDExtractorGeneric


def main():
    parser = argparse.ArgumentParser(
        description='Извлекува податоци од ЕЦД PDF документи во JSON формат'
    )
    parser.add_argument(
        'pdf_file',
        help='Патека до PDF фајлот со ЕЦД'
    )
    parser.add_argument(
        '-o', '--output',
        default='extracted_data.json',
        help='Име на излезниот JSON фајл (default: extracted_data.json)'
    )
    parser.add_argument(
        '-c', '--compare',
        help='Патека до фајл со очекувани податоци за споредба'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Прикажи детални информации'
    )
    
    args = parser.parse_args()
    
    try:
        print("=" * 60)
        print("🚀 ECD PDF Extractor")
        print("=" * 60)
        print(f"📄 Документ: {args.pdf_file}")
        print(f"💾 Излез: {args.output}")
        print("=" * 60)
        
        # Креирај екстрактор
        extractor = ECDExtractorGeneric(args.pdf_file, verbose=args.verbose)
        
        # Извлечи податоци
        data = extractor.extract_all()
        
        # Зачувај во JSON
        extractor.save_to_json(args.output)
        
        # Споредба со очекувани податоци (ако е наведено)
        if args.compare:
            print("\n" + "=" * 60)
            is_correct = extractor.compare_with_expected(args.compare)
            if is_correct:
                print("✅ Податоците се точни!")
            else:
                print("⚠️  Има разлики со очекуваните податоци")
        
        # Прикажи извлечени податоци ако е verbose
        if args.verbose:
            import json
            print("\n" + "=" * 60)
            print("📊 Извлечени податоци:")
            print("=" * 60)
            print(json.dumps(data, ensure_ascii=False, indent=2))
        
        print("\n✅ Успешно завршено!")
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Грешка: Фајлот не е пронајден - {args.pdf_file}")
        return 1
    except Exception as e:
        print(f"❌ Грешка: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
