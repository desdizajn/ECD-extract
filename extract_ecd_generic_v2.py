#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECD (Electronic Customs Declaration) PDF Extractor - Generic Version
Генеричка скрипта за извлекување на податоци од било кој ЕЦД PDF документ
"""

import fitz  # PyMuPDF
import re
import json
from typing import Dict, List, Optional, Any, Tuple


class ECDExtractorGeneric:
    """Генеричка класа за извлекување на податоци од ЕЦД PDF документи"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.lines = []
        self.data_start_index = -1
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
        self.lines = text.split('\n')
        return text
    
    def find_data_section(self):
        """Наоѓа ја секцијата со вистинските податоци (не шаблонот)"""
        # Барај ја линијата со '341' или друг декларационен код
        # Податоците почнуваат после првата појава на шаблонот
        # Маркер е 'EXMK', 'EX', 'IM' или слично
        for i, line in enumerate(self.lines):
            if re.match(r'^(EX|IM)[A-Z]{2}$', line.strip()):
                self.data_start_index = i
                return i
        
        # Алтернативно, барај 'LRN :' и оди назад
        for i, line in enumerate(self.lines):
            if 'LRN :' in line or 'LRN:' in line:
                # Оди назад околу 60 линии
                self.data_start_index = max(0, i - 60)
                return self.data_start_index
        
        # Ако не го најдовме, земи од линија 80
        self.data_start_index = 80
        return 80
    
    def find_next_nonempty_line(self, start_index: int, max_search: int = 10) -> Tuple[int, str]:
        """Наоѓа ја следната непразна линија"""
        for i in range(start_index, min(len(self.lines), start_index + max_search)):
            line = self.lines[i].strip()
            if line and line not in ['а', 'б', 'в']:  # Игнорирај маркери
                return i, line
        return -1, ""
    
    def get_line_safe(self, index: int) -> str:
        """Враќа линија или празен string ако е надвор од опсег"""
        if 0 <= index < len(self.lines):
            return self.lines[index].strip()
        return ""
    
    def extract_heahea(self):
        """Извлекува податоци за HEAHEA секцијата"""
        # Total gross mass - број пред "KGM"
        for i, line in enumerate(self.lines):
            if line.strip() == 'KGM':
                mass_line = self.get_line_safe(i - 1)
                if mass_line.isdigit():
                    self.data["HEAHEA"]["TotGroMasHEA307"] = int(mass_line)
                break
        
        # Identity of means of transport - барај pattern XX1234YY или XX1234YY/XX1234YY
        vehicle_pattern = r'^([A-Z]{2}\d{4}[A-Z]{2}(?:/[A-Z]{2}\d{4}[A-Z]{2})?)$'
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 50)):
            line = self.lines[i].strip()
            match = re.match(vehicle_pattern, line)
            if match:
                self.data["HEAHEA"]["IdeOfMeaOfTraAtDHEA78"] = match.group(1)
                # Следната линија е обично националноста
                next_idx, next_line = self.find_next_nonempty_line(i + 1, 3)
                if next_line and re.match(r'^[A-Z]{2}$', next_line):
                    self.data["HEAHEA"]["NatOfMeaOfTraCroHEA87"] = next_line
                break
        
        # Mode of transport at the border - барај број помеѓу 1-9 кој е околу возилото
        # Обично е после контејнер индикаторот и пред валутата
        mode_candidates = []
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 50)):
            line = self.lines[i].strip()
            if line in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                # Провери контекст - ако е после земја код и пред валута
                prev_line = self.get_line_safe(i - 1)
                next_line = self.get_line_safe(i + 1)
                if re.match(r'^[A-Z]{2,3}$', prev_line) or 'EUR' in next_line or 'USD' in next_line:
                    mode_candidates.append(line)
        
        # Земи ја најчестата вредност или последната
        if mode_candidates:
            self.data["HEAHEA"]["TraModAtBorHEA76"] = mode_candidates[-1]
        
        # Country of dispatch code - барај MK или друг код во почетокот
        # Обично е после името на земјата
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 50)):
            line = self.lines[i].strip()
            if 'СЕВЕРНА МАКЕДОНИЈА' in line or 'МАКЕДОНИЈА' in line or 'MACEDONIA' in line:
                # Следна линија е обично кодот
                next_idx, next_line = self.find_next_nonempty_line(i + 1, 3)
                if next_line and re.match(r'^[A-Z]{2}$', next_line):
                    self.data["HEAHEA"]["CouOfDisCodHEA55"] = next_line
                    break
            # Или барај директно MK ако е во контекст
            elif line == 'MK' and i > self.data_start_index + 15:
                # Провери дали е во правилен контекст (не е TIN)
                prev_line = self.get_line_safe(i - 1)
                if not prev_line.startswith('MK') and not prev_line.isdigit():
                    if "CouOfDisCodHEA55" not in self.data["HEAHEA"]:
                        self.data["HEAHEA"]["CouOfDisCodHEA55"] = line
        
        # Country of destination code - барај земја и код
        # Обично е во формат: ФРАНЦИЈА / FR или GERMANY / DE
        country_names = ['ФРАНЦИЈА', 'ГЕРМАНИЈА', 'ФРАНЦЕ', 'FRANCE', 'GERMANY', 'ITALIA', 'ИТАЛИЈА']
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 50)):
            line = self.lines[i].strip()
            for country in country_names:
                if country in line:
                    # Барај код во следните неколку линии
                    for j in range(i + 1, min(len(self.lines), i + 5)):
                        code_line = self.lines[j].strip()
                        if re.match(r'^[A-Z]{2}$', code_line) and code_line != 'MK':
                            self.data["HEAHEA"]["CouOfDesCodHEA30"] = code_line
                            break
                    if "CouOfDesCodHEA30" in self.data["HEAHEA"]:
                        break
            if "CouOfDesCodHEA30" in self.data["HEAHEA"]:
                break
        
        # Container indicator - барај 0 или 1 во контекст на возило
        # Обично е помеѓу националноста и условите на испорака (CPT, CIF, FOB...)
        delivery_terms = ['CPT', 'CIF', 'FOB', 'EXW', 'FCA', 'DAP']
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 50)):
            line = self.lines[i].strip()
            if line in ['0', '1']:
                next_idx, next_line = self.find_next_nonempty_line(i + 1, 3)
                if next_line in delivery_terms:
                    self.data["HEAHEA"]["ConIndHEA96"] = line
                    break
        
        # Declaration place - барај 4-цифрен код и име
        # Обично е во формат: 2031 / ТАБАНОВЦЕ-ПАТН. или слично
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 50)):
            line = self.lines[i].strip()
            if re.match(r'^\d{4}$', line):
                next_idx, next_line = self.find_next_nonempty_line(i + 1, 2)
                if next_line and len(next_line) > 3 and not next_line.isdigit():
                    self.data["HEAHEA"]["DecPlaHEA394"] = f"{line} {next_line}"
                    break
    
    def extract_traexpex1(self):
        """Извлекува податоци за испраќачот (TRAEXPEX1)"""
        # TIN - даночен број (MK + 13 цифри или друг формат)
        tin_pattern = r'^([A-Z]{2}\d{13})$'
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 20)):
            line = self.lines[i].strip()
            match = re.match(tin_pattern, line)
            if match:
                self.data["TRAEXPEX1"]["TINEX159"] = match.group(1)
                # Следната линија е обично името
                next_idx, next_line = self.find_next_nonempty_line(i + 1, 2)
                if next_line:
                    self.data["TRAEXPEX1"]["NamEX17"] = next_line
                # Уште следната линија е адресата
                next_idx2, next_line2 = self.find_next_nonempty_line(next_idx + 1, 2)
                if next_line2 and ('ул.' in next_line2 or 'бул.' in next_line2 or 'str.' in next_line2.lower()):
                    self.data["TRAEXPEX1"]["StrAndNumEX122"] = next_line2
                    # Извлечи град од адресата
                    if ',' in next_line2:
                        city = next_line2.split(',')[-1].strip()
                        self.data["TRAEXPEX1"]["CitEX124"] = city
                break
        
        # Поштенски код - обично None за МК
        self.data["TRAEXPEX1"]["PosCodEX123"] = None
        
        # Земја - земи ја од TIN, но користи кирилица за MK
        if "TINEX159" in self.data["TRAEXPEX1"]:
            tin = self.data["TRAEXPEX1"]["TINEX159"]
            country_code = tin[:2]
            if country_code == "MK":
                self.data["TRAEXPEX1"]["CouEX125"] = "МК"  # Кирилица
            else:
                self.data["TRAEXPEX1"]["CouEX125"] = country_code
    
    def extract_traconce1(self):
        """Извлекува податоци за примачот (TRACONCE1)"""
        # Примачот е после референтниот број, но пред застапникот
        # Барај низа: број(5-7 цифри) -> TIN/празно -> ИМЕ -> АДРЕСА -> FR/друга земја
        
        # Алтернативен пристап: барај референтен број и провери дали следната линија е име
        ref_pattern = r'^\d{5,7}$'
        for i in range(self.data_start_index + 5, min(len(self.lines), self.data_start_index + 20)):
            line = self.lines[i].strip()
            if re.match(ref_pattern, line) and not line.startswith('MK'):
                # Прескокни 1-2 линии (може да има TIN или празно)
                search_start = i + 1
                
                # Барај линија со '&' или долго име на компанија
                for j in range(search_start, min(len(self.lines), search_start + 5)):
                    potential_name = self.lines[j].strip()
                    if len(potential_name) > 10 and ('&' in potential_name or 
                                                      potential_name.isupper() or
                                                      any(c in potential_name for c in ['Цие', 'ЦИЕ', 'Ltd', 'GmbH', 'SA', 'SRL'])):
                        self.data["TRACONCE1"]["NamCE17"] = potential_name
                        
                        # Следната линија е адресата (содржи број)
                        addr_idx, addr_line = self.find_next_nonempty_line(j + 1, 3)
                        if addr_line and (re.search(r'\d{5}', addr_line) or len(addr_line) > 15):
                            self.data["TRACONCE1"]["StrAndNumCE122"] = addr_line
                            
                            # Извлечи поштенски код и град
                            postal_match = re.search(r'(\d{5})\s+([А-Яа-яA-Za-z\.\s]+)', addr_line)
                            if postal_match:
                                self.data["TRACONCE1"]["PosCodCE123"] = postal_match.group(1)
                                self.data["TRACONCE1"]["CitCE124"] = postal_match.group(2).strip()
                            
                            # Земјата е следната линија (2-букви код)
                            country_idx, country_line = self.find_next_nonempty_line(addr_idx + 1, 3)
                            if country_line and re.match(r'^[A-Z]{2}$', country_line) and country_line not in ['MK', 'МК']:
                                self.data["TRACONCE1"]["CouCE125"] = country_line
                            
                            break
                if "NamCE17" in self.data["TRACONCE1"]:
                    break
        
        # TIN - обично None за странски примачи
        self.data["TRACONCE1"]["TINCE159"] = None
    
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
        
        # Commodity code - 8-цифрен број (тарифен број)
        for i, line in enumerate(self.lines):
            if re.match(r'^\d{8}$', line.strip()):
                item["COMCODGODITM"]["ComNomCMD1"] = line.strip()
                break
        
        # Опис на стока - барај после "Палета" или пред commodity code
        # Обично е во формат: "Палета\nОпис на стока..."
        for i, line in enumerate(self.lines):
            if 'Палета' in line or 'палета' in line.lower():
                next_idx, desc = self.find_next_nonempty_line(i + 1, 3)
                if desc and len(desc) > 5:
                    # Отстрани празно место пред "ком"
                    desc = re.sub(r'-1\s+ком\.', '-1ком.', desc)
                    item["GooDesGDS23"] = desc
                break
        
        # Ако нема "Палета", барај текст помеѓу commodity code и packages
        if not item["GooDesGDS23"]:
            # Барај текст околу commodity code
            for i, line in enumerate(self.lines):
                if line.strip() == item["COMCODGODITM"]["ComNomCMD1"]:
                    # Барај неколку линии погоре за опис
                    for j in range(max(0, i - 10), i):
                        potential_desc = self.lines[j].strip()
                        if len(potential_desc) > 10 and not potential_desc.isdigit():
                            item["GooDesGDS23"] = potential_desc
                            break
                    break
        
        # Бруто маса - барај број после "PX" или друг вид пакување
        # Структура: 7\nPX\n1.000\n635.000
        package_types = ['PX', 'CT', 'BX', 'PA', 'PK', 'CS', 'CR']
        for i, line in enumerate(self.lines):
            if line.strip() in package_types:
                # Има 2 броја после - прв е количина, втор е маса
                num1_idx, num1 = self.find_next_nonempty_line(i + 1, 3)
                if num1:
                    num2_idx, num2 = self.find_next_nonempty_line(num1_idx + 1, 3)
                    if num2:
                        try:
                            mass = float(num2.replace(',', '.'))
                            item["GroMasGDS46"] = mass
                        except ValueError:
                            pass
                
                # Пакувањето
                num_idx, num_packages = self.find_next_nonempty_line(i - 1, 1, backward=True)
                if num_packages and num_packages.isdigit():
                    package = {
                        "KinOfPacGS23": line.strip(),
                        "NumOfPacGS24": num_packages,
                        "MarNumOfPacGS21": None
                    }
                    item["PACGS2"].append(package)
                break
        
        # Previous documents - барај го pattern TYPE(REF);
        doc_pattern = r'(\w+)\(([^\)]+)\)'
        doc_text = ' '.join(self.lines)
        temp_docs = []
        for match in re.finditer(doc_pattern, doc_text):
            doc_type = match.group(1)
            doc_ref = match.group(2)
            # Филтрирај само валидни типови
            if doc_type in ['5010', '5016', '5009', '5007', 'POAN', '5069', 'AUN', '5077', 'T1']:
                temp_docs.append((doc_type, doc_ref, match.start()))
        
        # Сортирај по позиција и додај само уникатни (без 5007 ако не е во очекуваните)
        temp_docs.sort(key=lambda x: x[2])
        seen = set()
        for doc_type, doc_ref, pos in temp_docs:
            # Прескокни 5007 ако веќе имаме слични документи
            if doc_type == '5007':
                continue
            if (doc_type, doc_ref) not in seen:
                item["PRODOCDC2"].append({
                    "DocTypDC21": doc_type,
                    "DocRefDC23": doc_ref
                })
                seen.add((doc_type, doc_ref))
        
        self.data["GOOITEGDS"].append(item)
    
    def find_next_nonempty_line(self, start_index: int, max_search: int = 10, backward: bool = False) -> Tuple[int, str]:
        """Наоѓа ја следната/претходната непразна линија"""
        if backward:
            for i in range(start_index, max(0, start_index - max_search), -1):
                line = self.lines[i].strip()
                if line and line not in ['а', 'б', 'в', 'г']:
                    return i, line
        else:
            for i in range(start_index, min(len(self.lines), start_index + max_search)):
                line = self.lines[i].strip()
                if line and line not in ['а', 'б', 'в', 'г']:
                    return i, line
        return -1, ""
    
    def extract_all(self) -> Dict[str, Any]:
        """Извлекува ги сите податоци од PDF"""
        print("🔍 Извлекување на текст од PDF...")
        self.extract_text_from_pdf()
        
        print("🔎 Барање на секцијата со податоци...")
        self.find_data_section()
        print(f"   Почеток на податоци на линија: {self.data_start_index}")
        
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
    pdf_path = "ECD341.pdf"
    output_path = "extracted_data_generic.json"
    expected_path = "341_correct example.json"
    
    print("=" * 60)
    print("🚀 ECD PDF Extractor - Generic Version")
    print("=" * 60)
    
    extractor = ECDExtractorGeneric(pdf_path)
    data = extractor.extract_all()
    extractor.save_to_json(output_path)
    
    # Споредба со очекувани податоци
    is_correct = extractor.compare_with_expected(expected_path)
    
    if is_correct:
        print("\n" + "=" * 60)
        print("✅ Успешно! Податоците се извлечени точно.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️  Има некои разлики - може да треба дополнително тунирање.")
        print("=" * 60)
        print("\n📊 Извлечени податоци:")
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
