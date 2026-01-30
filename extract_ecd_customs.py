#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECD Customs Format Extractor - Екстрактор за царински формат на ЕЦД
Специјализиран за документи како ECDcarina.pdf
"""

import fitz  # PyMuPDF
import re
from typing import Dict, List, Optional, Any, Tuple
from extract_ecd_generic import ECDExtractorGeneric


class ECDExtractorCustoms(ECDExtractorGeneric):
    """Екстрактор специјализиран за царински формат на ЕЦД"""
    
    def __init__(self, pdf_path: str, verbose: bool = False):
        super().__init__(pdf_path, verbose)
        # Повикај ја родителската __init__ која ја поставува структурата
    
    def find_data_section(self):
        """Наоѓа ја секцијата со вистинските податоци за царински формат"""
        # Во царинскиот формат, податоците почнуваат после РБД
        for i, line in enumerate(self.lines):
            # Барај линија со EXMK или IMMK
            if re.match(r'^(EX|IM)[A-Z]{2}$', line.strip()):
                self.data_start_index = max(0, i - 5)  # Почни малку порано
                if self.verbose:
                    print(f"   Почеток на податоци на линија: {self.data_start_index}")
                return self.data_start_index
            
            # Алтернативно, барај "Consignor/Exporter"
            if 'Consignor/Exporter' in line or 'Consignor / Exporter' in line:
                self.data_start_index = i
                if self.verbose:
                    print(f"   Почеток на податоци на линија: {i} (Consignor маркер)")
                return i
        
        # Ако не го најдовме, земи од линија 10
        self.data_start_index = 10
        return 10
    
    def extract_heahea(self):
        """Извлекува податоци за HEAHEA секцијата (царински формат)"""
        # Total gross mass - барај "Бруто маса" и земи го следниот број
        for i, line in enumerate(self.lines):
            if 'Бруто маса' in line:
                # Следните неколку линии содржат маса
                for j in range(i + 1, min(i + 5, len(self.lines))):
                    mass_line = self.lines[j].strip()
                    # Барај број со можен decimal point
                    mass_match = re.search(r'(\d+\.?\d*)', mass_line)
                    if mass_match:
                        try:
                            self.data["HEAHEA"]["TotGroMasHEA307"] = float(mass_match.group(1))
                            break
                        except ValueError:
                            pass
                break
        
        # Identity of means of transport - барај pattern XX1234YY или XX1234YY/XX1234YY
        vehicle_pattern = r'([A-Z]{2}\d{4}[A-Z]{2}(?:/[A-Z]{2}\d{4}[A-Z]{2})?)'
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 80)):
            line = self.lines[i].strip()
            match = re.search(vehicle_pattern, line)
            if match:
                self.data["HEAHEA"]["IdeOfMeaOfTraAtDHEA78"] = match.group(1)
                # Следната линија или во истата линија може да е националноста
                # Барај во истата линија по возилото
                rest_of_line = line[match.end():].strip()
                country_match = re.match(r'^([A-Z]{2})\s', rest_of_line)
                if country_match:
                    self.data["HEAHEA"]["NatOfMeaOfTraCroHEA87"] = country_match.group(1)
                else:
                    # Или во следната линија
                    next_idx, next_line = self.find_next_nonempty_line(i + 1, 3)
                    if next_line and re.match(r'^[A-Z]{2}$', next_line):
                        self.data["HEAHEA"]["NatOfMeaOfTraCroHEA87"] = next_line
                break
        
        # Mode of transport at the border - барај во контекст на "Вид на" и "на граница"
        for i, line in enumerate(self.lines):
            if 'на граница' in line or 'Вид на' in line:
                # Барај број 1-9 во близина
                for j in range(max(0, i - 2), min(len(self.lines), i + 3)):
                    mode_line = self.lines[j].strip()
                    if mode_line in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                        self.data["HEAHEA"]["TraModAtBorHEA76"] = mode_line
                        break
                if "TraModAtBorHEA76" in self.data["HEAHEA"]:
                    break
        
        # Country of dispatch code - барај MK после "Шифра на земја"
        for i, line in enumerate(self.lines):
            if 'Земја на поаѓање' in line or '15 Шифра на земја' in line:
                # Барај MK во следните линии
                for j in range(i, min(len(self.lines), i + 10)):
                    if 'a MK' in self.lines[j] or self.lines[j].strip() == 'MK':
                        self.data["HEAHEA"]["CouOfDisCodHEA55"] = "MK"
                        break
                if "CouOfDisCodHEA55" in self.data["HEAHEA"]:
                    break
        
        # Country of destination code - барај земја во "17 Земја на намена"
        for i, line in enumerate(self.lines):
            if '17 Земја на намена' in line or 'Земја на намена' in line:
                # Следните линии содржат земја и код
                for j in range(i + 1, min(len(self.lines), i + 5)):
                    dest_line = self.lines[j].strip()
                    # Барај 2-буквен код што не е MK
                    code_match = re.search(r'\b([A-Z]{2})\b', dest_line)
                    if code_match and code_match.group(1) not in ['MK', 'БР', 'УЛ', 'SI']:
                        self.data["HEAHEA"]["CouOfDesCodHEA30"] = code_match.group(1)
                        break
                if "CouOfDesCodHEA30" in self.data["HEAHEA"]:
                    break
        
        # Ако не е најдена преку "17 Земја на намена", барај во примач
        if "CouOfDesCodHEA30" not in self.data["HEAHEA"]:
            # Барај "SI" или друга земја во контекст на примач
            for i, line in enumerate(self.lines):
                if '8 Примач' in line:
                    # Барај земја код во следните 15 линии
                    for j in range(i + 1, min(len(self.lines), i + 15)):
                        country_line = self.lines[j].strip()
                        if re.match(r'^[A-Z]{2}$', country_line) and country_line not in ['MK', 'БР', 'УЛ']:
                            self.data["HEAHEA"]["CouOfDesCodHEA30"] = country_line
                            break
                    break
        
        # Container indicator - барај 0 или 1 во контекст на возило
        for i in range(self.data_start_index, min(len(self.lines), self.data_start_index + 60)):
            line = self.lines[i].strip()
            if line == '0' or line == '1':
                # Провери контекст - дали е блиску до превозно средство или услови на испорака
                prev_context = ' '.join(self.lines[max(0, i-3):i])
                next_context = ' '.join(self.lines[i+1:min(len(self.lines), i+4)])
                
                if ('DAP' in next_context or 'FCA' in next_context or 'CPT' in next_context or
                    'транспорт' in prev_context.lower()):
                    self.data["HEAHEA"]["ConIndHEA96"] = line
                    break
        
        # Declaration place - барај "Излезен царински орган" и земи 4-цифрен код
        for i, line in enumerate(self.lines):
            if 'Излезен царински орган' in line or '29 Излезен' in line:
                # Следната линија содржи код и место
                for j in range(i + 1, min(len(self.lines), i + 5)):
                    place_line = self.lines[j].strip()
                    # Барај 4-цифрен код (може да е со или без MK)
                    place_match = re.search(r'(MK)?(\d{6})', place_line)
                    if place_match:
                        code = place_match.group(2)
                        # Земи го и името ако постои
                        remaining = place_line[place_match.end():].strip()
                        if remaining:
                            self.data["HEAHEA"]["DecPlaHEA394"] = f"{code} {remaining}"
                        else:
                            self.data["HEAHEA"]["DecPlaHEA394"] = code
                        break
                if "DecPlaHEA394" in self.data["HEAHEA"]:
                    break
    
    def extract_traexpex1(self):
        """Извлекува податоци за испраќачот (TRAEXPEX1) - царински формат"""
        # Во царинскиот формат податоците се распоредени така:
        # Линија N: "2 Consignor/Exporter"
        # Линија N+1: Име
        # Линија N+2: Адреса
        # Линија N+3: "Не"
        # Линија N+4: TIN
        
        # Барај "Consignor/Exporter"
        for i, line in enumerate(self.lines):
            if 'Consignor/Exporter' in line or '2 Consignor' in line:
                # Името е на следната линија
                if i + 1 < len(self.lines):
                    name_line = self.lines[i + 1].strip()
                    if name_line and len(name_line) > 3 and name_line != 'Не':
                        self.data["TRAEXPEX1"]["NamEX17"] = name_line
                
                # Адресата е 2 линии после
                if i + 2 < len(self.lines):
                    addr_line = self.lines[i + 2].strip()
                    if addr_line and 'УЛ.' in addr_line.upper() or 'БУЛ.' in addr_line.upper():
                        # Парсирај адреса: "УЛ.ПЕЦО СПИРКОВСКИ БР.8А-3 ПРИЛЕП"
                        self.data["TRAEXPEX1"]["StrAndNumEX122"] = addr_line
                        
                # TIN е 4-5 линии после
                for j in range(i + 3, min(i + 8, len(self.lines))):
                    tin_line = self.lines[j].strip()
                    tin_match = re.search(r'([A-Z]{2}\d{13})', tin_line)
                    if tin_match:
                        self.data["TRAEXPEX1"]["TINEX159"] = tin_match.group(1)
                        break
                
                # Поштенски код - барај 4-5 цифри во следните линии
                for j in range(i + 3, min(i + 10, len(self.lines))):
                    postal_line = self.lines[j].strip()
                    if postal_line.isdigit() and len(postal_line) >= 4 and len(postal_line) <= 5:
                        self.data["TRAEXPEX1"]["PosCodEX123"] = postal_line
                        break
                
                # Град - барај чисто кириличен текст во следните линии
                for j in range(i + 3, min(i + 10, len(self.lines))):
                    city_line = self.lines[j].strip()
                    if (city_line and re.match(r'^[А-ЯA-Z\s]+$', city_line) and 
                        len(city_line) > 2 and len(city_line) < 30 and 
                        city_line != 'MK' and city_line != 'Не'):
                        self.data["TRAEXPEX1"]["CitEX124"] = city_line
                        break
                
                break
        
        # Ако не е најден поштенски код, постави на None
        if "PosCodEX123" not in self.data["TRAEXPEX1"]:
            self.data["TRAEXPEX1"]["PosCodEX123"] = None
        
        # Земја - земи ја од TIN
        if "TINEX159" in self.data["TRAEXPEX1"]:
            tin = self.data["TRAEXPEX1"]["TINEX159"]
            country_code = tin[:2]
            if country_code == "MK":
                self.data["TRAEXPEX1"]["CouEX125"] = "МК"
            else:
                self.data["TRAEXPEX1"]["CouEX125"] = country_code
    
    def extract_traconce1(self):
        """Извлекува податоци за примачот (TRACONCE1) - царински формат"""
        # Примачот е под "8 Примач"
        start_search = 0
        for i, line in enumerate(self.lines):
            if '8 Примач' in line:
                start_search = i
                break
        
        if start_search == 0:
            return
        
        # Име на примач - прва значајна линија после "8 Примач"
        for i in range(start_search + 1, min(len(self.lines), start_search + 10)):
            line = self.lines[i].strip()
            if line and len(line) > 3 and not re.match(r'^\d+$', line):
                # Ова е името
                if '9 Финансово' not in line and 'Не' != line and 'МИКЛОШИЧЕВА' not in line:
                    self.data["TRACONCE1"]["NamCE17"] = line
                    
                    # Адресата е следна значајна линија или линии
                    for j in range(i + 1, min(len(self.lines), i + 10)):
                        addr_line = self.lines[j].strip()
                        if addr_line and len(addr_line) > 5:
                            # Провери дали не е број, код, или "СЛОВЕН"
                            if (not re.match(r'^\d{4,6}$', addr_line) and 
                                not re.match(r'^[A-Z]{2}$', addr_line) and 
                                'СЛОВЕН' not in addr_line):
                                
                                # Провери дали има адресни компоненти
                                if 'УЛИЦА' in addr_line.upper() or 'УЛ.' in addr_line.upper():
                                    # Парсирај адреса: "МИКЛОШИЧЕВА УЛИЦА 1Д ДОМЖАЛЕ 00000"
                                    self.data["TRACONCE1"]["StrAndNumCE122"] = addr_line
                                    
                                    # Извлечи поштенски код (последни 4-6 цифри)
                                    postal_match = re.search(r'\s(\d{4,6})\s*$', addr_line)
                                    if postal_match:
                                        postal_code = postal_match.group(1)
                                        # Само ако не е сè нули
                                        if postal_code != '00000' and postal_code != '0000':
                                            self.data["TRACONCE1"]["PosCodCE123"] = postal_code
                                        else:
                                            self.data["TRACONCE1"]["PosCodCE123"] = None
                                        
                                        # Градот е пред поштенскиот код
                                        city_part = addr_line[:postal_match.start()].strip()
                                        words = city_part.split()
                                        if len(words) > 0:
                                            self.data["TRACONCE1"]["CitCE124"] = words[-1]
                                    else:
                                        # Нема поштенски код, градот може да е на крајот
                                        words = addr_line.split()
                                        if len(words) > 2:
                                            self.data["TRACONCE1"]["CitCE124"] = words[-1]
                                            self.data["TRACONCE1"]["PosCodCE123"] = None
                                    
                                    # Земја е следна линија (2-буквен код)
                                    for k in range(j + 1, min(len(self.lines), j + 5)):
                                        country_line = self.lines[k].strip()
                                        if re.match(r'^[A-Z]{2}$', country_line):
                                            self.data["TRACONCE1"]["CouCE125"] = country_line
                                            break
                                    break
                    break
        
        # TIN - обично None за странски примачи во царински формат
        self.data["TRACONCE1"]["TINCE159"] = None
    
    def extract_gooitegds(self):
        """Извлекува податоци за стоките (GOOITEGDS) - царински формат"""
        # Најди ги сите commodity codes (8-цифрени броеви)
        # Во царинскиот формат, секоја ставка има:
        # - "32 ... 33 Тарифна ознака" или "33 Тарифна" или "Тарифна ознака"
        # - commodity code на следната или истата линија
        
        commodity_positions = []
        search_start = max(self.data_start_index, 30)
        
        i = search_start
        while i < len(self.lines):
            line = self.lines[i].strip()
            combined_line = line
            
            # Комбинирај ја оваа линија со следната за да компензираме за line breaks
            if i + 1 < len(self.lines):
                combined_line = line + " " + self.lines[i + 1].strip()
            
            # Барај "33 Тарифна ознака" или "33 Тарифн" или само "Тарифна ознака"
            if ('33 Тарифн' in combined_line or '33 Тарифна ознака' in combined_line or 
                ('Тарифна ознака' in combined_line and '32' in combined_line)):
                
                # Барај 8-цифрен код на следните неколку линии
                for j in range(i + 1, min(i + 5, len(self.lines))):
                    check_line = self.lines[j].strip()
                    # Барај 8-цифрен код во таа линија
                    code_match = re.search(r'\b(\d{8})\b', check_line)
                    if code_match:
                        commodity_code = code_match.group(1)
                        # Провери дали веќе не го имаме овој код на оваа позиција
                        if not any(abs(pos[0] - j) < 2 and pos[1] == commodity_code for pos in commodity_positions):
                            commodity_positions.append((j, commodity_code))
                            if self.verbose:
                                print(f"      Најдена ставка: {commodity_code} на линија {j}")
                            break
            i += 1
        
        if not commodity_positions:
            # Ако нема commodity codes, креирај празна ставка
            self.data["GOOITEGDS"].append(self._create_empty_item())
            return
        
        if self.verbose:
            print(f"   Вкупно најдени ставки: {len(commodity_positions)}")
        
        # Извлечи ги сите ставки
        for item_num, (commodity_index, commodity_code) in enumerate(commodity_positions, 1):
            item = {
                "IteNumGDS7": str(item_num),
                "GroMasGDS46": None,
                "GooDesGDS23": "",
                "UNDanGooCodGDI1": None,
                "COMCODGODITM": {
                    "ComNomCMD1": commodity_code
                },
                "PACGS2": [],
                "PRODOCDC2": []
            }
            
            # Одреди го опсегот за оваа ставка
            next_commodity_index = commodity_positions[item_num][0] if item_num < len(commodity_positions) else len(self.lines)
            item_start = max(0, commodity_index - 10)
            item_end = min(len(self.lines), next_commodity_index)
            
            # Опис на стока - барај ПРЕД commodity code, обично после пакувањето
            # Описот е директно после пакувањето и пред "Ознаки и броеви"
            desc_found = False
            # Барај наназад од commodity code до "31 Колети"
            for i in range(commodity_index - 1, max(0, commodity_index - 15), -1):
                line = self.lines[i].strip()
                
                # Прескокни "Ознаки и броеви" и "32 Не"
                if ('Ознаки и броеви' in line or line == '32' or line == 'Не' or 
                    line.startswith('33 ') or line.isdigit()):
                    continue
                
                # Прескокни линии со пакување (формати: "Взаемно определено-X-YY" или "Палета-X-YY")
                if (re.search(r'(Взаемно определено|Палета|Картон|Кутија|Сандак)-\d+-[A-Z]{2}', line) or
                    'на стока' in line or 'опис' in line or 'Колети' in line or line.startswith('31 ')):
                    continue
                
                # Барај линија со опис (кирилични букви, подолга од 5 карактери)
                if (line and len(line) >= 5 and 
                    # Провери дали има кирилични букви или латинични букви (за стоки со латинични имиња)
                    (any(ord(c) >= 1040 and ord(c) <= 1103 for c in line) or 
                     any(c.isupper() for c in line)) and
                    # Не е маркер или поле
                    not line.startswith('32 ') and
                    not line.startswith('33 ') and
                    not line.startswith('34 ') and
                    not line.startswith('35 ') and
                    not line.startswith('37 ') and
                    not line.startswith('38 ') and
                    not line.startswith('39 ') and
                    not line.startswith('40 ') and
                    not line.startswith('41 ') and
                    not line.startswith('44 ') and
                    not line.startswith('46 ') and
                    'Бруто маса' not in line and
                    'Нето маса' not in line and
                    'Квота' not in line and
                    'ПОСТАПКА' not in line and
                    # Не е само број или код
                    not re.match(r'^\d+\.?\d*$', line) and
                    not re.match(r'^[A-Z]{2}$', line)):
                    # Ова изгледа како опис
                    item["GooDesGDS23"] = line.rstrip(',').strip()
                    desc_found = True
                    if self.verbose:
                        print(f"      Опис: {item['GooDesGDS23']}")
                    break
            
            # Бруто маса - барај "35 Бруто маса" во опсегот
            for i in range(item_start, item_end):
                if '35 Бруто маса' in self.lines[i]:
                    # Следната линија содржи маса
                    for j in range(i + 1, min(i + 10, item_end)):
                        mass_line = self.lines[j].strip()
                        # Барај број со decimal point
                        mass_match = re.search(r'(\d+\.?\d*)', mass_line)
                        if mass_match:
                            try:
                                mass = float(mass_match.group(1))
                                item["GroMasGDS46"] = mass
                                if self.verbose:
                                    print(f"      Маса: {mass}")
                                break
                            except ValueError:
                                pass
                    break
            
            # Пакување - барај "31 Колети" и type code
            # Поддржани формати:
            # 1. Стар формат: "Взаемно определено-24-ZZ"
            # 2. Нов формат: "Палета-14-PX" или "Картон-5-CT"
            for i in range(item_start, commodity_index + 3):
                line = self.lines[i].strip()
                
                # Стар формат
                if 'Взаемно определено' in line:
                    pack_match = re.search(r'определено-(\d+)-([A-Z]{2})', line)
                    if pack_match:
                        num_packages = pack_match.group(1)
                        pack_type = pack_match.group(2)
                        package = {
                            "KinOfPacGS23": pack_type,
                            "NumOfPacGS24": num_packages,
                            "MarNumOfPacGS21": None
                        }
                        item["PACGS2"].append(package)
                        if self.verbose:
                            print(f"      Пакување: {num_packages} x {pack_type}")
                        break
                
                # Нов формат: "Палета-14-PX", "Картон-5-CT", "Кутија-10-BX", итн.
                pack_match = re.search(r'(Палета|Картон|Кутија|Сандак|Врека|Контејнер)-(\d+)-([A-Z]{2})', line)
                if pack_match:
                    num_packages = pack_match.group(2)
                    pack_type = pack_match.group(3)
                    package = {
                        "KinOfPacGS23": pack_type,
                        "NumOfPacGS24": num_packages,
                        "MarNumOfPacGS21": None
                    }
                    item["PACGS2"].append(package)
                    if self.verbose:
                        print(f"      Пакување: {num_packages} x {pack_type} ({pack_match.group(1)})")
                    break
            
            # Previous documents - барај "44 Дополнителни информации"
            for i in range(commodity_index, min(commodity_index + 15, item_end)):
                line = self.lines[i].strip()
                if '44 Дополнителни' in line:
                    # Следната линија содржи документи
                    if i + 1 < len(self.lines):
                        doc_line = self.lines[i + 1].strip()
                        # Парсирај документи: "AUN-MK19..., POAN-MK26..., 5016-0052639/2026"
                        doc_pattern = r'([A-Z\d]+)-([A-Z\d]+/\d{4})'
                        for match in re.finditer(doc_pattern, doc_line):
                            doc_type = match.group(1)
                            doc_ref = match.group(2)
                            if doc_type in ['AUN', 'POAN', '5016', '5011', 'Y024', '5010', '5069']:
                                item["PRODOCDC2"].append({
                                    "DocTypDC21": doc_type,
                                    "DocRefDC23": doc_ref
                                })
                                if self.verbose:
                                    print(f"      Документ: {doc_type}-{doc_ref}")
                    break
            
            self.data["GOOITEGDS"].append(item)


def main():
    """Тестирање на екстракторот за царински формат"""
    import sys
    import json
    
    pdf_path = "ECDcarina.pdf" if len(sys.argv) < 2 else sys.argv[1]
    output_path = "extracted_customs.json"
    
    print("=" * 60)
    print("🚀 ECD Customs Format Extractor")
    print("=" * 60)
    print(f"📄 Документ: {pdf_path}")
    print("=" * 60)
    
    extractor = ECDExtractorCustoms(pdf_path, verbose=True)
    data = extractor.extract_all()
    extractor.save_to_json(output_path)
    
    print("\n📊 Извлечени податоци:")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
