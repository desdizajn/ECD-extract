#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch ECD Extractor - Обработува повеќе ЕЦД PDF фајлови одеднаш
"""

import os
import sys
import glob
import json
import argparse
from pathlib import Path
from extract_ecd_final import ECDExtractor


def process_directory(input_dir, output_dir, verbose=False):
    """Обработува сите PDF фајлови во директориум"""
    
    # Креирај излезен директориум ако не постои
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Најди ги сите PDF фајлови
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  Нема пронајдени PDF фајлови во {input_dir}")
        return []
    
    print(f"📁 Пронајдени {len(pdf_files)} PDF фајлови")
    print("=" * 60)
    
    results = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_file)
        output_file = os.path.join(output_dir, filename.replace('.pdf', '.json'))
        
        print(f"\n[{i}/{len(pdf_files)}] 📄 {filename}")
        
        try:
            extractor = ECDExtractor(pdf_file)
            data = extractor.extract_all()
            extractor.save_to_json(output_file)
            
            results.append({
                'file': filename,
                'status': 'success',
                'output': output_file
            })
            
            print(f"✅ Успешно: {output_file}")
            
        except Exception as e:
            results.append({
                'file': filename,
                'status': 'error',
                'error': str(e)
            })
            print(f"❌ Грешка: {str(e)}")
            if verbose:
                import traceback
                traceback.print_exc()
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Обработува повеќе ЕЦД PDF документи во JSON формат'
    )
    parser.add_argument(
        'input_dir',
        help='Директориум со PDF фајлови'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='extracted_data',
        help='Директориум за зачувување на JSON фајлови (default: extracted_data)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Прикажи детални информации'
    )
    parser.add_argument(
        '-r', '--report',
        help='Зачувај извештај во JSON фајл'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Batch ECD PDF Extractor")
    print("=" * 60)
    print(f"📂 Влезен директориум: {args.input_dir}")
    print(f"📁 Излезен директориум: {args.output_dir}")
    print("=" * 60)
    
    # Обработи ги фајловите
    results = process_directory(args.input_dir, args.output_dir, args.verbose)
    
    # Прикажи резиме
    print("\n" + "=" * 60)
    print("📊 РЕЗИМЕ")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"✅ Успешни: {success_count}")
    print(f"❌ Грешки: {error_count}")
    print(f"📝 Вкупно: {len(results)}")
    
    if error_count > 0:
        print("\n❌ Фајлови со грешки:")
        for r in results:
            if r['status'] == 'error':
                print(f"  - {r['file']}: {r['error']}")
    
    # Зачувај извештај ако е наведено
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Извештај зачуван во: {args.report}")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
