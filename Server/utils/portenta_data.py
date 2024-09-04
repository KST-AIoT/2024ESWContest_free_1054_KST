import json
import calculate_impedance 
from datetime import datetime

'''
    Portenta 데이터를 관리하는 클래스.
    주파수별로 v_0, v_1, 온도, 저항 등의 데이터를 수집하고 처리
'''
class portenta_data:
    def __init__(self, req_time, req_type, frequencies):
        self.req_time = req_time                    # MQTT요청 시간
        self.req_type = req_type                    # 요청 유형
        self.frequencies_list = set(frequencies)    # 전체 주파수 목록
        self.frequencies = []                       # 처리된 주파수 목록
        self.v_0 = []                               # 전압 v_0 리스트
        self.v_1 = []                               # 전압 v_1 리스트
        self.temperatures = []                      # 온도
        self.resistances = []                       # 저항값
        self.times = []                             # 시간
        self.last_edit_time = datetime.now()        # 마지막 수정 시간
    def add_data(self, frequency, v_0, v_1, temperature, resistance, time):
        '''
        수집된 데이터를 객체에 추가. 모든 주파수에 대한 데이터를 다 수집하면 None이 아닌 데이터를 반환
        '''
        if frequency in self.frequencies_list:
            self.frequencies_list.remove(frequency)
            self.frequencies.append(frequency)
            self.v_0.append(v_0)
            self.v_1.append(v_1)
            self.temperatures.append(temperature)
            self.resistances.append(resistance)
            self.times.append(time)
            self.last_edit_time = datetime.now()

        # 모든 주파수에 대해 데이터를 수집했으면 결과 반환
        if not self.frequencies_list:  
            return self.frequencies, self.v_0, self.v_1, self.temperatures, self.resistances, self.times #raw 데이터 반환
        return None # 아직 모든 데이터를 수집하지 않은 경우 None 반환
    def process_data(self):
        '''
        수집된 데이터를 처리하여 임피던스와 관련된 크기, 위상, 전압, 전류 등을 계산
        '''
        magnitude_list = []
        phase_list = []
        source_voltage_list = [] 
        water_voltage_list = []
        resistance_voltage_list = []
        circuit_current_list = []
        # 주파수별로 수집된 데이터를 바탕으로 임피던스를 계산
        for i in range(len(self.frequencies)):
            magnitude, phase, source_voltage, water_voltage, resistance_voltage, circuit_current = calculate_impedance(self.frequencies[i], self.v_0[i], self.v_1[i], self.resistances[i], self.times[i])
            magnitude_list.append(magnitude)
            phase_list.append(phase)
            source_voltage_list.append(source_voltage)
            water_voltage_list.append(water_voltage)
            resistance_voltage_list.append(resistance_voltage)
            circuit_current_list.append(circuit_current)
        return magnitude_list, phase_list, source_voltage_list, water_voltage_list, resistance_voltage_list, circuit_current_list
