import copy
import itertools
import math
import random
import sys
import cvxpy as cp

from Policy_SRPT import SRPT


def main():
    # Given a number of slots, a set of jobs, each has some tasks with the task duration
    # tasks of the same job has a fixed duration stored in job_duration, task number in job_demand
    # Suppose each task requires one slot to proceed
    # Try to find an optimal placement and output the sum JRT
    num_test = 100
    record = [0 for _ in range(10)]
    for _ in range(num_test):
        print(f"loop {_}")
        num_slot = 5
        num_of_jobs = 5
        num_of_sites = 5
        capacity = [num_slot for _ in range(num_of_sites)]
        # job_demand = [random.randint(1, 10) for _ in range(num_of_jobs)]
        job_demand = [[random.randint(1, 10) for _ in range(num_of_jobs)] for _ in range(num_of_sites)]
        job_duration = [random.randint(1, 10) for _ in range(num_of_jobs)]

  
        SRPT_order = SRPT(job_demand, job_duration, capacity)
        SWAG_order = SWAG_slot(job_demand, job_duration, capacity)
        print(f"SRPT: {SRPT_order}")
        print(f"SWAG: {SWAG_order}")



def SWAG_slot(job_demand, job_duration, capacity):
    num_of_sites = len(job_demand)
    num_of_jobs = len(job_demand[0])
    slot_workload = [[0 for _ in range(capacity[i])] for i in range(num_of_sites)]
    placed_jobs = [False for _ in range(num_of_jobs)]
    SWAG_order = [0 for _ in range(num_of_jobs)]

    for j in range(num_of_jobs):
        # Each loop test all remaining jobs
        # By tiling check their JRT, select the lowest one.
        current_index = current_SWAG_order(slot_workload, job_demand, job_duration, placed_jobs)
        placed_jobs[current_index] = True
        SWAG_order[j] = current_index
        # Update slot workload
        for i in range(num_of_sites):
            allocated = 0
            while allocated < job_demand[i][current_index]:
                min_slot_index = slot_workload[i].index(min(slot_workload[i]))
                slot_workload[i][min_slot_index] += job_duration[current_index]
                allocated += 1
    return SWAG_order


def current_SWAG_order(slot_workload, job_demand, job_duration, placed_jobs):
    index = 0
    finish_time = sys.maxsize
    num_sites = len(job_demand)
    num_jobs = len(job_demand[0])
    demand_sum = [sum(job_demand[i][j] * job_duration[j] for i in range(num_sites)) for j in range(num_jobs)]
    # print(slot_workload)
    for j in range(num_jobs):
        if not placed_jobs[j]:
            # Try to place this job
            temp_workload = copy.deepcopy(slot_workload)
            duration = job_duration[j]
            temp_finish_time = 0
            for i in range(num_sites):
                allocated = 0
                while allocated < job_demand[i][j]:
                    # Find the slot with minimum workload
                    slot_index = temp_workload[i].index(min(temp_workload[i]))
                    # Update slot workload and assignment info
                    temp_workload[i][slot_index] += duration
                    temp_finish_time = max(temp_finish_time, temp_workload[i][slot_index])
                    allocated += 1
            # print(f"slot: job {j} finish time: {temp_finish_time}")
            if temp_finish_time < finish_time:
                index = j
                finish_time = temp_finish_time
            elif temp_finish_time == finish_time and demand_sum[j] < demand_sum[index]:
                index = j
                finish_time = temp_finish_time
    return index




def sort_by_weight(weighted_demand):
    num_job = len(weighted_demand)
    order = [0 for i in range(num_job)]
    demand = copy.deepcopy(weighted_demand)
    for i in range(num_job):
        temp_min = demand.index(min(demand))
        # print(temp_min)
        order[i] = temp_min
        demand[temp_min] = 1000000000

    return order


def assignment_by_order(job_demand, job_duration, order, num_slot):
    num_of_jobs = len(job_demand)
    assignment = [[0 for _ in range(num_of_jobs)] for i in range(num_slot)]
    slot_workload = [0 for i in range(num_slot)]
    for i in range(num_of_jobs):
        for j in range(job_demand[order[i]]):
            min_slot_index = slot_workload.index(min(slot_workload))
            slot_workload[min_slot_index] += job_duration[order[i]]
            assignment[min_slot_index][i] += 1

    return assignment


def compute_completion_time(assignment, job_duration, order, num_of_sites):
    num_slot = len(assignment) // num_of_sites
    num_of_jobs = len(job_duration)
    slot_workload = [[0 for _ in range(num_slot)] for _ in range(num_of_sites)]

    sum_time = 0
    for i in range(num_of_jobs):
        max_time = 0
        for j in range(num_of_sites * num_slot):
            if assignment[j][i] != 0:
                slot_workload[j//num_slot][j % num_slot] += job_duration[order[i]] * assignment[j][i]  # duration
                max_time = max(max_time, slot_workload[j//num_slot][j % num_slot])
        sum_time += max_time
        # print(slot_workload)

    return sum_time


def tiling_assign(job_demand, job_duration, num_slot, job_order):
    num_of_sites = len(job_demand)
    num_of_jobs = len(job_demand[0])
    slot_workload = [[0 for _ in range(num_slot)] for _ in range(num_of_sites)]
    assignment = [[0 for _ in range(num_of_jobs)] for _ in range(num_slot * num_of_sites)]
    # np.zeros((num_of_sites, num_slot, num_of_jobs), int)

    for i in range(num_of_jobs):
        # Select the i-th (based on priorities) job to schedule on all slots
        current_job_index = job_order[i]
        duration = job_duration[current_job_index]
        for j in range(num_of_sites):
            allocated = 0
            while allocated < job_demand[j][current_job_index]:
                # Find the slot with minimum workload
                slot_index = slot_workload[j].index(min(slot_workload[j]))
                # Update slot workload and assignment info
                slot_workload[j][slot_index] += duration
                assignment[j * num_slot + slot_index][i] += 1
                allocated += 1

    return assignment



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
