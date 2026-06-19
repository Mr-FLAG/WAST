import numpy as np
import random,  copy, time
import sys
import bisect

from Event import Event, Event_Transmission, Transmission_queue
from Policy_SWAG import SWAG_slot
from ortools.graph.python import min_cost_flow
# Based on prof's idea, limitation on transmission bandwidth is simplified
# num_late = 0

def main():
    # print("a")
    num_sites = 10
    num_jobs = 10
    num_round = 1000
    # num_late = 0
    job_datasize = [1 for _ in range(num_jobs)]
    capacity = [10 for _ in range(num_sites)]
    bandwidth = 1
    a = [0 for _ in range(8)]
    time_cost = [0 for i in range(6)]
    num_trans = [0 for i in range(6)]

    for i in range(num_round):
        print(f"Round {i}")
        job_demand = [[random.randint(1, 10) for _ in range(num_jobs)] for _ in range(num_sites)]
        job_duration = [random.randint(1, 10) for _ in range(num_jobs)]

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

        SWAG_order = SWAG_slot(job_demand)
        SWAG_JRT = compute_JRT(job_demand, job_duration, capacity, SWAG_order, transmission_list)
        print(f"SWAG: {SWAG_order}, JRT={SWAG_JRT}, sum={sum(SWAG_JRT)}")
        a[0] += sum(SWAG_JRT)

        SWAG_slot_order = SWAG_slot(job_demand, job_duration, capacity)
        SWAG_slot_JRT = compute_JRT(job_demand, job_duration, capacity, SWAG_slot_order, transmission_list)
        print(f"SWAG_slot: {SWAG_slot_order}, JRT={SWAG_slot_JRT}, sum={sum(SWAG_slot_JRT)}")
        a[1] += sum(SWAG_slot_JRT)


    print(a)
    print(num_trans)
    # print(num_late)
    # print([a[i] / a[0] for i in range(8)])
    print(F"time_cost:{[time_cost[i] / num_round for i in range(6)]}")


def max_flow_ortools(job_demand, job_duration, job_datasize, capacity, bandwidth):  #
    num_jobs = len(job_duration)
    num_site = len(job_demand)
    num_late = 0
    job_transmission = []
    placed_jobs = [False for _ in range(num_jobs)]
    max_flow_order = [-1 for _ in range(num_jobs)]
    col_sum = [sum(col) for col in zip(*job_demand)]
    sum_demand = [col_sum[i] * job_duration[i] for i in range(num_jobs)]
    transmission_cost = [[0 for _ in range(num_site)] for i in range(num_site)] #np.zeros((num_site, num_site), dtype=float)
    slot_workload = [[0 for _ in range(capacity[i])] for i in range(num_site)]
    unit_trans_time = [job_datasize[i] / bandwidth for i in range(num_jobs)]

    # demand_order = np.argsort(sum_demand)
    for cur_round in range(num_jobs):
        # Each round, find the best job with its transmission.
        # Transmission add to the queue & cost; Also update the slot_workload
        # print(f"Current round: {cur_round}")
        job_index = -1
        opt_JRT = sys.maxsize
        ideal_JRT = [0 for _ in range(num_jobs)]
        cur_transmission = [[0 for _ in range(num_site)] for _ in range(num_site)]

        # Compute the ideal JRTs of unsettled jobs:
        # Traverse is based on these ideal JRTs
        for i in range(num_jobs):
            if not placed_jobs[i]:
                temp_count = 0
                temp_workload = copy.deepcopy(slot_workload)
                while temp_count < col_sum[i]:
                    j, k = get_min(temp_workload)
                    temp_count += 1
                    temp_workload[j][k] += job_duration[i]
                    ideal_JRT[i] = max(ideal_JRT[i], temp_workload[j][k])
        ideal_JRT_order = np.lexsort((sum_demand, ideal_JRT))  # np.argsort(ideal_JRT, kind='stable')
        # print(ideal_JRT)

        for cur_index in ideal_JRT_order:
            # Try to place cur_index-th job
            if not placed_jobs[cur_index]:
                # Check the optimal case: infinite bandwidth, task can be transferred to any site instantly:
                # If still larger, it can't be the job, move to next one.
                if ideal_JRT[cur_index] >= opt_JRT:
                    continue

                # Job's pending task = 0 (all in execution), set it as highest priority and move to next round.
                if col_sum[cur_index] == 0:
                    job_index = cur_index
                    cur_transmission = [[0 for _ in range(num_site)] for _ in range(num_site)]
                    break

                # Job has only 1 task: search, just search
                if col_sum[cur_index] == 1:
                    source_site = -1
                    dest_site = -1
                    temp_JRT = sys.maxsize
                    for i in range(num_site):
                        if job_demand[i][cur_index] == 1:
                            source_site = i
                            temp_JRT = min(slot_workload[i]) + job_duration[cur_index]
                            break
                    for i in range(num_site):
                        if i != source_site:
                            arrival_time = transmission_cost[source_site][i] + unit_trans_time[cur_index]
                            if arrival_time <= min(slot_workload[i]) and min(slot_workload[i]) + job_duration[
                                cur_index] < temp_JRT:
                                dest_site = i
                                temp_JRT = min(slot_workload[i]) + job_duration[cur_index]
                    if temp_JRT < opt_JRT:
                        job_index = cur_index
                        opt_JRT = temp_JRT
                        cur_transmission = [[0 for _ in range(num_site)] for _ in range(num_site)]
                        if dest_site != -1:
                            cur_transmission[source_site][dest_site] = 1
                        continue

                # JRT_e[i][j]: the local JRT of site i with j tasks assigned.
                # JRT_e[i][0] = 0: no task is executed at the site;
                cur_demand = [row[cur_index] for row in job_demand]
                JRT_e = [[0 for _ in range(cur_demand[i] + 1)] for i in range(num_site)]
                local_JRT = [0 for _ in range(num_site)]
                temp_workload = copy.deepcopy(slot_workload)
                for i in range(num_site):
                    allocated = 0
                    while allocated < cur_demand[i]:
                        allocated += 1
                        min_slot_index = temp_workload[i].index(min(temp_workload[i]))
                        temp_workload[i][min_slot_index] += job_duration[cur_index]
                        local_JRT[i] = max(local_JRT[i], temp_workload[i][min_slot_index])
                        JRT_e[i][allocated] = local_JRT[i]
                cur_JRT = max(local_JRT)

                # Local demand placed, now consider transmission
                # Compute the maximum transmission allowed for each site pair
                # transmission_allowed[i][j] is the maximum transmission allowed from i to j
                # transmission_allowed = np.tile(cur_demand[:, np.newaxis], (1, num_site))
                # transmission_allowed = [[0 for _ in range(num_site)] for _ in range(num_site)]
                # for i in range(num_site):
                #     for j in range(num_site):
                #         transmission_allowed[i][j] = job_demand[i][cur_index]

                # print(transmission_allowed)
                # print(cur_index, transmission_allowed)
                # Compute the JRT add situation, recorded in JRT_half 1
                # max_out = [sum(row) for row in transmission_allowed]
                # print(f"max add:{max_add}")
                # print("Transmission allowed:")
                # JRT_array = [[0] for _ in range(num_site)]
                # max_add = [sum(col) for col in zip(*transmission_allowed)]
                for i in range(num_site):
                    allocated = 0
                    # JRT_array[i][0] = local_JRT[i]
                    while (allocated < col_sum[cur_index] - cur_demand[i] and #max_add[i] col_sum[cur_index]
                           min(temp_workload[i]) + job_duration[cur_index] < min(opt_JRT, cur_JRT)):
                        min_slot_workload = min(temp_workload[i])
                        min_slot_index = temp_workload[i].index(min_slot_workload)
                        temp_workload[i][min_slot_index] += job_duration[cur_index]
                        JRT_e[i].append(temp_workload[i][min_slot_index])
                        allocated += 1

                # Sort the JRT from low to high
                JRT_p = [item for sublist in JRT_e for item in sublist]
                JRT_p = remove_duplicates(JRT_p)
                JRT_p = remove_less_than(JRT_p, ideal_JRT[cur_index]) # max(ideal_JRT[cur_index], min(local_bound))
                JRT_p = remove_more_than(JRT_p, min(opt_JRT, cur_JRT))
                JRT_p.sort()
                if col_sum[cur_index] >= sum(capacity):
                    JRT_p = filter_by_interval(JRT_p, 3)

                # print(JRT_p)
                # original_length = len(JRT_p)
                # JRT_p = keep_max_fractionals(JRT_p)
                # if record_time:
                # print(original_length, len(JRT_p))

                source = num_site * 2
                dest = source + 1
                seq1 = np.arange(num_site)
                start_nodes = np.append(np.repeat(seq1, num_site),
                                        [np.full(num_site, source), np.arange(num_site, num_site * 2)])
                seq2 = np.arange(num_site, num_site * 2)
                end_nodes = np.append(np.tile(seq2, num_site),
                                      [np.arange(0, num_site), np.full(num_site, dest)])
                unit_cost = np.append(np.ones(num_site * num_site, dtype=int), np.zeros(num_site * 2, dtype=int))
                # flat_allowed = np.array(transmission_allowed)  # [item for row in transmission_allowed for item in row]
                flat_allowed = np.repeat(cur_demand, num_site)
                for i in range(num_site):
                    unit_cost[i * num_site + i] = 0
                supplies = np.append(np.zeros(num_site * 2), np.array([col_sum[cur_index], -col_sum[cur_index]]))

                # print(len(start_nodes), len(end_nodes), len(flow_capacity), len(unit_cost), len(supplies))
                # print(start_nodes)
                # print(end_nodes)
                # print(flow_capacity)
                # print(supplies)
                # print(unit_cost)
                temp_transmission = [[0 for _ in range(num_site)] for _ in range(num_site)]
                lower_bound = 0
                upper_bound = len(JRT_p) - 1
                first_computation = True
                # print(cur_index, cur_JRT, JRT_p)

                while lower_bound <= upper_bound:
                    # Setting the JRT bound & Check whether it's possible to reach this JRT
                    cur_bound = (lower_bound + upper_bound) // 2
                    if first_computation:
                        cur_bound = upper_bound
                        first_computation = False
                    target_JRT = JRT_p[cur_bound]

                    # Based on target_JRT,
                    # Update the bound of each x:
                    for i in range(num_site):
                        for j in range(num_site):
                            if i != j:
                                temp_count = (target_JRT - transmission_cost[i][j]) // unit_trans_time[cur_index]
                                flat_allowed[i * num_site + j] = min(cur_demand[i], max(temp_count, 0))

                    flow_capacity = np.append(flat_allowed,
                                          [cur_demand, np.zeros(num_site, dtype=int)])

                    # Update the new upper bound to JRT array:
                    bound_list = [0 for _ in range(num_site)]
                    for i in range(num_site):
                        bound_list[i] = bisect.bisect_right(JRT_e[i], target_JRT) - 1
                    flow_capacity[-num_site:] = bound_list

                    smcf = min_cost_flow.SimpleMinCostFlow()
                    all_arcs = smcf.add_arcs_with_capacity_and_unit_cost(start_nodes, end_nodes,
                                                                         flow_capacity, unit_cost)
                    smcf.set_nodes_supplies(np.arange(0, len(supplies)), supplies)
                    status = smcf.solve()

                    if status != smcf.OPTIMAL:
                        lower_bound = cur_bound + 1
                    else:
                        upper_bound = cur_bound - 1
                        cur_JRT = target_JRT
                        solution_flows = smcf.flows(all_arcs)
                        # print(f"Solution Found:{solution_flows}")
                        temp_index = 0
                        temp_transmission = solution_flows[:num_site ** 2].reshape(num_site, num_site)
                        # for i in range(num_site):
                        #     for j in range(num_site):
                        #         if i != j:
                        #             temp_transmission[i][j] = solution_flows[i * num_site + j]
                        #         else:
                        #             temp_transmission[i][j] = 0
                        # for arc, flow, capacity in zip(all_arcs, solution_flows, flow_capacity):
                        # temp_transmission = x.value

                if cur_JRT < opt_JRT or cur_JRT == opt_JRT and sum_demand[cur_index] < sum_demand[job_index]:
                    # print(f"Find job {cur_index, cur_JRT}s better than {job_index, opt_JRT}s")
                    job_index = cur_index
                    opt_JRT = cur_JRT
                    cur_transmission = temp_transmission
            # print(cur_transmission)
            # Find the job with its transmission
            # Update demand, transmission list & cost matrix

        # print(f"Choose job {job_index}")
        # print(cur_transmission)
        # global num_late
        # num_late += late_arrival(job_demand, job_duration, unit_trans_time, transmission_cost, slot_workload, job_index,
        #                   cur_transmission)
        for i in range(num_site):
            for j in range(num_site):
                temp = 0
                while cur_transmission[i][j] > temp:
                    transmission_cost[i][j] += unit_trans_time[job_index]
                    job_demand[i][job_index] -= 1
                    temp += 1
                    # job_demand[j][job_index] += 1
            allocated = 0
            while allocated < job_demand[i][job_index] + sum(row[i] for row in cur_transmission):
                # Add local demands
                min_slot_index = slot_workload[i].index(min(slot_workload[i]))
                slot_workload[i][min_slot_index] += job_duration[job_index]
                allocated += 1
        # print(f"index:{current_index}")
        # print(cur_transmission)
        job_transmission.append(cur_transmission)
        max_flow_order[cur_round] = job_index
        placed_jobs[job_index] = True
    # print(slot_workload)
    # print(sum(sum(slot_workload[i]) for i in range(num_site)))
    # if record_time:
    #     print(computation_record)
    #     # print(sum_demand)
    #     print(sum(computation_record))
    # print(f"late arrival {num_late}")
    return max_flow_order, job_transmission

def late_arrival(job_demand, job_duration, unit_trans_time, transmission_cost, slot_workload, job_index, current_transmission):
    # Check whether there are late arrivals in the current job.
    num_sites = len(job_demand)
    # num_jobs = len(job_demand[0])
    sum_in = [sum(col) for col in zip(*current_transmission)]
    sum_out = [sum(row) for row in current_transmission]
    temp_trans_cost = copy.deepcopy(transmission_cost)
    copy_transmission = copy.deepcopy(current_transmission)

    for i in range(num_sites):
        if sum_in[i] != 0 and sum_out[i] != 0:
            copy_workload = copy.deepcopy(slot_workload[i])

            # Add existing local demand first
            temp_count = 0
            while job_demand[i][job_index] > sum_out[i] + temp_count:
                min_slot_index = copy_workload.index(min(copy_workload))
                copy_workload[min_slot_index] += job_duration[job_index]
                temp_count += 1

            # Search from all other sites, check if there are in time arrivals
            # Each time found, update transmission cost and slot workload
            earliest_arrival = [temp_trans_cost[j][i] + unit_trans_time[job_index] for j in range(num_sites)]

            while sum_in[i] >= 0:
                min_slot_index = copy_workload.index(min(copy_workload))
                found = False
                for j in range(num_sites):
                    if copy_transmission[j][i] > 0 and earliest_arrival[j] <= copy_workload[min_slot_index]:
                        earliest_arrival[j] += unit_trans_time[job_index]
                        copy_workload[min_slot_index] += job_duration[job_index]
                        sum_in[i] -= 1
                        copy_transmission[j][i] -= 1
                        found = True
                        break
                if not found:
                    return True
    return False


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


def filter_by_interval(A, interval):
    if not A:
        return []

    result = [A[0]]
    last_kept = A[0]

    for i in range(1, len(A)):
        if A[i] - last_kept > interval:
            result.append(A[i])
            last_kept = A[i]

    return result


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

def find_slot(A, x):
    num_slot = len(A)
    cur_idx = -1
    cur_workload = sys.maxsize
    for i in range(num_slot):
        if A[i] >= x:
            if A[i] < cur_workload:
                cur_workload = A[i]
                cur_idx = i
    return cur_idx

def keep_max_fractionals(arr):
    result = {}
    for num in arr:
        int_part = int(num)
        frac_part = num - int_part
        # 如果该整数部分还没有记录，或者当前小数部分更大
        if int_part not in result or frac_part > result[int_part] - int_part:
            result[int_part] = num
    # 按原数组顺序保留（因为原数组已排序）
    return sorted(result.values())


if __name__ == '__main__':
    main()
