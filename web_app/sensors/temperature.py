def measureTemperature():
    from smbus2 import SMBus
    from mlx90614 import MLX90614

    # Define ambient temperature compensation parameters
    TAMB = 25.0 # Reference ambient temperature (°C)
    ACOMP = -0.025 # Temperature compensation coefficient

    # Define voltage compensation parameters
    VOLTAGE_REF = 3.3  # Reference voltage (V)
    VOLTAGE_GAIN = 0.6 # Voltage gain of amplifier

    bus = SMBus(1)
    sensor = MLX90614(bus, address=0x5A)

    # # Read ambient temperature data
    # ta_c = round(sensor.get_amb_temp() - 273.15, 2)
    # # Read object temperature data and apply voltage compensation
    # to_c = round(sensor.get_obj_temp()-(VOLTAGE_REF-3)*VOLTAGE_GAIN  ,2)
    # #to_c = round((sensor.get_obj_temp() - VOLTAGE_REF) / VOLTAGE_GAIN - ACOMP * (ta_c - TAMB), 2)

    Tavrg = 0
    samples = 100
    calibFactor = 1.63
    for i in range(samples):
        Tavrg = Tavrg + (sensor.get_obj_temp() + calibFactor) 
        
    temp = Tavrg/samples
    print(temp)

    with open("/home/epms/EPMS/EpmsApp/logs/temperature.txt", "w") as f:
        f.write(str(temp))

    bus.close()

    return temp
