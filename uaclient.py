#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
from uaserver import rtp
import hashlib
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

def password(passwd, nonce):
    m = hashlib.md5()
    m.update(bytes(passwd, 'utf-8'))
    m.update(bytes(nonce, 'utf-8'))
    return m.hexdigest()

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
    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError:
        sys.exit("Usage: python proxy_registrar.py config")
    CONFIGURACION = uHandler.get_tags()

    IP_PROXY = CONFIGURACION['regproxy_ip']
    PORT_PROXY = int(CONFIGURACION['regproxy_puerto'])
    LOG_PATH = CONFIGURACION['log_path']
    ADRESS = CONFIGURACION['account_username']
    PUERTO = CONFIGURACION['uaserver_puerto']
    PASSWD = CONFIGURACION['account_passwd']
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP_PROXY,PORT_PROXY))

        log("Starting...", LOG_PATH)
        if METODO == 'REGISTER':
            LINEA = (METODO + ' sip:' + ADRESS + ':' + PUERTO +
                    ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n\r\n')
        elif METODO == 'INVITE':
            LINEA = (METODO + ' sip:' + OPCION + ' SIP/2.0\r\n' +
                    'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                    'o=' + ADRESS + ' ' + IP + '\r\n' + 's=misesion\r\n' +
                    'm=audio ' + str(PORT_AUDIO) + ' RTP' + '\r\n\r\n')
        elif METODO == 'BYE':
            LINEA = METODO + ' sip:' + OPCION + 'SIP/2.0\r\n\r\n'
        elif METODO != ('REGISTER', 'INVITE', 'ACK', 'BYE'):
            ERROR = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
        else:
            ERROR = "SIP/2.0 400 Bad Request\r\n\r\n"

        if not LINEA
            self.wfile.write(bytes(error, 'utf-8'))
            print('mandamos al cliente: ', error)
            ERROR = ERROR.replace("\r\n", " ")
            log('Error: ' + error, LOG_PATH)
        else:
            self.wfile.write(bytes(LINEA, 'utf-8'))
            print('mandamos al Proxy: ', LINEA)
            LINEA = LINEA.replace("\r\n", " ")
            log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' + LINEA, LOG_PATH)

        try:
            DATA = my_socket.recv(1024)
        except ConnectionRefusedError:
            log("Error: No server listening at " + SERVER_PROXY +
                " port " + str(PORT_PROXY), LOG_PATH)

        RECB = DATA.decode('utf-8')
        MENS = RECB.replace("\r\n", " ")
        log('Received from ' + SERVER_PROXY + ':' + str(PORT_PROXY) + ': ' + MENS, LOG_PATH)

        RECB_LIST = RECB.split()
        if RECB_LIST[1] == '401':
            NONCE_RECV = RECB_LIST[6].split('"')[1]
            NONCE = password(PASSWD, NONCE_RECV)
            LINEA = (METODO + ' sip:' + ADRESS + ':' + PUERTO +
                    ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n' +
                    'Authorization: Digest response="' + NONCE + '"' +
                    '\r\n\r\n')
            my_socket.send(bytes(LINEA, 'utf-8'))
            print('Enviamos al Proxy:\r\n', LINEA)
            LINEA = LINEA.replace("\r\n", " ")
            log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' + LINEA, LOG_PATH)
            DATA = my_socket.recv(1024)
            RECB = DATA.decode('utf-8')
            print('Recibo del Proxy:\r\n', RECB)
            MENS = RECB.replace("\r\n", " ")
            log('Received from ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' + MENS, LOG_PATH)
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
        else RECB_LIST[1] == '200':
            LINEA = 'Finishing.'

        if LINE:
            my_socket.send(bytes(LINEA, 'utf-8'))
            print(LINEA)
            LINEA = LINEA.replace("\r\n", " ")
            log('Sent to ' + SERVER_PROXY + ':' + str(PORT_PROXY) + ': ' + LINEA, LOG_PATH)
