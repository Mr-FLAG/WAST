import copy
import itertools
import math
import random
import sys

import cvxpy as cp

import SRPT
import SWAG


def main():
    # Given a number of slots, a set of jobs, each has some tasks with the task duration
    # tasks of the same job has a fixed duration stored in job_duration, task number in job_demand
    # Suppose each task requires one slot to proceed
    # Try to find an optimal placement and output the sum JRT
    num_test = 100
    step = 2
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

        # Original solution given the demand matrix regardless of computations slots number or task duration
        SRPT_original = SRPT.SRPT(job_demand)
        SWAG_original = SWAG.SWAG(job_demand)
        # Consider slots number and task duration
        SRPT_perslot = SRPT_slot(job_demand, job_duration, capacity)
        SWAG_perslot = SWAG_slot(job_demand, job_duration, capacity)

        print("demand: ", job_demand)
        print("duration:", job_duration)
        print("SRPT original: ", SRPT_original)
        print("SWAG original: ", SWAG_original)
        print("SRPT perslot: ", SRPT_perslot)
        print("SWAG perslot: ", SWAG_perslot)

        SRPT_original_assign = tiling_assign(job_demand, job_duration, num_slot, SRPT_original)
        SRPT_original_JRT = compute_completion_time(SRPT_original_assign, job_duration, SRPT_original, num_of_sites)
        record[0] += SRPT_original_JRT

        SRPT_original_opt = optimal_assign(job_demand, job_duration, num_slot, SRPT_original)
        SRPT_original_opt_JRT = compute_completion_time(SRPT_original_opt, job_duration, SRPT_original, num_of_sites)
        record[1] += SRPT_original_opt_JRT

        SRPT_perslot_assign = tiling_assign(job_demand, job_duration, num_slot, SRPT_perslot)
        SRPT_perslot_JRT = compute_completion_time(SRPT_perslot_assign, job_duration, SRPT_perslot, num_of_sites)
        record[2] += SRPT_perslot_JRT

        SRPT_opt_assign = optimal_assign(job_demand, job_duration, num_slot, SRPT_perslot)
        SRPT_opt_JRT = compute_completion_time(SRPT_opt_assign, job_duration, SRPT_perslot, num_of_sites)
        record[3] += SRPT_opt_JRT

        SWAG_original_assign = tiling_assign(job_demand, job_duration, num_slot, SWAG_original)
        SWAG_original_JRT = compute_completion_time(SWAG_original_assign, job_duration, SWAG_original, num_of_sites)
        record[4] += SWAG_original_JRT

        SWAG_original_opt = optimal_assign(job_demand, job_duration, num_slot, SWAG_original)
        SWAG_original_opt_JRT = compute_completion_time(SWAG_original_opt, job_duration, SWAG_original, num_of_sites)
        record[5] += SWAG_original_opt_JRT

        SWAG_perslot_assign = tiling_assign(job_demand, job_duration, num_slot, SWAG_perslot)
        SWAG_perslot_JRT = compute_completion_time(SWAG_perslot_assign, job_duration, SWAG_perslot, num_of_sites)
        record[6] += SWAG_perslot_JRT
        # for i in range(num_slot * num_of_sites):
        #     print(SWAG_perslot_assign[i])
        # print(SWAG_perslot_JRT)

        SWAG_opt_assign = optimal_assign(job_demand, job_duration, num_slot, SWAG_perslot)
        SWAG_opt_JRT = compute_completion_time(SWAG_opt_assign, job_duration, SWAG_perslot, num_of_sites)
        record[7] += SWAG_opt_JRT
  
        # if step = num_of_jobs, then JRT = SWAG_opt_JRT(record[7]) proved.
        # if step = 1, then JRT = SWAG_perslot_JRT(record[6]) - false. why?
        # by_step_SWAG = optimal_step_assign1(job_demand, job_duration, num_slot, SWAG_perslot, 2)
        # JRT = compute_completion_time(by_step_SWAG, job_duration, SWAG_perslot, num_of_sites)
        # print(JRT)
        # record[8] += JRT
        # print()
        # for i in range(num_slot * num_of_sites):
        #     print(by_step_SWAG[i])
        # print("by_step_SWAG: ", SWAG_perslot)
        
        # if step = 1, then 
        # if step = num_of_jobs, then JRT = global optimal
        by_step_order, by_step_assign = optimal_step_assign2(job_demand, job_duration, num_slot, num_of_jobs)
        JRT2 = compute_completion_time(by_step_assign, job_duration, by_step_order, num_of_sites)
        print("by_step_all: ", by_step_order)
        # print(by_step_assign)
        record[9] += JRT2

        # if SWAG_opt_JRT != JRT:
        #     print("Error")
        #     break
        print()

    for i in range(10):
        print(record[i]/num_test)
    # print(f"SRPT_ori: {test_a / num_test}")
    # print(f"SWAG_ori: {test_b / num_test}")
    # print(f"SRPT_per_slot: {test_c / num_test}")
    # print(f"SWAG_per_slot: {test_d / num_test}")
    # for i in range(num_slot):
    #     print(assignment_opt[i])


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


def SRPT_slot(job_demand, job_duration, capacity):
    num_of_sites = len(job_demand)
    num_of_jobs = len(job_demand[0])
    alone_finish_time = [0 for _ in range(num_of_jobs)]

    for i in range(num_of_sites):
        for j in range(num_of_jobs):
            alone_finish_time[j] = max(alone_finish_time[j], math.ceil(job_demand[i][j] / capacity[i]) * job_duration[j])

    # sorted = [False for _ in range(num_of_jobs)]
    order = [0 for _ in range(num_of_jobs)]
    for i in range(num_of_jobs):
        temp_min = alone_finish_time.index(min(alone_finish_time))
        # print(temp_min)
        order[i] = temp_min
        alone_finish_time[temp_min] = sys.maxsize
    return order


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


def optimal_step_assign1(job_demand, job_duration, num_slot, order, step):
    # Find the optimal assigning with job order given
    num_of_sites = len(job_demand)
    num_of_jobs = len(job_demand[0])

    ordered_demand = [[job_demand[j][order[i]] for i in range(num_of_jobs)] for j in range(num_of_sites)]
    ordered_duration = [job_duration[order[i]] for i in range(num_of_jobs)]
    slot_workload = [0 for _ in range(num_slot * num_of_sites)]
    assign = [[0 for _ in range(num_of_jobs)] for i in range(num_slot * num_of_sites)]
    ordered_num = 0
    while ordered_num != num_of_jobs:
        step = min(step, num_of_jobs - ordered_num)
        # Select "step" jobs and place its demand
        # To be updated: assign, slot_workload, assigned

        sub_assignment = cp.Variable((num_of_sites * num_slot, step), integer=True)
        sub_last_finish = cp.Variable((num_of_sites * num_slot, step), integer=True)
        Fin = cp.Variable(step, integer=True)

        constraints = []
        for i in range(num_slot * num_of_sites):
            for j in range(step):
                constraints += [
                    sub_assignment[i][j] >= 0
                ]

        # sum of allocation on all slots of a site = demand
        for i in range(num_of_sites):
            for j in range(step):
                constraints += [
                    cp.sum(sub_assignment[i * num_slot: (i + 1) * num_slot, j]) == ordered_demand[i][ordered_num+j] #job_demand[i][order[ordered_num+j]]
                ]

        # Finish time of each slot given j-th job's workload placed
        for i in range(num_slot * num_of_sites):
            for j in range(step):
                if j == 0:
                    constraints += [
                        sub_last_finish[i, 0] == sub_assignment[i, 0] * job_duration[order[ordered_num]] + slot_workload[i]
                    ]
                else:
                    constraints += [
                        sub_last_finish[i, j] == sub_last_finish[i, j - 1] + sub_assignment[i, j] * job_duration[
                            order[ordered_num+j]] + slot_workload[i]
                    ]

        for i in range(num_slot * num_of_sites):
            for j in range(step):
                constraints += [
                    Fin[j] >= sub_last_finish[i, j]
                ]

        obj = cp.Minimize(cp.sum(Fin))
        problem = cp.Problem(obj, constraints)
        problem.solve()

        for i in range(step):
            for j in range(num_of_sites * num_slot):
                assign[j][ordered_num + i] = round(sub_assignment[j][i].value)
                slot_workload[j] += sub_assignment[j][i].value * job_duration[ordered_num + i]
        ordered_num += step

    return assign


def optimal_step_assign2(job_demand, job_duration, num_slot, step):
    # Find the optimal assigning with job order unknown
    num_of_sites = len(job_demand)
    num_of_jobs = len(job_demand[0])

    slot_workload = [0 for _ in range(num_slot * num_of_sites)]
    assigned_jobs = [False for _ in range(num_of_jobs)]
    assign = [[0 for _ in range(num_of_jobs)] for i in range(num_slot * num_of_sites)]
    order = [0 for _ in range(num_of_jobs)]
    ordered_num = 0
    while ordered_num != num_of_jobs:
        step = min(step, num_of_jobs - ordered_num)
        # Select "step" jobs and place its demand
        order_current, optimal_assignment = update_step_jobs(job_demand, job_duration, slot_workload, assigned_jobs, step)
        # To be updated: assign, slot_workload, assigned_jobs
        for i in range(step):
            order[ordered_num + i] = order_current[i]
            assigned_jobs[order_current[i]] = True
            for j in range(num_of_sites * num_slot):
                assign[j][ordered_num + i] = optimal_assignment[j][i]
                slot_workload[j] += optimal_assignment[j][i] * job_duration[order_current[i]]
        ordered_num += step

    return order, assign


def update_step_jobs(job_demand, job_duration, slot_workload, assigned_jobs, step):
    num_of_sites = len(job_demand)
    num_of_jobs = len(job_demand[0])
    num_slot = len(slot_workload) // num_of_sites
    unsorted_indexes = []
    for j in range(num_of_jobs):
        if not assigned_jobs[j]:
            unsorted_indexes.append(j)
    permutations = list(itertools.permutations(unsorted_indexes, step))
    current_opt_time = sys.maxsize
    current_opt_order = [0 for _ in range(len(unsorted_indexes))]
    current_opt_assign = [[0 for _ in range(len(unsorted_indexes))] for _ in range(num_slot * num_of_sites)]

    for perm in permutations:
        # Given the current sub job-orders, compute the possible optimal JRT
        sub_assignment = cp.Variable((num_of_sites * num_slot, len(perm)), integer=True)
        sub_last_finish = cp.Variable((num_of_sites * num_slot, len(perm)), integer=True)
        Fin = cp.Variable(len(perm), integer=True)

        constraints = []
        for i in range(num_slot * num_of_sites):
            for j in range(len(perm)):
                constraints += [
                    sub_assignment[i][j] >= 0
                ]

        # sum of allocation on all slots of a site = demand
        for i in range(num_of_sites):
            for j in range(len(perm)):
                constraints += [
                    cp.sum(sub_assignment[i * num_slot: (i + 1) * num_slot, j]) == job_demand[i][perm[j]]
                ]

        # Finish time of each slot given j-th job's workload placed
        for i in range(num_slot * num_of_sites):
            for j in range(len(perm)):
                if j == 0:
                    constraints += [
                        sub_last_finish[i, 0] == sub_assignment[i, 0] * job_duration[perm[0]] + slot_workload[i]
                    ]
                else:
                    constraints += [
                        sub_last_finish[i, j] == sub_last_finish[i, j - 1] + sub_assignment[i, j] * job_duration[perm[j]] + slot_workload[i]
                    ]

        for i in range(num_slot * num_of_sites):
            for j in range(len(perm)):
                constraints += [
                    Fin[j] >= sub_last_finish[i, j]
                ]

        obj = cp.Minimize(cp.sum(Fin))
        problem = cp.Problem(obj, constraints)
        problem.solve()
        if obj.value < current_opt_time:
            current_opt_time = obj.value
            current_opt_order = copy.deepcopy(perm)
            for i in range(num_of_sites * num_slot):
                for j in range(step):
                    current_opt_assign[i][j] = round(sub_assignment[i][j].value)

    return current_opt_order, current_opt_assign



def optimal_assign(job_demand, job_duration, num_slot, order):
    num_of_sites = len(job_demand)
    num_of_jobs = len(job_demand[0])

    assign = [[0 for _ in range(num_of_jobs)] for i in range(num_slot * num_of_sites)]
    ordered_demand = [[job_demand[j][order[i]] for i in range(num_of_jobs)] for j in range(num_of_sites)]
    ordered_duration = [job_duration[order[i]] for i in range(num_of_jobs)]
    # print(ordered_demand)

    assignment = cp.Variable((num_of_sites * num_slot, num_of_jobs), integer=True)
    last_finish = cp.Variable((num_of_sites * num_slot, num_of_jobs), integer=True)
    Fin = cp.Variable(num_of_jobs, integer=True)

    constraints = []
    # allocation >= 0
    for i in range(num_slot * num_of_sites):
        for j in range(num_of_jobs):
            constraints += [
                assignment[i][j] >= 0
            ]

    # sum of allocation on all slots of a site = demand
    for i in range(num_of_sites):
        for j in range(num_of_jobs):
            constraints += [
                cp.sum(assignment[i * num_slot: (i+1) * num_slot, j]) == ordered_demand[i][j]
            ]

    # Finish time of each slot given j-th job's workload placed
    for i in range(num_slot * num_of_sites):
        for j in range(num_of_jobs):
            if j == 0:
                constraints += [
                    last_finish[i, 0] == assignment[i, 0] * ordered_duration[0]
                ]
            else:
                constraints += [
                    last_finish[i, j] == last_finish[i, j - 1] + assignment[i, j] * ordered_duration[j]
                ]

    # Finish time of each job
    # Bugs to be modified - each job's JRT != the longest workload among each slot
    for i in range(num_slot * num_of_sites):
        for j in range(num_of_jobs):
            constraints += [
                Fin[j] >= last_finish[i, j]
            ]

    obj = cp.Minimize(cp.sum(Fin))
    problem = cp.Problem(obj, constraints)
    problem.solve()
    # print(obj.value)

    for i in range(num_slot * num_of_sites):
        for j in range(num_of_jobs):
            assign[i][j] = round(assignment[i, j].value)  # assignment[i, j].value

    # print(assign)
    return assign


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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
