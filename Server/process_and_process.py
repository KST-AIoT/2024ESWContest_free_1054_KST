from AI_Model.LinearRegression.predict_model import predict_lr
from calculate_impedance import calculate_impedance


def process_and_predict(temperatures, frequencies, v_0, v_1, times, resistances):
    #데이터 변환
    magnitude_list = []
    phase_list = []
    for i in range(len(frequencies)):
        magnitude, phase = calculate_impedance(frequencies[i], v_0[i], v_1[i], resistances[i], times[i])
        magnitude_list.append(magnitude)
        phase_list.append(phase)
    #예측 수행 : 선형회귀 -> 오류 발생. 데이터 형식 바꿔줘야함
    return predict_lr(frequencies, phase_list, magnitude_list, temperatures)

