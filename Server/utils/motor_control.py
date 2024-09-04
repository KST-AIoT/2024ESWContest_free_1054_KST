def motor_control(estimate_ppm, target_ppm={"N": 400, "P": 100, "K": 200}):
    '''
    이 함수는 estimate_ppm과 target_ppm 값을 비교하여 모터를 제어하는 기능을 합니다.

    각 성분(N, P, K)의 추정값이 목표 값보다 작을 경우, 부족한 만큼 모터를 가동하여 ppm을 보충합니다.
    100ppm 당 모터가 1초 동안 가동되며, 총 가동 시간을 반환합니다.

    추후 양액의 총량 등을 고려한 메타데이터가 필요할 수 있음.

    :param estimate_ppm: 현재 추정된 ppm 값(질소, 인, 칼륨의 농도)
    :param target_ppm: 목표 ppm 값으로, 각 성분의 목표 농도
        - N: 질산칼슘 (Nitrate Calcium) - 기본값: 400 ppm
        - P: 제이인산암모늄 (Diammonium Phosphate) - 기본값: 100 ppm
        - K: 황산칼륨 (Potassium Sulfate) - 기본값: 200 ppm
    :return: 각 성분에 대해 모터가 작동할 시간(초) 값을 담은 딕셔너리
    '''

    # 각 성분에 대한 모터 가동 시간 (초)
    motor_runtime = {"N": 0, "P": 0, "K": 0}

    # N (질산칼슘) 모터 가동 시간 계산
    if estimate_ppm["N"] < target_ppm["N"]:
        deficit_n = target_ppm["N"] - estimate_ppm["N"]
        motor_runtime["N"] = deficit_n / 100  # 100ppm 당 1초

    # P (제이인산암모늄) 모터 가동 시간 계산
    if estimate_ppm["P"] < target_ppm["P"]:
        deficit_p = target_ppm["P"] - estimate_ppm["P"]
        motor_runtime["P"] = deficit_p / 100  # 100ppm 당 1초

    # K (황산칼륨) 모터 가동 시간 계산
    if estimate_ppm["K"] < target_ppm["K"]:
        deficit_k = target_ppm["K"] - estimate_ppm["K"]
        motor_runtime["K"] = deficit_k / 100  # 100ppm 당 1초

    # 모터 가동 시간을 반환
    return motor_runtime


