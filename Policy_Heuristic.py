import copy
import itertools
import math, time
import random
import sys, heapq
import cvxpy as cp
import numpy as np
import Policy_SWAG, Policy_SRPT
from Event import Transmission_queue, Event_Transmission



def main():
    num_slot = 10
    num_of_jobs = 1
    num_of_sites = 10
    num_test = 1
    record = [0 for _ in range(4)]
    job_datasize = [1 for _ in range(num_of_jobs)]
    bandwidth = 1
    time_cost = 0
    time_cost2 = 0

    print(record)
    print(f"Time cost: {time_cost / num_test}, {time_cost2 / num_test}")


# def compute_order_trans(slot_workload, job_demand, job_duration, job_datasize, bandwidth, job_transmission, placed_jobs,
#                         transmission_cost):
#     num_jobs = len(job_duration)
#     num_sites = len(job_demand)


def heuristic(job_demand, job_duration, job_datasize, capacity, bandwidth):
    num_jobs = len(job_duration)
    num_sites = len(job_demand)
    slot_workload = [[0 for _ in range(capacity[i])] for i in range(num_sites)]
    placed_jobs = [False for _ in range(num_jobs)]
    SWAG_LP_order = [-1 for _ in range(num_jobs)]
    transmission_cost = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
    unit_trans_time = [job_datasize[i] / bandwidth for i in range(num_jobs)]
    job_transmission = []

    # # Sort job by sum of this_demand, lower sum is more likely to win
    # col_sum = np.sum(job_demand, axis=0)
    # sum_demand = [col_sum[i] * job_duration[i] for i in range(num_jobs)]
    # demand_order = np.argsort(sum_demand)

    for cur_round in range(num_jobs):
        # Each round, find the best job with its transmission.
        # Transmission add to the queue & cost; Also update the slot_workload
        # Here search is done by traverse, and spare time interval is allowed
        current_transmission = []
        cur_JRT = sys.maxsize
        cur_index = -1
        # print(f"Round {cur_round}, current order: {SWAG_LP_order}")
        for this_index in range(num_jobs):
            if not placed_jobs[this_index]:
                this_demand = [row[this_index] for row in job_demand]
                transit_time = job_datasize[this_index] / bandwidth
                duration = job_duration[this_index]
                #Compute this job's JRT and transmission
                this_JRT, this_transmission = compute_current_job(this_demand, duration,
                                                                  transit_time, slot_workload, transmission_cost)
                # Update if this job has better JRT under some transmission
                if this_JRT < cur_JRT:
                    cur_JRT = this_JRT
                    cur_index = this_index
                    current_transmission = this_transmission

        # print(f"Round {cur_round}, find job {cur_index}, JRT: {cur_JRT}")
        placed_jobs[cur_index] = True
        SWAG_LP_order[cur_round] = cur_index
        job_transmission.append(current_transmission)
        # cur_trans_time = job_datasize[cur_index] / bandwidth
        # cur_duration = job_duration[cur_index]

        #After the round, find the best job job_index and its transmission 
        for i in range(num_sites):
            #Modify transferred demands
            for j in range(num_sites):
                removed = 0
                while removed < current_transmission[i][j]:
                    job_demand[i][cur_index] -= 1
                    removed += 1
                    
            #Place cur_index's local this_demand
            added = 0
            while added < job_demand[i][cur_index]:
                min_slot_index = slot_workload[i].index(min(slot_workload[i]))
                slot_workload[i][min_slot_index] += job_duration[cur_index]
                added += 1
                
            # Check transmission, update slot_workload and transmission_cost:
            for j in range(num_sites):
                transferred = 0
                while transferred < current_transmission[i][j]:
                    transmission_cost[i][j] += unit_trans_time[cur_index]
                    arrival_time = transmission_cost[i][j]
                    min_slot_index = slot_workload[j].index(min(slot_workload[j]))  
                    if arrival_time < min(slot_workload[i]):
                        #Transmission arrives in time, directly add it to the workload
                        slot_workload[j][min_slot_index] += job_duration[cur_index]
                    else:
                        slot_index = find_slot_index(slot_workload[j], arrival_time)
                        slot_workload[j][slot_index] = arrival_time + job_duration[cur_index]
                    transferred += 1

    return SWAG_LP_order, job_transmission


def compute_current_job(demand, duration, transit_time, slot_workload, transmission_cost):
    #Given the current workload, find the transmissions that minimize current job's JRT
    num_sites = len(demand)
    capacity = [len(workload) for workload in slot_workload]

    temp_demand = copy.deepcopy(demand)
    temp_workload = copy.deepcopy(slot_workload)
    temp_trans_cost = copy.deepcopy(transmission_cost)
    transmission = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
    placed_info = [[0 for _ in range(capacity[i])] for i in range(num_sites)]
    local_JRT = [0 for _ in range(num_sites)]
    temp_JRT = 0
    trans_JRT = 0

    #Place local demand
    for i in range(num_sites):
        allocated = 0
        while allocated < temp_demand[i]:
            min_slot_index = temp_workload[i].index(min(temp_workload[i]))
            temp_workload[i][min_slot_index] += duration
            placed_info[i][min_slot_index] += 1
            local_JRT[i] = max(local_JRT[i], temp_workload[i][min_slot_index])
            allocated += 1
    temp_JRT = max(local_JRT)

    # trans_queue = Transmission_queue()
    temp_trans = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
    # Consider transmission, each round move to smallest JRT
    while True:
        # print(f"Searching for job {job_index}, loop {num_loop}")
        # num_loop += 1
        found = True
        for i in range(num_sites):
            for k in range(capacity[i]):
                if temp_workload[i][k] == temp_JRT and placed_info[i][k] > 0:
                    # Find the destination that minimize this task's finish time
                    # start_time, dest_index, slot_index = find_destination2(temp_workload, i, temp_trans_cost,
                    #                                                       transit_time, transmission_allowed)
                    start_time, dest_index, slot_index = find_destination(temp_workload, i, temp_trans_cost, transit_time)
                    if dest_index != -1 and start_time + duration < temp_JRT:
                        # Find a dest that fin time is reduced most
                        # Update workload, transmission cost, demand
                        temp_trans[i][dest_index] += 1
                        temp_workload[i][k] -= duration
                        temp_trans_cost[i][dest_index] += transit_time
                        temp_demand[i] -= 1
                        # temp_transmission[i][dest_index] += 1
                        placed_info[i][k] -= 1
                        placed_info[dest_index][slot_index] += 1
                        temp_workload[dest_index][slot_index] = start_time + duration
                        trans_JRT = max(trans_JRT, temp_workload[dest_index][slot_index])
                    else:
                        found = False
                        break
            if not found:
                break
        
        # print("Out of the loop")
        if found:
            #Current round succeeds, all tasks find a destination
            #Update JRT and transmission:
            new_JRT = 0
            for i in range(num_sites):
                for j in range(capacity[i]):
                    if placed_info[i][j] > 0:
                        new_JRT = max(new_JRT, temp_workload[i][j])
            temp_JRT = new_JRT

            transmission = [[a + b for a, b in zip(row_a, row_b)] for row_a, row_b in zip(transmission, temp_trans)]
            temp_trans = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
        else:
            break

        # Finish time decided by transferred task
        # Can't be further reduced, loop stop
        if temp_JRT <= trans_JRT:
            break
    # print(f"Job {job_index} best JRT: {temp_JRT}")
    return temp_JRT, transmission


def find_destination(temp_workload, start_index, trans_cost, transit_time):
    # stricter constraint on destination:
    num_sites = len(temp_workload)
    start_time = sys.maxsize
    dest_index = -1
    slot_index = -1
    for i in range(num_sites):
        if i != start_index:
            arrival_time = trans_cost[start_index][i] + transit_time
            min_slot_index = temp_workload[i].index(min(temp_workload[i]))
            # if start_index == 1 and i == 4:
            #     print(arrival_time, min(temp_workload[i]))
            if arrival_time <= min(temp_workload[i]):
                temp_start_time = min(temp_workload[i])
                temp_slot_index = min_slot_index
                if temp_start_time < start_time:
                    start_time = temp_start_time
                    slot_index = temp_slot_index
                    dest_index = i
    return start_time, dest_index, slot_index

def find_destination2(temp_workload, start_index, trans_cost, transit_time):
    # loose constraint on destination:
    num_sites = len(temp_workload)
    start_time = sys.maxsize
    dest_index = -1
    slot_index = -1
    for i in range(num_sites):
        if i != start_index:
            arrival_time = trans_cost[start_index][i] + transit_time
            temp_slot_index = find_special_index(temp_workload[i], arrival_time)
            if max(temp_workload[i][temp_slot_index], arrival_time) + transit_time <= start_time:
                start_time = max(temp_workload[i][temp_slot_index], arrival_time) + transit_time
                slot_index = temp_slot_index
                dest_index = i
            # if arrival_time <= min(temp_workload[i]):
            #     temp_start_time = min(temp_workload[i])
            #     temp_slot_index = min_slot_index
            #     if temp_start_time < start_time:
            #         start_time = temp_start_time
            #         slot_index = temp_slot_index
            #         dest_index = i
    return start_time, dest_index, slot_index


def find_special_index(A, x):
    # Split values >= x and values < x
    greater_than_x = [(val, i) for i, val in enumerate(A) if val >= x]

    if greater_than_x:
        return min(greater_than_x)[1]
    else:
        return min(enumerate(A), key=lambda item: item[1])[0]

def find_slot_index(workload, arrival_time):
    # Find the index that is smallest but larger than event.arrival_time:
    num_slots = len(workload)
    temp_index = -1
    temp_workload = sys.maxsize
    for i in range(num_slots):
        if arrival_time < workload[i] < temp_workload:
            temp_workload = workload[i]
            temp_index = i
    return temp_index                
            
    
def compute_order_new(job_demand, job_duration, job_datasize, capacity, bandwidth, job_transmission):
    # Given the job demand & transmission, compute the order
    # Note transmission are fixed, but its order is not.
    num_sites = len(job_demand)
    num_jobs = len(job_demand[0])
    slot_workload = [[0 for _ in range(capacity[i])] for i in range(len(capacity))]
    # Record current bandwidth usage
    transmission_cost = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
    # Record transmissions that has been added to slot_workload
    transmission_added = [[[0 for _ in range(num_sites)] for _ in range(num_sites)] for _ in range(num_jobs)]
    placed_jobs = [False for _ in range(num_jobs)]
    SWAG_order = [-1 for _ in range(num_jobs)]
    SWAG_JRT = [0 for _ in range(num_jobs)]

    for j in range(num_jobs):
        # Find the next job to be placed
        cur_index = current_order_new(slot_workload, job_demand, job_duration, job_datasize, bandwidth,
                                      job_transmission,
                                      placed_jobs, transmission_cost)
        placed_jobs[cur_index] = True
        SWAG_order[j] = cur_index
        transit_time = job_datasize[cur_index] / bandwidth
        duration = job_duration[cur_index]

        # Update slot workload by adding selected job's tasks
        # This doesn't consider the current job's late transmission
        for i in range(num_sites):
            added = 0
            while added < job_demand[i][cur_index]:
                # Place local tasks first
                min_slot_index = slot_workload[i].index(min(slot_workload[i]))
                slot_workload[i][min_slot_index] += job_duration[cur_index]
                SWAG_JRT[cur_index] = max(SWAG_JRT[cur_index], slot_workload[i][min_slot_index])
                added += 1

            # Convert transmission into events
            temp_queue = Transmission_queue()
            for k in range(num_sites):
                transferred = 0
                # Check transmission from k to i of job j
                while transferred < job_transmission[cur_index][k][i]:
                    temp_event = Event_Transmission(cur_index, k, i, transmission_cost[k][i], transit_time, duration)
                    temp_queue.add_event(temp_event)
                    transmission_cost[k][i] += transit_time
                    transferred += 1

            while len(temp_queue.queue) != 0:
                event = temp_queue.pop_event()
                if event.start_time + event.transit_time <= min(slot_workload[i]):
                    # Arrives in time, directly add it to the workload
                    slot_index = slot_workload[i].index(min(slot_workload[i]))
                    slot_workload[i][slot_index] += duration
                    SWAG_JRT[cur_index] = max(SWAG_JRT[cur_index], slot_workload[i][slot_index])
                else:
                    # Find the index that is smallest but larger than event.arrival_time:
                    slot_index = find_slot_index(slot_workload[i], event.start_time + event.transit_time)
                    if slot_index != -1:
                        # Add this transmission to the workload
                        slot_workload[i][slot_index] = event.start_time + event.transit_time + duration
                        SWAG_JRT[cur_index] = max(SWAG_JRT[cur_index], slot_workload[i][slot_index])
    return SWAG_order, SWAG_JRT


def current_order_new(slot_workload, job_demand, job_duration, job_datasize, bandwidth, job_transmission,
                      placed_jobs, transmission_cost):
    # Among remaining jobs, find the one that JRT is smallest after placement
    num_sites = len(job_demand)
    num_jobs = len(job_demand[0])
    num_placed = sum(placed_jobs)

    final_index = -1
    final_JRT = sys.maxsize

    for j in range(num_jobs):
        if not placed_jobs[j]:
            # Try place job j, get JRT and compare
            # Suppose all previous transmissions are placed, No need to consider them
            # SWAG_order[num_placed] = j
            temp_JRT = 0
            temp_index = j
            temp_trans_cost = copy.deepcopy(transmission_cost)
            temp_workload = copy.deepcopy(slot_workload)
            temp_trans_added = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
            transit_time = job_datasize[j] / bandwidth
            duration = job_duration[j]
            for i in range(num_sites):
                added = 0
                # Place local tasks first
                while added < job_demand[i][j]:
                    min_slot_index = temp_workload[i].index(min(temp_workload[i]))
                    temp_workload[i][min_slot_index] += duration
                    temp_JRT = max(temp_JRT, temp_workload[i][min_slot_index])
                    added += 1

                # Convert transmission into events
                temp_queue = Transmission_queue()
                for k in range(num_sites):
                    # Check transmission from k to i of job j
                    while temp_trans_added[k][i] < job_transmission[j][k][i]:
                        temp_event = Event_Transmission(j, k, i, temp_trans_cost[k][i], transit_time, duration)
                        temp_queue.add_event(temp_event)
                        temp_trans_cost[k][i] += transit_time
                        temp_trans_added[k][i] += 1

                while len(temp_queue.queue) != 0:
                    event = temp_queue.pop_event()
                    if event.start_time + event.transit_time <= min(temp_workload[i]):
                        # Arrives in time, directly add it to the workload
                        slot_index = temp_workload[i].index(min(temp_workload[i]))
                        temp_workload[i][slot_index] += duration
                        temp_JRT = max(temp_JRT, temp_workload[i][slot_index])
                    else:
                        # Find the index that is smallest but larger than event.arrival_time:
                        slot_index = find_slot_index(temp_workload[i], event.start_time + event.transit_time)
                        if slot_index != -1:
                            # Add this transmission to the workload
                            temp_workload[i][slot_index] = event.start_time + event.transit_time + duration
                            temp_JRT = max(temp_JRT, temp_workload[i][slot_index])

            if temp_JRT < final_JRT:
                final_index = temp_index
                final_JRT = temp_JRT

    return final_index




def compute_JRT(demand_matrix, job_duration, capacity, order, transmission_queues):
    # Given current demand, duration, order & transmission
    # Compute each job's JRT, return their summation.
    num_of_sites = len(capacity)
    num_of_jobs = len(job_duration)
    JRT = [0 for _ in range(num_of_jobs)]
    # temp_demand = copy.deepcopy(demand_matrix)
    temp_transmission = copy.deepcopy(transmission_queues)
    # Record current workload
    slot_workload = [[0 for _ in range(capacity[i])] for i in range(len(capacity))]

    for j in range(num_of_jobs):
        cur_index = order[j]
        duration = job_duration[cur_index]
        for i in range(num_of_sites):
            added = 0
            # Place local demand first
            while added < demand_matrix[i][cur_index]:
                min_slot_index = slot_workload[i].index(min(slot_workload[i]))
                slot_workload[i][min_slot_index] += duration
                JRT[cur_index] = max(JRT[cur_index], slot_workload[i][min_slot_index])
                added += 1

            count = 0
            queue_length = temp_transmission[i].length()
            while count < queue_length:
                count += 1
                event = temp_transmission[i].pop_event()
                arrival_time = event.start_time + event.transit_time
                if event.job_index == cur_index:
                    if arrival_time <= min(slot_workload[i]):
                        # Arrives in time, directly add it to the workload
                        min_slot_index = slot_workload[i].index(min(slot_workload[i]))
                        slot_workload[i][min_slot_index] += duration
                        JRT[cur_index] = max(JRT[cur_index], slot_workload[i][min_slot_index])
                    else:
                        # Find the index that is smallest but larger than event.arrival_time:
                        # print("trigger spare time")
                        min_slot_index = find_slot_index(slot_workload[i], arrival_time)
                        if min_slot_index != -1:
                            # Add this transmission to the workload
                            slot_workload[i][min_slot_index] = arrival_time + duration
                        JRT[cur_index] = max(JRT[cur_index], slot_workload[i][min_slot_index])
                else:
                    temp_transmission[i].add_event(event)
    return JRT


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
