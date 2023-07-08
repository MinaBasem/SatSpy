import sys
import os
import re
import json
import requests
import geocoder
import pandas as pd
from bs4 import BeautifulSoup
from PyQt5 import QtWebEngineWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QAbstractItemView, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidgetItem, QLineEdit, QComboBox, QLabel, QSplashScreen, QSpacerItem, QSizePolicy, QFrame, QCheckBox, QCompleter, QTableWidget, QPlainTextEdit
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import operator
from functools import reduce

default_norad_id = 25544
def generateMap(norad_id):
    string = '''<!DOCTYPE HTML>
    <head>
    </head>
    <body style="width:20%; height:100%;">
        <div>
            <script>
                var norad_n2yo = '{0}';
                var size_n2yo = 'large';
                var allpasses_n2yo = '1';
                var map_n2yo = '3';
            </script>
            <script type="text/javascript" src="https://www.n2yo.com/js/widget-tracker.js"></script>
        </div>
    </body>'''.format(norad_id)

    with open('map.html', 'w') as file:
        file.write(string)

generateMap(default_norad_id)

n2yo_API_key = "HMD6AC-Q39DWN-F3S3XJ-5215"

satellite_name_id_df = pd.read_csv("sat_name_id_file.csv")
satellite_name_id_df["Combined"] = satellite_name_id_df['OBJECT_NAME'].astype(str) + " - " + satellite_name_id_df["NORAD_CAT_ID"].astype(str)
combined = list(satellite_name_id_df["Combined"])

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

def get_sat_details(link):
    response = requests.get(link)
    content = response.content.decode('utf-8')

    with open('n2yo.txt', 'w') as f:
        f.write(content)

    with open('n2yo.txt', 'r') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    sat_description = soup.find(id="satinfo").find_all("br")[-1].next_sibling

    match_sat_name = re.search(r'<H1>(.*?)</H1>', content)
    match_norad_id = re.search(r'<B>NORAD ID</B>\s*:\s*(\d+)\s*<a', content)
    match_int_code = re.search(r'<B>Int\'l Code</B>\s*:\s*(.+)\s*<a', content)
    match_period = re.search(r'<B>Period</B>\s*:\s*(.+)\s*<a', content)
    launch_site = re.search(r'<B>Launch site</B>\s*:\s*(.*?)\s*<br/>', content)

    if match_sat_name and match_norad_id and match_int_code and match_period and launch_site:
        return sat_description, match_sat_name.group(1), int(match_norad_id.group(1)), match_int_code.group(1), match_period.group(1), launch_site.group(1)
    else:
        return None, None, None, None, None, None

def obtainData(sat_id):   
    userLocation = geocoder.ip('me')
    data = requests.get("https://api.n2yo.com/rest/v1/satellite/positions/{0}/{1}/{2}/0/10800/&apiKey={3}".format(sat_id, userLocation.lat, userLocation.lng, n2yo_API_key))
    data = data.text
    obj = json.loads(data)
    sat_location_df = pd.json_normalize(obj['positions'])
    json_formatted_str = json.dumps(obj, indent= 6)
    with open("location.json", "w") as outfile:
        outfile.write(json_formatted_str)

    sat_latitudes = sat_location_df['satlatitude'].values.tolist()
    sat_longitudes = sat_location_df['satlongitude'].values.tolist()
    sat_altitude = sat_location_df['sataltitude'].values.tolist()

    return sat_latitudes, sat_longitudes, sat_altitude

class Main(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('SatSpy 1.0')
        generateMap(25544)
        CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
        self.map_view = os.path.join(CURRENT_DIR, "map.html")

        self.web = QtWebEngineWidgets.QWebEngineView()
        self.web.page().settings().setAttribute(QWebEngineSettings.ShowScrollBars, False)
        self.web.load(QtCore.QUrl.fromLocalFile(self.map_view))
        self.web.resize(200, 600)

        self.exitBtn = QPushButton('Exit', self)
        self.exitBtn.resize(self.exitBtn.sizeHint())
        self.exitBtn.clicked.connect(self.close)

        self.searchBtn = QPushButton('Search', self)
        self.searchBtn.resize(self.searchBtn.sizeHint())
        self.searchBtn.clicked.connect(self.searchButtonFunc)

        searchBox_Layout = QVBoxLayout()
        horizontalLine = QLabel("")
        horizontalLine.setFrameStyle(QFrame.HLine)
        self.satSearchBox = QLineEdit()
        sat_name_id_completer = QCompleter(combined)
        sat_name_id_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

        searchbox_grid_layout = QGridLayout()
        searchbox_grid_layout.addWidget(self.satSearchBox, 1, 0)
        searchbox_grid_layout.addWidget(self.searchBtn, 1, 1)
        self.satSearchBox.setCompleter(sat_name_id_completer)
        self.description_label = QLabel("Satellite Description: ")
        self.description_box = QPlainTextEdit(self)
        self.description_box.insertPlainText("")
        self.description_box.setReadOnly(True)
        self.description_box.toPlainText()
        searchBox_Layout.addWidget(QLabel("Find a satellite by Name or ID: "))
        searchBox_Layout.addLayout(searchbox_grid_layout)
        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.table = QTableWidget(5, 2)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.horizontalHeader().resizeSection(0, 100)
        self.table.horizontalHeader().resizeSection(1, 130)
        self.table.setItem(0, 0, QTableWidgetItem("Name:"))
        self.table.item(0, 0).setFlags(Qt.NoItemFlags)
        self.table.item(0, 0).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(0, 1, QTableWidgetItem(""))
        self.table.item(0, 1).setFlags(Qt.NoItemFlags)
        self.table.item(0, 1).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(1, 0, QTableWidgetItem("NORAD ID:"))
        self.table.item(1, 0).setFlags(Qt.NoItemFlags)
        self.table.item(1, 0).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(1, 1, QTableWidgetItem(""))
        self.table.item(1, 1).setFlags(Qt.NoItemFlags)
        self.table.item(1, 1).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(2, 0, QTableWidgetItem("Int'l Code:"))
        self.table.item(2, 0).setFlags(Qt.NoItemFlags)
        self.table.item(2, 0).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(2, 1, QTableWidgetItem(""))
        self.table.item(2, 1).setFlags(Qt.NoItemFlags)
        self.table.item(2, 1).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(3, 0, QTableWidgetItem("Period:"))
        self.table.item(3, 0).setFlags(Qt.NoItemFlags)
        self.table.item(3, 0).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(3, 1, QTableWidgetItem(""))
        self.table.item(3, 1).setFlags(Qt.NoItemFlags)
        self.table.item(3, 1).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(4, 0, QTableWidgetItem("Launch site:"))
        self.table.item(4, 0).setFlags(Qt.NoItemFlags)
        self.table.item(4, 0).setForeground(QBrush(QColor(255, 255, 255)))
        self.table.setItem(4, 1, QTableWidgetItem(""))
        self.table.item(4, 1).setFlags(Qt.NoItemFlags)
        self.table.item(4, 1).setForeground(QBrush(QColor(255, 255, 255)))

        left_Grid_Layout = QGridLayout()
        left_Grid_Layout.addLayout(searchBox_Layout, 1, 0, QtCore.Qt.AlignTop)
        left_Grid_Layout.addWidget(horizontalLine, 2, 0)
        left_Grid_Layout.addWidget(self.description_label, 3, 0)
        left_Grid_Layout.addWidget(self.description_box, 4, 0)
        left_Grid_Layout.addWidget(self.table, 5, 0)
        left_Grid_Layout.addItem(verticalSpacer, 6, 0)
        left_Grid_Layout.addWidget(self.exitBtn, 7, 0)
        left_Grid_Layout.setSpacing(15)

        h_Layout = QHBoxLayout(self)
        h_Layout.addLayout(left_Grid_Layout)
        h_Layout.addWidget(self.web, 3)

    def searchButtonFunc(self):
        sat_details = self.satSearchBox.text()
        sat_details = sat_details.split(' - ')
        sat_latitude, sat_longitude, sat_altitude = obtainData(sat_details[1])
        def countList(lst1, lst2):
            return reduce(operator.add, zip(lst1, lst2))
        sat_telemetry = countList(sat_latitude, sat_longitude)
        sat_telemetry = [sat_telemetry[idx:idx+2] for idx in range(0, len(sat_telemetry), 2)]
        with open("telemetry.txt", "w") as file:
            for element in sat_telemetry:
                file.write(str(element) + "," + "\n")
        with open("altitudes.txt", "w") as file:
            for element in sat_altitude:
                file.write(str(element) + "," + "\n")

        sat_description, sat_name, norad_id, int_code, sat_period, launch_site = get_sat_details("https://www.n2yo.com/satellite/?s={0}".format(sat_details[1]))
        print(sat_name, norad_id, int_code, sat_period, launch_site)

        generateMap(sat_details[1])
        self.web.load(QtCore.QUrl.fromLocalFile(self.map_view))
        self.description_box.setPlainText("{0}".format(sat_description))
        self.table.item(0, 1).setText("{0}".format(sat_name))
        self.table.item(1, 1).setText("{0}".format(norad_id))
        self.table.item(2, 1).setText("{0}".format(int_code))
        self.table.item(3, 1).setText("{0}".format(sat_period))
        self.table.item(4, 0).setTextAlignment(QtCore.Qt.AlignTop)
        self.table.item(4, 1).setText("{0}".format(launch_site))
        self.table.resizeRowsToContents()
        print(sat_description)

app = QApplication(sys.argv)
main = Main()
main.show()
main.setFixedWidth(1142)
main.setFixedHeight(730)
app.exec_()