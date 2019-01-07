#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
from uaserver.py import rtp
# Constantes. Dirección IP del servidor, puerto, clase de petcion,
# direccion y tiemp de expiracion

class Ua1Handler(ContentHandler):
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

def log(mensaje, log_path):
    fich = open(log_path, "a")
    fich.write(time.strftime('%Y%m%d%H%M%S '))
    fich.write(mensaje+"\r\n")
    fich.close()

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
        METODO = sys.argv[2]
        OPCION = sys.argv[3]
    except IndexError:
        sys.exit("Usage: python uaclient.py config method option")

    parser = make_parser() #lee linea a linea y busca etiquetas, generico para xml
    uHandler = Ua1Handler() #Hace cosas dependiendo de la etiqueta
    parser.setContentHandler(uHandler)
    parser.parse(open(CONFIG))
    CONFIGURACION = uHandler.get_tags()

    SERVER_PROXY = CONFIGURACION['regproxy_ip']
    PORT_PROXY = int(CONFIGURACION['regproxy_puerto'])
    PORT_AUDIO = int(CONFIGURACION['rtpaudio_puerto'])
    LOG_PATH = CONFIGURACION['log_path']
    ADRESS = CONFIGURACION['account_username']
    PUERTO = CONFIGURACION['uaserver_puerto']
    IP = CONFIGURACION['uaserver_ip']

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((SERVER_PROXY,PORT_PROXY))

        log("Starting...", LOG_PATH)
        if METODO == 'REGISTER':
            LINEA = (METODO + ' sip:' + ADRESS + ':' + PUERTO +
                    ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n\r\n')
        if METODO == 'INVITE':
            LINEA = (METODO + ' sip:' + OPCION + ' SIP/2.0\r\n' +
                    'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                    'o=' + ADRESS + ' ' + IP + '\r\n' + 's=misesion\r\n' +
                    'm=audio ' + str(PORT_AUDIO) + ' RTP' + '\r\n\r\n')
        if METODO == 'BYE':
            LINEA = METODO + ' sip:' + OPCION + 'SIP/2.0\r\n\r\n'

        my_socket.send(bytes(LINEA, 'utf-8'))
        print(LINEA)
        LINEA = LINEA.replace("\r\n", " ")
        log('Sent to ' + SERVER_PROXY + ':' + str(PORT_PROXY) + ': ' + LINEA, LOG_PATH)

        try:
            DATA = my_socket.recv(1024)
        except ConnectionRefusedError:
            log("Error: No server listening at " + SERVER_PROXY +
                " port " + str(PORT_PROXY), LOG_PATH)

        RECB = DATA.decode('utf-8')
        MENS = RECB.replace("\r\n", " ")
        log('Received from ' + SERVER_PROXY + ':' + str(PORT_PROXY) + ': ' + MENS, LOG_PATH)

        RECB_LIST = RECB.split()
        print(RECB_LIST)
        if RECB_LIST[1] == '401':
            LINEA = (METODO + ' sip:' + ADRESS + ':' + PUERTO +
                    ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n' +
                    'Authorization: Digest response="123123212312321212123' +
                    '\r\n\r\n')
        elif RECB_LIST[1] == '100' and RECB_LIST[4] == '180' and RECB_LIST[7] == '200':
            IP_SERVER = RECB_LIST[7]
            PORT_SERVER = RECB_LIST[10]
            LINEA = 'ACK sip:' + OPCION + ' SIP/2.0\r\n\r\n'
            self.rtp(IP_SERVER, PORT_SERVER)
        elif RECB_LIST[1] == '405':
            log("Error: " + RECB, LOG_PATH)
        elif RECB_LIST[1] == '400':
            log("Error: " + RECB, LOG_PATH)
        elif RECB_LIST[1] == '404':
            log("Error: " + RECB, LOG_PATH)
        else:
            pass

        my_socket.send(bytes(LINEA, 'utf-8'))
        print(LINEA)
        LINEA = LINEA.replace("\r\n", " ")
        log('Sent to ' + SERVER_PROXY + ':' + str(PORT_PROXY) + ': ' + LINEA, LOG_PATH)
        fich.close()
