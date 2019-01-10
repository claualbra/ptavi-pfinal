#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa para un servidor proxy/registrar."""

import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socketserver
import time
import json
from uaclient import log, password
import random
import socket


class PrHandler(ContentHandler):
    """Class Handler."""

    def __init__(self):
        """Inicializa los diccionarios."""
        self.diccionario = {}
        self.dicc_ua1xml = {'server': ['name', 'ip', 'puerto'],
                            'database': ['path', 'passwdpath'],
                            'log': ['path']}

    def startElement(self, name, attrs):
        """Crea el diccionario con los valores del fichero xml."""
        diccionario = {}
        if name in self.dicc_ua1xml:
            for atributo in self.dicc_ua1xml[name]:
                self.diccionario[name+'_'+atributo] = attrs.get(atributo, '')

    def get_tags(self):
        """Devuelve el diccionario creado."""
        return self.diccionario


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Inicializo los diccionarios de usuarios, registrados y nonce."""

    dicc_reg = {}
    dicc_passw = {}
    nonce = {}

    def json2password(self):
        """Descargo fichero json en el diccionario."""
        try:
            with open(CONTRASEÑA, 'r') as jsonfile:
                self.dicc_passw = json.load(jsonfile)
        except FileNotFoundError:
            pass

    def json2register(self):
        """Descargo fichero json en el diccionario."""
        try:
            with open(REGISTRO, 'r') as jsonfile:
                self.dicc_reg = json.load(jsonfile)
        except FileNotFoundError:
            pass

    def register2json(self):
        """
        Escribir diccionario.

        En formato json en elfichero registered.json.
        """
        with open(REGISTRO, 'w') as jsonfile:
            json.dump(self.dicc_reg, jsonfile, indent=4)

    def del_usuarios(self):
        """Elimina usurio que se ha pasado su tiempo de expiracion."""
        user_del = []
        for user in self.dicc_reg:
            if time.time() >= self.dicc_reg[user]['expires']:
                user_del.append(user)
        for user in user_del:
            del self.dicc_reg[user]

    def envio_client(self, ip, port, linea):
        """Envio mensajes al uaclient."""
        self.wfile.write(bytes(linea, 'utf-8'))
        print('mandamos al cliente: ', linea)
        log_send = linea.replace("\r\n", " ")
        log('Sent to ' + ip + ':' + str(port) + ': ' + log_send, LOG_PATH)

    def envio_destino(self, ip, port, mensaje):
        """Envio los mensajes al uaserver."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip, port))

            mens = mensaje.split('\r\n\r\n')
            mens_proxy = (mens[0] + '\r\nVia: SIP/2.0/UDP ' + IP + ':' +
                         str(PORT_SERVER) + '\r\n\r\n' + mens[1])
            print('mandamos al servidor: ', mens_proxy)
            my_socket.send(bytes(mens_proxy, 'utf-8'))
            mens_proxy = mens_proxy.replace("\r\n", " ")
            log('Sent to ' + ip + ':' + str(port) + ': ' +
                mens_proxy, LOG_PATH)

            try:
                data = my_socket.recv(1024).decode('utf-8')
                print('recibimos del servidor: ', data)
            except ConnectionRefusedError:
                log("Error: No server listening at " + ip +
                    " port " + str(port), LOG_PATH)
            recb = data.split()
            env_proxy = ''
            try:
                if recb[7] == '200':
                    recb_proxy = data.split('\r\n\r\n')
                    env_proxy = (recb_proxy[0] + '\r\n\r\n' +recb_proxy[1] +
                                 '\r\n\r\n' + recb_proxy[2] +
                                 '\r\nVia: SIP/2.0/UDP ' + IP + ':' +
                                 str(PORT_SERVER) + '\r\n\r\n' + recb_proxy[3])
            except IndexError:
                pass
            if env_proxy != '':
                print('hola')
                log_send = env_proxy.replace("\r\n", " ")
                log('Received from ' + ip + ':' +
                    str(port) + ': ' + log_send, LOG_PATH)
                self.envio_client(ip, port, env_proxy)

    def user_not_found(self):
        """Mensaje de usuario no encontrado."""
        linea_send = 'SIP/2.0 404 User Not Found\r\n\r\n'
        log_send = linea_send.replace("\r\n", " ")
        log('Error: ' + log_send, LOG_PATH)
        self.wfile.write(bytes(linea_send, 'utf-8'))

    def handle(self):
        """Escribe dirección y puerto del cliente."""
        ip_client = str(self.client_address[0])
        port_client = str(self.client_address[1])
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
            print("El cliente nos manda\r\n", linea)
            line = linea.split()
            if line[0] == 'REGISTER' and len(line) == 5:
                user = line[1].split(':')[1]
                linea_recb = linea.replace("\r\n", " ")
                log('Received from ' + ip_client + ':' +
                    port_client + ': ' + linea_recb, LOG_PATH)
                if user in self.dicc_passw.keys():
                    if user in self.dicc_reg.keys():
                        if line[4] == '0':
                            del self.dicc_reg[user]
                            linea_send = "SIP/2.0 200 OK\r\n\r\n"
                        else:
                            linea_send = "SIP/2.0 200 OK\r\n\r\n"
                    else:
                        self.nonce[user] = str(random.randint(0, 100000000))
                        linea_send = ('SIP/2.0 401 Unauthorized\r\n' +
                                      'WWW Authenticate: Digest ' +
                                      'nonce="' + self.nonce[user] +
                                      '"\r\n\r\n')
                    self.envio_client(ip_client, port_client, linea_send)
                else:
                    self.user_not_found()
            elif line[0] == 'REGISTER' and len(line) == 8:
                user = line[1].split(':')[1]
                port = line[1].split(':')[2]
                linea_recb = linea.replace("\r\n", " ")
                log('Received from ' + ip_client + ':' +
                    port_client + ': ' + linea_recb, LOG_PATH)
                pw = self.dicc_passw[user]['passwd']
                nonce = password(pw, self.nonce[user])
                nonce_recv = line[7].split('"')[1]
                if nonce == nonce_recv:
                    TimeExp = time.time() + int(line[4])
                    now = time.time()
                    self.dicc_reg[user] = {'ip': ip_client, 'expires': TimeExp,
                                           'puerto': port, 'registro': now}
                    linea_send = "SIP/2.0 200 OK\r\n\r\n"
                else:
                    self.nonce[user] = str(random.randint(0, 100000000))
                    linea_send = ('SIP/2.0 401 Unauthorized\r\n' +
                                  'WWW Authenticate: Digest ' +
                                  'nonce="' + self.nonce[user] +
                                  '"\r\n\r\n')
                self.envio_client(ip_client, port_client, linea_send)
            elif line[0] == 'INVITE':
                linea_recb = linea.replace("\r\n", " ")
                log('Received from ' + ip_client + ':' +
                    port_client + ': ' + linea_recb, LOG_PATH)
                user = line[6].split('=')[1]
                if user in self.dicc_reg.keys():
                    server = line[1].split(':')[1]
                    if server in self.dicc_reg.keys():
                        ip_destino = self.dicc_reg[server]['ip']
                        port_destino = int(self.dicc_reg[server]['puerto'])
                        self.envio_destino(ip_destino, port_destino, linea)
                    else:
                        self.user_not_found()
                else:
                    self.user_not_found()
            elif line[0] == 'ACK':
                linea_recb = linea.replace("\r\n", " ")
                log('Received from ' + ip_client + ':' +
                    port_client + ': ' + linea_recb, LOG_PATH)
                server = line[1].split(':')[1]
                if server in self.dicc_reg.keys():
                    ip_destino = self.dicc_reg[server]['ip']
                    port_destino = int(self.dicc_reg[server]['puerto'])
                    audio = self.envio_destino(ip_destino, port_destino, linea)
                else:
                    self.user_not_found()
            elif line[0] == 'BYE':
                linea_recb = linea.replace("\r\n", " ")
                log('Received from ' + ip_client + ':' +
                    port_client + ': ' + linea_recb, LOG_PATH)
                server = line[1].split(':')[1]
                if server in self.dicc_reg.keys():
                    ip_destino = self.dicc_reg[server]['ip']
                    port_destino = int(self.dicc_reg[server]['puerto'])
                    self.envio_destino(ip_destino, port_destino, linea)
                else:
                    self.user_not_found()
            elif line[0] != ('REGISTER', 'INVITE', 'ACK', 'BYE'):
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
                log("Error: SIP/2.0 405 Method Not Allowed", LOG_PATH)
                print('metodo erroneo')
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
                log("Error: SIP/2.0 400 Bad Request", LOG_PATH)
                print('pregunta mal formulada')
            self.register2json()


if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except (IndexError, ValueError):
        sys.exit("Usage: python proxy_registrar.py config")

    parser = make_parser()
    pHandler = PrHandler()
    parser.setContentHandler(pHandler)
    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError:
        sys.exit("Usage: python proxy_registrar.py config")
    CONFIGURACION = pHandler.get_tags()

    if CONFIGURACION['server_ip'] == '':
        IP = '127.0.0.1'
    else:
        IP = CONFIGURACION['server_ip']
    PORT_SERVER = int(CONFIGURACION['server_puerto'])
    PROXY = CONFIGURACION['server_name']
    LOG_PATH = CONFIGURACION['log_path']
    REGISTRO = CONFIGURACION['database_path']
    CONTRASEÑA = CONFIGURACION['database_passwdpath']

    serv = socketserver.UDPServer((IP, PORT_SERVER), SIPRegisterHandler)
    print("Server " + PROXY + " listening at port " + str(PORT_SERVER))
    log("Starting...", LOG_PATH)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.", LOG_PATH)
