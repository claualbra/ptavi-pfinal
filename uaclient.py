#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa que activa la parte del cliente."""

import sys
import socket
import time
import hashlib
import os
import threading
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class Ua1Handler(ContentHandler):
    """Class Handler."""

    def __init__(self):
        """Inicializa los diccionarios."""
        self.diccionario = {}
        self.dicc_ua1xml = {'account': ['username', 'passwd'],
                            'uaserver': ['ip', 'puerto'],
                            'rtpaudio': ['puerto'],
                            'regproxy': ['ip', 'puerto'],
                            'log': ['path'], 'audio': ['path']}

    def startElement(self, name, attrs):
        """Crea el diccionario con los valores del fichero xml."""
        if name in self.dicc_ua1xml:
            for atributo in self.dicc_ua1xml[name]:
                self.diccionario[name+'_'+atributo] = attrs.get(atributo, '')

    def get_tags(self):
        """Devuelve el diccionario creado."""
        return self.diccionario


def log(mensaje, log_path):
    """Abre un fichero log para poder escribir en él."""
    fich = open(log_path, "a")
    fich.write(time.strftime('%Y%m%d%H%M%S '))
    fich.write(mensaje+"\r\n")
    fich.close()


def password(passwd, nonce):
    """Devuelve el nonce de respuesta."""
    m = hashlib.md5()
    m.update(bytes(passwd, 'utf-8'))
    m.update(bytes(nonce, 'utf-8'))
    return m.hexdigest()


def rtp(ip, port, audio):
    """Manda Audio RTP."""
    # aEjecutar es un string
    # con lo que se ha de ejecutar en la shell
    aejecutar = 'mp32rtp -i ' + ip + ' -p ' + port + ' < ' + audio
    cvlc = 'cvlc rtp://@' + ip + ':' + port
    hcvlc = threading.Thread(target=os.system(cvlc + '&'))
    hmp3 = threading.Thread(target=os.system(aejecutar))
    hcvlc.start()
    hmp3.start()
    return cvlc + aejecutar


if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
        METODO = sys.argv[2]
        OPCION = sys.argv[3]
    except IndexError:
        sys.exit("Usage: python uaclient.py config method option")

    parser = make_parser()
    uHandler = Ua1Handler()
    parser.setContentHandler(uHandler)
    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError:
        sys.exit("Usage: python proxy_registrar.py config")
    CONFIGURACION = uHandler.get_tags()

    # Sacamos los datos del fichero xml
    if CONFIGURACION['regproxy_ip'] == '':
        IP_PROXY = '127.0.0.1'
    else:
        IP_PROXY = CONFIGURACION['regproxy_ip']
    PORT_PROXY = int(CONFIGURACION['regproxy_puerto'])
    LOG_PATH = CONFIGURACION['log_path']
    ADRESS = CONFIGURACION['account_username']
    PUERTO = CONFIGURACION['uaserver_puerto']
    PASSWD = CONFIGURACION['account_passwd']
    if CONFIGURACION['uaserver_ip'] == '':
        IP = '127.0.0.1'
    else:
        IP = CONFIGURACION['uaserver_ip']
    PORT_AUDIO = int(CONFIGURACION['rtpaudio_puerto'])
    AUDIO_PATH = CONFIGURACION['audio_path']
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
    log("Starting...", LOG_PATH)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP_PROXY, PORT_PROXY))

        if METODO == 'REGISTER':
            LINEA = (METODO + ' sip:' + ADRESS + ':' + PUERTO +
                     ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n\r\n')
        elif METODO == 'INVITE':
            LINEA = (METODO + ' sip:' + OPCION + ' SIP/2.0\r\n' +
                     'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                     'o=' + ADRESS + ' ' + IP + '\r\n' + 's=misesion\r\n' +
                     'm=audio ' + str(PORT_AUDIO) + ' RTP' + '\r\n\r\n')
        elif METODO == 'BYE':
            LINEA = METODO + ' sip:' + OPCION + ' SIP/2.0\r\n\r\n'
        else:
            LINEA = METODO + ' sip:' + OPCION + ' SIP/2.0\r\n\r\n'

        my_socket.send(bytes(LINEA, 'utf-8'))
        print('Enviamos al Proxy:\r\n', LINEA)
        LINEA = LINEA.replace("\r\n", " ")
        log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
            LINEA, LOG_PATH)

        try:
            DATA = my_socket.recv(1024)
        except ConnectionRefusedError:
            sys.exit("Conexion fallida")
            log("Error: No server listening at " + SERVER_PROXY +
                " port " + str(PORT_PROXY), LOG_PATH)

        RECB = DATA.decode('utf-8')
        print('Recibo del Proxy:\r\n', RECB)
        MENS = RECB.replace("\r\n", " ")
        log('Received from ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
            MENS, LOG_PATH)

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
            log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
                LINEA, LOG_PATH)
            DATA = my_socket.recv(1024)
            RECB = DATA.decode('utf-8')
            print('Recibo del Proxy:\r\n', RECB)
            MENS = RECB.replace("\r\n", " ")
            log('Received from ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
                MENS, LOG_PATH)
        elif (RECB_LIST[1] == '100' and RECB_LIST[4] == '180' and
              RECB_LIST[7] == '200'):
            IP_SERVER = RECB_LIST[16]
            PORT_RTP = RECB_LIST[19]
            LINEA = 'ACK sip:' + OPCION + ' SIP/2.0\r\n\r\n'
            my_socket.send(bytes(LINEA, 'utf-8'))
            print('Enviamos al Proxy:\r\n', LINEA)
            LINEA = LINEA.replace("\r\n", " ")
            log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
                LINEA, LOG_PATH)
            print(IP_SERVER)
            LINEA = rtp(IP_SERVER, PORT_RTP, AUDIO_PATH)
            log('Sent to ' + IP_SERVER + ':' + PORT_RTP + ': ' +
                LINEA, LOG_PATH)
        elif RECB_LIST[1] == '404':
            log("Error: " + RECB, LOG_PATH)
        elif RECB_LIST[1] == '405':
            log("Error: " + RECB, LOG_PATH)
        elif RECB_LIST[1] == '400':
            log("Error: " + RECB, LOG_PATH)

        log('Finishing.', LOG_PATH)
