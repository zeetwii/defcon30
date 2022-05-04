import math # needed for floor


def stepPayload(rotationAngle):

    stepAngle = 0.36 #1.8 * 14 / 70

    totalSteps = int(rotationAngle / stepAngle)

    print(f"totalSteps: {totalSteps}")

    payload = []
    payload.append(str(0))
    payload.append(str(0))

    for i in range(math.floor(totalSteps / 255)):
        payload.append(str(255))

    payload.append(str(totalSteps % 255))

    print(f"payload: {payload}")

    return payload


stepPayload(360)
