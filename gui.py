import PySimpleGUI as sg
import datetime
import pycountry
import os

import sql_handler
import api_caller


def start_gui(c):

    MAX_COL = 21 #Number of flags per row
    MAX_ROW = 30 
    sg.theme('DarkTeal1')   # Color theme of window
    
    # All the stuff inside your window.
    layout = [[sg.Button("Add Match")]
            ]

    #So I can make rows of flag buttons easier instead of smashing it all in layout
    
    pic_list = [flag_file for flag_file in os.listdir('./osu flags/') if flag_file.endswith(".png")]
    collect = [pic_list[i:i+MAX_COL] for i in range(0, len(pic_list), MAX_COL)]
    for list_slice in collect:
        a = [[sg.Button("",tooltip = flag[:-4],disabled = check_country_exists(flag[:-4],c),
                image_filename='./osu flags/'+flag,image_size=(50, 50),
                image_subsample=2, border_width=0,button_color=("red",change_color(flag[:-4],c)),
                disabled_button_color=("red","red"), key = flag[:-4],
                pad=((1,1),(1,1))) for flag in list_slice]]
        
        layout+=a #Put the layout together         



    #Create the Window
    main_window = sg.Window('osu!Tourney the World', layout)

    return main_window

def event_loop(window,conn):
    #Grabbing the values from fill-ins
    close_window = False

    #.read() is incredibly important to make the window show
    #I just messed up so this is a reminder.
    event, values = window.read()

    if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
        return None, not close_window

    elif event == 'Add Match':
        values2, event2 = pop_up(window, conn)

        if event2 == "Ok":
            return values2, close_window

    else: #For the rest of the countries
        #Open up the country window with info somehow
        country_info(event,conn)

        
    return None, False #delete later probably

def country_info(key_country,conn):
    #opens a window containing opponents from flag
    table_col = ["Name","id","pp","World#","Country#","Badges",
                 "Score","Team","Tourney Name","Date","Mode"]
    data = []

    c = conn.cursor()

    #update country button here
    #check if button can be clickable
    #temporary workaround to search key by value
    if key_country in pycountry_dict:
        country_abr = [k for k,v in pycountry_dict.items() if v == key_country][0]

    else:
        country_abr = pycountry.countries.get(name=key_country).alpha_2

    all_matches = (c.execute("SELECT * FROM opponents WHERE country = ?",(country_abr,)).fetchall())
    unique_played = c.execute("SELECT count (DISTINCT osu_id) FROM opponents WHERE country = ?",(country_abr,)).fetchone()[0]
    matches_played = c.execute("SELECT count (*) FROM opponents WHERE country = ?",(country_abr,)).fetchone()[0]
    total_wins = c.execute("SELECT count (*) FROM opponents WHERE country = ? AND win = '1'",(country_abr,)).fetchone()[0]

    #this will be really hard to remember later, so just look at the database order
    for match in all_matches:
        data.append([match[0],match[1],match[4],match[5],match[6],match[3],
                     ("{} - {}".format(match[10],match[11])),match[8],match[9],match[7],gamemode(match[13])])

    layout_c = [[sg.Text(key_country, font=32),
                     sg.Text("RANK: {}".format(change_color(key_country,c)+ " Belt"),font = 18)],
                [sg.Text("Matches played: {}".format(matches_played)),sg.Text("Wins: {}".format(total_wins))],
                [sg.Text("People played: {}".format(unique_played))],
                [sg.Table(values=data,headings=table_col)]]
    
    if does_country_exist(key_country):
        win3 = sg.Window(key_country,layout_c)
        event3, values3 = win3.read()

def gamemode(num):
    #Takes number and translates to gamemode
    if num == 0:
        return "Standard"
    elif num == 1:
        return "Taiko"
    elif num == 2:
        return "Catch"
    elif num == 3:
        return "Mania"    

def pop_up(window, conn):
       
    layout_add = [ [sg.Text('osu!Tourneys Flag Counter:',font=24)],
            [sg.Text('Enter your API*:'), sg.InputText('', key='password', password_char='*')],
            [sg.Text("Game Mode*:"), 
                sg.Radio('Standard', "RADIO1", default=True,key='is_s'),
                sg.Radio('Taiko', "RADIO1", default=False,key='is_t'),
                sg.Radio('Catch', "RADIO1", default=False,key='is_c'),
                sg.Radio('Mania', "RADIO1", default=False,key='is_m')],
            [sg.Text("User*:"),
                sg.Radio('Username', "RADIO2", default=True,key='is_username'),
                sg.Radio('User ID', "RADIO2",default=False,key='is_user_id')],
            [sg.Text('Enter user*:'), sg.InputText(key='user_id')],
            [sg.Text('How many badges did they have?:'),
                sg.InputText(size=(5,5),key='badges')],
            [sg.Text('Enter Team Name (if applicable):'),
                sg.InputText(key='team_name')],
            [sg.Text('Enter Tourney Name:'),
                sg.InputText(key='tourney_name')],
            [sg.Text('Did you win?'),sg.Checkbox('',default = False,key='win'),
                sg.Text('Use their current pp/badges?'),sg.Checkbox('',
                                                     default = False,key='pp_curr')],
            [sg.Text('What was the score? (You-Them)*:'),
                sg.InputText(size=(5,5),key='my_score'),
                sg.InputText(size=(5,5),key='their_score')],
            [sg.Text('Use date?:'),sg.Checkbox('',default = False,key='has_date')],
            [sg.Text('Date of match:  Day', pad=(0,0)),
                sg.InputText(size=(3,5),key='day'),sg.Text('Month', pad=(0,0)),
                sg.InputText(size=(3,5),key='month'),sg.Text('Year', pad=(0,0)),
                sg.InputText(size=(7,5),key='year')],
            [sg.Ok(), sg.Cancel()],
            [sg.Text("* = must be filled")]]

    win2 = sg.Window('Add Match', layout_add)
    
    while True:
        error_message = ''
        event2, values2 = win2.read()
        if event2 == sg.WIN_CLOSED or event2 == 'Cancel': # Close Window
            close_gui(win2)
            break
        
        elif event2 == 'Ok':
            if values2["password"] == '':
                error_message+= "API Key empty \n"
            if values2["user_id"] == '':
                error_message+= "Username empty \n"
            if values2['has_date']:
                try:
                    x = datetime.date(int(values2["year"]),int(values2["month"]),int(values2["day"]))
                except:
                    error_message+= "Invalid Time \n"
                
            if error_message != '':
                sg.popup('Error', error_message)
            else:
                call_sql(values2, event2,window, conn)

    return None, None

def call_sql(values2,event2,window,conn):
    c = conn.cursor()
    user_data = api_caller.call(values2)

    if user_data != None:       
        sql_handler.add_data(conn,
            """INSERT INTO opponents VALUES (:username,:osu_id,:country,
            :badges, :pp, :rank_world,:rank_country, :date,
            :team_name, :tourney_name, :my_score,:their_score,:win, :mode)""",
            {'username':user_data["username"],
            'osu_id':user_data["osu_id"],'country':user_data["country"],
            'badges':user_data["badges"],'pp':user_data["pp"],
            'rank_world':user_data["rank_world"],'rank_country':user_data["rank_country"],
            'date':user_data["date"],'team_name':user_data["team_name"],
            'tourney_name':user_data["tourney_name"],'my_score':user_data["my_score"],
            'their_score':user_data["their_score"],'win':user_data["win"],
            'mode':user_data["mode"]})

        #update country button here
        #check if button can be clickable
        #temporary workaround to search key by value
        if [k for k,v in pycountry_dict.items() if v == user_data["country"]] != []:
            country_full = [k for k,v in pycountry_dict.items() if v == user_data["country"]][0]

        try:
            country_full = pycountry.countries.get(alpha_2=user_data["country"])

        except:
            print('Not an abbreviation')

        else:
            update_buttons(window,country_full.name)
            update_background(window,country_full.name,c)
    else:
        sg.popup('Error', "Invalid Player")
        
        
#AN: Netherland Antilles split up, but transitionally reserved        
#AP: Does not exist
#EU: Exceptionally Reserved
#XK: Temporarily assigned to Kosovo, otherwise a user-assigned code

pycountry_dict = {"Asia Pacific Region": "AP", "European Union": "EU",
                  "Kosovo":"XK","Netherland Antilles":"AN"}

def does_country_exist(country):
    #Checks if country in dict or in pycountry
    return (country in pycountry_dict) or (pycountry.countries.get(name=country) != None)

def check_country_exists(flag,c):
    #This is repetitive of update_buttons
    #This will check if country in db when app STARTS
    if flag in pycountry_dict:
        country = pycountry_dict[flag]
        
    else:
        try:
            country = pycountry.countries.get(name=flag).alpha_2
        except:
            print("Does not have an abbreviation")
            
    amount = c.execute("SELECT count (DISTINCT osu_id) FROM opponents WHERE country = ?",(country,)).fetchone()[0]

    return amount == 0

def update_buttons(window, country):
    #Will collect all buttons and see if there's a country
    #in the database, if so, the buttons are enabled
    window[country].update(disabled=False)

def change_color(flag,c):
    #Will check how many UNIQUE players in db. Will color button
    #depending on amount
    
    if flag in pycountry_dict:
        country = pycountry_dict[flag]
        
    else:
        try:
            country = pycountry.countries.get(name=flag).alpha_2
        except:
            print("Does not have an abbreviation")
            
    amount = c.execute("SELECT count(DISTINCT osu_id) FROM opponents WHERE country = ?",(country,)).fetchone()[0]

    if amount >= 1 and amount < 5:
        return "White"
    elif amount >= 5 and amount < 10:
        return "Orange"
    elif amount >= 10 and amount < 20:
        return "Green"
    elif amount >= 20 and amount < 35:
        return "Blue"
    elif amount >= 35 and amount < 50:
        return "Purple"
    elif amount >= 50 and amount < 75: 
        return "Brown"
    elif amount >= 75 and amount < 100:
        return "Black"
    elif amount >= 100: 
        return "Pink"
    
    return "Grey"
    
def update_background(window, country, c):
    #updates the button color
    window[country].update(button_color=('grey',change_color(country,c)))

def close_gui(window):
    window.close()

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidTimeError(Error):
    "Raised when the datetime entered is invalid"
    pass

class InvalidScore(Error):
    "Raised when the score is invalid"
    pass
