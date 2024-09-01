import json
from calculate_impedance import calculate_impedance 



#[0번째 , 1번째, , ...,]
class portenta_data:
    def __init__(self, request_time, request_type, frequencies):
        self.request_time = request_time
        self.reqeust_type = request_type
        self.frequencies_list = set(frequencies) #주파수 목록
        self.frequencies = []
        self.v_0 = []
        self.v_1 = []
        self.temperatures = []
        self.resistances = []
        self.times = []
    def add_data(self, frequency, v_0, v_1, temperature, resistance, time):
        if frequency in self.frequencies_list:
            self.frequencies_list.remove(frequency)
            self.frequencies.append(frequency)
            self.v_0.append(v_0)
            self.v_1.append(v_1)
            self.temperatures.append(temperature)
            self.resistances.append(resistance)
            self.times.append(time)

        if not self.frequencies_list:  # frequencies_list가 비어있으면 모든 데이터를 받은 것
            return self.frequencies, self.v_0, self.v_1, self.temperatures, self.resistances, self.times #raw 데이터 반환
        return None
    def proceess_data(self):
        magnitude_list = []
        phase_list = []
        for i in range(len(self.frequencies)):
            magnitude, phase = calculate_impedance(self.frequencies[i], self.v_0[i], self.v_1[i], self.resistances[i], times[i])
            magnitude_list.append(magnitude)
            phase_list.append(phase)
        return magnitude_list, phase_list
