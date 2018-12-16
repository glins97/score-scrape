#!/usr/bin/env python
# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import re
import time
import cPickle
import os
from bs4 import BeautifulSoup
import sys

class Player():
    def __init__(self, id, name, **kwargs):
        self.id = id
        self.name = name
        self.url = "https://www.whoscored.com/Players/{}/History/".format(id)

        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

    def update_data(self, driver):
        driver.get(self.url)
        btns = driver.find_element_by_id("player-tournament-stats-options").find_elements_by_xpath(".//*")[1::2][:-1]
        data_types = ['sumary_data', 'defensive_data', 'offensive_data', 'passing_data']
        final_data = {}
        failed = False
        for index, btn in enumerate(btns):
            try:
                data = []
                btn.click()
                if index > 0:
                    time.sleep(1)
                soup = BeautifulSoup(driver.find_element_by_id("top-player-stats-summary-grid").get_attribute('outerHTML'), 'lxml')
                for row in soup.find_all('tr'):
                    row_data = []
                    for column in row.find_all('td'):
                        row_data.append(column.text.strip())
                    data.append(row_data)
                final_data[data_types[index]] = data
            except:
                failed = True
                print 'FAILED ON', self.name, 'CONTINUING...'
        for attr in final_data:
            setattr(self, attr, final_data[attr])

        if not failed:
            self.save()

    def save(self):
        with open('{}/players/{}.pkl'.format(os.path.abspath(''), self.id), 'wb') as fd:
            cPickle.dump(self, fd)

    def __str__(self):
        return '{}, {}'.format(self.name, self.id)

class Parser():
    players = []

    def __init__(self, league_url):
        self.league_url = league_url

    def run(self):
        self._get_players_data()

    def _get_players(self):
        self.players = []
        files = []
        for file in os.listdir("players/"):
            if file.endswith(".pkl"):
                files.append(os.path.join("players/", file))

        if files:
            for file in files:
                with open(file, 'rb') as fd:
                    self.players.append(cPickle.load(fd))
            return

        driver = webdriver.Firefox()
        driver.get(self.league_url)
        table_source = driver.find_element_by_id("statistics-table-summary").get_attribute('innerHTML')
        all_players_btn = driver.find_elements_by_class_name("listbox")[1].find_elements_by_class_name("option ")[1]
        all_players_btn.click()

        while table_source == driver.find_element_by_id("statistics-table-summary").get_attribute('innerHTML'):
            time.sleep(0.1)
        table_source = driver.find_element_by_id("statistics-table-summary").get_attribute('innerHTML')

        while "clickable" in driver.find_element_by_id("next").get_attribute("class"):
            for id, name in re.findall("""<a class="player-link" href="/Players/(\d+?)/Show/.+?">(.+?)</a>""", table_source):
                self.players.append(Player(id, name))

            time.sleep(0.5)
            driver.find_element_by_id("next").click()

            while table_source == driver.find_element_by_id("statistics-table-summary").get_attribute('innerHTML'):
                time.sleep(0.1)
            table_source = driver.find_element_by_id("statistics-table-summary").get_attribute('innerHTML')

        for id, name in re.findall("""<a class="player-link" href="/Players/(\d+?)/Show/.+?">(.+?)</a>""", table_source):
            self.players.append(Player(id, name))

        for player in self.players:
            player.save()

    def _get_players_data(self):
        if not self.players:
            self._get_players()

        players = [player for player in self.players if not hasattr(player, 'sumary_data')]
        size = len(players)
        driver = webdriver.Firefox() if players else None
        for index, player in enumerate(players):
            index += 1
            START_TIME = time.time()
            player.update_data(driver)
            sys.stdout.write("{}/{}, {:.2f}%, ETA: {:.2f}m\t\r".format(index, size, index*100.0/size, (size - 1 - index) * (time.time() - START_TIME)/60.0 ))
            sys.stdout.flush()


league_url = 'https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/7361/Stages/16368/PlayerStatistics/England-Premier-League-2018-2019'
Parser(league_url).run()
