# FABRICA

import argparse
import paho.mqtt.client as mqtt
import random
import time

from print_with_color import print_with_color as printwc

pecasNaFabrica = [5,5,5,5,5,5,5,5,5,5]

class Fabrica:

    def __init__(self, id_fabrica=2, tipo_fabrica="puxada", tamanho_lote=48, num_linhas=8, id_almoxarifado=1):

        self.id_fabrica = id_fabrica
        self.tipo_fabrica = tipo_fabrica
        self.tamanho_lote = tamanho_lote
        self.num_linhas = num_linhas
        self.id_almoxarifado = id_almoxarifado
    
    def enviar_pedido_pecas(self, lista_pedido_pecas, id_linha):

        pedido = ""
        for peca, quantidade in enumerate(lista_pedido_pecas):
            pedido += str(peca) + "," + str(quantidade) + ";"
        pedido = pedido[:-1]

        result = client.publish("fabrica_almoxarifado",
                                "fabrica/" + str(self.id_fabrica) +             \
                                "/almoxarifado/" + str(self.id_almoxarifado) +  \
                                "/linha/" + str(id_linha) + "/" + pedido)

    def receber_pedido_pecas(self, lista_pedido_pecas, id_linha):
        
        pedido = ""
        for peca, quantidade in enumerate(lista_pedido_pecas):
            pedido += str(peca) + "," + str(quantidade) + ";"
        pedido = pedido[:-1]

        result = client.publish("fabrica_linha",
                                "fabrica/" + str(self.id_fabrica) +     
                                "/linha/" + str(id_linha) +        
                                "/pedido_pecas/" + pedido)
    #envia o pedido de peças para o almoxarifado
    def enviar_produtos_estoque(self, lista_produtos):

        printwc(f"Enviando produtos para o estoque: {lista_produtos}", color="yellow")

        pedido = ""
        for produto, quantidade in enumerate(lista_produtos):
            pedido += str(produto) + "," + str(quantidade) + ";"
        pedido = pedido[:-1]

        result = client.publish("estoque_fabrica", "fabrica/" + str(id_fabrica) + "/estoque/1/" + pedido)
    
    def enviar_pedido_linha(self, lista_produtos, id_linha=0):

        pedido = ""
        for produto, quantidade in enumerate(lista_produtos):
            pedido += str(produto) + "," + str(quantidade) + ";"
        pedido = pedido[:-1]

        result = client.publish("fabrica_linha",
                                "fabrica/" + str(id_fabrica) +  \
                                "/linha/" + str(id_linha) +     \
                                "/pedido_produto/" + pedido)
    
    def enviar_pedido_linha_distribuido(self, lista_produtos):

        parte_lista_produto = [0] * 5
        for produto, quantidade in enumerate(lista_produtos):
            parte_lista_produto[produto] = quantidade // self.num_linhas
        
        for linha in range(self.num_linhas-1):
            self.enviar_pedido_linha(parte_lista_produto, id_linha=linha)
        
        for produto, quantidade in enumerate(lista_produtos):
            parte_lista_produto[produto] += quantidade % self.num_linhas
        
        self.enviar_pedido_linha(parte_lista_produto, id_linha=self.num_linhas-1)
    
    def converter_lista(self, lista1):
        
        lista2 = lista1.split(";")

        lista3 = []
        for pedido_produto in lista2:
            lista3.append(pedido_produto.split(","))
        
        lista4 = [0] * len(lista3)
        for indice, quantidade in lista3:
            lista4[int(indice)] = int(quantidade)
        
        return lista4

    def handler(self, acao, lista=None, id_linha=None):

        if(lista):
            lista = self.converter_lista(lista)

        match acao:
            case "enviar pedido para linha":
                self.enviar_pedido_linha_distribuido(lista)

            case "enviar pedido de peças para almoxarifado":
                self.enviar_pedido_pecas(lista, id_linha)

            case "receber pedido do almoxarifado":
                self.receber_pedido_pecas(lista, id_linha)

            case "enviar pedido de produtos para o estoque":
                self.enviar_produtos_estoque(lista)

            case "enviar lote para linha":
                lista = [10, 10, 10, 9, 9]
                self.enviar_pedido_linha_distribuido(lista)

def on_connect(client, userdata, flags, return_code):

    if return_code == 0:
        printwc("Fábrica conectada.", color="purple")
        client.subscribe("estoque_fabrica")
        client.subscribe("fabrica_linha")
        client.subscribe("fabrica_almoxarifado")

    else:
        printwc(f"Não foi possível conectar a fábrica. Return code: {return_code}", color="purple")

def on_message(client, userdata, message):

    msg = str(message.payload.decode("utf-8"))
    #printwc(f"Menssagem recebida: {msg}", color="blue")
    
    comando = msg.split("/")
    
    match comando[0]:

        case "linha" if((comando[3] == id_fabrica) & (comando[4] == "pedido_pecas")):

            fabrica.handler(acao="enviar pedido de peças para almoxarifado", lista=comando[5], id_linha=comando[1])
        
        case "linha" if((comando[3] == fabrica.id_fabrica) & (comando[4] == "pedido_produtos")):

            lista = fabrica.converter_lista(comando[5])

            fabrica.handler(acao="enviar pedido de produtos para o estoque", lista=comando[5])

        case "estoque" if((comando[3] == fabrica.id_fabrica) & (fabrica.tipo_fabrica == "puxada")):
            fabrica.handler(acao="enviar pedido para linha", lista=comando[4])
        
        case "almoxarifado" if(comando[3] == fabrica.id_fabrica):
            fabrica.handler(acao="receber pedido do almoxarifado", lista=comando[6], id_linha=comando[5])

#argumentos para execução da fábrica
parser = argparse.ArgumentParser(description='Argumentos para execução da fábrica.')

parser.add_argument('-i', '--id_fabrica', type=str, default="2",
                    help="Define o ID da fábrica")
parser.add_argument('-n', '--num_linhas', type=int, default="8",
                    help="Define o número de linhas da fábrica")
parser.add_argument('-t', '--tipo_fabrica', type=str, default="puxada",
                    help="Define o tipo de fábrica (puxada ou empurrada)")

args = parser.parse_args()

broker_hostname ="mosquitto"
port = 1883

id_fabrica = args.id_fabrica
client = mqtt.Client("fabrica" + id_fabrica)
client.on_connect=on_connect
client.on_message=on_message

client.connect(broker_hostname, port) 
client.loop_start()

num_linhas = 8

do = True

fabrica = Fabrica(id_fabrica=args.id_fabrica, num_linhas=args.num_linhas, tipo_fabrica=args.tipo_fabrica)

while(True):
    if(client.is_connected()):
        if(fabrica.tipo_fabrica == 'empurrada'):
            fabrica.handler(acao="enviar lote para linha")
        time.sleep(1)