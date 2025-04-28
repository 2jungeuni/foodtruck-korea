import xml.etree.ElementTree as ET

# XML 파일 경로 설정 (원본 파일)
input_file = "osm.ped.add.xml"
# 수정된 XML 파일을 저장할 경로
output_file = "ped.rou.xml"

# XML 파싱
tree = ET.parse(input_file)
root = tree.getroot()

# 모든 <person> 요소에서 "type" 속성 제거
for person in root.findall(".//person"):
    if "type" in person.attrib:
        del person.attrib["type"]

# 변경된 XML을 새 파일에 저장 (XML 선언 포함)
tree.write(output_file, encoding="utf-8", xml_declaration=True)

print(f'"{output_file}" 파일로 저장되었습니다.')

