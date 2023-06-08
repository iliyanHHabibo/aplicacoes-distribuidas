#58654 - Bárbara Peres
#58626 - Iliyan Habibo
#Grupo 44

from datetime import date 
import requests
import json


def valida_args(input_user):
    """retorna verdadeiro se a mensagem for válida, falso caso contrário"""
   
    #check se o primeiro arumento de input_user é um comando válido
    if input_user[0] in ["SEARCH","FILTER","DETAILS"]:
        
        #comando SEARCH
        if input_user[0] == "SEARCH":
            if len (input_user) == 3:
                #cidades disponiveis na API do professor: athens, lisbon, madrid, paris
                if input_user[1] in ("Lisboa","Madrid","Paris","Dublin","Bruxelas","liubliana","Amsterdão","Berlim","Roma","Viena"):
                    return True 

        #comando FILTER
        if input_user[0] == "FILTER":
            #DIVERSIFY
            if input_user[1] == "DIVERSIFY":
                if len(input_user) == 2:
                    return True
                
            #DST,AIRLINE,SUN,list ids viagens
            #dias de SUN entre 2 e 4
            if int(input_user[3]) >= 2 and int(input_user[3]) <= 4:
                return True
            
        
        #comando DETAILS
        if input_user[0] == "DETAILS":
            if len(input_user) == 2:
                return True
    
    return False

def envia_requests(input):
    """envia requests para o servidor. recebe uma lista com os argumentos do input do utilizador"""
    if input[0] == "SEARCH":
        params = {"location":input[1],"cost":int(input[2])}
        r = requests.get("http://127.0.0.1:5000/search",params=params)
        return r.content.decode()

    if input[0] == "FILTER":
        if input[1] == "DIVERSIFY":
            params = {"parametro1": input[1]}
            r = requests.get("http://127.0.0.1:5000/filter",params=params)
            return r.content.decode()
        else:
            lista_ids = input[4:]
            params = {"comando":input[0],"DST":input[1],"AIRLINE":input[2],"SUN":input[3],"ids":lista_ids}
            r = requests.get("http://127.0.0.1:5000/filter",params=params)
            return r.content.decode()

    if input[0] == "DETAILS":
        params = {"viagem_ID":input[1]}
        r = requests.get("http://127.0.0.1:5000/details",params=params)
        return r.content.decode()


if __name__ == "__main__":
    while True:
        input_user = input("Escreva a sua mensagem: ")
        input_user = input_user.split()

        #validar argumentos
        if not valida_args(input_user):
            print ("Mensagem inválida")

        elif valida_args(input_user):
            r = envia_requests(input_user)
            print(r) 

    

    
#é suposto haver um exit?