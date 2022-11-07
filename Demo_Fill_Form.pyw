#!/usr/bin/env python
import PySimpleGUI as sg
import configparser
import json
import asyncio
import pandas as pd
import csv

from datetime import date, datetime


from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)

'''
    Example of GUI
'''




# some functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient('api', api_id, api_hash)



async def main():
    sg.theme('TanBlue')
    await client.start()
    me = await client.get_me()
 
    layout = [
        [sg.Text(' ' * 15), sg.Text('Telegram Message Tracker', size=(30, 1), font=("Helvetica", 25))],
        [sg.Text('Input channel url or user Id', font=("Helvetica", 16))],
        [sg.InputText('https://t.me/letradingfrancais', key='in1', font=("Helvetica", 13))],
     
        [sg.Text('_' * 80)],
        [sg.Text('Choose a path to export', size=(35, 1), font=("Helvetica", 16))],
        [sg.InputText('Default Folder', key='path', font=("Helvetica", 13)), sg.Button('Export')],
        [sg.MLine(default_text='', disabled=True, size=(70, 6),
                  key='result'),]
    ]

    window = sg.Window('Form Fill Demonstration', layout, default_element_size=(40, 1), grab_anywhere=False)

    while True:
        
        event, values = window.read(timeout=1000)
        
        if event == 'Export':
            filename = sg.popup_get_file('Save Settings', save_as=True, no_window=True, file_types=(('CSV files', '*.csv'), ('ALL Files', '*.* *'),))
            if filename == '':
                break
            with open(filename, 'w', encoding='UTF8', newline='') as f:
                channelId = values['in1']

                displayText = ''

                if channelId.isdigit():
                    entity = PeerChannel(int(channelId))
                else:
                    entity = channelId

                writer = csv.writer(f)
                my_channel = await client.get_entity(entity)

                offset_id = 0
                limit = 100
                all_messages = []
                total_messages = 0
                total_count_limit = 0

                while True:
                    displayText += "Current Offset ID is:" + str(offset_id) + "; Total Messages:" + str(total_messages) +'\n'
                    history = await client(GetHistoryRequest(
                        peer=my_channel,
                        offset_id=offset_id,
                        offset_date=None,
                        add_offset=0,
                        limit=limit,
                        max_id=0,
                        min_id=0,
                        hash=0
                    ))
                    if not history.messages:
                        break
                    messages = history.messages
                    for message in messages:
                        all_messages.append(message.to_dict())
                        printdata = [message.message, message.date]
                        writer.writerow(printdata)
                    offset_id = messages[len(messages) - 1].id
                    total_messages = len(all_messages)
                    if total_count_limit != 0 and total_messages >= total_count_limit:
                        break
                    

                window['result'].update(displayText)
                window['path'].update(filename)
                window.SaveToDisk(filename)
            
        #     # save(values)
        # elif event == 'LoadSettings':
        #     filename = sg.popup_get_file('Load Settings', no_window=True)
        #     window.LoadFromDisk(filename)
            # load(form)
        elif event in ('Exit', None):
            break

    window.close()

with client:
    
        if __name__ == '__main__':
            client.loop.run_until_complete(main())
