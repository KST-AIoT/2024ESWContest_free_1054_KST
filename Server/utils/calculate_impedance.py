import numpy as np
import pandas as pd
import cmath
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt



def calculate_impedance(frequency, v_0, v_1, resistance, sampling_time, visualize=False, plot_filename=None):
    # 초반 50개 데이터 제거
    v_0 = v_0[50:]
    v_1 = v_1[50:]

    np_v_0 = np.array(v_0, dtype=np.float64)
    np_v_1 = np.array(v_1, dtype=np.float64)

    # 시간 축 생성
    num_samples = len(np_v_0)
    total_time = sampling_time
    delta_time = total_time / num_samples
    time_axis_0 = np.linspace(0, total_time - delta_time, num_samples)
    time_axis_1 = time_axis_0 + delta_time / 2

    def cos_wave(t, A, phi):
        t = np.array(t, dtype=np.float64)
        A = np.float64(A)
        phi = np.float64(phi)
        return A * np.cos(2 * np.pi * frequency / 1000000 * t + phi)

    # Bias 제거
    bias_0 = np.mean(np_v_0)
    bias_1 = np.mean(np_v_1)
    np_v_0_detrended = np_v_0 - bias_0
    np_v_1_detrended = np_v_1 - bias_1

    # 10주기까지만 데이터 자르기
    period = 1e6 / frequency
    max_time = 10 * period
    mask_0 = time_axis_0 <= max_time
    mask_1 = time_axis_1 <= max_time

    min_elements = 120
    # mask 길이 확인 및 조정
    if np.sum(mask_0) < min_elements:
        additional_time = (min_elements - np.sum(mask_0)) * delta_time
        mask_0 = time_axis_0 <= (max_time + additional_time)

    if np.sum(mask_1) < min_elements:
        additional_time = (min_elements - np.sum(mask_1)) * delta_time
        mask_1 = time_axis_1 <= (max_time + additional_time)

    time_axis_0_trimmed = time_axis_0[mask_0]
    time_axis_1_trimmed = time_axis_1[mask_1]
    np_v_0_trimmed = np_v_0_detrended[mask_0]
    np_v_1_trimmed = np_v_1_detrended[mask_1]

    # curve_fit을 사용하여 코사인 파형에 맞게 회귀 수행
    params_0, _ = curve_fit(cos_wave, time_axis_0_trimmed, np_v_0_trimmed)
    params_1, _ = curve_fit(cos_wave, time_axis_1_trimmed, np_v_1_trimmed)

    if params_0[0] < 0:
        params_0[0] *= -1
        params_0[1] += np.pi if params_0[1] < 0 else -np.pi

    if params_1[0] < 0:
        params_1[0] *= -1
        params_1[1] += np.pi if params_1[1] < 0 else -np.pi

    params_0[1] = np.deg2rad(np.rad2deg(params_0[1]) % 360)
    params_1[1] = np.deg2rad(np.rad2deg(params_1[1]) % 360)

    # 복소수 형태로 전압 계산
    source_voltage = cmath.rect(params_0[0], params_0[1])
    water_voltage = cmath.rect(params_1[0], params_1[1])
    resistance_voltage = source_voltage - water_voltage

    # 회로 전류 계산 (저항이 주어진 경우)
    circuit_current = resistance_voltage / resistance

    # 임피던스 계산 (물의 임피던스)
    water_impedance = water_voltage / circuit_current

    # 크기와 위상 각을 구한 후, 위상 조정
    def to_magnitude_phase(complex_value, reference_phase=0):
        magnitude, phase = cmath.polar(complex_value)
        phase = np.rad2deg(phase) - reference_phase
        return magnitude, phase % 360

    # 모든 전압을 기준 위상으로 조정
    source_voltage_mag, source_voltage_phase = to_magnitude_phase(source_voltage)
    water_voltage_mag, water_voltage_phase = to_magnitude_phase(water_voltage, source_voltage_phase)
    resistance_voltage_mag, resistance_voltage_phase = to_magnitude_phase(resistance_voltage, source_voltage_phase)
    circuit_current_mag, circuit_current_phase = to_magnitude_phase(circuit_current, source_voltage_phase)
    water_impedance_mag, water_impedance_phase = to_magnitude_phase(water_impedance)

    # 최종적으로 source_voltage의 phase는 0이 됩니다.
    source_voltage = (source_voltage_mag, 0)
    water_voltage = (water_voltage_mag, water_voltage_phase)
    resistance_voltage = (resistance_voltage_mag, resistance_voltage_phase)
    circuit_current = (circuit_current_mag, circuit_current_phase)

    # 시각화 (옵션)
    if visualize:
        sampled_time_0, sampled_fitted_v_0 = sample_points_for_fitted_curve(time_axis_0_trimmed, cos_wave(time_axis_0_trimmed, params_0[0], params_0[1]) + bias_0)
        sampled_time_1, sampled_fitted_v_1 = sample_points_for_fitted_curve(time_axis_1_trimmed, cos_wave(time_axis_1_trimmed, params_1[0], params_1[1]) + bias_1)

        plt.figure(figsize=(10, 6))
        plt.plot(time_axis_0_trimmed, np_v_0_trimmed + bias_0, label='Raw v_0', marker='o')
        plt.plot(sampled_time_0, sampled_fitted_v_0, label='Fitted v_0 (with bias)', linestyle='--', marker='x')
        plt.plot(time_axis_1_trimmed, np_v_1_trimmed + bias_1, label='Raw v_1', marker='o')
        plt.plot(sampled_time_1, sampled_fitted_v_1, label='Fitted v_1 (with bias)', linestyle='--', marker='x')
        plt.xlabel('Time (microseconds)')
        plt.ylabel('Voltage')
        plt.title(f'Voltage vs Time (Frequency: {frequency} Hz)')
        plt.legend()
        plt.grid(True)

        if plot_filename:
            plt.savefig(plot_filename)
        plt.show()

    # 임피던스의 크기와 위상 각 반환
    return water_impedance_mag, water_impedance_phase, source_voltage, water_voltage, resistance_voltage, circuit_current

def trim_to_cycles(time_axis, signal, frequency, cycles=10):
    period = 1e6 / frequency
    max_time = cycles * period
    mask = time_axis <= max_time
    trimmed_time_axis = time_axis[mask]
    trimmed_signal = np.array(signal)[:len(trimmed_time_axis)]
    return trimmed_time_axis, trimmed_signal

def calculate_time_axis(sampling_time, num_samples):
    delta_time = sampling_time / num_samples
    return np.linspace(0, sampling_time - delta_time, num_samples)

def sample_points_for_fitted_curve(time_axis, fitted_curve, num_points=1000):
    sampled_time = np.linspace(time_axis[0], time_axis[-1], num_points)
    sampled_curve = np.interp(sampled_time, time_axis, fitted_curve)
    return sampled_time, sampled_curve