import openai
import json
import numpy as np
import time
import pickle
from tqdm import tqdm
import requests
import re
import math
import copy
openai.api_key = "sk-brIlMSSc9dUu2JED382jmCnWGPDbbuR2eKy04jaY0u5zLkQy"
from ga import GA
import random
#"radius" (a floating - point number in meters representing the coverage of the edge server),
#优化策略M1,M2,M3,M4
M = ["Please help me create a new algorithm that has a totally different form from the given ones. \n",
     "Please help me create a new algorithm that has a totally different form from the given ones but can be motivated from them. \n",
     "Please assist me in creating a new algorithm that has a different form but can be a modified version of the algorithm provided. \n",
     "Please identify the main algorithm parameters and assist me in creating a new algorithm that has a different parameter settings of the score function provided. \n"]
def generate_answer(prompt, id):
    # print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    # print(prompt)
    # print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    url = "https://api.gptgod.online/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-ZG29SkPDJGmJPDAwhDmziRW3oOtp031QiqCT33kQtE314fCF",
        "Content-Type": "application/json"
    }
    data = {
        #"model": "llama-3.1-8b",
        #"model": "gpt-4o-mini",
        "model": "gemini-pro",
        #"model": "deepseek-v3",
        #"model" : "gpt-3.5-turbo-16k",
        "messages": prompt,
        "stream": False,
        "temperature": 0.0
    }

    # if id == 1:
    #      data["model"] = "gpt-4o"
    # if id == 2:
    #      data["model"] = "gpt-3.5-turbo"
    # if id == 3:
    #      data["model"] = "deepseek-v3"
    #     data["model"] = "gpt-3.5-turbo-16k"
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 检查响应状态码
        return response.json()
    except requests.RequestException as e:
        print(f"请求出错: {e}")
        time.sleep(20)
        return generate_answer(prompt, i)
    except (KeyError, IndexError) as e:
        print(f"解析响应出错: {e}")
        return None

def construct_message(id, agent_contexts, agents, idx, index_list, fitness_list, agent_number):
    max_performance = 0
    selection_list = []
    for i in range(0, len(fitness_list)):
        selection_list.append([i, fitness_list[i]])
    if len(agents) == 0:
        #if id ==0:
        #if id ==0 or id ==(agent_number-1):
        if id == 2 or id == 3:
            #selection_list.sort(key=lambda x: x[1], reverse=True)
            selection_list = optimize_selection(selection_list, 1)
            index = selection_list[0][0] / agent_number#来自第几回合
            index = int(index)
            index2 = selection_list[0][0] % agent_number#来自第几个智能体
            context = agent_contexts[index2][2*index+1]["content"]
            print("性能：", selection_list[0][1])
            max_performance = selection_list[0][1]
            #print("context",context)
            if id == 2:
             #return {"role": "user","content": context + "Please assist me in creating a new algorithm that has a different form but can be a modified version of the algorithm provided.In addition, pay attention to the records of performance improvement after optimization in the study of history."}
             return {"role": "user","content": context + "Please help me create a new function named 'score' that is similar in concept to the provided algorithm but different in form.In addition, pay attention to the records of performance improvement after optimization in the study of history."}, max_performance
            #if id == agent_number-1:
            if id == 3:
             return {"role":"user", "content": context + "Please determine the main algorithm numerical parameters and help create a new function named 'score'. The parameter settings of this new function should be different from those of the provided function. In addition, pay attention to the records of performance improvement after optimization in historical research."}, max_performance
             #return {"role": "user","content": context + "Please identify the main algorithm parameters and assist me in creating a new function named 'score' that has a different parameter settings of the score function provided.In addition, pay attention to the records of performance improvement after optimization in the study of history."}, max_performance
        # if id == 0:
        #  for  i  in range(0, len(fitness_list),agent_number):
        #         selection_list.append([i, fitness_list[i]])
        #  list = optimize_selection(selection_list)
        #  #list[0][0]是索引，list[0][1]是performance
        #  index = (list[0][0] / agent_number)#判断是第几轮
        #  index = int(index)
        #  context = agent_contexts[2*index+1]["content"]#取答案
        #  return {"role": "user", "content": context+"Please assist me in creating a new algorithm that has a different form but can be a modified version of the algorithm provided.In addition, pay attention to the records of performance improvement after optimization in the study of history."}
        # if id == agent_number-1:
        #     for i in range(agent_number-1, len(fitness_list), agent_number):
        #         selection_list.append([i, fitness_list[i]])
        #     list = optimize_selection(selection_list)
        #     # list[0][0]是索引，list[0][1]是performance
        #     index = list[0][0] / agent_number  # 判断是第几轮
        #     index = int(index)
        #     context = agent_contexts[2 * index + 1]["content"]  # 取答案
        #     #print("id == 3, context: ", context)
        #     return {"role": "user", "content": context + "Please identify the main algorithm parameters and assist me in creating a new algorithm that has a different parameter settings of the score function provided.In addition, pay attention to the records of performance improvement after optimization in the study of history."}
    prefix_string = "These are the recent/updated opinions from other agents: "

    if id == 0:  # agent B做探索
        for i, agent in enumerate(agents):
            agent_response = agent[2*idx-1]["content"]
            response = "\n\n One agent response: ```{}```".format(agent_response)
            prefix_string = prefix_string + response
        selection_list.sort(key=lambda x: x[1], reverse=True)  # 跟最大的比较
        max_performance =selection_list[0][1]
        #prefix_string = prefix_string + "\n\n Please help me create an algorithm that is learned from the high - performance ones among the given algorithms and those in the historical context. \n"
        prefix_string = prefix_string + "\n\n Please help me create a new algorithm that has a totally different form from the given ones and historical context. \n"
    if id == 1:  # agent C做总结
        selection_list = optimize_selection(selection_list, 3)
        max_performance = selection_list[0][1]
        for i in range(len(selection_list)):
         index = selection_list[i][0] / agent_number  # 来自第几回合
         index = int(index)
         index2 = selection_list[i][0] % agent_number  # 来自第几个智能体
         agent_response = agent_contexts[index2][2 * index + 1]["content"]
         response = "\n\n One agent response: ```{}```".format(agent_response)
         prefix_string = prefix_string + response
         if selection_list[i][1] > max_performance:
             max_performance = selection_list[i][1]
        prefix_string = prefix_string + "\n\n Please help me create an algorithm that is learned from the high - performance ones among the given algorithms and those in the historical context. \n"
    #prefix_string =prefix_string + "\n\n Use these opinions carefully as additional advice, and provide an updated answer? Make sure to state your answer at the end of the response."
    # if id == 1:#agent B做探索
    #  prefix_string = prefix_string + "\n\n Please help me create a new algorithm that has a totally different form from the given ones and historical context. \n"
    # if id == 2:#agent C做总结
    #  #prefix_string = prefix_string + "\n\n Please help me create a new algorithm that has a totally different form from the given ones and historical context but can be motivated from them. \n"
    #  prefix_string = prefix_string + "\n\n Please help me create an algorithm that is learned from the high - performance ones among the given algorithms and those in the historical context. \n"
    return {"role": "user", "content": prefix_string} , max_performance

def construct_assistant_message(completion):
    if completion and "choices" in completion and len(completion["choices"]) > 0:
        content = completion["choices"][0]["message"]["content"]
        return {"role": "assistant", "content": content}
    else:
        print("无法解析响应数据。")
        return None

def fitness(response):
    pattern = r'```python(.*?)```'
    match = re.search(pattern, response['content'], re.DOTALL)
    api_code = match.group(1).strip()
    return api_code

def optimize_selection(pop, num):
    pop.sort(key=lambda x: x[1], reverse=True)
    # sort_list = [pop[0]]
    # #从pop里面选出四个性能最大且不同的算法
    # for i in range(1,len(pop)):
    #     if pop[i][1] != sort_list[-1][1] and len(sort_list)<4:
    #            sort_list.append(pop[i])
    # number = 0
    # print("len pop:",len(pop))
    # print("len",len(sort_list))
    # while len(sort_list)<4:
    #     print("number",number)
    #     print("???: ", len(sort_list)+number)
    #     sort_list.append(pop[len(sort_list)+number])
    #     number = number+1
    ranks = [i for i in range(len(pop))]
    probs = [1 / (rank + 1 + len(pop)) for rank in ranks]
    #parents = random.choices(sort_list, weights = [0.25,0.25,0.25,0.25], k=1)
    parents = random.choices(pop, weights=probs, k=num)
    return parents


if __name__ == "__main__":
    agents = 4
    rounds = 5
    np.random.seed(0)

    evaluation_round = 1#控制实验次数
    scores = []

    performance = 0
    number = 0
    for rd in range(evaluation_round):
        agent_contexts = [[{"role":"user", "content":"""I need you to design a priority function that can determine the priority of a series of requests. The edge server will deploy the requested microservices according to the priority. Each microservice can complete one task, and different microservices may complete the same task. The goal is to satisfy more requests after deploying the microservices.
The function is named "score", with inputs "base" and "valid_requests", and the output is "best_index".
"base" is of dictionary type, containing detailed information about the edge server. The attributes are "location" (a list of two floating - point numbers representing the longitude and latitude of the edge server respectively), "resource" (a list of three numbers representing the amounts of three types of resources available to the edge server), and "allocated_services" (a list of microservice indices representing the microservices already deployed on the edge server).
"valid_requests" is of list type, and its elements are of dictionary type, representing the requests for this edge server. Each request contains the attributes "name" (an integer value representing the index of the task to be completed by the request), "index_1" (a list of two elements representing the index of the user and the index of the request), "location" (of the same type as that of the edge server, representing the geographical location of the request), "index_3" (an integer value representing the index of the microservice), and "resource" (the same as the attribute of the edge server, representing the cost of deploying this microservice).
"best_index" is the index of the element with the highest priority in the "valid_requests" list. First, describe your new algorithm and main steps in one sentence. The description must be inside braces. Next, implement it in Python as a function named "score". Please note that the attributes used in the function "score" must be derived from the parts of the above - mentioned information that you consider useful (either part or all of the above - mentioned information). Do not give additional explanations."""}]for agent in range(agents)]
        content = agent_contexts[0][0]['content']
        question_prompt = content
        fitness_list = []
        for round in range(rounds):
            print("------------------------------------------------------")
            print("round: ", round)
            for i, agent_context in enumerate(agent_contexts):
                max_performance = 0
                index_list = []
                if round != 0:
                    #if i == 0:
                    #if i == 0 or i==(agents-1):#第一个和最后一个agent不接收其他agent的上下文信息
                    if i == 2 or i == 3:
                         # agent_contexts_other = [agent_contexts[i]]
                         # index_list = [i]
                         agent_contexts_other = []
                    else:
                         agent_contexts_other = agent_contexts[:i] + agent_contexts[i+1:]
                         for j in range(0,len(agent_contexts)):
                             if j != i:
                                 index_list.append(j)
                    message, max_performance = construct_message(i, agent_contexts, agent_contexts_other, round, index_list, fitness_list, agents)
                    agent_context.append(message)
                    #print('message',message)

                completion = generate_answer(agent_context, i)
                assistant_message = construct_assistant_message(completion)
                agent_context.append(assistant_message)
                print("response")
                print("///////////////////////////////////////////")
                print(assistant_message)
                print("+++++++++++++++++++++++++++++++++++++++++++")

                x = GA()
                api_code = fitness(assistant_message)
                f = x.evaluate(api_code)
                print('performance: ',f)
                feedback = ""
                if i == 0:
                    if f<=max_performance:
                        feedback = "The performance of the new algorithm you explored is not better than that of the previous ones."
                    else:
                        feedback = "The new algorithm you explored have a higher performance than the best-performing ones in the existing algorithm set."
                if i == 1:
                    if f<=max_performance:
                        feedback = "The algorithm you created do not outperform the algorithms with the highest performance among those you learned. "
                    else:
                        feedback = "The performance of the algorithm you created exceeds that of the algorithms you originally learned."
                if i == 2:
                    if f<=max_performance:
                        feedback = "The algorithm you optimized in form is not better than the original one."
                    else:
                        feedback = "The algorithm you optimized in form has better performance than the original one."
                if i == 3:
                    if f<=max_performance:
                        feedback = "The performance of the algorithm after parameter adjustment is worse than that of the original one."
                    else :
                        feedback = "The performance of the algorithm after parameter adjustment is better than that of the original one."
                #if i != 2:# agent C是做总结性探索，不能告诉他算法的性能，否则会有偏向
                # if round != 0:
                #  agent_context[2*round+1]["content"] = agent_context[2*round+1]["content"]+"And its performance is ```{}```.".format(f)+feedback
                #agent_context.append(dic)
                fitness_list.append(f)
        performance += max(fitness_list)
        # for i in range(len(fitness_list)):
        #         if fitness_list[i] != -1:
        #             performance += fitness_list[i]
        #             number += 1
    print("mean_performance:", performance / evaluation_round)
    #print("mean_performance:", performance / number)

