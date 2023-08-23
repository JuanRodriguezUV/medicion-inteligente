import time, machine, network, gc, app.secrets as secrets
from app.ota_updater import OTAUpdater

wlan = network.WLAN(network.STA_IF) # create station interface
wlan.active(True)       # activate the interface

def connectToWifiAndUpdate():
    
    time.sleep(1)
    print('Memory free', gc.mem_free())
    
    k=0 #Contador de intentos de reconexión WiFi
    
    try:
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
                wlan.connect('Familia Rodriguez', '16670397') # connect to an AP
                
            time.sleep(1)
            
        print('Conexión establecida!')
        
        if not wlan.isconnected():      # check if the station is connected to an AP
            connectToWifiAndUpdate()

        #Importante que el repositorio tenga releases y cofiguras las versiones. #Dejando main_dir='' se accede a la carpeta general del repositorio si se desea acceder a una carpeta en específio se escribe en este parametro
        otaUpdater = OTAUpdater('https://github.com/JuanRodriguezUV/medicion-inteligente', main_dir='app', secrets_file="secrets.py")
        hasUpdated = otaUpdater.install_update_if_available()
        
        if hasUpdated:
            machine.reset()
        else:
            del(otaUpdater)
            gc.collect()
            print('Memory free', gc.mem_free())
            
    except Exception:
        print("Ha habido una excepción")
        time.sleep_ms(5000) #Garantizamos un tiempo par que los medidores enciendan con normalidad 
        connectToWifiAndUpdate()
        
def startApp():
    import app.TG
    
connectToWifiAndUpdate()
startApp()
    

            
            