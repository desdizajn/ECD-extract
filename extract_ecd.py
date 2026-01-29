#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECD PDF Extractor - Универзална скрипта за извлекување податоци од ЕЦД
Работи со било кој ЕЦД документ
"""

import sys
import argparse
import json
from extract_ecd_generic import ECDExtractorGeneric


def main():
    parser = argparse.ArgumentParser(
        description='ЕЦД PDF Extractor - Извлекување на податоци од електронски царински декларации',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примери:
  %(prog)s --pdf "ECD341.pdf" --out "output.json"
  %(prog)s --pdf "ECD.pdf" --out "out.json" --verbose
  %(prog)s --pdf "ECD341.pdf" --out "test.json" --compare "expected.json"
        '''
    )
    
    parser.add_argument(
        '--pdf',
        required=True,
        help='Патека до PDF фајлот со ЕЦД'
    )
    parser.add_argument(
        '--out',
        default='extracted_data.json',
        help='Име на излезниот JSON фајл (default: extracted_data.json)'
    )
    parser.add_argument(
        '--compare', '-c',
        help='Патека до фајл со очекувани податоци за споредба (опционално)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Прикажи детални информации'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 ECD PDF Extractor - Generic Version")
    print("=" * 60)
    print(f"📄 Влезен PDF: {args.pdf}")
    print(f"💾 Излезен JSON: {args.out}")
    print("=" * 60)
    
    try:
        extractor = ECDExtractorGeneric(args.pdf, verbose=args.verbose)
        data = extractor.extract_all()
        extractor.save_to_json(args.out)
        
        # Споредба со очекувани податоци (ако е наведено)
        if args.compare:
            print()
            is_correct = extractor.compare_with_expected(args.compare)
            
            if is_correct:
                print("\n" + "=" * 60)
                print("✅ Успешно! Податоците се извлечени точно.")
                print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print("⚠️  Има некои разлики со очекуваните податоци.")
                print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✅ Успешно! Податоците се извлечени.")
            print("=" * 60)
        
        # Прикажи извлечени податоци ако е verbose
        if args.verbose:
            print("\n📊 Извлечени податоци:")
            print("=" * 60)
            print(json.dumps(data, ensure_ascii=False, indent=2))
    
    except FileNotFoundError:
        print(f"\n❌ Грешка: Фајлот '{args.pdf}' не е пронајден!")
        return 1
    except Exception as e:
        print(f"\n❌ Грешка при обработка: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
