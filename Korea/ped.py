import xml.etree.ElementTree as ET

# 입력 파일과 출력 파일 이름을 설정합니다.
input_file = "ped.add.xml"       # 기존 XML 파일 이름
output_file = "ped.rou.xml"  # 수정된 XML 파일 이름

# XML 파싱
tree = ET.parse(input_file)
root = tree.getroot()

# 모든 <person> 요소 안의 <personTrip> 요소를 찾아 처리합니다.
for person in root.findall('person'):
    for elem in person:
        if elem.tag == "personTrip":
            # walkFactor 속성이 있으면 제거합니다.
            if "walkFactor" in elem.attrib:
                del elem.attrib["walkFactor"]
            # 태그 이름을 "walk"로 변경합니다.
            elem.tag = "walk"

# 수정된 XML을 출력 파일로 저장 (XML 선언 포함)
tree.write(output_file, encoding="utf-8", xml_declaration=True)

print(f'"{output_file}" 파일로 저장되었습니다.')
