class Time:
    def __init__(self,time,step):
        self.time = time
        self.step = step
    def __str__(self):
        string = 'time: '+str(self.time)+' step: '+str(self.step)
        return string