import numpy as np
import cvxpy as cp
import matplotlib.pyplot as plt
from collections import deque
import random, math, copy, time
import sys
import bisect

import LP_flow
from Event import Event, Event_Transmission, Transmission_queue
from SWAG import SWAG
from SWAG_slot import SWAG_slot

# from SWAG_extend import compute_JRT
import LP
from ortools.graph.python import min_cost_flow
# num_late = 0

def main():
    # print("a")
    num_sites = 10
    num_jobs = 10
    num_round = 100
    # num_late = 0
    job_datasize = [1 for _ in range(num_jobs)]
    capacity = [10 for _ in range(num_sites)]
    bandwidth = 1
    a = [0 for _ in range(8)]
    time_cost = [0 for i in range(6)]
    num_trans = [0 for i in range(6)]

    for i in range(num_round):
        print(f"Round {i}")
        # job_demand = [[8, 5, 1, 3, 5, 1, 2, 7, 1, 7], [4, 1, 2, 5, 8, 6, 8, 9, 7, 5], [6, 8, 10, 9, 3, 4, 2, 6, 1, 8],
        #               [5, 8, 7, 10, 5, 4, 1, 10, 7, 4], [9, 4, 3, 9, 9, 7, 8, 1, 10, 2], [1, 5, 3, 6, 10, 7, 7, 10, 1, 1],
        #               [2, 1, 2, 8, 2, 8, 5, 10, 6, 3], [10, 1, 8, 2, 6, 8, 5, 5, 4, 3], [9, 1, 3, 1, 4, 7, 6, 10, 8, 10],
        #               [7, 4, 9, 3, 10, 5, 6, 1, 10, 2]]
        # job_duration = [1, 1, 5, 4, 4, 1, 5, 2, 3, 2]
        job_demand = [[random.randint(1, 10) for _ in range(num_jobs)] for _ in range(num_sites)]
        job_duration = [random.randint(1, 10) for _ in range(num_jobs)]
        # job_demand = [[2, 5, 8], [10, 1, 6], [9, 10, 2]]
        # job_duration = [2, 2, 7]
        # job_demand = [[61], [99],
        #               [57], [6],
        #               [14], [27],
        #               [12], [39],
        #               [7], [87]]
        # job_duration = [5]

        job_demand2 = copy.deepcopy(job_demand)
        job_demand3 = copy.deepcopy(job_demand)
        job_demand4 = copy.deepcopy(job_demand)
        job_demand5 = copy.deepcopy(job_demand)
        job_demand6 = copy.deepcopy(job_demand)
        # job_demand4 = copy.deepcopy(job_demand)
        demand_summation = [sum(job_demand[i][j] * job_duration[j] for i in range(num_sites)) for j in range(num_jobs)]
        print(job_demand)
        print(job_duration, demand_summation)

        transmission_list = [Transmission_queue() for _ in range(num_sites)]

        SWAG_order = SWAG(job_demand)
        SWAG_JRT = compute_JRT(job_demand, job_duration, capacity, SWAG_order, transmission_list)
        print(f"SWAG: {SWAG_order}, JRT={SWAG_JRT}, sum={sum(SWAG_JRT)}")
        a[0] += sum(SWAG_JRT)

        SWAG_slot_order = SWAG_slot(job_demand, job_duration, capacity)
        SWAG_slot_JRT = compute_JRT(job_demand, job_duration, capacity, SWAG_slot_order, transmission_list)
        print(f"SWAG_slot: {SWAG_slot_order}, JRT={SWAG_slot_JRT}, sum={sum(SWAG_slot_JRT)}")
        a[1] += sum(SWAG_slot_JRT)

        start_time = time.time()
        GEO_order, job_transmission = GEODIS_2(job_demand, job_duration, job_datasize, capacity, bandwidth)
        this_cost = time.time() - start_time
        time_cost[0] += this_cost
        # print(job_transmission)
        transmission_list = transfer_transit(GEO_order, job_transmission, job_duration, job_datasize, bandwidth)
        num_transit = sum(transmission_list[i].length() for i in range(num_sites))
        # print(transmission_list)
        LP_JRT = compute_JRT(job_demand, job_duration, capacity, GEO_order, transmission_list)
        print(f"GEODIS: {list(map(int, GEO_order))}, JRT={LP_JRT}, sum={sum(LP_JRT)}, time cost={this_cost}, transfers={num_transit}")
        a[2] += sum(LP_JRT)

        start_time = time.time()
        GEO_order2, geo_transmission2 = GEODIS_2(job_demand2, job_duration, job_datasize, capacity, bandwidth)
        this_cost = time.time() - start_time
        time_cost[1] += this_cost
        # print(job_transmission)
        transmission_list2 = transfer_transit(GEO_order2, geo_transmission2, job_duration, job_datasize, bandwidth)
        num_transit = sum(transmission_list2[i].length() for i in range(num_sites))
        # print(transmission_list)
        LP_JRT = compute_JRT(job_demand2, job_duration, capacity, GEO_order2, transmission_list2)
        print(
            f"GEODIS2: {list(map(int, GEO_order2))}, JRT={LP_JRT}, sum={sum(LP_JRT)}, time cost={this_cost}, transfers={num_transit}")
        a[3] += sum(LP_JRT)

        # solver2 = "HIGHS"
        slot_workload = [[0] * i for i in capacity]
        start_time = time.time()
        MIP_order, job_transmission3, num_late = LP_flow.max_flow_ortools(job_demand3, job_duration, job_datasize, capacity, bandwidth)
        this_cost = time.time() - start_time
        time_cost[2] += this_cost
        # print(job_transmission)
        transmission_list3 = transfer_transit(MIP_order, job_transmission3, job_duration, job_datasize, bandwidth)
        num_transit = sum(transmission_list3[i].length() for i in range(num_sites))
        # print(transmission_list)
        MIP_JRT = compute_JRT(job_demand3, job_duration, capacity, MIP_order, transmission_list3)
        print(
            f"Max_flow: {list(map(int, MIP_order))}, JRT={MIP_JRT}, sum={sum(MIP_JRT)}, time cost={this_cost}, transfers={num_transit}")
        a[4] += sum(MIP_JRT)
        num_trans[4] += num_transit
        #

        # solver3 = "Cplex"
        # start_time = time.time()
        # LP_order, job_transmission4 = LP2_optimize.SWAG_MIP(job_demand4, job_duration, job_datasize, capacity, bandwidth, "CPLEX")
        # this_cost = time.time() - start_time
        # time_cost[3] += this_cost
        # # print(job_transmission2)
        # transmission_list4 = transfer_transit(LP_order, job_transmission4, job_duration, job_datasize, bandwidth)
        # num_transit = sum(transmission_list4[i].length() for i in range(num_sites))
        # LP_JRT = compute_JRT(job_demand4, job_duration, capacity, LP_order, transmission_list4)
        # print(f"{solver3}_LP: {list(map(int, LP_order))}, JRT={LP_JRT}, sum={sum(LP_JRT)}, time cost={this_cost}, transfers={num_transit}")
        # a[5] += sum(LP_JRT)
        # num_trans[5] += num_transit

        # start_time = time.time()
        # MIP_order, job_transmission5 = SWAG_MIP(job_demand5, job_duration, job_datasize, capacity, bandwidth, True,
        #                                         "GUROBI")
        # this_cost = time.time() - start_time
        # time_cost[4] += this_cost
        # # print(job_transmission)
        # transmission_list5 = transfer_transit(MIP_order, job_transmission5, job_duration, job_datasize, bandwidth)
        # num_transit = sum(transmission_list3[i].length() for i in range(num_sites))
        # # print(transmission_list)
        # MIP_JRT = compute_JRT(job_demand5, job_duration, capacity, MIP_order, transmission_list5)
        # print(
        #     f"GUROBI_MIP: {MIP_order}, JRT={MIP_JRT}, sum={sum(MIP_JRT)}, time cost={this_cost}, transfers={num_transit}")
        # a[6] += sum(MIP_JRT)
        #
        # start_time = time.time()
        # LP_order, job_transmission6 = SWAG_MIP(job_demand6, job_duration, job_datasize, capacity, bandwidth, False,
        #                                        "GUROBI")
        # this_cost = time.time() - start_time
        # time_cost[5] += this_cost
        # # print(job_transmission2)
        # transmission_list6 = transfer_transit(LP_order, job_transmission6, job_duration, job_datasize, bandwidth)
        # num_transit = sum(transmission_list6[i].length() for i in range(num_sites))
        # LP_JRT = compute_JRT(job_demand6, job_duration, capacity, LP_order, transmission_list6)
        # print(f"SCIP_LP: {LP_order}, JRT={LP_JRT}, sum={sum(LP_JRT)}, time cost={this_cost}, transfers={num_transit}")
        # a[7] += sum(LP_JRT)

    print(a)
    print(num_trans)
    # print(num_late)
    # print([a[i] / a[0] for i in range(8)])
    print(F"time_cost:{[time_cost[i] / num_round for i in range(6)]}")

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
