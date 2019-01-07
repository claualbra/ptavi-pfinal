#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import Ua1Handler, log
import time
import os
# Constantes. Dirección IP del servidor, puerto, clase de petcion,
# direccion y tiemp de expiracion

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
                Port_client + ': ' + linea_recb, LOG_PATH)
            print("El cliente nos manda ", linea)

            line = linea.split()
            if line[0] == 'INVITE':
                client_ip = line[7]
                rtp_port = line[10]
                mensaje =('SIP/2.0 100 Trying\r\n\r\n' +
                        'SIP/2.0 180 Ringing\r\n\r\n' +
                        'SIP/2.0 200 OK\r\n' +
                        'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                        'o=' + ADRESS + ' ' + IP + '\r\n' + 's=misesion\r\n' +
                        'm=audio ' + str(PORT_AUDIO) + ' RTP' + '\r\n\r\n')
            elif line[0] == 'ACK':
                self.rtp(client_ip, client_port)
            elif line[0] == 'BYE':
                mensaje = 'SIP/2.0 200 OK\r\n\r\n'
            elif line[0] != ('REGISTER', 'INVITE', 'ACK', 'BYE'):
                error = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
            else:
                error = "SIP/2.0 400 Bad Request\r\n\r\n"
            if not mensaje:
                self.wfile.write(bytes(error, 'utf-8'))
                print('mandamos al cliente: ', error)
                error = error.replace("\r\n", " ")
                log('Error: ' + error, LOG_PATH)
            else:
                self.wfile.write(bytes(mensaje, 'utf-8'))
                print('mandamos al cliente: ', linea_send)
                mensaje = mensaje.replace("\r\n", " ")
                log('Sent to ' + Ip_client + ':' + rtp_port + ': ' + mensaje, LOG_PATH)

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python uaserver.py config")

    parser = make_parser() #lee linea a linea y busca etiquetas, generico para xml
    u2Handler = Ua1Handler() #Hace cosas dependiendo de la etiqueta
    parser.setContentHandler(u2Handler)
    parser.parse(open(CONFIG))
    CONFIGURACION = u2Handler.get_tags()

    PORT_AUDIO = int(CONFIGURACION['rtpaudio_puerto'])
    LOG_PATH = CONFIGURACION['log_path']
    PUERTO = int(CONFIGURACION['uaserver_puerto'])
    IP = CONFIGURACION['uaserver_ip']
    AUDIO_PATH = CONFIGURACION['audio_path']
    ADRESSS = CONFIGURACION['account_username']

    serv = socketserver.UDPServer((IP, PUERTO), EchoHandler)
    print('Listening...')
    log("Starting...", LOG_PATH)

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.", LOG_PATH)
