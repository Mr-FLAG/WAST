from collections import deque
from queue import PriorityQueue
import Event

class Job:
    def __init__(self):
        self.Job_ID = 0
        self.arrival_time = 0.0
        self.num_waiting_task = 0  # Tasks that are waiting to get a slot to operate
        self.num_performing_task = 0  # Tasks that are operating in the slots
        self.finish_time = 0.0
        self.task_duration_queue = deque()  # Queue to store task durations
        self.data_size = 0.0
        # self.finished = False


class Job_Total(Job):
    def __init__(self, Job_ID=None, arrival_time=0.0, num_task=0, task_duration_time=0.0, distribution=None):
        super().__init__()  # Inherit properties from Job class
        self.num_task = num_task
        self.num_finished_task = 0
        self.total_duration = 0.0
        self.finish_time = 0.0
        self.distribution = distribution if distribution is not None else []
        self.data_size = 0.0
        self.num_transmission = 0
        # self.datasize = 0.0
        
        if Job_ID is not None:
            self.Job_ID = Job_ID
            self.arrival_time = arrival_time
            self.task_duration_time = task_duration_time

    def __hash__(self):
        # Hashing based on Job_ID to ensure unique identification
        return hash(self.Job_ID)

    def __lt__(self, other):
        # This defines the less-than operation for comparison (used for heapq or sorting)
        return self.arrival_time < other.arrival_time

    def __eq__(self, other):
        # Equality comparison based on Job_ID
        return self.Job_ID == other.Job_ID

    def __repr__(self):
        # For a cleaner print output
        return f"Job_Total(Job_ID={self.Job_ID}, arrival_time={self.arrival_time})"