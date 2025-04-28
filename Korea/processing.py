import xml.etree.ElementTree as ET
from xml.dom import minidom

# 기존 XML 파일 경로 및 저장할 새 파일 경로
input_file  ="osm.rou.xml"
output_file = "osm.rou.xml"

# XML 파싱
tree = ET.parse(input_file)
root = tree.getroot()

# 새로운 파일용 root 생성
combined_root = ET.Element("routes")

# 기존 vehicle 태그를 추출하여 새로운 구조로 변환
for vehicle in root.findall("vehicle"):
    vehicle_id = vehicle.get("id")
    depart = vehicle.get("depart", "000.00")
    depart_lane = vehicle.get("departLane", "best")
    depart_pos = vehicle.get("departPos", "random_free")
    depart_speed = vehicle.get("departSpeed", "max")
    vehicle_type = vehicle.get("type", "rl")

    # route 연결
    route_id = f"{vehicle_id}_route"  # route ID 생성
    route_edges = vehicle.find("route").get("edges")

    # 새로운 route 태그 추가
    route_element = ET.Element("route", id=route_id, edges=route_edges)
    combined_root.append(route_element)

    # 새로운 vehicle 태그 추가
    vehicle_element = ET.Element(
        "vehicle",
        id=vehicle_id,
        type=vehicle_type,
        depart=depart,
        departLane=depart_lane,
        departPos=depart_pos,
        departSpeed=depart_speed,
        route=route_id,
    )
    combined_root.append(vehicle_element)

# XML을 정리된 형태로 출력
def prettify_xml(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="    ")

# 정리된 XML 저장
formatted_xml = prettify_xml(combined_root)
with open(output_file, "w", encoding="utf-8") as f:
    f.write(formatted_xml)

print(f"새로운 파일이 '{output_file}' 이름으로 성공적으로 생성되었습니다!")
