import numpy as np
import cvxpy as cp
import matplotlib.pyplot as plt
from collections import deque
import random, math, copy, time
import sys
import bisect


from Event import Event, Event_Transmission, Transmission_queue
import Policy_SRPT, Policy_MinFlow, Policy_Heuristic
from Policy_SWAG import SWAG_slot

# from SWAG_extend import compute_JRT
from ortools.graph.python import min_cost_flow
# num_late = 0

def main():
    print("a")


        

def GEODIS(job_demand, job_duration, job_datasize, capacity, bandwidth):
    # Assign tasks at the same site first
    num_jobs = len(job_duration)
    num_sites = len(job_demand)
    job_transmission = []
    workload_q = [0 for _ in range(num_sites)]
    unit_trans_time = [job_datasize[i] / bandwidth for i in range(num_jobs)]
    col_sum = np.sum(job_demand, axis=0)

    #Find balanced allocation of each job i.e. minimize its JRT based on empty workload
    temp_JRT = np.zeros(num_jobs)
    for i in range(num_jobs):
        workload_copy = copy.deepcopy(workload_q)
        for j in range(num_sites):
            cur_num = job_demand[j][i]
            while cur_num > 0:
                fin_time = sys.maxsize
                fin_dest = -1
                for k in range(num_sites):
                    # Compute the finish time of current task if processed at site k
                    temp_fin = workload_copy[k] + unit_trans_time[i] * bool (k - j) + job_duration[i] / capacity[k]
                    if temp_fin < fin_time:
                        fin_time = temp_fin
                        fin_dest = k
                #Place the task at fin_dest
                workload_copy[fin_dest] += unit_trans_time[i] * bool (fin_dest - j) + job_duration[i] / capacity[fin_dest]
                temp_JRT[i] = np.maximum(temp_JRT[i], workload_copy[fin_dest])
                cur_num -= 1

    GEO_order = temp_JRT.argsort()
    # print(f"JRT: {temp_JRT}")
    # print(f"GEO_order:{GEO_order}")

    #Based on order, minimize make-span job by job
    for i in GEO_order:
        cur_trans = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
        for j in range(num_sites):
            cur_num = job_demand[j][i]
            while cur_num > 0:
                fin_time = sys.maxsize
                fin_dest = -1
                for k in range(num_sites):
                    # Compute the finish time of current task if processed at site k
                    temp_fin = workload_q[k] + unit_trans_time[i] * bool(k - j) + job_duration[i] / capacity[k]
                    if temp_fin < fin_time:
                        fin_time = temp_fin
                        fin_dest = k
                # Place the task at fin_dest
                workload_q[fin_dest] += unit_trans_time[i] * bool(fin_dest - j) + job_duration[i] / capacity[fin_dest]
                if fin_dest != j:
                    cur_trans[j][fin_dest] += 1
                    job_demand[j][i] -= 1
                cur_num -= 1
        job_transmission.append(cur_trans)
    # col_sum_2 = np.sum(job_demand, axis=0)
    # for i in range(num_jobs):
    #     if col_sum[GEO_order[i]] != col_sum_2[GEO_order[i]] + np.sum(job_transmission[i]):
    #         print("error!")
    #         return None
    return list(GEO_order), job_transmission

def GEODIS_2(job_demand, job_duration, job_datasize, capacity, bandwidth):
    # Assign one task at one site, next time change a site until all tasks are assigned.
    num_jobs = len(job_duration)
    num_sites = len(job_demand)
    job_transmission = []
    transmission_cost = [[0 for _ in range(num_sites)] for i in range(num_sites)]
    workload_q = [0 for _ in range(num_sites)]
    unit_trans_time = [job_datasize[i] / bandwidth for i in range(num_jobs)]
    # col_sum = np.sum(job_demand, axis=0)
    transpose_d = [list(col) for col in zip(*job_demand)]
    threshold = 1

    #Find balanced allocation of each job i.e. minimize its JRT based on empty workload
    temp_JRT = np.zeros(num_jobs)
    for i in range(num_jobs):
        workload_copy = copy.deepcopy(workload_q)
        num_assigned = [0 for _ in range(num_sites)]
        count = 0
        # print(transpose_d[i])
        # End condition: tasks of each site are all assigned
        while num_assigned != transpose_d[i]:
            cur_site = (count//threshold) % num_sites
            # print(num_assigned, transpose_d[i])
            if num_assigned[cur_site] < transpose_d[i][cur_site]:
                fin_time = sys.maxsize
                fin_dest = -1
                for k in range(num_sites):
                    # Compute the finish time of current task if processed at site k
                    # print(job_duration[i])
                    temp_fin = workload_copy[k] + unit_trans_time[i] * bool (k - cur_site) + job_duration[i] / capacity[k]
                    if temp_fin < fin_time:
                        fin_time = temp_fin
                        fin_dest = k
                #Place the task at fin_dest
                workload_copy[fin_dest] += unit_trans_time[i] * bool (fin_dest - cur_site) + job_duration[i] / capacity[fin_dest]
                temp_JRT[i] = np.maximum(temp_JRT[i], workload_copy[fin_dest])
                num_assigned[cur_site] += 1
            count += 1

    # print(f"JRT: {temp_JRT}")
    GEO_order = temp_JRT.argsort()
    # print(f"GEO_order:{GEO_order}")
    # order_2 = GEO_order.argsort()
    # print(f"order_2:{order_2}")

    #Based on order, minimize make-span job by job
    for i in GEO_order:
        cur_trans = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
        num_assigned = [0 for _ in range(num_sites)]
        count = 0
        # End condition: tasks of each site are all assigned
        while num_assigned != transpose_d[i]:
            cur_site = (count//threshold) % num_sites
            # print(transpose_d[i][cur_site])
            if num_assigned[cur_site] < transpose_d[i][cur_site]:
                fin_time = sys.maxsize
                fin_dest = -1
                for k in range(num_sites):
                    # Compute the finish time of current task if processed at site k
                    temp_fin = workload_q[k] + unit_trans_time[i] * bool(k - cur_site) + job_duration[i] / capacity[
                        k]
                    if temp_fin < fin_time:
                        fin_time = temp_fin
                        fin_dest = k
                # Place the task at fin_dest
                workload_q[fin_dest] += unit_trans_time[i] * bool(fin_dest - cur_site) + job_duration[i] / capacity[
                    fin_dest]
                # temp_JRT[i] = np.maximum(temp_JRT[i], workload_q[fin_dest])
                num_assigned[cur_site] += 1
                if fin_dest != cur_site:
                    cur_trans[cur_site][fin_dest] += 1
                    job_demand[cur_site][i] -= 1
            count += 1
        job_transmission.append(cur_trans)
    # col_sum_2 = np.sum(job_demand, axis=0)
    # for i in range(num_jobs):
    #     if col_sum[GEO_order[i]] != col_sum_2[GEO_order[i]] + np.sum(job_transmission[i]):
    #         print("error!")
    #         return None
    return list(GEO_order), job_transmission

def GEODIS_cumu(cur_workload, ideal_order, job_demand, job_duration, job_datasize, capacity, bandwidth):
    # Assign one task at one site, next time change a site until all tasks are assigned.
    num_jobs = len(job_duration)
    num_sites = len(job_demand)
    scheduled_length = len(ideal_order)
    job_transmission = []
    transmission_cost = [[0 for _ in range(num_sites)] for i in range(num_sites)]
    # cur_workload = [0 for _ in range(num_sites)]
    unit_trans_time = [job_datasize[i] / bandwidth for i in range(num_jobs)]
    # col_sum = np.sum(job_demand, axis=0)
    transpose_d = [list(col) for col in zip(*job_demand)]
    # change site every threshold times
    threshold = 1

    #Find balanced allocation of each job i.e. minimize its JRT based on empty workload
    temp_JRT = np.zeros(num_jobs)
    for i in range(scheduled_length, num_jobs):
        workload_copy = copy.deepcopy(cur_workload)
        num_assigned = [0 for _ in range(num_sites)]
        count = 0
        # print(transpose_d[i])
        # End condition: tasks of each site are all assigned
        while num_assigned != transpose_d[i]:
            cur_site = (count//threshold) % num_sites
            # print(num_assigned, transpose_d[i])
            if num_assigned[cur_site] < transpose_d[i][cur_site]:
                fin_time = sys.maxsize
                fin_dest = -1
                for k in range(num_sites):
                    # Compute the finish time of current task if processed at site k
                    # print(job_duration[i])
                    temp_fin = workload_copy[k] + unit_trans_time[i] * bool (k - cur_site) + job_duration[i] / capacity[k]
                    if temp_fin < fin_time:
                        fin_time = temp_fin
                        fin_dest = k
                #Place the task at fin_dest
                workload_copy[fin_dest] += unit_trans_time[i] * bool (fin_dest - cur_site) + job_duration[i] / capacity[fin_dest]
                temp_JRT[i] = np.maximum(temp_JRT[i], workload_copy[fin_dest])
                num_assigned[cur_site] += 1
            count += 1

    # print(f"JRT: {temp_JRT}")
    # temp_JRT = temp_JRT[scheduled_length:]
    GEO_order = temp_JRT.argsort()
    GEO_order[:scheduled_length] = ideal_order
    # GEO_order[scheduled_length:] += scheduled_length
    # print(f"GEO_order:{GEO_order}")
    # order_2 = GEO_order.argsort()
    # print(f"order_2:{order_2}")

    #Based on order, minimize make-span job by job
    for i in GEO_order[scheduled_length:]:
        cur_trans = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
        num_assigned = [0 for _ in range(num_sites)]
        count = 0
        # End condition: tasks of each site are all assigned
        while num_assigned != transpose_d[i]:
            cur_site = (count//threshold) % num_sites
            # print(transpose_d[i][cur_site])
            if num_assigned[cur_site] < transpose_d[i][cur_site]:
                fin_time = sys.maxsize
                fin_dest = -1
                for k in range(num_sites):
                    # Compute the finish time of current task if processed at site k
                    temp_fin = cur_workload[k] + unit_trans_time[i] * bool(k - cur_site) + job_duration[i] / capacity[
                        k]
                    if temp_fin < fin_time:
                        fin_time = temp_fin
                        fin_dest = k
                # Place the task at fin_dest
                cur_workload[fin_dest] += unit_trans_time[i] * bool(fin_dest - cur_site) + job_duration[i] / capacity[
                    fin_dest]
                # temp_JRT[i] = np.maximum(temp_JRT[i], workload_q[fin_dest])
                num_assigned[cur_site] += 1
                if fin_dest != cur_site:
                    cur_trans[cur_site][fin_dest] += 1
                    job_demand[cur_site][i] -= 1
            count += 1
        job_transmission.append(cur_trans)

    return list(GEO_order), job_transmission




def transfer_transit(job_order, job_transmission, job_duration, job_datasize, bandwidth, current_time=0):
    num_jobs = len(job_order)
    num_sites = len(job_transmission[0])
    transmission_cost = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
    transmission_list = [Transmission_queue() for _ in range(num_sites)]
    for i in range(num_jobs):
        unit_transit = sys.maxsize
        if bandwidth != 0:
            unit_transit = job_datasize[job_order[i]] / bandwidth
        for j in range(num_sites):
            for k in range(num_sites):
                allocated = 0
                while job_transmission[i][j][k] > allocated:
                    event = Event_Transmission(job_order[i], j, k, transmission_cost[j][k] + current_time, unit_transit,
                                               job_duration[job_order[i]])
                    transmission_list[k].add_event(event)
                    transmission_cost[j][k] += unit_transit
                    allocated += 1
    return transmission_list


def compute_JRT(demand_matrix, job_duration, capacity, order, transmission_queue):
    # Given current demand, duration, order & transmission
    # Compute each job's JRT, return their summation.
    num_sites = len(capacity)
    num_jobs = len(job_duration)
    JRT = [0 for _ in range(num_jobs)]
    temp_demand = copy.deepcopy(demand_matrix)
    temp_transmission = copy.deepcopy(transmission_queue)
    # Record current workload
    slot_workload = [[0 for _ in range(capacity[i])] for i in range(len(capacity))]

    for i in range(num_sites):
        while temp_transmission[i].queue:
            temp_event = temp_transmission[i].pop_event()
            temp_demand[i][temp_event.job_index] += 1

    for j in range(num_jobs):
        for i in range(num_sites):
            # Currently place j-th job's demand on i-th site:
            while temp_demand[i][order[j]] != 0:
                min_workload = min(slot_workload[i])
                slot_index = slot_workload[i].index(min_workload)
                slot_workload[i][slot_index] += job_duration[order[j]]
                JRT[order[j]] = max(JRT[order[j]], slot_workload[i][slot_index])
                temp_demand[i][order[j]] -= 1
    return JRT

def compute_JRT2(demand_matrix, job_duration, capacity, order, transmission_queue):
    # Given current demand, duration, order & transmission
    # Compute each job's JRT, return their summation.
    num_sites = len(capacity)
    num_jobs = len(job_duration)
    JRT = [0 for _ in range(num_jobs)]
    temp_demand = copy.deepcopy(demand_matrix)
    temp_transmission = copy.deepcopy(transmission_queue)
    # Record current workload
    slot_workload = [[0 for _ in range(capacity[i])] for i in range(len(capacity))]

    for i in range(num_sites):
        while temp_transmission[i].queue:
            temp_event = temp_transmission[i].pop_event()
            temp_demand[i][temp_event.job_index] += 1

    for j in range(num_jobs):
        for i in range(num_sites):
            # Currently place j-th job's demand on i-th site:
            while temp_demand[i][order[j]] != 0:
                min_workload = min(slot_workload[i])
                slot_index = slot_workload[i].index(min_workload)
                slot_workload[i][slot_index] += job_duration[order[j]]
                JRT[order[j]] = max(JRT[order[j]], slot_workload[i][slot_index])
                temp_demand[i][order[j]] -= 1

    return JRT


def remove_duplicates(lst):
    return list(dict.fromkeys(lst))


def remove_less_than(lst, value):
    return [x for x in lst if x >= value]


def remove_more_than(lst, value):
    return [x for x in lst if x < value]


def get_column(matrix, col_index):
    return [row[col_index] for row in matrix]


def get_min(matrix):
    temp = sys.maxsize
    row = -1
    col = -1
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            if matrix[i][j] < temp:
                temp = matrix[i][j]
                row, col = i, j
    return row, col

if __name__ == '__main__':
    main()
