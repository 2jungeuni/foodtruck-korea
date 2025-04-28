import gurobipy as gp
from gurobipy import GRB

def solve(trucks,
          persons,
          trucks_loc,
          persons_loc,
          dist_matrix):
    trucks_ = range(len(trucks))
    persons_ = range(len(persons))
    locations_ = range(len(dist_matrix))

    # 모델 설정
    model = gp.Model("food_truck")
    model.Params.LogToConsole = False

    # 의사결정변수 정의
    # x[t, l]: 트럭 t가 위치 l에 배치되면 1
    x = model.addVars(trucks_, locations_, vtype=GRB.BINARY, name="x")
    # y[c, t]: 고객 c가 트럭 t를 이용하면 1
    y = model.addVars(persons_, trucks_, vtype=GRB.BINARY, name="y")
    # z[c, t, l]: 트럭 t가 위치 l에 있고, 고객 c가 트럭 t를 이용하면 1 (y[t, l] * y[c, t]의 선형화)
    z = model.addVars(persons_, trucks_, locations_, vtype=GRB.BINARY, name="z")

    # 제약식
    # 1. 트럭 t는 정학히 1개 위치에 배치
    for t in trucks_:
        model.addConstr(gp.quicksum(x[t, l] for l in locations_) == 1)

    # 2. 각 고객 c는 최대 한 대 트럭만 이용
    for c in persons_:
        model.addConstr(gp.quicksum(y[c, t] for t in trucks_) <= 1)

    # 3. 고객 c의 위치를 loc_c라 할 때, y[c, t] <= x[t, loc_c]
    #    트럭 t가 loc_c에 있지 않으면 그 고객 c를 할당할 수 없음
    for c in persons_:
        loc_c = persons_loc[persons[c]]
        for t in trucks_:
            model.addConstr(y[c, t] <= x[t, loc_c])

    # 선형화 제약 (z = x * y)
    for c in persons_:
        for t in trucks_:
            for l in locations_:
                model.addConstr(z[c, t, l] <= x[t, l])
                model.addConstr(z[c, t, l] <= y[c, t])
                model.addConstr(z[c, t, l] >= x[t, l] + y[c, t] - 1)

    # 목적함수
    model.ModelSense = GRB.MAXIMIZE

    # 목표 1: 최대 고객 커버
    # 우선순위가 높은 목표(priority=2)로 설정
    obj1 = gp.quicksum(y[c, t] for c in persons_ for t in trucks_)
    model.setObjectiveN(obj1, index=0, priority=2)

    # 목표 2: 총 이동 거리 최소화
    # 우선순위가 낮은 목표(priority=1)로 설정
    obj2 = gp.quicksum(-1 * dist_matrix[trucks_loc[trucks[t]]][l] * z[c, t, l]
                       for c in persons_ for t in trucks_ for l in locations_)
    model.setObjectiveN(obj2, index=1, priority=1)

    # 최적화 수행
    model.optimize()

    # 결과 출력
    result_locations = {t: None for t in trucks}
    result_persons = {t: [] for t in trucks}
    result_travel_distances = {t: 0 for t in trucks}

    if model.SolCount > 0:
        print("Optimal solution found: ")


        # 고객 할당 결과
        covered_customers = 0
        for c in persons_:
            served_by = [t for t in trucks_ if y[c, t].X > 0.5]
            if len(served_by) > 0:
                covered_customers += 1
                t_ = served_by[0]
                result_persons[trucks[t_]].append(persons[c])
                result_locations[trucks[t_]] = persons_loc[persons[c]]
                print(f"\tCustomer {persons[c]} at location {persons_loc[persons[c]]} served by {trucks[t_]}")

        print(f"Total covered customers: {covered_customers}")

        # 총 이동거리(트럭 위치 l ~ 고객 위치 persons_loc[persons[c]]의 합)
        # z[c, t, l] = 1 이면 dist_matrix[l][persons_loc[c]]를 더해줌
        for t in trucks_:
            total_dist = 0
            for c in persons_:
                for l in locations_:
                    if z[c, t, l].X > 0.5:
                        total_dist += dist_matrix[l][persons_loc[persons[c]]]
            result_travel_distances[trucks[t]] = total_dist

    else:
        print("No feasible solution found")

    return result_locations, result_persons, result_travel_distances