#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
import json

def log(Mensaje):
    fich.write(time.strftime('%Y%m%d%H%M%S '))
    fich.write(Mensaje+"\r\n")

class PrHandler(ContentHandler):
    def __init__(self):
        self.diccionario= {}
        self.dicc_ua1xml = {'server': ['name', 'ip', 'puerto'],
                        'database': ['path', 'passwdpath'], 'log': ['path']}
    def startElement(self, name, attrs):
        diccionario = {}
        if name in self.dicc_ua1xml:
            for atributo in self.dicc_ua1xml[name]:
                self.diccionario[name+'_'+atributo] = attrs.get(atributo, '')

    def get_tags(self):
        return self.diccionario

class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Inicializo el diccionario de usuarios."""

    dicc = {}

    def json2register(self):
        """Descargo fichero json en el diccionario."""
        try:
            with open(REGISTRO, 'r') as jsonfile:
                self.dicc = json.load(jsonfile)
        except:
            pass

    def register2json(self):
        """
        Escribir diccionario.

        En formato json en elfichero registered.json.
        """
        with open(REGISTRO, 'w') as jsonfile:
            json.dump(self.dicc, jsonfile, indent=4)

    def del_usuarios(self):
        user_del = []
        for user in self.dicc:
            if self.dicc[user]['registro'] >= self.dicc[user]['expires']:
                user_del.append(user)
        for user in user_del:
            del self.dicc[user]

    def handle(self):
        """Escribe dirección y puerto del cliente (de tupla client_address)."""
        Ip_client = str(self.client_address[0])
        Port_client = str(self.client_address[1])
        self.json2register()

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
            user = line[1].split(':')[1]
            if line[0] == 'REGISTER' and len(line) == 5:
                if user in self.dicc.keys():
                    if line[4] == '0':
                        del self.dicc[user]
                        linea_send = "SIP/2.0 200 OK\r\n\r\n"
                    else:
                        linea_send = "SIP/2.0 200 OK\r\n\r\n"
                else:
                    linea_send = ('SIP/2.0 401 Unauthorized\r\n' +
                                'WWW Authenticate: Digest' +
                                'nonce="898989898798989898989"\r\n\r\n')
            if line[0] == 'REGISTER' and len(line) == 8:
                TimeExp = time.time() + int(line[4])
                now = time.time()
                self.dicc[user] = {'ip': Ip_client, 'expires': TimeExp,
                                    'puerto': Port_client, 'registro': now}
                linea_send = "SIP/2.0 200 OK\r\n\r\n"

            self.del_usuarios()
            self.register2json()

            self.wfile.write(bytes(linea_send, 'utf-8'))
            print('mandamos al cliente: ', linea_send)
            linea_send = linea_send.replace("\r\n", " ")
            log('Sent to ' + Ip_client + ':' + Port_client + ': ' + linea_send)

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except (IndexError, ValueError):
        sys.exit("Usage: python proxy_registrar.py config")


    parser = make_parser() #lee linea a linea y busca etiquetas, generico para xml
    pHandler = PrHandler() #Hace cosas dependiendo de la etiqueta
    parser.setContentHandler(pHandler)
    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError:
        sys.exit("Usage: python proxy_registrar.py config")
    CONFIGURACION = pHandler.get_tags()

    PROXY = CONFIGURACION['server_name']
    PORT = int(CONFIGURACION['server_puerto'])
    LOG_PATH = CONFIGURACION['log_path']
    REGISTRO = CONFIGURACION['database_path']

    fich = open(LOG_PATH, "a")
    log("Starting...")

    serv = socketserver.UDPServer(('', PORT), SIPRegisterHandler)
    print("Server " + PROXY + " listening at port " + str(PORT))

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.")
