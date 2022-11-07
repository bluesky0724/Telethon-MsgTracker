#!/usr/bin/env python
import PySimpleGUI as sg
import configparser
import json
import asyncio
import pandas as pd
import csv

from datetime import date, datetime
from threading import Thread
from time import sleep
from eventemitter import EventEmitter

import threading

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)

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

# Config shared variables for read_msg thread

new_messages = False
start_flag = False
end_flag = True
displayText = ''

emitter = EventEmitter()

# Disply to multi line
result = ''

c = threading.Condition()

   
async def _thread_run(filename, chainId, is_real_time):
    # Create the client and connect
    client = TelegramClient('api', api_id, api_hash)
    global displayText
    global new_messages
    async with client:
        await client.start()
        print(str(filename) + " " + str(is_real_time)) 
        with open(filename, 'w', encoding='UTF8', newline='') as f:
            channelId = chainId
            writer = csv.writer(f)

            if channelId.isdigit():
                entity = PeerChannel(int(channelId))
            else:
                entity = channelId

            my_channel = await client.get_entity(entity)

            offset_id = 0
            limit = 100
            all_messages = []
            total_messages = 0
            total_count_limit = 0

            while True:
                c.acquire()
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
                emitter.emit('update_panel', displayText)
                new_messages = True
                c.notify()
                for message in messages:
                    all_messages.append(message.to_dict())
                    printdata = [message.message, message.date]
                    writer.writerow(printdata)
                offset_id = messages[len(messages) - 1].id
                total_messages = len(all_messages)
                if total_count_limit != 0 and total_messages >= total_count_limit:
                    break
                
                c.release()
                    

async def thread_run(filename, chainId, is_real_time):
    await _thread_run(filename, chainId, is_real_time)
 

class Telegram_thread(Thread):
    
    def __init__(self, filename, chainId, is_real_time):
        Thread.__init__(self)
        self.filename = filename
        self.is_real_time = is_real_time
        self.chainId = chainId

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("Read thread started!")
        loop.run_until_complete(thread_run(self.filename, self.chainId, self.is_real_time))
        print("Read thread ended!")
        loop.close()

        
def main():
    sg.theme('TanBlue')
    global new_messages
    global displayText
    
    layout = [
        [sg.Text(' ' * 15), sg.Text('Telegram Message Tracker', size=(30, 1), font=("Helvetica", 25))],
        [sg.Text('Input channel url or user Id', font=("Helvetica", 16))],
        [sg.InputText('https://t.me/letradingfrancais', key='in1', font=("Helvetica", 13))],
       
        [sg.Text('_' * 80)],
        [sg.Text('Choose a path to export', size=(35, 1), font=("Helvetica", 16))],
        [sg.InputText('Default Folder', key='path', font=("Helvetica", 13)), sg.Button('Browse')],
        [sg.Button('Export')],
        [sg.MLine(default_text='', disabled=True, size=(70, 6),
                  key='result'),]
    ]

    window = sg.Window('Form Fill Demonstration', layout, default_element_size=(40, 1), grab_anywhere=False)

    def update_result(event, *args, **kwargs):
        print('%s %s %s', event, args, kwargs)
        window['result'].update(displayText)

    emitter.on('update_panel', update_result)
    

    while True:
        event, values = window.read(timeout=1000)
        c.acquire()
        if new_messages == True:
            window['result'].update(displayText)
            new_messages == False
            c.notify()

        if event == 'Browse':
            filename = sg.popup_get_file('Save Settings', save_as=True, no_window=True, file_types=(('CSV files', '*.csv'), ('ALL Files', '*.* *'),))
            if filename == '':
                break
            window['path'].update(filename)

        if event == 'Export':

            thrd = Telegram_thread(filename=filename, chainId=values['in1'], is_real_time=True)
            thrd.start()

                # window['result'].update(displayText)
                # window['path'].update(filename)
                # window.SaveToDisk(filename)
        #     # save(values)
        # elif event == 'LoadSettings':
        #     filename = sg.popup_get_file('Load Settings', no_window=True)
        #     window.LoadFromDisk(filename)
            # load(form)
        elif event in ('Exit', None):
            break

        c.release()

    window.close()

if __name__ == '__main__':
    main()
