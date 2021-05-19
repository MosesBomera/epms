import time
from smbus2 import SMBus
from mlx90614 import MLX90614


# Initiate bus
bus = SMBus(1)
sensor = MLX90614(bus, address=0x5A)

# Time initialization
seconds = time.time()
local_time = time.ctime(seconds)


# Get temperature reading

temp = sensor.get_object_1()

# Write the values to the file.
with open("/home/pi/Desktop/epms/logs/temperature.log", "w+") as f:
    f.write(f"Timestamp: {local_time}  Temp: {temp}\n")

# Close the bus
bus.close()

