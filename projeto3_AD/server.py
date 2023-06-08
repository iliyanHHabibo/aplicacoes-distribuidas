#58654 - Bárbara Peres
#58626 - Iliyan Habibo
#Grupo 44



from flask import Flask,request,make_response
import requests
import json
import bd
import sqlite3
import funcoes_auxiliares_server as fa

#criar uma base de dados e as tabelas locations e airlines.
#fechamos a conexao com o commit por isso para voltar a usar a bd temos que criar uma nova conexao
nome_bd = 'projeto3.db'
conn,cursor = bd.connect_db(nome_bd)
bd.preenche_locations(cursor)
bd.preenche_airlines(cursor)
bd.commit(conn)


app = Flask(__name__)

 #APIs do professor
URL_weatherAPI_prof = 'https://lmpinto.eu.pythonanywhere.com/v1/forecast.json?'
URL_flightsAPI_prof = 'https://lmpinto.eu.pythonanywhere.com/roundtrip/'

#weather and flight API (do professor) keys. a key pode ser uma string qualquer
URL_weatherAPI_prof_key = 'bbjbvje'
URL_flightsAPI_prof_key = 'ygyghjgjh'

#rotas
@app.route("/search",methods=["GET"])




def search():
    #guardar a location e o custo (maximo de ida-e-volta)
    location = request.args["location"]
    cost = int(request.args["cost"])

    #e assim que se constroi o url
    #response = requests.get(URL_flightsAPI_prof + key(random string) + "LIS/ATH/2023-04-26/2023-04-29/1/0/0/Economy/EUR")

    #descobrir o IATA code da location
    conn,cursor = bd.connect_db(nome_bd)
    cursor.execute ("SELECT IATA FROM locations WHERE name = ?",(location,))
    results = cursor.fetchall()
    IATA_location = results[0][0]
    bd.commit(conn)

    #dicionario com os destinos (key) IATA codes (value) das locations e dicionario com os destinos e wea_names 
    destinos_IATAs,destinos_wea_names = fa.busca_locations(nome_bd)

    #guardar o forecast para os proximos 14 dias
    dicionario_weather = fa.make_request_weatherAPI (destinos_IATAs,destinos_wea_names,URL_weatherAPI_prof,URL_weatherAPI_prof_key)
   
    #colocar os dados de dicionario_weather na tabela weather
    fa.preenche_weather(nome_bd,dicionario_weather)

    #ir buscar as conditions de cada dia para cada destino à tabela weather
    dicionario_conditions = fa.busca_weather (nome_bd,dicionario_weather)

    #ver se cada destino tem pelo menos dois dias de sol/limpo
    wea_names_sunny_clear = fa.filtrar_weather (dicionario_conditions)
    
    #usar o dicionario destinos_wea_names para delete os destinos que nao tem pelo menos dois dias de sol/limpo
    #fazer o mesmo com o dicionario destinos_IATAs para depois fazer o pedido a flight API
    #tenho que usar uma copia do dicionario destinos_wea_names porque nao posso alterar um dicionario enquanto estou a iterar sobre ele (da erro)
    for destinos,wea_name in destinos_wea_names.copy().items():
        if wea_name not in wea_names_sunny_clear:
            del destinos_wea_names[destinos]
            del destinos_IATAs[destinos]

    #datas de partida e de regresso
    datas_partida = ["2023-04-26","2023-04-27","2023-04-28","2023-04-29"]
    datas_regresso = ["2023-04-29","2023-04-30","2023-05-01","2023-05-02"]

 
    #fazer o pedido à flight API e guardar os dados nas tabelas roundtrips e legs
    fa.make_request_flightAPI (nome_bd, IATA_location, URL_flightsAPI_prof, URL_flightsAPI_prof_key,location,destinos_IATAs,datas_partida,datas_regresso)
                    
    #dicionario que vai ser a resposta ao pedido
    response_dict = {'trips':[]} 
    
    #vamos buscar à tabela roundtrips os ids das roundtrips que sao menores que o custo
    conn,cursor = bd.connect_db(nome_bd)
    cursor.execute ("SELECT id,cost,id_leg0,id_leg1 FROM roundtrips WHERE cost <= ?",(cost,))
    results1 = cursor.fetchall()
    bd.commit(conn)
    
    roundtrips_dict = {}
    counter = 0
    for linha in results1:
        trip_dict = {'id': linha[0], 'cost': linha[1],'leg0':linha[2],'leg1':linha[3]}
        roundtrips_dict[counter] = trip_dict
        counter += 1
    
    #eliminamos as roundtrips cujo preço é maior que o cost
    for i in range(len(roundtrips_dict)):
        if roundtrips_dict[i]['cost'] > cost:
            del roundtrips_dict[i]
    
    #vamos buscar à tabela legs os dados das legs
    conn,cursor = bd.connect_db(nome_bd)
    leg0_list = []
    leg1_list = []
    for i in range(len(roundtrips_dict)):
        cursor.execute ("SELECT id,dep_IATA,arr_IATA,dep_datetime,arr_datetime FROM legs WHERE id = ? ",(roundtrips_dict[i]['leg0'],))
        results_leg0 = cursor.fetchall()
        cursor.execute ("SELECT id,dep_IATA,arr_IATA,dep_datetime,arr_datetime FROM legs WHERE id = ? ",(roundtrips_dict[i]['leg1'],))
        results_leg1 = cursor.fetchall()

        #colocar os dados do SELECT na leg0_dict e leg1_dict
        if len(results_leg0) > 0:
            leg0_list.append({'id' : results_leg0[0][0], 'dep_IATA':results_leg0[0][1],'arr_IATA':results_leg0[0][2],'dep_datetime':results_leg0[0][3],'arr_datetime':results_leg0[0][4]})

        if len(results_leg1) > 0:
            leg1_list.append({'id' : results_leg1[0][0],'dep_IATA':results_leg1[0][1],'arr_IATA':results_leg1[0][2],'dep_datetime':results_leg1[0][3],'arr_datetime':results_leg1[0][4]})

        
    bd.commit(conn)
    
    response = fa.response_search(roundtrips_dict,leg0_list,leg1_list)

    response_data = json.dumps(response)
    response = make_response(response_data, 200)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route("/filter", methods=["GET"])
def filter():
    filter_param = request.args.get("parametro1") # Retrieve the value of the "parametro1" parameter
    
    # Perform your desired operations using the filter_param
    
    response = {"message": "filter applied successfully"}
    response_data = json.dumps(response)
    response = make_response(response_data, 200)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route("/details",methods=["GET"])
def details():
    viagem_ID = request.args["viagem_ID"]
    
    response = fa.detalhes(viagem_ID,nome_bd)
    response_data = json.dumps(response)
    response = make_response(response_data, 200)
    response.headers['Content-Type'] = 'application/json'
    return response


if __name__ == "__main__":
    app.run(debug=True)

#devera haver um tratamento de erros. o servidor e que ve se as capitais estao disponiveis e se nao tiverem, retornar code 404 e dizer capital invalida


