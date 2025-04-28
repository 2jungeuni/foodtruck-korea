import os
import sys
import csv
import math
import random
import pickle
import pprint
import warnings
from enum import Enum
from typing import List, Dict, Tuple, Union, Set

from traci import TraCIException

from config import cfg
from opt import opt

warnings.filterwarnings("ignore", category=UserWarning)

# Check if SUMO_HOME is set in the environment variables and if so, append SUMO tools to Python path.
# 환경 변수에서 SUMO_HOME이 설정되어 있으면, SUMO 툴을 파이썬 경로에 추가합니다.
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

import traci
import sumolib

# Keep track of all persons and the ones who have been serviced.
# 모든 사람과 이미 서비스를 받은 사람들을 추적합니다.
All = set()
Serviced = set()

# Map each parking area to an index, and vice versa.
# 각 주차장의 엣지 ID를 인덱스와 매핑하고, 그 반대도 매핑합니다.
locations = {'-81016194#21': 0,
             '-81163819#10': 1,
             '-685069351#5': 2,
             '-156599622#4': 3,
             '378886810#3': 4,
             '-378886819#4': 5,
             '-82905028#1': 6}

idx_locations = {0: '-81016194#21',
                 1: '-81163819#10',
                 2: '-685069351#5',
                 3: '-156599622#4',
                 4: '378886810#3',
                 5: '-378886819#4',
                 6: '-82905028#1'}

# Initialize a cost matrix with large default values (1e5).
# 큰 값으로 비용 행렬을 초기화합니다.
cost_matrix = [[1e5 for __ in range(len(locations))] for _ in range(len(locations))]

# Returns the Euclidean distance between two positions (pos1, pos2).
# 두 위치 (pos1, pos2) 사이의 유클리드 거리를 계산하여 반환합니다.
def distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# Gets the maximum simulation tiem from SUMO; defaults to 3,600 if not set.
# SUMO에서 최대 시뮬레이션 시간을 가져오고, 설종되어 있지 않으면 기본값(3,600초)을 사용합니다.
def get_max_time() -> int:
    max_sim_time = traci.simulation.getEndTime()
    return 3600 if max_sim_time == -1 else max_sim_time

# This function executes the simulation loop, handles truck and person intersections,
# and logs data at each timestep or specified interval.
# 이 함수는 시뮬레이션 루프를 실행하며, 트럭과 보행자의 상호 작용을 처리하고,
# 각 시뮬레이션 스텝 또는 지정된 간격에 로그를 기록합니다.
def run(
        end: int = None,
        interval: int = 600,
        time_limit: float = 10,
        verbose: bool = False
):
    # If no end time is provided, get maximum from SUMO or default to 3,600.
    # 종료 시각이 주어지지 않으면, SUMO 설정값 또는 기본값(3,600초)을 사용합니다.
    if end is None:
        end = get_max_time()

    if verbose:
        print("--- Simulation time ---")
        print(f"    end: {end}")
        print(f"    interval: {interval}")

    timestep = traci.simulation.getTime()

    running = True
    log = [["timestep", "vehicle id", "position", "carbon emission", "service rate"]]
    while running:
        traci.simulationStep(timestep)

        # Check each vehicle in the simulation.
        # 시뮬레이션 내 모든 차량을 확인합니다.
        for veh in list(traci.vehicle.getIDList()):
            vtype = traci.vehicle.getTypeID(veh)
            if vtype == "truck":
                if len(All) != 0:
                    log.append([timestep, veh, traci.vehicle.getRoadID(veh), traci.vehicle.getCO2Emission(veh),
                                len(Serviced) / len(All)])

        # Perform logic every 'interval' steps.
        # 시뮬레이션 'interval' 스텝마다 로직을 수행합니다.
        if timestep % interval == 0:
            # Get lists of all vehicles and persons in the simulation.
            # 시뮬레이션 내 모든 차량과 보행자의 ID 리스트를 가져옵니다.
            all_vehicles = list(traci.vehicle.getIDList())
            all_persons = list(traci.person.getIDList())

            # Prepare a list of trucks that are at a parking area.
            # 주차장에 있는 트럭 리스트를 준비합니다.
            all_trucks = []
            for veh in all_vehicles:
                vtype = traci.vehicle.getTypeID(veh)
                vehicle_pos = traci.vehicle.getPosition(veh)

                if vtype == "truck":
                    if traci.vehicle.getRoadID(veh) in locations:
                        for p in all_persons:
                            try:
                                person_pos = traci.person.getPosition(p)
                                dist = distance(person_pos, vehicle_pos)
                                All.add(p)

                                # If within 1,000 meters, consider that person serviced and remove from simulation.
                                # 1,000미터 이내이면, 해당 보행자는 서비스를 받았다고 보고 시뮬레이션에서 제거합니다.
                                if dist <= 1000:
                                    Serviced.add(p)
                                    traci.person.remove(p, reason=0)
                                    all_persons = list(traci.person.getIDList())

                            except TraCIException:
                                continue

                        if len(traci.vehicle.getStops(veh)) == 1:
                            all_trucks.append(veh)

            # If there are still vehicles and persons in the simulation, call the solver to plan routes.
            # 시뮬레이션에 차량과 보행자가 있다면, 솔버를 호출하여 경로를 계획합니다.
            if all_vehicles and all_persons:
                loc_trucks = {}
                for truck in all_trucks:
                    loc_trucks[truck] = locations[traci.vehicle.getRoadID(truck)]

                loc_persons = {}
                for person in all_persons:
                    loc_persons[person] = locations[traci.person.getRoadID(person)]

                # Call the optimization solver with the current data.
                # 현재 데이터를 활용하여 최적화 솔버를 호출합니다.
                result_locations, result_persons, result_travel_distance = opt.solve(all_trucks,
                                                                                     all_persons,
                                                                                     loc_trucks,
                                                                                     loc_persons,
                                                                                     cost_matrix)
                print("--------------- Results ---------------")
                print(result_locations)
                print("---------------------------------------")

                # Assign new stops to each truck based on solver results.
                # 솔버 결과에 따라 각 트럭에 새로운 정류소를 할당합니다.
                for veh, loc in result_locations.items():
                    if loc:
                        # Get current edge of the truck.
                        # 트럭이 현재 엣지(도로)를 가져옵니다.
                        current_edge = traci.vehicle.getRoadID(veh)

                        # Determine the next edge from the results.
                        # 솔버 결과에 따른 다음 엣지를 결정합니다.
                        next_edge = idx_locations[loc]

                        # Find a route between current_edge and next_edge for the truck.
                        # 현재 엣지에서 다음 엣지로의 트럭 경로를 탐색합니다.
                        route = traci.simulation.findRoute(fromEdge=current_edge,
                                                           toEdge=next_edge,
                                                           vType="truck")

                        # Insert a stop at the next location with a 300s duration.
                        # 다음 위치에 300초 동안 정차하는 정류소를 추가합니다.
                        current_stops = traci.vehicle.getStops(veh)
                        traci.vehicle.insertStop(vehID=veh,
                                                 nextStopIndex=len(current_stops),
                                                 edgeID=f"pa-{loc+1}",
                                                 duration=300,
                                                 flags=65)

                    else:
                        # Insert a stop at the next location with a 300s duration.
                        # 다음 위치에 300초 동안 정차하는 정류소를 추가합니다.
                        current_stops = traci.vehicle.getStops(veh)
                        traci.vehicle.insertStop(vehID=veh,
                                                 nextStopIndex=len(current_stops),
                                                 edgeID=f"pa-{locations[traci.vehicle.getRoadID(veh)] + 1}",
                                                 duration=300,
                                                 flags=65)

        # Increase timestep by 1.
        # 시뮬레이션 시간을 1 증가시킵니다.
        timestep += 1
        if timestep >= end:
            running = False

    # Once simulation ends, write the log to a CSV file.
    # 시뮬레이션이 종료되면, 로그를 CSV 파일로 저장합니다.
    with open("log.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(log)

    # Close the SUMO/Traci connection.
    # SUMO / Traci 연결을 종료합니다.
    traci.close()
    sys.stdout.flush()

if __name__ == "__main__":
    # Decide which SUMO binary to use (GUI or CLI).
    # GUI 또는 CLI용 SUMO 바이너리를 결정합니다.
    if cfg.no_gui:
        sumoBinary = sumolib.checkBinary('sumo')
    else:
        sumoBinary = sumolib.checkBinary('sumo-gui')

    # Start SUMO with specified config, no teleport, no collisions.
    # 지정된 설정, 텔레포트 금지, 충돌 비활성화 옵션으로 SUMO를 시작합니다.
    traci.start([sumoBinary,
                 "--no-warnings",
                 "-c", cfg.sumo_config,
                 "--time-to-teleport", "-1",
                 "--max-depart-delay", "-1",
                 "--collision.action", "none"])

    # Build the cost matrix by finding routes between each pair of locations.
    # 각 위치 쌍 간의 경로를 찾고, 그 길이를 이용해 비용 행렬을 설정합니다.
    for f_edge, f_idx in locations.items():
        for t_edge, t_idx in locations.items():
            if f_edge == t_edge:
                cost_matrix[f_idx][t_idx] = 0
            else:
                route = traci.simulation.findRoute(f_edge, t_edge, vType="truck")
                cost_matrix[f_idx][t_idx] = route.length

    # Run the main simulation with parameters from config.
    # 설정값을 사용하여 메인 시뮬레이션 함수를 실행합니다.
    run(
        end=cfg.end,
        interval=cfg.interval,
        time_limit=cfg.time_limit,
        verbose=cfg.verbose
    )