#58654 - Bárbara Peres
#58626 - Iliyan Habibo
#Grupo 44

import sqlite3
from os.path import isfile

def connect_db(dbname):
    db_is_created = isfile(dbname) #ve se existe um ficheiro da bd 
    conn = sqlite3.connect(dbname) #cria a bd
    conn.execute ("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor() #cria um cursor para a bd
    if not db_is_created:
        #criar as tabelas
        cursor.execute ("CREATE TABLE locations\
                            (id INTEGER, name TEXT PRIMARY KEY, IATA TEXT,wea_name TEXT)")
            
        cursor.execute ("CREATE TABLE weather\
                        (id INTEGER PRIMARY KEY,date TEXT,location TEXT,condition TEXT, mintemp_c INTEGER, maxtemp_c INTEGER)")#\
                        #FOREIGN KEY (location) REFERENCES locations(wea_name) ON DELETE CASCADE)")
        
        cursor.execute ("CREATE TABLE airlines\
                        (code TEXT PRIMARY KEY, name TEXT)")
        
        cursor.execute ("CREATE TABLE legs\
                        (id TEXT PRIMARY KEY, dep_IATA TEXT, arr_IATA TEXT, dep_datetime TEXT, arr_datetime TEXT, duration_min INTEGER, airlineCodes TEXT)")#,\
                        #FOREIGN KEY(dep_IATA) REFERENCES locations(IATA) ON DELETE CASCADE,\
                        #FOREIGN KEY(arr_IATA) REFERENCES locations(IATA) ON DELETE CASCADE,\
                        #FOREIGN KEY(airlineCodes) REFERENCES airlines(code) ON DELETE CASCADE))

        cursor.execute ("CREATE TABLE roundtrips\
                        (id TEXT PRIMARY KEY,cost INTEGER,id_leg0 TEXT, id_leg1 TEXT)")#,\
                        #FOREIGN KEY(id_leg0) REFERENCES legs(id) ON DELETE CASCADE,\
                        #FOREIGN KEY(id_leg1) REFERENCES legs(id) ON DELETE CASCADE)")

    return conn, cursor

def preenche_locations(cursor):
    #adicionamos atenas porque está nas APIs do professor
    cidades = ["Lisboa","Madrid","Paris","Dublin","Bruxelas","liubliana","Amsterdão","Berlim","Roma","Viena"]
    IATA = ["LIS","MAD","ORY","DUB","BRU","LJU","AMS","BER","FCO","VIE"]
    wea_names = ["lisbon","madrid","paris","dublin","brussels","ljubljana","amsterdam","berlin","rome","vienna"]


    for i in range(len(cidades)):
        cursor.execute("INSERT OR IGNORE INTO locations VALUES (?,?,?,?)",(i,cidades[i],IATA[i],wea_names[i]))

def preenche_airlines(cursor):
    airline_codes = ['TP', 'IB', 'AF', 'BA', 'LH', 'FR', 'VY', 'U2', 'AZ', 'LX']
    airline_names = ['TAP Portugal', 'Iberia', 'Air France', 'British Airways', 'Lufthansa', 'Ryanair', 'Vueling', 'easyJet', 'Alitalia', 'Swiss']

    for i in range(len(airline_codes)):
        cursor.execute("INSERT OR IGNORE INTO airlines VALUES (?,?)",(airline_codes[i],airline_names[i]))
    
#usamos isto quando quisermos guardar as changes e fechar a conexao. para abrir outra conexao chamar outra vez a funcao connect_db
def commit(conn):
    conn.commit()


