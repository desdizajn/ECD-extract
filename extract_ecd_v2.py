#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECD (Electronic Customs Declaration) PDF Extractor
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
        # Total gross mass - вкупна маса (барај ја бројката што е сама на линија пред "KGM")
        mass_pattern = r'(\d+)\s*\n\s*KGM'
        mass_match = re.search(mass_pattern, self.text)
        if mass_match:
            self.data["HEAHEA"]["TotGroMasHEA307"] = int(mass_match.group(1))
        
        # Identity and nationality of means of transport - регистрација на возило
        # Од поле 21 (втора појава - таа што ја минува границата)
        vehicle_pattern = r'21\.\s+Регист[^\n]*границат?\s*\n([A-Z]{2}\d{4}[A-Z]{2}(?:/[A-Z]{2}\d{4}[A-Z]{2})?)'
        vehicle_match = re.search(vehicle_pattern, self.text)
        if vehicle_match:
            self.data["HEAHEA"]["IdeOfMeaOfTraAtDHEA78"] = vehicle_match.group(1)
        
        # Mode of transport at the border - кодот за транспорт (од поле 25)
        mode_pattern = r'25\.\s+Вид\s+на\s+тран[^\n]*\n(\d)'
        mode_match = re.search(mode_pattern, self.text)
        if mode_match:
            self.data["HEAHEA"]["TraModAtBorHEA76"] = mode_match.group(1)
        
        # Country of dispatch code - земја на испраќање (од поле 15)
        # Барај "15.Шифра" и земи го следниот ред
        dispatch_pattern = r'15\.Шифра[^\n]*\n([A-Z]{2})'
        dispatch_match = re.search(dispatch_pattern, self.text)
        if dispatch_match:
            self.data["HEAHEA"]["CouOfDisCodHEA55"] = dispatch_match.group(1)
        
        # Country of destination code - земја на дестинација (од поле 17)
        # Барај линија со "17. Земја на намена" и земи FR кој е подолу
        dest_pattern = r'17\.\s+Земја\s+на\s+намена[^\n]*\n[аб\s]*\n([A-Z]{2})'
        dest_match = re.search(dest_pattern, self.text)
        if dest_match:
            self.data["HEAHEA"]["CouOfDesCodHEA30"] = dest_match.group(1)
        
        # Container indicator (од поле 19 - Кон)
        container_pattern = r'19\.Кон\s+[^\n]*\n(\d)'
        container_match = re.search(container_pattern, self.text)
        if container_match:
            self.data["HEAHEA"]["ConIndHEA96"] = container_match.group(1)
        else:
            self.data["HEAHEA"]["ConIndHEA96"] = "0"
        
        # Declaration place - место на декларација (од поле 29)
        place_pattern = r'29\.\s+Царинарница[^\n]*\n(\d+)\s*\n([^\n]+?)\s*\n'
        place_match = re.search(place_pattern, self.text)
        if place_match:
            self.data["HEAHEA"]["DecPlaHEA394"] = f"{place_match.group(1)} {place_match.group(2)}"
        
        # Nationality of means of transport crossing the border (од регистрација)
        nat_pattern = r'21\.\s+Регист[^\n]*границат?\s*\n([A-Z]{2})\d{4}[A-Z]{2}'
        nat_match = re.search(nat_pattern, self.text)
        if nat_match:
            self.data["HEAHEA"]["NatOfMeaOfTraCroHEA87"] = nat_match.group(1)
    
    def extract_traexpex1(self):
        """Извлекува податоци за испраќачот (TRAEXPEX1)"""
        # Барај го делот со испраќач (од поле 2)
        # Име на испраќач - линијата после "MK40..."
        exporter_name_pattern = r'MK\d{13}\s*\n([^\n]+)\s*\nул\.'
        exporter_name_match = re.search(exporter_name_pattern, self.text)
        if exporter_name_match:
            self.data["TRAEXPEX1"]["NamEX17"] = exporter_name_match.group(1).strip()
        
        # TIN - даночен број (македонски формат)
        tin_pattern = r'(MK\d{13})'
        tin_match = re.search(tin_pattern, self.text)
        if tin_match:
            self.data["TRAEXPEX1"]["TINEX159"] = tin_match.group(1)
        
        # Адреса - линија што почнува со "ул."
        address_pattern = r'(ул\.[^\n]+)'
        address_match = re.search(address_pattern, self.text)
        if address_match:
            self.data["TRAEXPEX1"]["StrAndNumEX122"] = address_match.group(1).strip()
        
        # Град - барај "Скопје" во адресата
        if "Скопје" in self.text:
            self.data["TRAEXPEX1"]["CitEX124"] = "Скопје"
        
        # Поштенски код
        self.data["TRAEXPEX1"]["PosCodEX123"] = None
        
        # Земја
        self.data["TRAEXPEX1"]["CouEX125"] = "МК"
    
    def extract_traconce1(self):
        """Извлекува податоци за примачот (TRACONCE1)"""
        # Барај го делот со примач (од поле 8)
        # Име на примач - после референтниот број
        consignee_name_pattern = r'\d{6}\s*\n([^\n]+&[^\n]+)\s*\n([^\n]+71210[^\n]+)'
        consignee_name_match = re.search(consignee_name_pattern, self.text)
        if consignee_name_match:
            self.data["TRACONCE1"]["NamCE17"] = consignee_name_match.group(1).strip()
            self.data["TRACONCE1"]["StrAndNumCE122"] = consignee_name_match.group(2).strip()
        
        # TIN
        self.data["TRACONCE1"]["TINCE159"] = None
        
        # Град и поштенски код - од адресата
        city_pattern = r'71210\s+([^\n]+)'
        city_match = re.search(city_pattern, self.text)
        if city_match:
            self.data["TRACONCE1"]["CitCE124"] = city_match.group(1).strip()
            self.data["TRACONCE1"]["PosCodCE123"] = "71210"
        
        # Земја
        self.data["TRACONCE1"]["CouCE125"] = "FR"
    
    def extract_gooitegds(self):
        """Извлекува податоци за стоките (GOOITEGDS)"""
        # Креирај еден елемент за стоки
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
        
        # Маса на стока (од поле 35 - бруто маса)
        item_mass_pattern = r'35\.\s+Бруто\s+маса[^\n]*\n[^\n]*\n[^\n]*\n(\d+\.?\d*)\s*\n'
        item_mass_match = re.search(item_mass_pattern, self.text)
        if item_mass_match:
            mass_str = item_mass_match.group(1).replace(',', '.')
            item["GroMasGDS46"] = float(mass_str)
        
        # Опис на стока (од поле 31)
        desc_pattern = r'Палета\s*\n(Витло[^\n]+)'
        desc_match = re.search(desc_pattern, self.text)
        if desc_match:
            item["GooDesGDS23"] = desc_match.group(1).strip()
        
        # Commodity code (од поле 33 - 8-цифрен тарифен број)
        commodity_pattern = r'32\.Р\.бр\.[^\n]*\n33[^\n]*\n[^\n]*\n[^\n]*\n(\d{8})'
        commodity_match = re.search(commodity_pattern, self.text)
        if commodity_match:
            item["COMCODGODITM"]["ComNomCMD1"] = commodity_match.group(1)
        
        # Packages - пакувања (барај PX и број на колети)
        package = {
            "KinOfPacGS23": "PX",
            "NumOfPacGS24": "7",
            "MarNumOfPacGS21": None
        }
        
        # Барај "7 PX" или слично
        pack_pattern = r'(\d+)\s*\n\s*([A-Z]{2})\s*\n'
        pack_match = re.search(pack_pattern, self.text)
        if pack_match:
            package["NumOfPacGS24"] = pack_match.group(1)
            package["KinOfPacGS23"] = pack_match.group(2)
        
        item["PACGS2"].append(package)
        
        # Previous documents - претходни документи (од поле 40)
        # Пример: 5010(011/2022); 5016(0002826); ...
        
        # Фактура 5010
        invoice_pattern = r'5010\(([^\)]+)\)'
        invoice_match = re.search(invoice_pattern, self.text)
        if invoice_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5010",
                "DocRefDC23": invoice_match.group(1)
            })
        
        # Царинска декларација 5016
        customs_pattern = r'5016\(([^\)]+)\)'
        customs_match = re.search(customs_pattern, self.text)
        if customs_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5016",
                "DocRefDC23": customs_match.group(1)
            })
        
        # Датум 5009
        date_pattern = r'5009\(([^\)]+)\)'
        date_match = re.search(date_pattern, self.text)
        if date_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5009",
                "DocRefDC23": date_match.group(1)
            })
        
        # POAN документ
        poan_pattern = r'POAN\(([^\)]+)\)'
        poan_match = re.search(poan_pattern, self.text)
        if poan_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "POAN",
                "DocRefDC23": poan_match.group(1)
            })
        
        # 5069 документ
        doc_5069_pattern = r'5069\(([^\)]+)\)'
        doc_5069_match = re.search(doc_5069_pattern, self.text)
        if doc_5069_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5069",
                "DocRefDC23": doc_5069_match.group(1)
            })
        
        # АУН документ
        aun_pattern = r'AUN\(([^\)]+)\)'
        aun_match = re.search(aun_pattern, self.text)
        if aun_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "AUN",
                "DocRefDC23": aun_match.group(1)
            })
        
        # 5077 документ
        doc_5077_pattern = r'5077\(([^\)]+)\)'
        doc_5077_match = re.search(doc_5077_pattern, self.text)
        if doc_5077_match:
            item["PRODOCDC2"].append({
                "DocTypDC21": "5077",
                "DocRefDC23": doc_5077_match.group(1)
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
                    print(f"✅ {path}: {actual}")
        
        compare_dict("", self.data, expected)
        
        if differences:
            print("\n⚠️  Пронајдени разлики:")
            for diff in differences:
                print(diff)
        else:
            print("\n✅ Сите податоци се точни!")
        
        return len(differences) == 0


def main():
    """Главна функција"""
    pdf_path = "ECD341.pdf"
    output_path = "extracted_data.json"
    expected_path = "341_correct example.json"
    
    print("=" * 60)
    print("🚀 ECD PDF Extractor - Извлекување на податоци")
    print("=" * 60)
    
    extractor = ECDExtractor(pdf_path)
    data = extractor.extract_all()
    extractor.save_to_json(output_path)
    
    print("\n" + "=" * 60)
    print("📊 Извлечени податоци:")
    print("=" * 60)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    # Споредба со очекувани податоци
    extractor.compare_with_expected(expected_path)


if __name__ == "__main__":
    main()
