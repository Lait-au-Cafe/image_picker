import argparse
import glob
import sys
import os
import json
import datetime
import re

parser = argparse.ArgumentParser()
parser.add_argument("target_dir", help="Path to directory where target images are placed. ")
parser.add_argument("--dataset_name", required=True, help="The name of dataset. Used to identify dataset. Give any name you like. ")
args = parser.parse_args()

# Search for the cache of the last session. 
last_cache_data = {}
cache_candidates = glob.glob(".cache_{}_*".format(args.dataset_name))
regexp = re.compile(".cache_" + args.dataset_name + r"_[0-9]{8}-[0-9]{6}$")
cache_candidates = list(filter(lambda path: regexp.search(path), cache_candidates))
if len(cache_candidates) != 0:
    cache_latest = sorted(cache_candidates)[-1]
    with open(cache_latest, mode='r', encoding='utf-8') as cache_file:
        last_cache_data = json.load(cache_file)

# cache of this session
today = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")
cache_data = last_cache_data
cache_filepath = os.path.dirname(os.path.abspath(__file__)) + "/.cache_{}_{}".format(args.dataset_name, today)
def update_cache(key, value):
    cache_data[key] = value
    print(cache_data)
    with open(cache_filepath, mode='w', encoding='utf-8') as f:
        json.dump(cache_data, f)

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot

class ImagePanel(QWidget):
    def __init__(self, app, src_path):
        super().__init__()
        self.src_path = src_path
        self.is_selected = False
        self.initUI(app)

    def initUI(self, app):
        layout = QHBoxLayout()
        self.setLayout(layout)

        scale = 0.5
        image = QImage(self.src_path)
        image = image.scaled(image.width() * scale, image.height() * scale)
        pixmap = QPixmap.fromImage(image)
        image_label = QLabel()
        image_label.scaleFactor = 1.
        image_label.setPixmap(pixmap)
        image_label.setStyleSheet("border: 5px solid gray;")
        layout.addWidget(image_label)
        self.image_label = image_label

        self.setAttribute(Qt.WA_Hover, True)
        self.enterEvent = lambda e: app.setOverrideCursor(Qt.PointingHandCursor)
        self.leaveEvent = lambda e: app.restoreOverrideCursor()
        self.mouseReleaseEvent = self.onClick

    def onClick(self, event):
        self.is_selected = not self.is_selected
        if self.is_selected:
            self.image_label.setStyleSheet("border: 5px solid limegreen;")
        else:
            self.image_label.setStyleSheet("border: 5px solid gray;")

class ImageListPanel(QWidget):
    def __init__(self, app, image_path_list, start_index = 0, width = 1300):
        super().__init__()
        self.img_path_list = image_path_list
        self.width = width
        self.images_per_page = 32
        self.last_image_index = start_index
        self.image_panels = []
        self.initUI(app)

    def initUI(self, app):
        layout = QGridLayout()
        self.setLayout(layout)

        self.next_page()
        
        size = self.sizeHint()
        self.setFixedSize(size.width(), size.height())

    def next_page(self):
        for panel in self.image_panels:
            self.layout().removeWidget(panel)
        self.image_panels = []

        max_width = self.width
        width = 0
        x, y = (-1, 0)
        start_idx = self.last_image_index
        end_idx = self.last_image_index + self.images_per_page
        image_path_list = self.img_path_list[start_idx:end_idx]
        for img_path in image_path_list:
            image_panel = ImagePanel(app, img_path)
            image_panel_size = image_panel.sizeHint()
            width += image_panel_size.width()
            if width < max_width: x += 1
            else: x, y, width = (0, y + 1, image_panel_size.width())
            self.image_panels.append(image_panel)
            self.layout().addWidget(image_panel, y, x)
        self.last_image_index = end_idx
        update_cache('last_index', start_idx)

class MainPanel(QWidget):
    def __init__(self, app, image_path_list, output_file, start_index = 0):
        super().__init__()
        self.output_file = output_file
        self.initUI(app, image_path_list, start_index)

    def initUI(self, app, image_path_list, start_index):
        self.setWindowTitle("Image Picker")
        layout = QVBoxLayout()
        self.setLayout(layout)

        image_list_panel = ImageListPanel(app, image_path_list, start_index)
        layout.addWidget(image_list_panel)
        self.image_list_panel = image_list_panel

        submit_button = QPushButton("Submit [Space]")
        submit_button.setToolTip("Submit selected images. ")
        submit_button.clicked.connect(self.onSubmitButtonPressed)
        font = submit_button.font()
        font.setPointSize(48)
        font.setBold(True)
        font = submit_button.setFont(font)
        layout.addWidget(submit_button)

    #     self.KeyPressEvent = self.onKeyDown

    # def onKeyDown(self, event):
    #     print("KeyPress")

    @pyqtSlot()
    def onSubmitButtonPressed(self):
        print("Submit. ")
        image_panels = self.image_list_panel.image_panels
        for image_panel in image_panels:
            if image_panel.is_selected:
                # print("Image path:", image_panel.src_path)
                self.output_file.write(image_panel.src_path + "\n")
                self.output_file.flush()
        self.image_list_panel.next_page()


with open(args.dataset_name + ".txt", mode='a', encoding='utf-8') as f:
    img_paths = []
    img_paths.extend(glob.glob(args.target_dir + "/*.jpg"))
    img_paths.extend(glob.glob(args.target_dir + "/*.png"))

    app = QApplication(sys.argv)
    window = MainPanel(app, img_paths, f, last_cache_data.get('last_index') or 0)
    window.show()
    sys.exit(app.exec_())