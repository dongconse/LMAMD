import openai
import json
import numpy as np
import time
import pickle
import requests
import re
import math
import copy
from eva import EVA
import random
#"radius" (a floating-point number in meters representing the coverage of the edge server),
def generate_answer(prompt, id):
    url = "https://api.gptgod.online/v1/chat/completions"
    headers = {
        "Authorization": "Bearer your api",#your api
        "Content-Type": "application/json"
    }
    data = {
        #"model": "llama-3.1-8b",
        #"model": "gpt-4o-mini",
        "model" : "gpt-3.5-turbo-16k",
        "messages": prompt,
        "stream": False,
        "temperature": 0.0
    }
    if id == 1:
        data["model"] = "deepseek-v3"
    if id == 2:
          data["model"] = "gemini-pro"
    if id == 3:
          data["model"] = "gpt-4o"
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"error in request: {e}")
        time.sleep(20)
        return generate_answer(prompt, i)
    except (KeyError, IndexError) as e:
        print(f"An error occurred while parsing the response : {e}")
        return None

def construct_message(id, agent_contexts, agents, idx, index_list, fitness_list, agent_number):
    max_performance = 0
    selection_list = []
    for i in range(0, len(fitness_list)):
        selection_list.append([i, fitness_list[i]])
    if len(agents) == 0:
        if id == 2 or id == 3:
            selection_list = optimize_selection(selection_list, 1)
            index = selection_list[0][0] / agent_number#index of round
            index = int(index)
            index2 = selection_list[0][0] % agent_number#index of agent
            context = agent_contexts[index2][2*index+1]["content"]
            print("selected performance:", selection_list[0][1])
            max_performance = selection_list[0][1]
            if id == 2:
             return {"role": "user","content": context + "Please help me create a new function named 'score' that is similar in concept to the provided algorithm but different in form.In addition, pay attention to the records of performance improvement after optimization in the study of history."}, max_performance
            if id == 3:
             return {"role":"user", "content": context + "Please adjust the main algorithm numerical parameters and create a new function named 'score'. In addition, pay attention to the records of performance improvement after optimization in historical research."}, max_performance
    prefix_string = "These are the recent/updated opinions from other agents: "

    if id == 0:
        for i, agent in enumerate(agents):
            agent_response = agent[2*idx-1]["content"]
            response = "\n\n One agent response: ```{}```".format(agent_response)
            prefix_string = prefix_string + response
        selection_list.sort(key=lambda x: x[1], reverse=True)  # 跟最大的比较
        max_performance =selection_list[0][1]
        prefix_string = prefix_string + "\n\n Please help me create a new algorithm that has a totally different form from the given ones and historical context. \n"
    if id == 1:
        selection_list = optimize_selection(selection_list, 3)
        max_performance = selection_list[0][1]
        for i in range(len(selection_list)):
         index = selection_list[i][0] / agent_number
         index = int(index)
         index2 = selection_list[i][0] % agent_number
         agent_response = agent_contexts[index2][2 * index + 1]["content"]
         response = "\n\n One agent response: ```{}```".format(agent_response)
         prefix_string = prefix_string + response
         if selection_list[i][1] > max_performance:
             max_performance = selection_list[i][1]
        prefix_string = prefix_string + "\n\n Please help me create an algorithm that is learned from the high - performance ones among the given algorithms and those in the historical context. \n"
    return {"role": "user", "content": prefix_string} , max_performance

def construct_assistant_message(completion):
    if completion and "choices" in completion and len(completion["choices"]) > 0:
        content = completion["choices"][0]["message"]["content"]
        return {"role": "assistant", "content": content}
    else:
        print("The response data cannot be parsed.")
        return None

def fitness(response):
    pattern = r'```python(.*?)```'
    match = re.search(pattern, response['content'], re.DOTALL)
    api_code = match.group(1).strip()
    return api_code
def optimize_selection(pop, num):
    pop.sort(key=lambda x: x[1], reverse=True)
    rank_max = len(pop) - 1
    ranks = [i for i in range(len(pop))]
    numerators = [rank_max - rank + 1 for rank in ranks]
    denominator = sum(numerators)
    probs = [num / denominator for num in numerators]
    parents = random.choices(pop, weights=probs, k=num)
    return parents

if __name__ == "__main__":
    agents = 4
    rounds = 5
    np.random.seed(0)

    evaluation_round = 10
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
                    if i == 2 or i == 3:
                         agent_contexts_other = []
                    else:
                         agent_contexts_other = agent_contexts[:i] + agent_contexts[i+1:]
                         for j in range(0,len(agent_contexts)):
                             if j != i:
                                 index_list.append(j)
                    message, max_performance = construct_message(i, agent_contexts, agent_contexts_other, round, index_list, fitness_list, agents)
                    agent_context.append(message)

                completion = generate_answer(agent_context, i)
                assistant_message = construct_assistant_message(completion)
                x = EVA()
                api_code = fitness(assistant_message)
                f = x.evaluate(api_code)
                while(f == -1):
                    completion = generate_answer(agent_context, i)
                    assistant_message = construct_assistant_message(completion)
                    api_code = fitness(assistant_message)
                    f = x.evaluate(api_code)
                print('performance: ', f)
                agent_context.append(assistant_message)
                print("response")
                print("///////////////////////////////////////////")
                print(assistant_message)
                print("+++++++++++++++++++++++++++++++++++++++++++")

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
                if round != 0:
                 agent_context[2*round+1]["content"] = agent_context[2*round+1]["content"]+"And its performance is ```{}```.".format(f)+feedback
                fitness_list.append(f)
        performance += max(fitness_list)
    print("mean_performance:", performance / evaluation_round)
