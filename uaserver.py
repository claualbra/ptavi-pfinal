#!/usr/bin/python3
# -*- coding: utf-8 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import Ua1Handler, log, rtp
import sys
import socketserver


class EchoHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""
    rtp = []

    def enviar_proxy(self,linea):
        self.wfile.write(bytes(linea, 'utf-8'))
        print('Enviamos al Proxy:\r\n', linea)
        linea = linea.replace("\r\n", " ")
        log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' + linea, LOG_PATH)

    def handle(self):
        """Escribe dirección y puerto del cliente."""
        Ip_client = str(self.client_address[0])

        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            linea = line.decode('utf-8')
            linea_recb = linea.replace("\r\n", " ")
            log('Received from ' + IP_PROXY + ':' +
                str(PORT_PROXY) + ': ' + linea_recb, LOG_PATH)
            print("El cliente nos manda ", linea)

            line = linea.split()
            if line[0] == 'INVITE':
                self.rtp.append(line[7])
                self.rtp.append(line[10])
                mensaje =('SIP/2.0 100 Trying\r\n\r\n' +
                        'SIP/2.0 180 Ringing\r\n\r\n' +
                        'SIP/2.0 200 OK\r\n' +
                        'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                        'o=' + ADRESS + ' ' + IP + '\r\n' + 's=misesion\r\n' +
                        'm=audio ' + str(PORT_AUDIO) + ' RTP' + '\r\n\r\n')
                self.enviar_proxy(mensaje)
            elif line[0] == 'ACK':
                mensaje = rtp(self.rtp[0], self.rtp[1], AUDIO_PATH)
                log('Sent to ' + self.rtp[0] + ':' + str(self.rtp[1]) + ': ' + mensaje, LOG_PATH)
            elif line[0] == 'BYE':
                mensaje = 'SIP/2.0 200 OK\r\n\r\n'
                self.enviar_proxy(mensaje)
            elif metodo != ('INVITE', 'ACK', 'BYE'):
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
                log("Error: SIP/2.0 405 Method Not Allowed", LOG_PATH)
                print('metodo erroneo')
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
                log("Error: SIP/2.0 400 Bad Request", LOG_PATH)
                print('pregunta mal formulada')

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python uaserver.py config")

    parser = make_parser() #lee linea a linea y busca etiquetas, generico para xml
    u2Handler = Ua1Handler() #Hace cosas dependiendo de la etiqueta
    parser.setContentHandler(u2Handler)
    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError:
        sys.exit("Usage: python proxy_registrar.py config")
    CONFIGURACION = u2Handler.get_tags()

    LOG_PATH = CONFIGURACION['log_path']
    PUERTO = int(CONFIGURACION['uaserver_puerto'])
    IP = CONFIGURACION['uaserver_ip']
    IP_PROXY = CONFIGURACION['regproxy_ip']
    PORT_PROXY = int(CONFIGURACION['regproxy_puerto'])
    ADRESS = CONFIGURACION['account_username']
    PORT_AUDIO = int(CONFIGURACION['rtpaudio_puerto'])
    AUDIO_PATH = CONFIGURACION['audio_path']

    serv = socketserver.UDPServer((IP, PUERTO), EchoHandler)
    print('Listening...')
    log("Starting...", LOG_PATH)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.", LOG_PATH)
