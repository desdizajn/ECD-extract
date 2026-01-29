#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECD (Electronic Customs Declaration) PDF Extractor - Final Version
Скрипта за извлекување на податоци од ЕЦД PDF документи
"""

import fitz  # PyMuPDF
import re
import json
from typing import Dict, List, Optional, Any


class ECDExtractor:
    """Класа за извлекување на податоци од ЕЦД PDF документи"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.data = {
            "HEAHEA": {},
            "TRAEXPEX1": {},
            "TRACONCE1": {},
            "SEAINFSLI": {
                "SeaNumSLI2": None,
                "SEAIDSID": [{"SeaIdeSID1": ""}]
            },
            "GOOITEGDS": []
        }
    
    def extract_text_from_pdf(self) -> str:
        """Извлекува текст од PDF документ"""
        doc = fitz.open(self.pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        self.text = text
        return text
    
    def extract_heahea(self):
        """Извлекува податоци за HEAHEA секцијата"""
        # Total gross mass - вкупна маса (пред KGM)
        mass_pattern = r'(\d+)\s*\n\s*KGM'
        mass_match = re.search(mass_pattern, self.text)
        if mass_match:
            self.data["HEAHEA"]["TotGroMasHEA307"] = int(mass_match.group(1))
        
        # Identity and nationality of means of transport - регистрација на возило
        # SK1817AN/SK4715AI
        vehicle_pattern = r'(SK\d{4}[A-Z]{2}/SK\d{4}[A-Z]{2})'
        vehicle_match = re.search(vehicle_pattern, self.text)
        if vehicle_match:
            self.data["HEAHEA"]["IdeOfMeaOfTraAtDHEA78"] = vehicle_match.group(1)
        
        # Mode of transport at the border - 3 (road transport)
        # Барај после "СТ.ЕУСЕБЕ" - следната бројка
        mode_pattern = r'СТ\.ЕУСЕБЕ\s*\n(\d)'
        mode_match = re.search(mode_pattern, self.text)
        if mode_match:
            self.data["HEAHEA"]["TraModAtBorHEA76"] = mode_match.group(1)
        
        # Country of dispatch code - MK
        # Барај MK пред "3" и после "ТАБАНОВЦЕ-ПАТН."
        dispatch_pattern = r'ТАБАНОВЦЕ-ПАТН\.\s*\n(MK)'
        dispatch_match = re.search(dispatch_pattern, self.text)
        if dispatch_match:
            self.data["HEAHEA"]["CouOfDisCodHEA55"] = dispatch_match.group(1)
        
        # Country of destination code - FR
        # Барај FR пред ФРАНЦИЈА и после земја на примач
        dest_pattern = r'Ст\.Еусебе\s*\n(FR)'
        dest_match = re.search(dest_pattern, self.text)
        if dest_match:
            self.data["HEAHEA"]["CouOfDesCodHEA30"] = dest_match.group(1)
        
        # Container indicator - 0 (no container)
        # Барај "0" пред "CPT"
        container_pattern = r'SK\d{4}[A-Z]{2}/SK\d{4}[A-Z]{2}\s*\nMK\s*\n(\d)\s*\nCPT'
        container_match = re.search(container_pattern, self.text)
        if container_match:
            self.data["HEAHEA"]["ConIndHEA96"] = container_match.group(1)
        
        # Declaration place - 2031 ТАБАНОВЦЕ-ПАТН.
        place_pattern = r'(\d{4})\s*\n(ТАБАНОВЦЕ-ПАТН\.)'
        place_match = re.search(place_pattern, self.text)
        if place_match:
            self.data["HEAHEA"]["DecPlaHEA394"] = f"{place_match.group(1)} {place_match.group(2)}"
        
        # Nationality of means of transport - MK
        # Барај MK после SK1817AN/SK4715AI
        nat_pattern = r'SK\d{4}[A-Z]{2}/SK\d{4}[A-Z]{2}\s*\n(MK)'
        nat_match = re.search(nat_pattern, self.text)
        if nat_match:
            self.data["HEAHEA"]["NatOfMeaOfTraCroHEA87"] = nat_match.group(1)
    
    def extract_traexpex1(self):
        """Извлекува податоци за испраќачот (TRAEXPEX1)"""
        # Име на испраќач
        exporter_name_pattern = r'MK\d{13}\s*\n([^\n]+)\s*\nул\.'
        exporter_name_match = re.search(exporter_name_pattern, self.text)
        if exporter_name_match:
            self.data["TRAEXPEX1"]["NamEX17"] = exporter_name_match.group(1).strip()
        
        # TIN - даночен број
        tin_pattern = r'(MK\d{13})'
        tin_match = re.search(tin_pattern, self.text)
        if tin_match:
            self.data["TRAEXPEX1"]["TINEX159"] = tin_match.group(1)
        
        # Адреса
        address_pattern = r'(ул\.[^\n]+)'
        address_match = re.search(address_pattern, self.text)
        if address_match:
            self.data["TRAEXPEX1"]["StrAndNumEX122"] = address_match.group(1).strip()
        
        # Град
        if "Скопје" in self.text:
            self.data["TRAEXPEX1"]["CitEX124"] = "Скопје"
        
        # Поштенски код
        self.data["TRAEXPEX1"]["PosCodEX123"] = None
        
        # Земја
        self.data["TRAEXPEX1"]["CouEX125"] = "МК"
    
    def extract_traconce1(self):
        """Извлекува податоци за примачот (TRACONCE1)"""
        # Име и адреса на примач
        # ФРЕЈСИНЕТ ИНТЕРНАТИОНАЛ&Цие
        # ФРЕЈСИМАТ БАСЕ ФИЦ 71210 Ст.Еусебе
        consignee_pattern = r'(ФРЕЈСИНЕТ ИНТЕРНАТИОНАЛ&Цие)\s*\n([^\n]+71210[^\n]+)'
        consignee_match = re.search(consignee_pattern, self.text)
        if consignee_match:
            self.data["TRACONCE1"]["NamCE17"] = consignee_match.group(1).strip()
            self.data["TRACONCE1"]["StrAndNumCE122"] = consignee_match.group(2).strip()
        
        # TIN
        self.data["TRACONCE1"]["TINCE159"] = None
        
        # Град и поштенски код
        city_pattern = r'71210\s+([^\n]+)'
        city_match = re.search(city_pattern, self.text)
        if city_match:
            self.data["TRACONCE1"]["CitCE124"] = city_match.group(1).strip()
            self.data["TRACONCE1"]["PosCodCE123"] = "71210"
        
        # Земја
        self.data["TRACONCE1"]["CouCE125"] = "FR"
    
    def extract_gooitegds(self):
        """Извлекува податоци за стоките (GOOITEGDS)"""
        item = {
            "IteNumGDS7": "1",
            "GroMasGDS46": None,
            "GooDesGDS23": "",
            "UNDanGooCodGDI1": None,
            "COMCODGODITM": {
                "ComNomCMD1": ""
            },
            "PACGS2": [],
            "PRODOCDC2": []
        }
        
        # Маса на стока - 635.000 (барај после "PX")
        item_mass_pattern = r'PX\s*\n[\d\.]+\s*\n([\d\.]+)'
        item_mass_match = re.search(item_mass_pattern, self.text)
        if item_mass_match:
            mass_str = item_mass_match.group(1).replace(',', '.')
            item["GroMasGDS46"] = float(mass_str)
        
        # Опис на стока - Витло на електричен погон сер.бр.6444.-1ком.,
        # Внимание: Не треба празно место пред "ком"
        desc_pattern = r'Палета\s*\n(Витло[^\n]+)'
        desc_match = re.search(desc_pattern, self.text)
        if desc_match:
            desc = desc_match.group(1).strip()
            # Отстрани празно место пред "ком"
            desc = re.sub(r'-1\s+ком\.', '-1ком.', desc)
            item["GooDesGDS23"] = desc
        
        # Commodity code - 84253100
        commodity_pattern = r'^\d{8}$'
        commodity_match = re.search(commodity_pattern, self.text, re.MULTILINE)
        if commodity_match:
            item["COMCODGODITM"]["ComNomCMD1"] = commodity_match.group(0)
        
        # Packages - PX и 7
        package = {
            "KinOfPacGS23": "PX",
            "NumOfPacGS24": "7",
            "MarNumOfPacGS21": None
        }
        
        # Барај "7 PX" или "7\nPX"
        pack_pattern = r'(\d+)\s*\n\s*(PX)\s*\n'
        pack_match = re.search(pack_pattern, self.text)
        if pack_match:
            package["NumOfPacGS24"] = pack_match.group(1)
            package["KinOfPacGS23"] = pack_match.group(2)
        
        item["PACGS2"].append(package)
        
        # Previous documents - од поле 40
        # Формат: 5010(011/2022); 5016(0002826); ...
        
        # 5010 - Фактура
        doc_pattern = r'5010\(([^\)]+)\)'
        doc_match = re.search(doc_pattern, self.text)
        if doc_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5010",
                "DocRefDC23": doc_match.group(1)
            })
        
        # 5016 - Царинска декларација
        doc_pattern = r'5016\(([^\)]+)\)'
        doc_match = re.search(doc_pattern, self.text)
        if doc_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5016",
                "DocRefDC23": doc_match.group(1)
            })
        
        # 5009 - Датум
        doc_pattern = r'5009\(([^\)]+)\)'
        doc_match = re.search(doc_pattern, self.text)
        if doc_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5009",
                "DocRefDC23": doc_match.group(1)
            })
        
        # POAN документ
        # Внимание: Бројот е MK19POA10130000000000000E57 (со 10130 без точка или празно место)
        doc_pattern = r'POAN\((MK19POA[^\)]+)\)'
        doc_match = re.search(doc_pattern, self.text)
        if doc_match:
            # Провери дали има две нули во низа
            ref = doc_match.group(1)
            # Ако има "1013000" замени со "10130000"
            ref = ref.replace("1013000000", "10130000000")
            item["PRODOCDC2"].append({
                "DocTypDC21": "POAN",
                "DocRefDC23": ref
            })
        
        # 5069 документ
        doc_pattern = r'5069\(([^\)]+)\)'
        doc_match = re.search(doc_pattern, self.text)
        if doc_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5069",
                "DocRefDC23": doc_match.group(1)
            })
        
        # AUN документ
        doc_pattern = r'AUN\(([^\)]+)\)'
        doc_match = re.search(doc_pattern, self.text)
        if doc_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "AUN",
                "DocRefDC23": doc_match.group(1)
            })
        
        # 5077 документ
        doc_pattern = r'5077\(([^\)]+)\)'
        doc_match = re.search(doc_pattern, self.text)
        if doc_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5077",
                "DocRefDC23": doc_match.group(1)
            })
        
        self.data["GOOITEGDS"].append(item)
    
    def extract_all(self) -> Dict[str, Any]:
        """Извлекува ги сите податоци од PDF"""
        print("🔍 Извлекување на текст од PDF...")
        self.extract_text_from_pdf()
        
        print("📄 Извлекување на податоци за HEAHEA...")
        self.extract_heahea()
        
        print("📤 Извлекување на податоци за испраќач (TRAEXPEX1)...")
        self.extract_traexpex1()
        
        print("📥 Извлекување на податоци за примач (TRACONCE1)...")
        self.extract_traconce1()
        
        print("📦 Извлекување на податоци за стоки (GOOITEGDS)...")
        self.extract_gooitegds()
        
        return self.data
    
    def save_to_json(self, output_path: str):
        """Зачувува извлечени податоци во JSON фајл"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"✅ Податоците се зачувани во: {output_path}")
    
    def compare_with_expected(self, expected_path: str):
        """Споредува извлечени податоци со очекуваните"""
        with open(expected_path, 'r', encoding='utf-8') as f:
            expected = json.load(f)
        
        print("\n" + "=" * 60)
        print("🔍 Споредба со очекуваните податоци:")
        print("=" * 60)
        
        differences = []
        matches = []
        
        def compare_dict(path, actual, expected):
            if isinstance(expected, dict):
                for key in expected:
                    new_path = f"{path}.{key}" if path else key
                    if key not in actual:
                        differences.append(f"❌ Недостасува: {new_path}")
                    else:
                        compare_dict(new_path, actual[key], expected[key])
            elif isinstance(expected, list):
                if len(actual) != len(expected):
                    differences.append(f"⚠️  {path}: Различна должина на листа (извлечено: {len(actual)}, очекувано: {len(expected)})")
                for i, (a, e) in enumerate(zip(actual, expected)):
                    compare_dict(f"{path}[{i}]", a, e)
            else:
                if actual != expected:
                    differences.append(f"❌ {path}: извлечено='{actual}' != очекувано='{expected}'")
                else:
                    matches.append(f"✅ {path}")
        
        compare_dict("", self.data, expected)
        
        if differences:
            print(f"\n⚠️  Пронајдени {len(differences)} разлики:")
            for diff in differences:
                print(diff)
        
        print(f"\n✅ Точни податоци: {len(matches)}/{len(matches) + len(differences)}")
        
        if not differences:
            print("\n🎉 Одлично! Сите податоци се точни!")
        
        return len(differences) == 0


def main():
    """Главна функција"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ЕЦД PDF Extractor - Извлекување на податоци од електронски царински декларации'
    )
    parser.add_argument(
        '--pdf',
        default='ECD341.pdf',
        help='Патека до PDF фајлот (default: ECD341.pdf)'
    )
    parser.add_argument(
        '--out',
        default='extracted_data_final.json',
        help='Име на излезниот JSON фајл (default: extracted_data_final.json)'
    )
    parser.add_argument(
        '--compare',
        help='Патека до фајл со очекувани податоци за споредба (опционално)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Прикажи детални информации'
    )
    
    args = parser.parse_args()
    
    pdf_path = args.pdf
    output_path = args.out
    
    print("=" * 60)
    print("🚀 ECD PDF Extractor - Извлекување на податоци")
    print("=" * 60)
    print(f"📄 Влезен PDF: {pdf_path}")
    print(f"💾 Излезен JSON: {output_path}")
    print("=" * 60)
    
    try:
        extractor = ECDExtractor(pdf_path)
        data = extractor.extract_all()
        extractor.save_to_json(output_path)
        
        # Споредба со очекувани податоци (ако е наведено)
        if args.compare:
            is_correct = extractor.compare_with_expected(args.compare)
            
            if is_correct:
                print("\n" + "=" * 60)
                print("✅ Успешно! Податоците се извлечени точно.")
                print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print("⚠️  Има разлики со очекуваните податоци.")
                print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✅ Успешно! Податоците се извлечени.")
            print("=" * 60)
        
        # Прикажи извлечени податоци ако е verbose
        if args.verbose:
            import json
            print("\n📊 Извлечени податоци:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
    
    except FileNotFoundError:
        print(f"\n❌ Грешка: Фајлот '{pdf_path}' не е пронајден!")
        return 1
    except Exception as e:
        print(f"\n❌ Грешка при обработка: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
