import numpy as np
import cvxpy as cp
# from Strategy_Bandwidth import Use_bandwidth
import sys
import math

def main():
    print('SRPT')
    
def SRPT(demand_matrix, job_duration, capacity):
    num_of_sites = len(demand_matrix)
    num_of_jobs = len(demand_matrix[0])
    order = [0 for i in range(num_of_jobs)]#np.zeros(num_of_jobs, dtype=int)
    job_sorted = np.zeros(num_of_jobs, dtype=bool)
    largest_subjob = [0 for i in range(num_of_jobs)]
    for i in range(num_of_sites):
        for j in range(num_of_jobs):
            largest_subjob[j] = max(math.ceil(demand_matrix[i][j]/capacity[i])*job_duration[j], largest_subjob[j])
    for i in range(num_of_jobs):
        order[i] = find_min(largest_subjob, job_sorted)
        job_sorted[order[i]] = True
    return order

# def SRPT_T(demand_matrix, bandwidth):
#     SRPT_order = SRPT(demand_matrix)
#     return Use_bandwidth(demand_matrix, SRPT_order, bandwidth)


def find_min(largest_subjob, sorted):
    num_of_jobs = len(sorted)
    index = 0
    temp_subjob = sys.maxsize
    for i in range(num_of_jobs):
        if not sorted[i] and largest_subjob[i] < temp_subjob:
            index = i
            temp_subjob = largest_subjob[i]
    return index
    

if __name__ == "__main__":
    main()