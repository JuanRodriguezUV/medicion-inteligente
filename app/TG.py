# import LCD
from LCD.ili934xnew import ILI9341, color565
from machine import Pin, SPI, RTC
import LCD
import LCD.m5stack
import LCD.tt14
import LCD.glcdfont
import LCD.tt14
import LCD.tt24
import LCD.tt32

#import connection
import urequests
import network
import json

# import logging
import machine
import struct
import time
import modbus
import modbus.defines as cst
from modbus import modbus_rtu

wlan = network.WLAN(network.STA_IF) # create station interface
wlan.active(True)       # activate the interface

#wifiList = wlan.scan()             # scan for access points
#print('Redes disponibles-----------------------------------------------------------------')
#for item in wifiList:
#    print('Red:' + str(item[0]) + ' Canal :' + str(item[2]) + ' Señal: ' + str(item[3]) )
#print('----------------------------------------------------------------------------------')



def wifiConncect():
    
    k=0 #Contador de intentos de reconexión WiFi
    
    while not wlan.isconnected():
        print('Conectando...')
        print(wlan.status())
        k=k+1
        print(k)
        if k>= 30:
            machine.reset()
        
        if wlan.status() == 1001:
            pass
        else:            
            wlan.connect('medidor_inteligente', '16670397') # connect to an AP
            
        time.sleep(1)
        
    print('Conexión establecida!')
    
if not wlan.isconnected():      # check if the station is connected to an AP
    wifiConncect()
    
#Configuración tipo de letra y encendido LCD
pin_cts = machine.Pin(21, machine.Pin.OUT)
fonts = [LCD.tt32]
power = Pin(LCD.m5stack.TFT_LED_PIN, Pin.OUT)
power.value(1)

#Configuración comunicación LCD SPI
spi = SPI(
    2,
    baudrate=40000000,
    miso=Pin(LCD.m5stack.TFT_MISO_PIN),
    mosi=Pin(LCD.m5stack.TFT_MOSI_PIN),
    sck=Pin(LCD.m5stack.TFT_CLK_PIN))

#Configuración pines y dimensiones LCD
display = ILI9341(
    spi,
    cs=Pin(LCD.m5stack.TFT_CS_PIN),
    dc=Pin(LCD.m5stack.TFT_DC_PIN),
    rst=Pin(LCD.m5stack.TFT_RST_PIN),
    w=240,
    h=320,
    r=6)

display.erase() #Borrar lo que tenga escrito la LCD
display.set_font(LCD.tt32) #Determinar tipo de letra


rtc = RTC() #Variable de reloj

def serial_prep(mode):
    if mode == modbus_rtu.serial_cb_tx_begin:
        # print("Begin Tx")
        # SP485E IC needs CTS high to allow transmit
        pin_cts.value(1)

    elif mode == modbus_rtu.serial_cb_tx_end:
        # print("End Tx")
        # Once Tx is done, switch back to allowing receive
        pin_cts.value(0)

    elif mode == modbus_rtu.serial_cb_rx_begin:
        # print("Begin Rx")
        # Probably already in Rx mode, but just in case
        pin_cts.value(0)

    elif mode == modbus_rtu.serial_cb_rx_end:
        # print("End Rx")
        pin_cts.value(0)

    else:
        raise ValueError("Given 'mode' does not have a defined action")


#Función para juntar los H bits y Low bits luego usar IEEE754 para tener los binarios en coma flotante
def bin_to_float(num1,num2): 
    bits= (num1 << 16) + num2
    s = struct.pack('>l', bits)
    valor_float = struct.unpack('>f', s)[0]
    return valor_float



def main():
    pin_cts.value(0)

    #Configuración puerto de comuniaciones UART
    # En el ESP32 se están usando los pines Rx=16 y Tx=17, los cuales son puertos UART 2
    # Parity None, 0 (even) or 1 (odd)
    # Baudrate: 9600 (default)
    # Bits = 8 (default)
    # Bits de parada = 1
    print("Opening UART 2")
    uart = machine.UART(2, 9600, bits=8, parity=None,
                        stop=1, timeout=1000, timeout_char=50)

    # master = modbus_rtu.RtuMaster(uart)
    master = modbus_rtu.RtuMaster(uart, serial_prep_cb=serial_prep)

    # print("Reading from register 0x00")
    # 'execute' returns a pair of 16-bit words
    
main()

while True:
    
    try:
        
        #################### HORA Y FECHA ############################

        url_fecha="http://worldtimeapi.org/api/timezone/America/Bogota"

        response_fecha = urequests.get(url_fecha)

        datos_objeto = response_fecha.json()
        fecha_hora = str(datos_objeto["datetime"])
        año = int(fecha_hora[0:4])
        mes = int(fecha_hora[5:7])
        día = int(fecha_hora[8:10])
        hora = int(fecha_hora[11:13])
        minutos = int(fecha_hora[14:16])
        segundos = int(fecha_hora[17:19])
        sub_segundos = int(round(int(fecha_hora[20:26]) / 10000))

        rtc.datetime((año, mes, día, 0, hora, minutos, segundos, sub_segundos))

        print("Fecha:{2:02d}/{1:02d}/{0:4d}".format(*rtc.datetime()))
        print("Hora: {4:02d}:{5:02d}:{6:02d}".format(*rtc.datetime()))

        ######################### FIN #############################

        display.set_color(60000,0) #Configuración de impresión LCD
        display.set_pos(5,20)

        #MEDIDOR 1 TOMZ HIKING

        #Voltaje
        data1 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x16, 1)
        print("Voltaje:{} [V],".format(data1[0]*0.1))
        voltaje_LCD = str(data1[0]*0.1)
        display.print('Voltaje= {} [V]    '.format(voltaje_LCD))

        display.set_color(10000,0)
        display.set_pos(5,60)

        #Frecuencia
        data2 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x11, 1)
        print("Frecuencia={} [Hz]".format(data2[0]*0.01))
        frecuencia_LCD = str(data2[0]*0.01)
        display.print("Frecuencia= {} [Hz]    ".format(frecuencia_LCD))

        display.set_color(20000,0)
        display.set_pos(5,100)

        #Corriente
        data3 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x19, 1)
        corriente=data3[0]*0.01
        print("Corriente={} [A]".format(corriente))
        corriente_LCD = str(corriente)
        display.print("Corriente= {} [A]    ".format(corriente_LCD))

        display.set_color(1500,0)
        display.set_pos(5,140)

        #Factor de potencia
        data4 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x2B, 1)
        fp = data4[0]*0.001
        print("Factor potencia={:.3}".format(fp))
        Fp_LCD = str(fp)
        display.print("Factor potencia= {:.3}    ".format(fp))

        display.set_color(2300,0)
        display.set_pos(5,180)

        ##Potencia activa
        data5 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x1E, 1)
        P = data5[0]*0.001
        print("P Activa={:.4} [kW]".format(P))
        P_LCD = str(P)
        display.print("P Activa= {:.4} [W]  ".format(P))
        
        ##Total kWh
        data11 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x01, 2)
        Total_kWh = data11[0]*0.01
        print("Total kWh={:.4} [kWh]".format(Total_kWh))
        
        ##Potencia reactiva
        data12 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x0D, 2)
        P_reactiva = data12[0]*0.01
        print("Potencia reactiva={:.4} [kVArh]".format(P_reactiva))
        
        ##Export kWh
        data13 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x09, 2)
        Export_kWh= data13[0]*0.01
        print("Potencia activa exportada={:.4} [kWh]".format(Export_kWh))
        
        ##Import kWh
        data14 = master.execute(1, cst.READ_HOLDING_REGISTERS, 0x0B, 2)
        Import_kWh= data14[0]*0.01
        print("Potencia activa importada={:.4} [kWh]".format(Import_kWh))
        
        #MEDIDOR 2 EASTRON SDM360-MODBUS
        
        #Voltaje
        data6 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x00, 2)
        voltaje_2 = bin_to_float(data6[0],data6[1]) 
        print("Voltaje 2:{} [V],".format(voltaje_2))

        #Frecuencia
        data7 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x46, 2)
        frecuencia_2 = bin_to_float(data7[0],data7[1])
        print("Frecuencia 2={} [Hz]".format(frecuencia_2))

        #Corriente
        data8 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x06, 2)
        corriente_2= bin_to_float(data8[0],data8[1])
        print("Corriente 2={} [A]".format(corriente_2))

        #Factor de potencia
        data9 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x3E, 2)
        fp_2 = bin_to_float(data9[0],data9[1])
        print("Factor potencia 2={:.3}".format(fp_2))

        #Potencia activa
        data10 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x0C, 2)
        P2 = bin_to_float(data10[0],data10[1])
        P2 = P2*0.001
        print("P Activa 2={:.4} [kW]".format(P2))
        
        ##Total system power 2
        data15 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x34, 2)
        Total_system_power = bin_to_float(data15[0],data15[1])
        Total_system_power = Total_system_power*0.001
        print("Total system power 2={:.4} [kW]".format(Total_system_power))
        
        ##Total system volt amps 2
        data16 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x38, 2)
        Total_system_volt_amps = bin_to_float(data16[0],data16[1])
        Total_system_volt_amps = Total_system_volt_amps*0.001
        print("Total system volt amps 2={:.4} [kVA]".format(Total_system_volt_amps))
        
        ##Total system VAr 2
        data17 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x3C, 2)
        Total_system_VAr = bin_to_float(data17[0],data17[1])
        Total_system_VAr = Total_system_VAr*0.001
        print("Total system VAr 2={:.4} [kVAr]".format(Total_system_VAr))
        
        ##Import Wh since last reset 2
        data18 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x48, 2)
        Import_Wh_since_last_reset = bin_to_float(data18[0],data18[1])
        Import_Wh_since_last_reset = Import_Wh_since_last_reset
        print("Import Wh since last reset 2={:.4} [kWh/MWh]".format(Import_Wh_since_last_reset))
        
        ##Export Wh since last reset 2
        data19 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x4A, 2)
        Export_Wh_since_last_reset = bin_to_float(data19[0],data19[1])
        Export_Wh_since_last_reset = Export_Wh_since_last_reset
        print("Export Wh since last reset 2={:.4} [kWh/MWh]".format(Export_Wh_since_last_reset))
        
        ##Import VArh since last reset 2
        data20 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x4C, 2)
        Import_VArh_since_last_reset = bin_to_float(data20[0],data20[1])
        Import_VArh_since_last_reset = Import_VArh_since_last_reset
        print("Import VArh since last reset ={:.4} [kVArh/MVArh]".format(Import_VArh_since_last_reset))
        
        ##Export VArh since last reset 2
        data21 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x4E, 2)
        Export_VArh_since_last_reset = bin_to_float(data21[0],data21[1])
        Export_VArh_since_last_reset = Export_VArh_since_last_reset
        print("Export VArh since last reset 2={:.4} [kVArh/MVArh]".format(Export_VArh_since_last_reset))
        
        ##VAh since last reset 2
        data22 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x50, 2)
        VAh_since_last_reset = bin_to_float(data22[0],data22[1])
        VAh_since_last_reset = VAh_since_last_reset
        print("VAh since last reset 2={:.4} [kVArh/MVArh]".format(VAh_since_last_reset))
        
        ##Ah since last reset 2
        data23 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x52, 2)
        Ah_since_last_reset = bin_to_float(data23[0],data23[1])
        Ah_since_last_reset = Ah_since_last_reset
        print("Ah since last reset 2={:.4} [Ah/kAh]".format(Ah_since_last_reset))
        
        ##Total system power demand 2
        data24 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x54, 2)
        Total_system_power_demand = bin_to_float(data24[0],data24[1])
        Total_system_power_demand = Total_system_power_demand *0.001
        print("Total system power demand 2={:.4} [kW]".format(Total_system_power_demand))
        
        ##Maximum total system power demand 2
        data25 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x56, 2)
        Maximum_total_system_power_demand = bin_to_float(data25[0],data25[1])
        Maximum_total_system_power_demand = Maximum_total_system_power_demand *0.001
        print("Maximum total system power demand 2={:.4} [kW]".format(Maximum_total_system_power_demand))
        
        ##Total system VA demand 2
        data26 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x64, 2)
        Total_system_VA_demand = bin_to_float(data26[0],data26[1])
        Total_system_VA_demand = Total_system_VA_demand *0.001
        print("Total system VA demand 2={:.4} [kVA]".format(Total_system_VA_demand))
        
        ##Maximum total system VA demand 2
        data27 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x66, 2)
        Maximum_total_system_VA_demand = bin_to_float(data27[0],data27[1])
        Maximum_total_system_VA_demand = Maximum_total_system_VA_demand *0.001
        print("Maximum total system VA demand 2={:.4} [kVA]".format(Maximum_total_system_VA_demand))
        
        ##Total active energy 2
        data28 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x156, 2)
        Total_active_energy = bin_to_float(data28[0],data28[1])
        Total_active_energy = Total_active_energy 
        print("Total active energy 2={:.4} [kWh]".format(Total_active_energy))
        
        ##Total reactive energy 2
        data29 = master.execute(2, cst.READ_INPUT_REGISTERS, 0x158, 2)
        Total_reactive_energy = bin_to_float(data29[0],data29[1])
        Total_reactive_energy = Total_reactive_energy 
        print("Total reactive energy 2={:.4} [kVarh]".format(Total_reactive_energy))
        

        #FIN MEDIDAS

        #URLS envío de información bases de datos
        #url = "http://192.168.137.1/uRequestESP32/uRequest.php" #Base de datos local medidor 1 mysql phpmyadmin
        url2 ="https://us-east-1.aws.data.mongodb-api.com/app/data-vipwg/endpoint/data/v1/action/insertOne" #Base datos nube MONGOdb
        #url3 = "http://192.168.137.1/uRequestESP32/uRequest2.php" #Base de datos local medidor 2 mysql phpmyadmin

        #Diccionario medidor1
        data = {
        "voltaje [V]": data1[0]*0.1,
        "frecuencia [Hz]": data2[0]*0.01,
        "corriente [A]": data3[0]*0.01,
        "factor_potencia": data4[0]*0.001, 
        "p_activa [kW]": data5[0]*0.001,
        
        "Total_kWh [kWh]": data11[0]*0.01,
        "p_reactiva [kVArh]": data12[0]*0.01,
        "p_activa_exportada [kWh]": data13[0]*0.01,
        "p_activa_importada [kWh]": data14[0]*0.01,
        
        "fecha": "{2:02d}/{1:02d}/{0:4d}".format(*rtc.datetime()),
        "hora": "{4:02d}:{5:02d}:{6:02d}".format(*rtc.datetime())
        }

        #Diccionario medidor2
        data2 = {
        "voltaje [V]": voltaje_2,
        "frecuencia [Hz]": frecuencia_2,
        "corriente [A]": corriente_2,
        "factor_potencia": fp_2, 
        "p_activa [kW]": P2,
        
        "Total system power [KW]": Total_system_power,
        "Total system volt amps [kVA]": Total_system_volt_amps,
        "Total system VAr [kVAr]": Total_system_VAr,
        "Import Wh last reset [kWh/MWh]": Import_Wh_since_last_reset,
        "Export Wh last reset [kWh/MWh]": Export_Wh_since_last_reset,
        "Import VArh last reset [kVArh/MVArh]": Import_VArh_since_last_reset,
        "Export VArh last reset [kVArh/MVArh]": Export_VArh_since_last_reset,
        "VAh since reset [kVArh/MVArh]": VAh_since_last_reset,
        "Ah since last reset [Ah/kAh]": Ah_since_last_reset,
        "Total system power demand [kW]": Total_system_power_demand,
        "Maximum total system power demand [kW]": Maximum_total_system_power_demand,
        "Total system VA demand [kVA]": Total_system_VA_demand,
        "Maximum total system VA demand [kVA]": Maximum_total_system_VA_demand,
        "Total active energy [kWh]": Total_active_energy,
        "Total reactive energy [kVarh]": Total_reactive_energy,
        
        "fecha": "{2:02d}/{1:02d}/{0:4d}".format(*rtc.datetime()),
        "hora": "{4:02d}:{5:02d}:{6:02d}".format(*rtc.datetime())
        }

        #Headers
        headers = {'Content-Type': 'application/json'}
        headers2 = { "api-key": "er39p9Z5TD0C9KBksJh3UrQ2UwuJPZ3M2fneDa5rwtABvnnnOE4Kbs40mqCBBsgZ" } #Api MONGOdb

        #Payload MONGOdb: base de datos medidorInteligente - colección medidor 1
        insertPayload = {
        "dataSource": "Cluster0",
        "database": "medidorInteligente",
        "collection": "medidor1",
        "document": data,
        }

        #Payload MONGOdb: base de datos medidorInteligente - colección medidor 2
        insertPayload2 = {
        "dataSource": "Cluster0",
        "database": "medidorInteligente",
        "collection": "medidor2",
        "document": data2,
        }

        #Envío de información 
        #response  = urequests.post(url, json=data, headers=headers)
        #print(response.content)

        response2 = urequests.post(url2, json=insertPayload, headers=headers2)
        print(response2.content)

        #response3 = urequests.post(url3, json=data2, headers=headers)
        #print(response3.content)

        response4 = urequests.post(url2, json=insertPayload2, headers=headers2)
        print(response4.content)

        #Tiempo de envío entre cada medida
        #time.sleep_ms(3600000) #1 hora
        time.sleep_ms(4000)

    except Exception:
        print("Ha habido una excepción")
        time.sleep_ms(5000) #Garantizamos un tiempo par que los medidores enciendan con normalidad 
        wifiConncect()




#Posibles mejoras:
#contar numero de excepciones y cuales son
    
    
    
