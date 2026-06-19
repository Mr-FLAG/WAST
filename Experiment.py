# This is a sample Python script.
import sys, csv, math
import datetime, time
import numpy as np
from collections import deque
import heapq

import Policy_SRPT, Policy_SWAG, Policy_GEODIS, Policy_Heuristic, Policy_MinFlow
from Job import Job, Job_Total
from Event import Event, Event_Transmission, Transmission_queue
#use_solver = "HIGHS"
# num_late = 0

def main():
    data_resources = ["Ali2018_4"]  # Ali2017:5000 Ali2018_4: 15000
    strategies = ["FLOW"]  #"SRPT", "SWAG", "heuristic", "FLOW"
    alphas = [1.0] #0.0, 0.5, 1.0, 2.0
    utilities = [0.6] #0.5, 0.6, 0.7, 0.8
    bandwidths = [3]#3, 6, 12
    job_number = 1000
    start_index = 15000

    # Define the number of sites and site capacity
    site_capacity = 32
    num_of_sites = 10
    capacity = [site_capacity for _ in range(num_of_sites)]

    workload_threshold = sys.maxsize
    forecast_threshold = sys.maxsize
    last_compute_time = 0
    computation_count = 0
    threshold_ratio = 3
    total_job_in_computation = 0

    # Each site's capacity is set to site_capacity
    for data_resource in data_resources:
        for utility in utilities:
            for alpha in alphas:
                # Assuming compute_workload is a defined function
                file_name = f"{data_resource}_distributed_sites={num_of_sites}_alpha={alpha}"
                workload = compute_workload(file_name, job_number, start_index, capacity, workload_threshold)
                workload[0] /= utility
                # workload_coefficient = workload[0] / utility
                # average_task_duration = workload[1]

                for strategy in strategies:
                    for bandwidth in bandwidths:
                        # Initialize queues
                        total_job_queue = read_jobs(file_name, job_number, start_index, num_of_sites,
                                                    workload_threshold, workload)
                        # forecast_threshold = sys.maxsize #compute_threshold(total_job_queue)
                        # print(forecast_threshold, int((total_job_queue[-1].arrival_time - total_job_queue[0].arrival_time)*threshold_ratio/job_number))
                        # forecast_threshold = int((total_job_queue[-1].arrival_time - total_job_queue[0].arrival_time)*threshold_ratio/job_number)
                        # print(f"Forecast threshold = {forecast_threshold}, ratio = {threshold_ratio}")
                        total_process_list = []
                        event_heapq_list = [[] for _ in range(num_of_sites)]  # Event queues for each site
                        process_list = [[] for _ in range(num_of_sites)]  # Wait lists for each site
                        transmission_list = [Transmission_queue() for _ in
                                             range(num_of_sites)]  # Transmission queues for each site
                        # Record when will the bandwidth be available
                        transmission_cost = [[0 for _ in range(num_of_sites)] for _ in range(num_of_sites)]
                        ideal_order = []  # Order of jobs to be processed
                        num_trans=0

                        # Here the bandwidth between any two sites is the same
                        # bandwidth = [i for i in range(num_of_sites)]
                        # You can use a predefined bandwidth resource array

                        # Record info for charts
                        finish_list = []
                        SD_stack = []  
                        sum_computation_time_queue = []
                        # Allo_Deviation_stack = []  # Stack to record standard deviation events
                        # queue_length_stack = []  # Another stack

                        print(datetime.datetime.now())
                        print(
                            f"{file_name}.csv loaded, {len(total_job_queue)} jobs, using {strategy}, B = {bandwidth}, Utility = {utility * 100}%.")

                        simulation_start_time = time.time()  # Equivalent to System.currentTimeMillis()
                        # Initialize current time and maximum queue length
                        current_time = 0.0
                        max_queue_length = 0
                        # finish_count = 0

                        while total_job_queue or total_process_list:
                            # Find the earliest event & arriving job to decide which happen first.
                            # Consider the empty case: set time to be MAX so that the other will happen earlier.
                            earliest_event = find_earliest_event(event_heapq_list)
                            earliest_event_time = earliest_event.release_time if earliest_event else sys.maxsize
                            next_job_arrival_time = total_job_queue[0].arrival_time if total_job_queue else sys.maxsize
                            recompute = False
                            if next_job_arrival_time < earliest_event_time:
                                # Job arrival first
                                current_time = next_job_arrival_time
                                cur_length = sum([transmission_list[i].length() for i in range(num_of_sites)])
                                release_transmission(total_process_list, process_list, transmission_list, current_time)
                                num_trans += (cur_length -
                                              sum([transmission_list[i].length() for i in range(num_of_sites)]))
                                # finish_count = 0
                                while total_job_queue and total_job_queue[0].arrival_time == next_job_arrival_time:
                                    current_job = total_job_queue.pop(0)  # Remove and return the first job
                                    add_job(current_job, total_process_list, process_list)
                                    print(
                                        f"Job{current_job.Job_ID} with {current_job.num_task} task(s),"
                                        f" arrives at {current_job.arrival_time:.2f},"
                                        f" now {len(total_process_list)} job(s).")
                                    max_queue_length = max(max_queue_length, len(total_process_list))
                                    if current_job.num_task == 1:
                                        # for j in range(len(ideal_order)):
                                        #     ideal_order[j] += 1
                                        index = len(ideal_order)
                                        ideal_order.insert(0, index)
                                        continue
                                    else:
                                        recompute = True
                                        # last_compute_time = current_time
                                        # if not total_job_queue:
                                        #     forecast_threshold = sys.maxsize
                                # recompute = True
                            elif earliest_event is not None:
                                # Event finish first
                                # print(f"Found the earliest event: {earliest_event.Job_ID}")
                                current_time = earliest_event.release_time
                                cur_length = sum([transmission_list[i].length() for i in range(num_of_sites)])
                                release_transmission(total_process_list, process_list, transmission_list, current_time)
                                num_trans += (cur_length -
                                              sum([transmission_list[i].length() for i in range(num_of_sites)]))
                                # if current_time - last_compute_time >= forecast_threshold:
                                #     recompute = True
                                #     last_compute_time = current_time
                                for i in range(num_of_sites):
                                    while event_heapq_list[i] and event_heapq_list[i][0].release_time == current_time:
                                        current_event = heapq.heappop(event_heapq_list[i])  # Peek at the earliest event
                                        job_index = find_aggregate_job_index(total_process_list,
                                                                             current_event.Job_ID)
                                        total_process_list[job_index].num_finished_task += 1
                                        process_list[i][job_index].num_performing_task -= 1
                                        if total_process_list[job_index].num_finished_task >= total_process_list[
                                            job_index].num_task:
                                            # A job completes, remove it
                                            # finish_count += 1
                                            print(
                                                f"Job{current_event.Job_ID} with {total_process_list[job_index].num_finished_task} task(s) "
                                                f"finishes at {current_time:.2f} "
                                                f"Now {max(len(total_process_list) - 1, 0)} job(s) remaining.")
                                            remove_total_job(total_process_list, process_list, finish_list,
                                                             job_index, current_time)
                                            # recompute = True
                                            # print(f"Order before: {ideal_order}")
                                            if job_index in ideal_order:
                                                ideal_order.remove(job_index)
                                            else:
                                                ideal_order.pop()
                                            # print(f"Order remove: {ideal_order}")
                                            for k in range(len(ideal_order)):
                                                if ideal_order[k] > job_index:
                                                    ideal_order[k] -= 1
                                            # Also, need to modify all transmissions because they use Job_index as indicator
                                            for k in range(num_of_sites):
                                                for event in transmission_list[k].queue:
                                                    if event.job_index > job_index:
                                                        event.job_index -= 1
                                            # print(f"Order at now: {ideal_order}")
                            else:
                                # A transmission arrives first
                                current_time = find_earliest_transmission(transmission_list)
                                # current_time = event.release_time
                                cur_length = sum([transmission_list[i].length() for i in range(num_of_sites)])
                                release_transmission(total_process_list, process_list, transmission_list, current_time)
                                num_trans += (cur_length -
                                              sum([transmission_list[i].length() for i in range(num_of_sites)]))
                                # sub_job = find_job(process_list[i], current_event.Job_ID)
                                # sub_job.num_performing_task -= 1
                                # if sub_job.num_performing_task == 0 and sub_job.num_waiting_task == 0:
                                #     recompute = True
                            if recompute:
                                # current_demand, current_duration, current_datasize = record_info(num_of_sites, process_list)
                                computation_count += 1
                                computation_start_time = time.time()
                                # Clear transmission link
                                retract_transmission(process_list, transmission_list)
                                # current_workload = [[0 for _ in range(i)] for i in capacity]
                                # for i in range(num_of_sites):
                                #     temp_index = 0
                                #     for event in event_heapq_list[i]:
                                #         current_workload[i][temp_index] = event.release_time - current_time
                                #         temp_index += 1
                                # total_job_in_computation += len(total_process_list)
                                ideal_order, transmission_list, time_cost = compute_order(strategy, total_process_list, process_list,
                                                                               capacity, bandwidth,
                                                                               transmission_list, current_time, forecast_threshold)#, current_workload
                                sum_computation_time_queue.append(time_cost)
                            # print(ideal_order)
                            # print(process_list)


                            for i in range(num_of_sites):
                                while process_list[i] and len(event_heapq_list[i]) < capacity[i]:
                                    for j in ideal_order:
                                        hungry_job = process_list[i][j]
                                        while hungry_job.num_waiting_task > 0 and len(event_heapq_list[i]) < capacity[
                                            i]:
                                            # Decrease waiting tasks and increase performing tasks
                                            hungry_job.num_waiting_task -= 1
                                            hungry_job.num_performing_task += 1
                                            # Get the task duration
                                            task_duration = hungry_job.task_duration_queue.popleft()

                                            # Create a new event and set its properties, add to the event priority queue
                                            new_event = Event(hungry_job.Job_ID, current_time, task_duration)
                                            # new_event.Job_ID = hungry_job.Job_ID
                                            # new_event.enter_time = current_time
                                            # new_event.release_time = new_event.enter_time + task_duration
                                            heapq.heappush(event_heapq_list[i], new_event)
                                    if len(event_heapq_list[i]) == capacity[i] or process_list[i][-1].num_waiting_task == 0:
                                        break

                                    # hungry_job = find_hungry_job(process_list[i], ideal_allocation[i])

                                    # if hungry_job.num_waiting_task > 0:
                                    #     # Decrease waiting tasks and increase performing tasks
                                    #     hungry_job.num_waiting_task -= 1
                                    #     hungry_job.num_performing_task += 1
                                    #     # Get the task duration
                                    #     task_duration = hungry_job.task_duration_queue.popleft()  # Assuming task_duration_queue is a deque

                                    #     # Create a new event and set its properties, add to the event priority queue
                                    #     new_event = Event()
                                    #     new_event.Job_ID = hungry_job.Job_ID
                                    #     new_event.enter_time = current_time
                                    #     new_event.release_time = new_event.enter_time + task_duration
                                    #     event_pq[i].append(new_event)  # Assuming event_pq is a priority queue or a heapq in Python
                                    # else:
                                    #     break

                        #     aggregate_allocation = record_aggregate_allocation(num_of_sites, process_list)
                        #     SD = compute_SD(aggregate_allocation)

                        #     if not SD_stack:  # equivalent of `isEmpty()` in Java
                        #         SD_stack.append(Event_StandardDeviation(SD, current_time))
                        #     elif SD_stack[-1].standard_deviation != SD:  # `peek()` is equivalent to accessing the last item with [-1]
                        #         SD_stack[-1].release_time = current_time
                        #         SD_stack.append(Event_StandardDeviation(SD, current_time))

                        #     allocation_deviation = compute_deviation(aggregate_allocation, ideal_allocation)
                        #     if not Allo_Deviation_stack:
                        #         Allo_Deviation_stack.append(Event_StandardDeviation(allocation_deviation, current_time))
                        #     elif Allo_Deviation_stack[-1].standard_deviation != allocation_deviation:
                        #         Allo_Deviation_stack[-1].release_time = current_time
                        #         Allo_Deviation_stack.append(Allo_Deviation_stack(allocation_deviation, current_time))

                        # SD_stack[-1].release_time = current_time
                        # Allo_Deviation_stack[-1].release_time = current_time

                        elapsed_time_sec = time.time() - simulation_start_time
                        hours = int(elapsed_time_sec // 3600)
                        minutes = int((elapsed_time_sec % 3600) // 60)
                        seconds = int(elapsed_time_sec) % 60

                        average_JRT = 0
                        for job in finish_list:
                            this_JRT = job.finish_time - job.arrival_time
                            # print(f"{job.Job_ID}, {job.total_duration/job.num_task}, {this_JRT}")
                            average_JRT += this_JRT
                        # Print details
                        print(f"{data_resource}; alpha={alpha}; {strategy}; {int(utility*100)}%; B={bandwidth}; slots={site_capacity}; start={start_index}")
                        # print(f"Forecast threshold = {forecast_threshold}, ratio = {threshold_ratio}")
                        print(f"Total time cost: {hours} hours {minutes} minutes {seconds:.2f} seconds")
                        print(f"Compute {computation_count} time(s), cost {sum(sum_computation_time_queue)} second(s)")
                        print(f"Average JRT: {average_JRT / job_number}")
                        print(f"Current Time: {datetime.datetime.now()}")
                        print(f"Total transmission: {num_trans}")
                        print("-" * 20)
                        write_job_completion_time(finish_list, data_resource, strategy, num_of_sites, alpha, bandwidth,
                                                  utility, job_number, start_index, site_capacity)
                        # write_standard_deviation(SD_stack, data_resource, strategy, num_of_sites, alpha, bandwidth,
                        #                          utility, job_number)
                        write_computation_time(sum_computation_time_queue, data_resource, strategy, num_of_sites, alpha,
                                               bandwidth,
                                               utility, job_number, start_index, site_capacity)
                        # write_computation_time()
                        computation_count = 0
                        if strategy.startswith("D"):
                            break
    # print(f"num_late {num_late}")
    # print(f"Total job in computation: {total_job_in_computation}")


def compute_order(strategy, total_wait_list, wait_list, capacity, bandwidth, transmission_list, current_time, forecast_threshold=sys.maxsize):
    num_of_sites = len(capacity)
    num_of_jobs = len(total_wait_list)
    current_demand = [[0 for _ in range(num_of_jobs)] for _ in range(num_of_sites)]
    current_duration = [total_wait_list[i].total_duration / total_wait_list[i].num_task for i in range(num_of_jobs)]
    current_datasize = [total_wait_list[i].data_size for i in range(num_of_jobs)]
    current_workload = [[0 for _ in range(i)] for i in capacity]
    job_transit = []
    order = []
    # global num_late

    # for i in range(num_of_sites)
    # Abstraction for ease of use
    # Also, transfer_workload(capacity, event_heapq_list, current_time) into current_workload
    for i in range(num_of_sites):
        for index, temp_job in enumerate(wait_list[i]):
            current_demand[i][index] = temp_job.num_waiting_task
    # print(current_demand)
    start_time = time.perf_counter()
    if strategy == "SWAG":
        order = Policy_SWAG.SWAG_slot(current_demand, current_duration, capacity)
    elif strategy == "SRPT":
        order = Policy_SRPT.SRPT(current_demand, current_duration, capacity)
    elif strategy == "FCFS":
        order = [i for i in range(len(current_demand[0]))]
    elif strategy == "FLOW":
        order, job_transit= Policy_MinFlow.max_flow_ortools(current_demand, current_duration, current_datasize, capacity,
                                               bandwidth)  # , forecast_threshold
    elif strategy == "heuristic":
        order, job_transit = Policy_Heuristic.heuristic(current_demand, current_duration, current_datasize, capacity, bandwidth)
    elif strategy == "GEODIS":
        order, job_transit = Policy_GEODIS.GEODIS(current_demand, current_duration, current_datasize,
                                                                     capacity,
                                                                     bandwidth)
    else:
        print("Unknown Strategy. Take default as FCFS")
        order = [i for i in range(len(current_demand[0]))]
    duration = time.perf_counter() - start_time
    # num_late += cur_late
    if job_transit:
        transmission_list = transfer_transit(order, job_transit, wait_list, current_datasize, bandwidth,
                                             current_time)
    return order, transmission_list, duration

def compute_threshold(total_job_queue):
    interval_array = []
    last_arrival_time = 0
    first = True
    for total_job in total_job_queue:
        if first:
            last_arrival_time = total_job.arrival_time
            first = False
        else:
            interval = total_job.arrival_time - last_arrival_time
            if interval != 0:
                interval_array.append(interval)
                last_arrival_time = total_job.arrival_time
    # print(interval_array)
    return max(interval_array) + 1

def transfer_transit(job_order, job_transmission, wait_list, job_datasize, bandwidth, current_time):
    num_jobs = len(job_order)
    num_sites = len(wait_list)
    transmission_cost = [[0 for _ in range(num_sites)] for _ in range(num_sites)]
    transmission_list = [Transmission_queue() for _ in range(num_sites)]

    for i in range(num_jobs):
        # Process i-th job in the order
        unit_transit = job_datasize[job_order[i]] / bandwidth
        for j in range(num_sites):
            for k in range(num_sites):
                if j != k:
                    allocated = 0
                    while allocated < job_transmission[i][j][k]:
                        duration = wait_list[j][job_order[i]].task_duration_queue.popleft()
                        wait_list[j][job_order[i]].num_waiting_task -= 1
                        event = Event_Transmission(job_order[i], j, k, transmission_cost[j][k] + current_time,
                                                   unit_transit, duration)
                        transmission_list[k].add_event(event)
                        transmission_cost[j][k] += unit_transit
                        allocated += 1
    return transmission_list


def release_transmission(total_wait_list, wait_list, transmission_list, current_time):
    num_of_sites = len(wait_list)
    for i in range(num_of_sites):
        while transmission_list[i].queue:
            # check if the transmission event is due
            temp_event = transmission_list[i].top_event()
            if temp_event.start_time + temp_event.transit_time <= current_time:
                wait_list[i][temp_event.job_index].num_waiting_task += 1
                total_wait_list[temp_event.job_index].num_transmission += 1
                wait_list[i][temp_event.job_index].task_duration_queue.append(temp_event.task_duration)
                transmission_list[i].pop_event()
            else:
                break
        # for j in range(num_of_sites):
        #     # update the transmission cost
        #     transmission_cost[i][j] = max(transmission_cost[i][j], current_time)


def retract_transmission(wait_list, transmission_list):
    for i in range(len(wait_list)):
        while transmission_list[i].queue:
            event = transmission_list[i].pop_event()
            wait_list[event.start_site][event.job_index].num_waiting_task += 1
            wait_list[event.start_site][event.job_index].task_duration_queue.append(event.task_duration)


# def write_standard_deviation(SD_stack, data_resource, strategy, num_of_sites, alpha, bandwidth, utility, job_number):
#     path_name = record_path("StandardDeviation", data_resource, strategy, num_of_sites, alpha, utility, bandwidth)
#     with open(path_name, 'w', newline='') as csv_file:
#         writer = csv.writer(csv_file)
#         average_jrt = 0  # Job Response Time (JRT) sum
#         while SD_stack:
#             SD_event = SD_stack.pop()
#             row = [SD_event.SD, SD_event.enter_time, SD_event.release_time]
#             writer.writerow(row)


def write_job_completion_time(finish_list, data_resource, strategy, num_of_sites, alpha, bandwidth, utility,
                              job_number, start_index, site_capacity):
    path_name = record_path("CompletionTime", data_resource, strategy, num_of_sites, alpha, utility, bandwidth, start_index, site_capacity, job_number)
    # Writing to the CSV file
    with open(path_name, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        average_jrt = 0  # Job Response Time (JRT) sum

        while finish_list:
            finished_job = finish_list.pop()
            job_id = finished_job.Job_ID
            num_task = finished_job.num_task
            total_duration = finished_job.total_duration
            arrival_time = finished_job.arrival_time
            finish_time = finished_job.finish_time
            response_time = finish_time - arrival_time
            num_trans = finished_job.num_transmission
            distribution = finished_job.distribution

            # Build row with job details
            row = [job_id, num_task, total_duration, arrival_time, finish_time, response_time, num_trans] + distribution
            writer.writerow(row)
            # average_jrt += response_time


def write_computation_time(time_list, data_resource, strategy, num_of_sites, alpha, bandwidth, utility,
                              job_number, start_index, site_capacity):
    path_name = record_path("ComputationTime", data_resource, strategy, num_of_sites, alpha, utility, bandwidth, start_index, site_capacity, job_number)
    # Writing to the CSV file
    with open(path_name, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)

        while time_list:
            temp_time = time_list.pop()
            writer.writerow([temp_time])
            # average_jrt += job_duration

def record_path(record_type, data_resource, strategy, num_of_sites, alpha, load, bandwidth, start_index, site_capacity, job_number):
    if strategy.startswith("L") or strategy.startswith("h") or strategy.startswith("G") :
        return f"result_{record_type}/{data_resource}_{strategy}_site={num_of_sites}_slot={site_capacity}_alpha={alpha}_load={load}_start={start_index}_num={job_number}_B={bandwidth}.csv"  #
    else:
        return f"result_{record_type}/{data_resource}_{strategy}_site={num_of_sites}_slot={site_capacity}_alpha={alpha}_load={load}_start={start_index}_num={job_number}.csv"  #


def find_hungry_job(job_list, allocation):
    # Initially set the first job as the most "hungry"
    hungry_job = job_list[0]
    hunger_ratio = float('inf')

    for index, temp_job in enumerate(job_list):
        if temp_job.num_waiting_task > 0:
            temp_ratio = float('inf') - 1 if allocation[index] == 0 else temp_job.num_performing_task / abs(
                allocation[index])
            if temp_ratio < hunger_ratio:
                hungry_job = temp_job
                hunger_ratio = temp_ratio
    return hungry_job


def record_info(num_of_sites, wait_list):
    # Create a 2D list (matrix) to hold the current demand for each site
    # current_demand = [[0] * len(wait_list[0])] * num_of_sites
    current_demand = [[0 for _ in range(len(wait_list[i]))] for i in range(num_of_sites)]
    current_duration = [0 for _ in range(len(wait_list[0]))]
    current_datasize = [0 for _ in range(len(wait_list[0]))]
    for i in range(num_of_sites):
        for index, temp_job in enumerate(wait_list[i]):
            current_demand[i][index] = temp_job.num_waiting_task
    return current_demand


def record_demand_2(num_of_sites, wait_list):
    # this time use precise workload rather than regard all as 1
    # Create a 2D list (matrix) to hold the current demand for each site
    current_demand = [[0 for _ in range(len(wait_list[i]))] for i in range(num_of_sites)]
    for i in range(num_of_sites):
        for index, temp_job in enumerate(wait_list[i]):
            demand = sum(temp_job.task_duration_queue)
            current_demand[i][index] = demand
    return current_demand


def update_time_and_demand(transmission_queue, wait_list, current_demand, current_bandwidth, current_time):
    num_of_sites = len(current_demand)
    num_of_jobs = len(current_demand[0])
    temp_duration_queue = [deque() for _ in range(num_of_jobs)]  # Use deque for efficient pop operations
    bandwidth_used = [0 for i in range(num_of_sites)]

    # Decrease demand
    for i in range(num_of_sites):
        index = 0
        bandwidth_used[i] = 0

        for job in wait_list[i]:
            difference = job.num_waiting_task - current_demand[i][index]
            if difference > 0:
                # Demand decrease, move out
                bandwidth_used[i] += difference
                current_bandwidth[i] -= difference
                job.num_waiting_task = current_demand[i][index]
                for _ in range(difference):
                    temp_duration_queue[index].append(job.task_duration_queue.popleft())
            index += 1

    # Increase demand
    for i in range(num_of_sites):
        index = 0
        for job in wait_list[i]:
            difference = job.num_waiting_task - current_demand[i][index]
            if difference < 0:
                difference = -difference  # Make it positive
                # Demand increase, move in
                bandwidth_used[i] += difference
                current_bandwidth[i] -= difference
                job.num_waiting_task = current_demand[i][index]
                for _ in range(difference):
                    job.task_duration_queue.append(temp_duration_queue[index].popleft())
            index += 1

        if bandwidth_used[i] != 0:
            temp_event = Event_Transmission(bandwidth_used[i], current_time)  # Ensure this class is defined
            transmission_queue[i].append(temp_event)
            # Debugging output can be added if necessary
            # print(f"site {i} uses {bandwidth_used[i]} bandwidth.")


def remove_total_job(total_wait_list, wait_list, finish_list, aggregate_job_index, current_time):
    # Get the aggregate job from the total wait list
    aggregate_job = total_wait_list[aggregate_job_index]
    aggregate_job.finish_time = current_time

    # Find the job index in the first site's wait list
    job_index = find_job_index(wait_list[0], aggregate_job.Job_ID)

    # Remove the job from all wait lists
    for local_list in wait_list:
        del local_list[job_index]
        # jobs.remove(job_index)  # Use pop() to remove by index

    # Add the completed job to the finish list
    finish_list.append(aggregate_job)  # Assuming finish_list is a queue

    # Remove the aggregate job from the total wait list
    del total_wait_list[aggregate_job_index]


def find_aggregate_job_index(total_wait_list, job_id):
    i = -1
    for i in range(len(total_wait_list)):
        if total_wait_list[i].Job_ID == job_id:
            return i
    assert i == -1, "No matching job for the event of job " + job_id


def find_job_index(jobs, job_id):
    for i in range(len(jobs)):
        if jobs[i].Job_ID == job_id:
            return i
    return -1


def find_job(job_list, job_id):
    for job in job_list:
        if job.Job_ID == job_id:
            return job
    return None


def add_job(current_job, total_wait_list, wait_list):
    total_wait_list.append(current_job)
    # Add all sub-jobs to all sites
    for i in range(len(wait_list)):
        temp_job = Job()
        temp_job.Job_ID = current_job.Job_ID
        temp_job.arrival_time = current_job.arrival_time
        temp_job.num_waiting_task = current_job.distribution[i]
        temp_job.num_performing_task = 0
        temp_job.data_size = current_job.data_size
        while len(temp_job.task_duration_queue) < temp_job.num_waiting_task:
            temp_job.task_duration_queue.append(current_job.task_duration_queue.pop())
        sorted(temp_job.task_duration_queue, reverse=True)
        wait_list[i].append(temp_job)

    # q = sorted(current_job.task_duration_queue, reverse=True)[:temp_job.num_waiting_task]


def find_earliest_event(event_heapq_list):
    earliest_event = None
    min_time = float('inf')
    # Iterate over each priority queue in the list
    for current_pq in event_heapq_list:
        if current_pq and current_pq[0].release_time < min_time:
            # Peek at the top element (the one with the earliest release_time)
            earliest_event = current_pq[0]
            min_time = current_pq[0].release_time

    return earliest_event

def find_earliest_transmission(transmission_list):
    num_site = len(transmission_list)
    cur_time = sys.maxsize
    for i in range(num_site):
        if not transmission_list[i].empty():
            cur_time = min(cur_time, transmission_list[i].top_event().start_time + transmission_list[i].top_event().transit_time)
    return cur_time


def read_jobs(file_name, job_number, start_index, num_of_sites, workload_threshold, workload):
    # workload[0]: system workload
    # [1]: average task duration
    total_job_queue = []
    file_path = f"data_processed/{file_name}.csv"
    try:
        with open(file_path, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            first_arrival_time = 0.0
            temp_index = 0
            for row in csvreader:
                arrival_time = int(float(row[1]))
                num_task = int(row[2])
                total_duration = float(row[3])
                data_size = int(float(row[4]))

                # Filter large jobs
                if temp_index < start_index:  # or (total_duration / num_task) > workload_threshold:
                    temp_index += 1
                    continue
                if not total_job_queue:
                    first_arrival_time = int(float(row[1]))

                temp_job = Job_Total()  # Create Job_Total object
                temp_job.Job_ID = f"{temp_index}"
                temp_job.arrival_time = round((arrival_time - first_arrival_time) * workload[0],
                                              2) # Adjust arrival time
                temp_job.num_task = num_task
                temp_job.total_duration = total_duration
                temp_job.data_size = data_size
                temp_job.distribution = [int(row[i + 5]) for i in range(num_of_sites)]
                for i in range(num_of_sites + 5, len(row)):
                    temp_job.task_duration_queue.append(float(row[i]))

                total_job_queue.append(temp_job)
                temp_index += 1
                if len(total_job_queue) >= job_number:
                    break
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return total_job_queue


def compute_workload(file_name, job_num, start_index, capacity, threshold):
    # workload[0]: system workload
    # [1]: average task duration
    workload = [0, 0]
    # Calculate total capacity
    total_capacity = sum(capacity)
    try:
        # Read the pre-processed file
        file_path = f"data_processed/{file_name}.csv"

        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            temp_index = 0
            last_arrival_time = 0
            first_arrival_time = 0
            num_total_tasks = 0

            for row in reader:
                if temp_index >= job_num + start_index:
                    break

                total_duration = float(row[3])
                num_task = int(row[2])

                # Skip jobs that are too large or before the start index
                if temp_index < start_index: #or (total_duration / num_task) > threshold
                    temp_index += 1
                    continue

                if temp_index == start_index:
                    first_arrival_time = float(row[1])

                num_total_tasks += num_task
                workload[0] += total_duration

                if temp_index == (job_num + start_index - 1):
                    last_arrival_time = float(row[1])

                temp_index += 1

            # Calculate the workload metrics
            workload[1] = workload[0] / num_total_tasks
            workload[0] /= ((last_arrival_time - first_arrival_time) * total_capacity)

            print(f"Workload = {workload[0]}")
            print(f"Per task duration = {workload[1]}")
            print(first_arrival_time, last_arrival_time)

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

    return workload


def compute_sum_JRT(demand_matrix, order):
    times = show_finish_time(demand_matrix, order)
    return sum(times)


def show_finish_time(demand_matrix, order):
    num_of_sites = demand_matrix.shape[0]
    num_of_jobs = demand_matrix.shape[1]
    step_site_allocation = np.zeros(num_of_sites, dtype=int)
    finish_time = np.zeros(num_of_jobs, dtype=int)

    for i in range(num_of_jobs):
        temp = 0
        for j in range(num_of_sites):
            step_site_allocation[j] += demand_matrix[j][order[i]]
            temp = max(temp, step_site_allocation[j])
        finish_time[order[i]] = temp

    return finish_time


def copy_matrix(demand_matrix):
    return np.copy(demand_matrix)


def format_number(value):
    return f"{value:.2f}"


def is_empty(A: list[deque]) -> bool:
    if not A:
        return True
    for queue in A:
        if queue:
            return False
    return True


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
