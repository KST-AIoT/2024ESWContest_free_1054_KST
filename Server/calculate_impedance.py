import numpy as np
import cmath
from scipy.optimize import curve_fit

def calculate_impedance(frequency, v_0, v_1, resistance, sampling_time):
    # numpy 배열로 변환
    np_v_0 = np.array(v_0, dtype=np.float64)
    np_v_1 = np.array(v_1, dtype=np.float64)

    # 시간 축 생성
    total_time = len(np_v_0) * sampling_time
    time_axis_0 = np.arange(0, total_time, sampling_time)
    time_axis_1 = np.arange(0, total_time, sampling_time) + sampling_time / 2

    # 정현파 함수 정의
    def cos_wave(t, A, phi):
        return A * np.cos(2 * np.pi * frequency / 1000000 * t + phi)

    # curve_fit을 사용하여 데이터에 맞는 파라미터 찾기
    params_0, _ = curve_fit(cos_wave, time_axis_0, np_v_0)
    params_1, _ = curve_fit(cos_wave, time_axis_1, np_v_1)

    # 파라미터 조정
    if params_0[0] < 0:
        params_0[0] *= -1
        params_0[1] = params_0[1] + np.pi if params_0[1] < 0 else params_0[1] - np.pi

    if params_1[0] < 0:
        params_1[0] *= -1
        params_1[1] = params_1[1] + np.pi if params_1[1] < 0 else params_1[1] - np.pi

    # 각도 조정
    params_0[1] = np.deg2rad(np.rad2deg(params_0[1]) % 360)
    params_1[1] = np.deg2rad(np.rad2deg(params_1[1]) % 360)

    # 복소수 형태의 전압 계산
    source_v = cmath.rect(params_0[0], params_0[1])
    water_v = cmath.rect(params_1[0], params_1[1])
    resi_v = source_v - water_v

    # 회로 전류 계산
    circuit_cur = resi_v / resistance

    # 임피던스 계산
    water_z = water_v / circuit_cur

    # 임피던스의 크기와 위상 각
    water_z_polar = cmath.polar(water_z)
    magnitude = water_z_polar[0]
    phase = np.rad2deg(water_z_polar[1])

    # 출력 결과
    return magnitude, phase
'''
# 예시 사용
frequency = 100
v_0 = [1.0, 2.0, 3.0, 4.0]  # 실제 데이터로 대체
v_1 = [1.1, 2.1, 3.1, 4.1]  # 실제 데이터로 대체
resistance = 10  # 저항값
sampling_time = 1000  # 마이크로세컨드 단위

result = calculate_impedance(frequency, v_0, v_1, resistance, sampling_time)
print(result)
'''