import json
import math
import copy
import random

with open('geolife_3000.json', 'r') as f1:
    eua = json.load(f1)

all_eua = [eua for i in range(4)]


class GA:
    def __init__(self, opt=1):
        self.data = copy.deepcopy(eua)
        self.opt = opt

    def score_1(self, base, valid_service_method):
        def calculate_distance(loc1, loc2):
            return math.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

        best_index = -1
        highest_score = -float('inf')
        for idx, method in enumerate(valid_service_method):
            distance = calculate_distance(base['location'], method['location'])
            if distance <= base['radius']:
                resource_availability = [b - m for b, m in zip(base['resource'], method['resource'])]
                if all(avail >= 0 for avail in resource_availability):
                    score = (base['radius'] - distance) + sum(resource_availability)
                    if score > highest_score:
                        highest_score = score
                        best_index = idx
        return best_index

    def score_2(self, base, valid_service_method):
        def calculate_distance(loc1, loc2):
            return math.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

        def calculate_resource_score(base_resource, method_resource):
            return min(br / mr if mr > 0 else 0 for br, mr in zip(base_resource, method_resource))

        best_score = float('-inf')
        best_index = -1

        for i, method in enumerate(valid_service_method):
            distance = calculate_distance(base['location'], method['location'])
            if distance > base['radius']:
                continue

            resource_score = calculate_resource_score(base['resource'], method['resource'])
            if resource_score <= 0:
                continue

            service_count_score = -len(base['allocated_services'])
            penalty = 1 if method['name'] in base['allocated_services'] else 0

            index_weight = 1 / (1 + method['index_3'])

            score = (1 / (1 + distance)) * resource_score * (1 + service_count_score) * (1 - penalty) * index_weight

            if score > best_score:
                best_score = score
                best_index = i

        return best_index

    def score_3(self, base, valid_service_method):
        def calculate_distance(loc1, loc2):
            return math.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

        def calculate_resource_score(base_resource, method_resource):
            return sum(min(0, br - mr) for br, mr in zip(base_resource, method_resource))

        best_score = float('-inf')
        best_index = -1

        for i, method in enumerate(valid_service_method):
            distance = calculate_distance(base['location'], method['location'])
            resource_score = calculate_resource_score(base['resource'], method['resource'])
            service_count_score = -len(base['allocated_services'])

            # Weighted score calculation
            score = (0.5 * distance) + (0.3 * resource_score) + (0.2 * service_count_score)

            if score > best_score:
                best_score = score
                best_index = i

        return best_index

    def score_4(self, base, valid_service_method):
        def calculate_distance(loc1, loc2):
            return math.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

        def calculate_score(method):
            distance = calculate_distance(base['location'], method['location'])
            resource_score = sum([min(base['resource'][i], method['resource'][i]) for i in range(3)])
            service_score = len(base['allocated_services'])
            return (1 / (distance + 1)) * resource_score * (1 + service_score)

        scores = [calculate_score(method) for method in valid_service_method]
        best_index = scores.index(max(scores))

        return best_index

    def funopt(self, base, valid_bin_indices, opt) -> int:
        # print("opt",opt)
        if opt == 1:
            return self.score_1(base, valid_bin_indices)
        elif opt == 2:
            return self.score_2(base, valid_bin_indices)
        elif opt == 3:
            return self.score_3(base, valid_bin_indices)
        elif opt == 4:
            return self.score_4(base, valid_bin_indices)

    def calculate_distance(self, lon1, lat1, lon2, lat2):
        """
        使用haversine公式计算两点间的距离（单位：千米）

        :param lat1: 第一个点的纬度
        :param lon1: 第一个点的经度
        :param lat2: 第二个点的经度
        :param lon2: 第二个点的纬度
        :return: 两点间的距离（千米）
        """
        R = 6371000  # 地球平均半径，单位：千米
        # print(type(lon1))
        # print(type(lat1))
        # print(type(lon2))
        # print(type(lat2))

        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)

        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)

        a = math.sin(dLat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dLon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c

        return distance

    def check_base_coverage(self, user_location, base_location, base_radius):
        distance = self.calculate_distance(user_location[0], user_location[1], base_location[0], base_location[1])
        return distance <= base_radius

    def get_valid_bin_indices(self, base: dict, services: list, methods: list) -> list:
        """Returns indices of bins in which item can fit."""
        valid_bin_indices = []
        for i in range(len(services)):
            for j in range(len(services[i]['locations'])):
                f = self.check_base_coverage(services[i]['locations'][j], base['location'], base['radius'])
                if (f):
                    # i表示第几个用户，j表示第i个用户的第j个请求
                    valid_bin_indices.append([i, j])  # services[i]["lianlus"][j]表示第i个用户请求的第j个微服务

        lis = []

        for i in valid_bin_indices:
            if services[i[0]]['flags'][i[1]] == True:
                continue
            else:
                if services[i[0]]['lianlus'][i[1]] in base['allocated_services']:
                    services[i[0]]['flags'][i[1]] = True
                    continue
                else:
                    lis.append(i)

        bins = []

        for i in lis:
            name = services[i[0]]['lianlus'][i[1]]

            a = methods[name - 1]

            for j in range(len(a)):
                f = 1
                for k in range(3):
                    if a[j][k] > base['resource'][k]:
                        f = 0
                        break
                if f == 1:
                    bins.append({"name": name,  # 微服务的名字
                                 "index_1": i,  # 对应services中的第i[0]个用户第i[1]个微服务
                                 "location": services[i[0]]["locations"][i[1]],  # 微服务的地理位置
                                 # "index_2":services[i]['index'],  #对应method中的索引
                                 "number": base["category"][name - 1],
                                 "index_3": j,  # 对应method中符合条件的资源的下标
                                 "resource": a[j]  # 所选的资源
                                 })
        return bins

    def online_binpack(self, bases, services, methods, opt):
        for i, base in enumerate(bases):
            while 1:
                valid_bin_indices = self.get_valid_bin_indices(base, services, methods)

                if len(valid_bin_indices) == 0:
                    break

                priorities_index = self.funopt(base, valid_bin_indices, opt)
                # print('length', len(valid_bin_indices))
                # print('index',priorities_index)
                # print('best',valid_bin_indices[priorities_index])
                best_service = valid_bin_indices[priorities_index]

                services[best_service['index_1'][0]]['flags'][best_service['index_1'][1]] = True

                base['allocated_services'].append(best_service['name'])

                for j in range(3):
                    base['resource'][j] -= best_service['resource'][j]

        return

    def fitness(self):
        services = self.data['user_requests']

        success_count = 0
        # print('services:', services)

        all = 0

        for i in services:
            all += len(i['flags'])
            for j in range(len(i['flags'])):
                if i["flags"][j] == True:
                    success_count += 1
        # print("success_count",success_count)
        # print("all",all)
        fitness = success_count / all
        # Score of heuristic function is negative of average number of bins used
        # across instances (as we want to minimize number of bins).

        return fitness

    def total(self):
        methods = self.data['methods']  # 微服务实现方法

        services = self.data['user_requests']

        bases = self.data['base_stations']  # 基站
        self.online_binpack(bases, services, methods, self.opt)


def Crossover(p1, p2):
    id = random.randint(0, len(p1.data["base_stations"]) - 1)
    p1.total()
    p2.total()
    pm = GA(p1.opt)
    print("len_p2", len(p2.data["base_stations"][id]["allocated_services"]))
    pm.data["base_stations"][id]["allocated_services"] = copy.deepcopy(
        p2.data["base_stations"][id]["allocated_services"])
    pn = GA(p2.opt)
    print("len_p1", len(p1.data["base_stations"][id]["allocated_services"]))
    pn.data["base_stations"][id]["allocated_services"] = copy.deepcopy(
        p1.data["base_stations"][id]["allocated_services"])
    return pm, pn


def Mutation(p1):
    id = random.randint(0, len(p1.data["base_stations"]) - 1)
    p1.total()
    if len(p1.data["base_stations"][id]["allocated_services"]) == 0:
        return GA(p1.opt)
    else:
        p3 = GA(p1.opt)
        p3.data["base_stations"][id]["allocated_services"] = copy.deepcopy(
            p1.data["base_stations"][id]["allocated_services"])
        print("length", len(p3.data["base_stations"][id]["allocated_services"]))
        service_id = random.randint(0, len(p3.data["base_stations"][id]["allocated_services"]) - 1)
        p3.data["base_stations"][id]["allocated_services"].remove(
            p3.data["base_stations"][id]["allocated_services"][service_id])
        return p3


def ga(mx_iter=2, uc=0, um=1):
    poplations = [GA(i) for i in range(1, 5)]
    poplation = 0
    lenn = len(poplations)
    iter = 1
    while (iter <= mx_iter):
        new_poplations = []
        j = 0
        for pop1 in poplations:
            poplations_1 = copy.deepcopy(poplations)
            poplations_1.pop(j)
            pop2 = random.choice(poplations_1)
            p1 = random.random()
            if p1 <= uc:
                c1, c2 = Crossover(pop1, pop2)
                new_poplations.append(c1)
                new_poplations.append(c2)
            p2 = random.random()

            if p2 <= um:
                m1 = Mutation(pop1)
                new_poplations.append(m1)
            j += 1
        poplations += new_poplations
        fit = []
        i = 0
        for pop in poplations:
            pop.total()
            fit.append([pop.fitness(), i])
            i += 1
        fit = sorted(fit, key=lambda x: x[0], reverse=True)
        temp = []
        for i in range(lenn):
            temp.append(poplations[fit[i][1]])
        poplations = temp
        poplation = poplations[0]

        iter += 1

    return poplation


# print(ga(30, 0.5, 0.2).fitness())
x = GA()
x.total()
print(x.fitness())

