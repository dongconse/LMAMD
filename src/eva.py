import json
import math
import copy
import random
import types
import sys
import warnings
import re

with open('data//EUA//user_count//eua_200.json', 'r') as f1:
     eua = json.load(f1)

class EVA:
    def __init__(self):
       self.data = copy.deepcopy(eua)
    def reset(self):
       self.data = copy.deepcopy(eua)
    def calculate_distance(self, lon1, lat1, lon2, lat2):
        R = 6371000

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

    def get_valid_requests(self, base: dict, services: list, methods: list) -> list:
        valid_bin_indices = []
        for i in range(len(services)):
            for j in range(len(services[i]['locations'])):
             f = self.check_base_coverage(services[i]['locations'][j], base['location'], base['radius'])
             if(f):
                valid_bin_indices.append([i,j])

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

                    bins.append({"name":name
                                 "index_1":i,
                                 "location":services[i[0]]["locations"][i[1]],
                                 #"index_2":services[i]['index'],
                                 "number": base["category"][name - 1],
                                 "index_3":j,
                                 "resource":a[j]
                                       })
        return bins

    def deployment(self, bases, services, methods, module):
        for i, base in enumerate(bases):
            while 1:
                valid_requests_indices = self.get_valid_requests(base, services, methods)
                if len(valid_requests_indices) == 0:
                    break
                score = getattr(module, 'score')
                 
                priorities_index = score(base, valid_requests_indices)
                 
                best_service = valid_requests_indices[priorities_index]

                services[best_service['index_1'][0]]['flags'][best_service['index_1'][1]] = True

                base['allocated_services'].append(best_service['name'])

                for j in range(3):
                    base['resource'][j] -= best_service['resource'][j]
        return

    def evaluateGreedy(self, module) :
        methods = self.data['methods']
        services = self.data['user_requests']
        bases = self.data['base_stations']
        self.deployment(bases, services, methods, module)
        success_count = 0
        all = 0
        for i in services:
            all += len(i['flags'])
            for j in range(len(i['flags'])):
               if i["flags"][j] == True:
                success_count += 1
        fitness = success_count / all
        return fitness

    def evaluate(self, code_string):
        try:
            # Suppress warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
            # Create a new module object
            LMAMD_module = types.ModuleType("LMAMD_module")
            # Execute the code string in the new module's namespace
            exec(code_string, LMAMD_module.__dict__)
            # Add the module to sys.modules so it can be imported
            sys.modules[LMAMD_module.__name__] = LMAMD_module
            fitness = self.evaluateGreedy(LMAMD_module)
            self.reset()
            return fitness
        except Exception as e:
            print(f"Error: {e}")
            return -1
