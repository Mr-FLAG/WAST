import heapq


class Event:
    Event_ID = ""

    def __init__(self, Job_ID, enter_time, task_duration):
        self.Job_ID = Job_ID
        self.enter_time = enter_time
        self.release_time = enter_time + task_duration

    def __lt__(self, job):
        return self.release_time < job.release_time


class Event_Transmission(Event):
    def __init__(self, job_index: int, start_site: int, dest_site: int, start_time: float, transit_time: float,
                 task_duration: float):
        self.job_index = job_index
        self.start_site = start_site
        self.dest_site = dest_site
        self.start_time = start_time
        self.transit_time = transit_time
        self.task_duration = task_duration
        # self.transmission_duration = arrival_time - start_time

    def __lt__(self, event):
        return self.start_time + self.transit_time < event.start_time + event.transit_time

    def __repr__(self):
        return f"({self.job_index}, {self.start_site}, {self.dest_site},  {self.start_time + self.transit_time})"


class Transmission_queue:
    def __init__(self):
        self.queue = []

    def add_event(self, event: Event_Transmission):
        heapq.heappush(self.queue, event)

    def pop_event(self):
        return heapq.heappop(self.queue) if self.queue else None

    def top_event(self):
        return self.queue[0]

    def length(self):
        return len(self.queue)

    def empty(self):
        return len(self.queue) == 0

    def __repr__(self):
        # Representation of the queue for debugging
        return f"Transmission ({self.queue})"


class Event_StandardDeviation(Event):
    SD = 0.0

    def __init__(self, SD, enter_time):
        self.SD = SD
        self.enter_time = enter_time
