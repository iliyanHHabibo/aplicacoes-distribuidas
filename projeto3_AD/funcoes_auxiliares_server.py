#58654 - Bárbara Peres
#58626 - Iliyan Habibo
#Grupo 44



import bd
import requests
import datetime

def busca_locations(nome_bd):
    #vamos buscar à tabela locations os destinos, as IATAs e os wea_names
    conn,cursor = bd.connect_db(nome_bd)
    cursor.execute ("SELECT name, IATA, wea_name FROM locations")
    results = cursor.fetchall()

    destinos_IATAs = {}
    destinos_wea_names = {}
    for linha in results:
        destinos_IATAs[linha[0]] = linha[1]
        destinos_wea_names[linha[0]] = linha[2]
    bd.commit(conn)
    
    return destinos_IATAs,destinos_wea_names

def make_request_weatherAPI (destinos_IATAs,destinos_wea_names,URL_weatherAPI_prof,URL_weatherAPI_prof_key): 
    #guardar o forecast para os proximos 14 dias
    dicionario_weather = {}
    for i in range (len(destinos_wea_names)):
        #meter destinos (de destinos_IATAS) que sao as keys numa lista
        destinos = list(destinos_IATAs.keys())

        #meter wea_names (de destinos_wea_names) que sao os values numa lista
        wea_names = list(destinos_wea_names.values())
        try:
            #fazer request à API do tempo
            params = {"key":URL_weatherAPI_prof_key,"q":wea_names[i],"days":14}  # request forecast for the next 14 days
            r = requests.get(URL_weatherAPI_prof, params=params)
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while retrieving weather data for {wea_names[i]}: {e}")
            continue
        if r.status_code == 200:
            forecast_days = r.json()["forecast"]["forecastday"]
            dicionario_weather[wea_names[i]] = {}
            for j in range(14):
                dicionario_weather[wea_names[i]][j+1] = forecast_days[j]

    return dicionario_weather


def busca_weather (nome_bd,dicionario_weather):
     #ir buscar as conditions de cada dia para cada destino à tabela weather
    conn,cursor = bd.connect_db(nome_bd)
    dicionario_conditions = {}
    contador_ids = 0
    for wea_name in dicionario_weather.keys():
        dicionario_conditions[wea_name] = []
        for dia in dicionario_weather[wea_name]:
            cursor.execute("SELECT condition FROM weather WHERE id = ?",(contador_ids,))
            dicionario_conditions[wea_name].append(cursor.fetchone()[0])
            contador_ids += 1
    bd.commit(conn)
    return dicionario_conditions


def preenche_weather(nome_bd,dicionario_weather):
    #colocar os dados de dicionario_weather na tabela weather
    conn,cursor = bd.connect_db(nome_bd)
    contador_ids = 0
    for wea_name in dicionario_weather.keys():
        for dia in dicionario_weather[wea_name]:
            #usamos o ignore caso haja linhas iguais ou linhas com id iguais
            cursor.execute("INSERT OR IGNORE INTO weather (id,date,location,condition,mintemp_c,maxtemp_c) VALUES (?,?,?,?,?,?)", (contador_ids,dicionario_weather[wea_name][dia]['date'],wea_name,dicionario_weather[wea_name][dia]['day']['condition']['text'],dicionario_weather[wea_name][dia]['day']['mintemp_c'],dicionario_weather[wea_name][dia]['day']['maxtemp_c']))
            contador_ids += 1
    bd.commit(conn)

def filtrar_weather (dicionario_conditions): 
    #retorna wea_names com pelo menos dois dias de sol/limpo
    wea_names_sunny_clear = []
    for wea_name in dicionario_conditions.keys():
        contador = 0
        for condition in dicionario_conditions[wea_name]:
            if condition == "Sunny" or condition == "Clear":
                contador += 1
            if contador >= 2:
                wea_names_sunny_clear.append(wea_name)
                break 
        contador = 0
    return wea_names_sunny_clear

def get_roundtrips (r):
    """recebe json da flight API e devolve roundtrips_dict"""
    #devolve dicionario com info para colocar na tabela roundtrips
    #key: id da roundtrip. value: lista com os ids das legs e o preço ([id_leg0,id_leg1,price])
    roundtrips_dict = {}
    
    for j in range(len(r['trips'])):
        #ver se nao ha stopovers. se nao houver, existe apenas um '~' em cada id: LIS-FCO:TP834~26:0
        if r['trips'][j]['legIds'][0].count('~') == 1 and r['trips'][j]['legIds'][1].count('~') == 1:
            roundtrips_dict[r['trips'][j]['id']] = [r['trips'][j]['legIds'][0],r['trips'][j]['legIds'][1]]
        

    for i in range(len(r['fares'])):
        for j in range(len(r['trips'])):
            #:19 porque o id tem apenas 19 caracteres
            if r['fares'][i]['id'][:19] == r['trips'][j]['id'][:19]:
                if r['trips'][j]['legIds'][0].count('~') == 1 and r['trips'][j]['legIds'][1].count('~') == 1:
                    roundtrips_dict[r['trips'][j]['id']].append(r['fares'][i]['price']['totalAmount'])
                    
    return roundtrips_dict


#devolve dicionario com info para colocar na tabela legs
def get_legs (r, roundtrips_dict):
    """recebe json e roundtrips dict e devolve um dicionario com info para colocar na tabela legs"""
    #key: leg0 ou leg1. value: lista com id da leg,dep_IATA,arr_IATA,dep_datetime,arr_datetime,duration_min,airlineCodes
    legs_dict = {}
    for i in range(len(r['legs'])): 
        airline_codes = [r['legs'][i]['segments'][0]["airlineCode"], r['legs'][i]['segments'][-1]["airlineCode"]]
        for j in roundtrips_dict:
            if roundtrips_dict [j][0] == r['legs'][i]['id']:
                legs_dict['leg0'] = [r['legs'][i]['id'], r['legs'][i]['segments'][0]['departureAirportCode'], r['legs'][i]['segments'][-1]['arrivalAirportCode'],\
                                      r['legs'][i]['departureDateTime'], r['legs'][i]['arrivalDateTime'],\
                                         r['legs'][0]['segments'][0]['durationMinutes'], " ".join(airline_codes)]
            
            
            elif roundtrips_dict [j][1] == r['legs'][i]['id']:
                legs_dict['leg1'] = [r['legs'][i]['id'], r['legs'][i]['segments'][0]['departureAirportCode'], r['legs'][i]['segments'][-1]['arrivalAirportCode'],\
                                         r['legs'][i]['departureDateTime'], r['legs'][i]['arrivalDateTime'],\
                                         r['legs'][0]['segments'][-1]['durationMinutes'], " ".join(airline_codes)]

    return legs_dict

def make_request_flightAPI (nome_bd, IATA_location, URL_flightsAPI_prof, URL_flightsAPI_prof_key,location,destinos_IATAs,datas_partida,datas_regresso):
    #faz requests a flight API e preenche logo as tabelas roundtrips e legs
    for i in range(len(datas_partida)):
        for destino,IATA_code in destinos_IATAs.items():
            if destino != location:
                r = requests.get(URL_flightsAPI_prof + URL_flightsAPI_prof_key + "/" + IATA_location + "/" \
                                + IATA_code + "/" + datas_partida[i] + "/" + datas_regresso[i] + "/1/0/0/Economy/EUR")
                
                #https://lmpinto.eu.pythonanywhere.com/roundtrip/nnn/LIS/MAD/2023-04-26/2023-04-29/1/0/0/Economy/EUR
                #make a 404 error if the request is not successful and continue to the next destination
                try:
                    r = r.json()
                except requests.exceptions.JSONDecodeError:
                    continue
                #obter os dados para a tabela roundtrips e legs
                #roundtrips dict. key: roundtrip_id, value: [id_leg0,id_leg1,price]
                roundtrip_data = get_roundtrips(r)

            #colocar roundtrips_data na tabela roundtrips
                conn,cursor = bd.connect_db(nome_bd)
                for j in roundtrip_data.keys():
                    cursor.execute ("INSERT OR IGNORE INTO roundtrips (id,cost,id_leg0,id_leg1) VALUES (?,?,?,?)",(j,int(roundtrip_data[j][2]),roundtrip_data[j][0],roundtrip_data[j][1]))
                bd.commit(conn)
                
                
                #PEGAR NOS TOTAL AMOUNTS DE GET ROUNDTRIP E APAGAR LOGO VOOS QUE SAO MENORES QUE COST
                #abrir bd de novo
                conn,cursor = bd.connect_db(nome_bd)

                legs_data = get_legs(r, roundtrip_data)
                for j in legs_data.keys():
                    cursor.execute("INSERT OR IGNORE INTO legs (id, dep_IATA, arr_IATA, dep_datetime, arr_datetime, duration_min, airlineCodes) VALUES (?,?,?,?,?,?,?)", (legs_data[j][0], legs_data[j][1], legs_data[j][2], legs_data[j][3], legs_data[j][4], legs_data[j][5], legs_data[j][6]))
                
                bd.commit(conn)

#faz um dicionario de resposta para o pedido search
def response_search (roundtrips_dict,leg0_list,leg1_list):
    response_dict = {'trips':[]}
    #fazemos 2 fors. um para juntar o roundtrips dict com as leg0 e outro para juntar o roundtrips dict com as leg1
    for i in range(len(roundtrips_dict)):
        for j in range(len(leg0_list)):
            if roundtrips_dict[i]['leg0'] == leg0_list[j]['id']:
                response_dict['trips'].append ({'id':roundtrips_dict[i]['id'],'cost':roundtrips_dict[i]['cost'],\
                                                'src': leg0_list[j]['dep_IATA'],'dst':leg0_list[j]['arr_IATA'],\
                                                    'departure_date':leg0_list[j]['dep_datetime'],'arrival_date':leg0_list[j]['arr_datetime']})
        for k in range(len(leg1_list)):  
            if roundtrips_dict[i]['leg1'] == leg1_list[k]['id']:
                response_dict['trips'].append ({'id':roundtrips_dict[i]['id'],'cost':roundtrips_dict[i]['cost'],\
                                                'src': leg1_list[k]['dep_IATA'],'dst':leg1_list[k]['arr_IATA'],\
                                                    'departure_date':leg1_list[k]['dep_datetime'],'arrival_date':leg1_list[k]['arr_datetime']})
    
    return response_dict

def detalhes (roundtrip_ID,nome_bd):
    conn, cursor = bd.connect_db(nome_bd)
    cursor.execute("SELECT cost, id_leg0, id_leg1 FROM roundtrips WHERE id = ?", (roundtrip_ID,))
    results = cursor.fetchone()
    cost = results[0]
    id_leg0 = results[1]
    id_leg1 = results[2]

    # buscar info da leg0
    cursor.execute("SELECT dep_IATA, arr_IATA, dep_datetime, arr_datetime, duration_min, airlineCodes FROM legs WHERE id = ?", (id_leg0,))
    results = cursor.fetchone()
    dep_IATA_leg0 = results[0]
    arr_IATA_leg0 = results[1]
    dep_datetime_leg0 = results[2]
    arr_datetime_leg0 = results[3]
    duration_min_leg0 = results[4]
    airlineCodes_leg0 = results[5]

    # buscar info da leg1
    cursor.execute("SELECT dep_IATA, arr_IATA, dep_datetime, arr_datetime, duration_min, airlineCodes FROM legs WHERE id = ?", (id_leg1,))
    results = cursor.fetchone()
    dep_IATA_leg1 = results[0]
    arr_IATA_leg1 = results[1]
    dep_datetime_leg1 = results[2]
    arr_datetime_leg1 = results[3]
    duration_min_leg1 = results[4]
    airlineCodes_leg1 = results[5]

    # buscar info de weather
    # so preciso da data da leg0 e depois uso os ids da tabela weather para ir buscar os outros 3 dias
    # (é só adicionar 1, 2 ou 3 ao id da data leg0)
    datetime_str = str(dep_datetime_leg0)

    # Convert the datetime string to a datetime object
    datetime_obj = datetime.datetime.fromisoformat(datetime_str)

    # Retrieve the date portion from the datetime object
    date = datetime_obj.date()

    cursor.execute("SELECT id FROM weather WHERE date = ?", (date,))
    id_weather_dia0 = cursor.fetchone()[0]

    # guarda condition dos 4 dias
    dicionario_weather = {0: None, 1: None, 2: None, 3: None}
    counter = 0
    for i in range(id_weather_dia0, id_weather_dia0 + 4):
        cursor.execute("SELECT condition FROM weather WHERE id = ?", (i,))
        dicionario_weather[counter] = cursor.fetchone()[0]
        counter += 1

    bd.commit(conn)
    
    dict_out = {"cost": cost, "dst": arr_IATA_leg0, "leg0":{"airline": airlineCodes_leg0,"arrival":arr_datetime_leg0,"departure":dep_datetime_leg0,\
    "duration": duration_min_leg0},"leg1":{"airline": airlineCodes_leg1,"arrival":arr_datetime_leg1,"departure":dep_datetime_leg1,"duration":\
    duration_min_leg1},"weather":{"0":dicionario_weather[0],"1":dicionario_weather[1],"2":dicionario_weather[2],"3":dicionario_weather[3]}}
    
    return dict_out
