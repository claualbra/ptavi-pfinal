#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
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

def log(Mensaje):
    fich.write(time.strftime('%Y%m%d%H%M%S '))
    fich.write(Mensaje+"\r\n")


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

        fich = open(LOG_PATH, "a")
        LINEA = ''

        if METODO == 'REGISTER':
            log("Starting...")
            LINEA = (METODO + ' sip:' + ADRESS + ':' + PUERTO +
                    ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n\r\n')
        if METODO == 'INVITE':
            LINEA = (METODO + ' sip:' + OPCION + ' SIP/2.0\r\n' +
                    'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                    'o=' + ADRESS + ' ' + IP + '\r\n' + 's=misesion\r\n' +
                    'm=audio ' + str(PORT_AUDIO) + ' RTP' + '\r\n\r\n')

        my_socket.send(bytes(LINEA, 'utf-8'))
        print(LINEA)
        LINEA = LINEA.replace("\r\n", " ")
        log('Sent to ' + SERVER_PROXY + ':' + str(PORT_PROXY) + ': ' + LINEA)

        try:
            DATA = my_socket.recv(1024)
        except ConnectionRefusedError:
            log("Error: No server listening at " + SERVER_PROXY +
                " port " + str(PORT_PROXY))

        RECB = DATA.decode('utf-8')
        MENS = RECB.replace("\r\n", " ")
        log('Received from ' + SERVER_PROXY + ':' + str(PORT_PROXY) + ': ' + MENS)

        RECB_LIST = RECB.split()
        print(RECB_LIST)
        if RECB_LIST[1] == '401':
            LINEA = (METODO + ' sip:' + ADRESS + ':' + PUERTO +
                    ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n' +
                    'Authorization: Digest response="123123212312321212123' +
                    '\r\n\r\n')
        elif RECB_LIST[1] == '100' and RECB_LIST[4] == '180' and RECB_LIST[7] == '200':
            LINEA = 'ACK sip:' + OPCION + ' SIP/2.0\r\n\r\n'
            
        my_socket.send(bytes(LINEA, 'utf-8'))
        print(LINEA)
        LINEA = LINEA.replace("\r\n", " ")
        log('Sent to ' + SERVER_PROXY + ':' + str(PORT_PROXY) + ': ' + LINEA)
        fich.close()
