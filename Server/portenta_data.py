import json
from calculate_impedance import calculate_impedance 
from datetime import datetime


#[0번째 , 1번째, , ...,]
class portenta_data:
    def __init__(self, req_time, req_type, frequencies):
        self.req_time = req_time
        self.req_type = req_type
        self.frequencies_list = set(frequencies) #주파수 목록
        self.frequencies = []
        self.v_0 = []
        self.v_1 = []
        self.temperatures = []
        self.resistances = []
        self.times = []
        self.last_edit_time = datetime.now()
    def add_data(self, frequency, v_0, v_1, temperature, resistance, time):
        if frequency in self.frequencies_list:
            self.frequencies_list.remove(frequency)
            self.frequencies.append(frequency)
            self.v_0.append(v_0)
            self.v_1.append(v_1)
            self.temperatures.append(temperature)
            self.resistances.append(103.3) #todo: 저항값 변환하기
            #self.resistances.append(resistance)
            self.times.append(time)
            self.last_edit_time = datetime.now()

        if not self.frequencies_list:  # frequencies_list가 비어있으면 모든 데이터를 받은 것
            return self.frequencies, self.v_0, self.v_1, self.temperatures, self.resistances, self.times #raw 데이터 반환
        return None
    def process_data(self):
        magnitude_list = []
        phase_list = []
        source_voltage_list = [] 
        water_voltage_list = []
        resistance_voltage_list = []
        circuit_current_list = []
        for i in range(len(self.frequencies)):
            magnitude, phase, source_voltage, water_voltage, resistance_voltage, circuit_current = calculate_impedance(self.frequencies[i], self.v_0[i], self.v_1[i], self.resistances[i], self.times[i])
            magnitude_list.append(magnitude)
            phase_list.append(phase)
            source_voltage_list.append(source_voltage)
            water_voltage_list.append(water_voltage)
            resistance_voltage_list.append(resistance_voltage)
            circuit_current_list.append(circuit_current)
        return magnitude_list, phase_list, source_voltage_list, water_voltage_list, resistance_voltage_list, circuit_current_list
