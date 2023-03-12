import os

basedir = os.path.abspath(os.path.dirname(__file__))
SPO2_PATH = os.path.join(basedir, 'logs', 'sp02.txt')

def measureSp02():
    response = {
        "status": False,
        "value": "An error occured, Try again"
    }

    from .libs import max30102
    from .libs import hrcalc
    from time import sleep

    m = max30102.MAX30102();
    spo2 = 0
    spo2_sum = 0
    counter = 0 
    m.reset()
    m.setup()

    fingerAttached = False
    for i in range(200): 
        ir, red = m.read_fifo();

    for i in range(2): #check for 3 seconds for finger attachment 
        ir, red = m.read_fifo();
        if(ir > 40000 and red >40000):
            fingerAttached = True
            break
        else:
            sleep(1)


    if(fingerAttached): # procced if finger attached      
        for i in range(10):
            red, ir = m.read_sequential(100)
            data = hrcalc.calc_hr_and_spo2(ir, red)
            if (data[3] == True):
                if(data[2] > 90):
                    spo2_sum += data[2]
                    counter += 1
                    
        m.shutdown()               
        try:            
            spo2 =  spo2_sum / counter
            print(spo2)
            with open(SPO2_PATH, "w") as f:
                f.write(str(spo2))

            response = {
                "status": True,
                "value": spo2
            }
        except ZeroDivisionError:
            print("!Sensor Error")
            response = {
                "status": False,
                "value": "Sensor Error"
            }
    else:
        print("Please Attach Finger")
        response = {
            "status": False,
            "value": "Please Attach Finger"
        }

    return response
