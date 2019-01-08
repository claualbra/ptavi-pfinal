#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
import json
from uaclient import log, password
import random

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
    dicc_register = {}
    dicc_passw = {}
    nonce = {}

    def json2password(self):
        """Descargo fichero json en el diccionario."""
        try:
            with open(CONTRASEÑA, 'r') as jsonfile:
                self.dicc_passw = json.load(jsonfile)
        except:
            pass

    def json2register(self):
        """Descargo fichero json en el diccionario."""
        try:
            with open(REGISTRO, 'r') as jsonfile:
                self.dicc_register = json.load(jsonfile)
        except:
            pass

    def register2json(self):
        """
        Escribir diccionario.

        En formato json en elfichero registered.json.
        """
        with open(REGISTRO, 'w') as jsonfile:
            json.dump(self.dicc_register, jsonfile, indent=4)

    def del_usuarios(self):
        user_del = []
        for user in self.dicc_register:
            if self.dicc_register[user]['registro'] >= self.dicc_register[user]['expires']:
                user_del.append(user)
        for user in user_del:
            del self.dicc_register[user]

    def envio_destino(ip, port, mensaje):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip,port))

            my_socket.send(bytes(mensaje, 'utf-8'))
            mensaje = mensaje.replace("\r\n", " ")
            log('Sent to ' + ip + ':' + str(port) + ': ' + mensaje, LOG_PATH)

            try:
                data = my_socket.recv(1024).decode('utf-8')
            except ConnectionRefusedError:
                log("Error: No server listening at " + SERVER_PROXY +
                    " port " + str(PORT_PROXY), LOG_PATH)
            return data
    def handle(self):
        """Escribe dirección y puerto del cliente."""
        Ip_client = str(self.client_address[0])
        self.json2register()
        self.json2password()
        self.del_usuarios()

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
            print("El cliente nos manda\r\n", linea)
            line = linea.split()
            if line[0] == 'REGISTER' and len(line) == 5:
                user = line[1].split(':')[1]
                if user in self.dicc_passw.keys():
                    if user in self.dicc_register.keys():
                        if line[4] == '0':
                            del self.dicc_register[user]
                            linea_send = "SIP/2.0 200 OK\r\n\r\n"
                        else:
                            linea_send = "SIP/2.0 200 OK\r\n\r\n"
                    else:
                        self.nonce[user] = str(random.randint(0, 100000000))
                        linea_send = ('SIP/2.0 401 Unauthorized\r\n' +
                                    'WWW Authenticate: Digest ' +
                                    'nonce="' + self.nonce[user] + '"\r\n\r\n')
                else:
                    linea_send = 'SIP/2.0 404 User Not Found\r\n\r\n'
                    linea_send = linea_send.replace("\r\n", " ")
                    log('Error: ' + linea_send, LOG_PATH)
            elif line[0] == 'REGISTER' and len(line) == 8:
                user = line[1].split(':')[1]
                pw = self.dicc_passw[user]['passwd']
                nonce = password(pw, self.nonce[user])
                nonce_recv = line[7].split('"')[1]
                if nonce == nonce_recv:
                    TimeExp = time.time() + int(line[4])
                    now = time.time()
                    Port_client = line[1].split(':')[1]
                    self.dicc_register[user] = {'ip': Ip_client, 'expires': TimeExp,
                                        'puerto': Port_client, 'registro': now}
                    linea_send = "SIP/2.0 200 OK\r\n\r\n"
            elif line[0] == 'INVITE':
                user = line[6].split('=')[1]
                port = self.dicc_register[user]['puerto']
                linea_recb = linea.replace("\r\n", " ")
                log('Received from ' + Ip_client + ':' +
                    port + ': ' + linea_recb, LOG_PATH)
                if user in self.dicc_register.keys():
                    server = line[1].split(':')[1]
                    if server in self.dicc_register.keys():
                        ip_destino = self.dicc_register[server]['ip']
                        port_destino = int(self.dicc_register[server]['puerto'])
                        linea_send = self.envio_destino(ip_destino, port_destino, linea)
                        log_send = linea_send.replace("\r\n", " ")
                        log('Received from ' + Ip_client + ':' +
                            str(port_destino) + ': ' + log_send, LOG_PATH)
                        log('Sent to ' + Ip_client + ':' + port + ': ' + log_send, LOG_PATH)
                    else:
                        linea_send = 'SIP/2.0 404 User Not Found\r\n\r\n'
                        log_send = linea_send.replace("\r\n", " ")
                        log('Error: ' + log_send, LOG_PATH)
                else:
                    linea_send = 'SIP/2.0 404 User Not Found\r\n\r\n'
                    log_send = linea_send.replace("\r\n", " ")
                    log('Error: ' + log_send, LOG_PATH)
            elif line[0] == 'ACK':
                linea_send = self.envio_destino(ip_destino, port_destino, linea)
            elif line[0] == 'BYE':
                linea_send = self.envio_destino(ip_destino, port_destino, linea)
            else:
                linea_send = self.envio_destino(ip_destino, port_destino, linea)
            self.wfile.write(bytes(linea_send, 'utf-8'))
            print('mandamos al cliente: ', linea_send)
            self.register2json()

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

    IP = CONFIGURACION['server_ip']
    PORT_SERVER = int(CONFIGURACION['server_puerto'])
    PROXY = CONFIGURACION['server_name']
    LOG_PATH = CONFIGURACION['log_path']
    REGISTRO = CONFIGURACION['database_path']
    CONTRASEÑA = CONFIGURACION['database_passwdpath']

    serv = socketserver.UDPServer((IP, PORT), SIPRegisterHandler)
    print("Server " + PROXY + " listening at port " + str(PORT))
    log("Starting...", LOG_PATH)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.", LOG_PATH)
