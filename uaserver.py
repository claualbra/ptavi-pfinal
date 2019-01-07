#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
import os
# Constantes. Dirección IP del servidor, puerto, clase de petcion,
# direccion y tiemp de expiracion

def log(Mensaje):
    fich.write(time.strftime('%Y%m%d%H%M%S '))
    fich.write(Mensaje+"\r\n")

class Ua2Handler(ContentHandler):
    def __init__(self):
        self.diccionario= {}
        self.dicc_ua1xml = {'account': ['username', 'passwd'],
                        'uaserver': ['ip', 'puerto'], 'rtpaudio': ['puerto'],
                        'regproxy': ['ip', 'puerto'],
                        'log': ['path'], 'audio': ['path']}
    def startElement(self, name, attrs):
        diccionario = {}
        if name in self.dicc_ua1xml:
            for atributo in self.dicc_ua1xml[name]:
                self.diccionario[name+'_'+atributo] = attrs.get(atributo, '')

    def get_tags(self):
        return self.diccionario
def rtp(ip,port):
    # aEjecutar es un string
    # con lo que se ha de ejecutar en la shell
    aEjecutar = 'mp32rtp -i ' ip ' -p ' port '<' + AUDIO_PATH
    print("Vamos a ejecutar", aEjecutar)
    os.system(aEjecutar)

class EchoHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""

    def handle(self):
        """Escribe dirección y puerto del cliente."""
        Ip_client = str(self.client_address[0])
        Port_client = str(self.client_address[1])

        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            linea = line.decode('utf-8')
            linea_recb = linea.replace("\r\n", " ")
            log('Received from ' + Ip_client + ':' +
                Port_client + ': ' + linea_recb)
            print("El cliente nos manda ", linea)

            line = linea.split()
            if line[0] == 'INVITE':
                client_ip = line[6].split(' ')[0].split('=')[1]
                client_port = line[6].split(' ')[1]
                mensaje =('SIP/2.0 100 Trying\r\n\r\n' +
                        'SIP/2.0 180 Ringing\r\n\r\n' +
                        'SIP/2.0 200 OK\r\n' +
                        'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                        'o=' + ADRESS + ' ' + IP + '\r\n' + 's=misesion\r\n' +
                        'm=audio ' + str(PORT_AUDIO) + ' RTP' + '\r\n\r\n')
            if line[0] == 'ACK':
                self.rtp(client_ip, client_port)
            self.wfile.write(bytes(mensaje, 'utf-8'))
            print('mandamos al cliente: ', linea_send)
            mensaje = mensaje.replace("\r\n", " ")
            log('Sent to ' + Ip_client + ':' + Port_client + ': ' + mensaje)

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python uaserver.py config")

    parser = make_parser() #lee linea a linea y busca etiquetas, generico para xml
    u2Handler = Ua2Handler() #Hace cosas dependiendo de la etiqueta
    parser.setContentHandler(u2Handler)
    parser.parse(open(CONFIG))
    CONFIGURACION = u2Handler.get_tags()

    PORT_AUDIO = int(CONFIGURACION['rtpaudio_puerto'])
    LOG_PATH = CONFIGURACION['log_path']
    PUERTO = int(CONFIGURACION['uaserver_puerto'])
    IP = CONFIGURACION['uaserver_ip']
    AUDIO_PATH = CONFIGURACION['audio_path']

    fich = open(LOG_PATH, "a")

    serv = socketserver.UDPServer((IP, PUERTO), EchoHandler)
    print('Listening...')

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.")
