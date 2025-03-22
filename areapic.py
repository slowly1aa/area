from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QFileDialog, QSlider, QCheckBox, QMessageBox
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QPen
from PyQt6.QtCore import Qt, QRect, QTimer
import sys
import cv2
import numpy as np
import pyautogui
import requests
import datetime
import pygame
import os
import threading
from datetime import timedelta
from io import BytesIO

class ScreenshotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen pattern detection and Discord notifications")
        self.setGeometry(200, 200, 500, 500)
        self.setStyleSheet("background-color: #f5f5f5; border-radius: 10px;")
        
        self.webhook_url = " "
        self.webhook_url_input = QLineEdit(self)
        self.webhook_url_input.setPlaceholderText("請輸入 Discord Webhook URL")
        self.webhook_url_input.setText(self.webhook_url)
        
        self.select_image_btn = QPushButton("選擇目標圖片", self)
        self.select_image_btn.clicked.connect(self.select_image)
        
        self.image_preview = QLabel(self)
        self.image_preview.setFixedSize(200, 200)
        
        self.similarity_label = QLabel("相似度閾值:")
        self.similarity_slider = QSlider(Qt.Orientation.Horizontal)
        self.similarity_slider.setRange(50, 100)
        self.similarity_slider.setValue(75)
        
        self.send_screenshot_checkbox = QCheckBox("發送截圖", self)
        self.send_screenshot_checkbox.setChecked(True)
        
        self.start_detection_btn = QPushButton("開始偵測並發送", self)
        self.start_detection_btn.clicked.connect(self.start_detection)
        
        layout = QVBoxLayout()
        layout.addWidget(self.webhook_url_input)
        layout.addWidget(self.select_image_btn)
        layout.addWidget(self.image_preview)
        layout.addWidget(self.similarity_label)
        layout.addWidget(self.similarity_slider)
        layout.addWidget(self.send_screenshot_checkbox)
        layout.addWidget(self.start_detection_btn)
        self.setLayout(layout)
        
        self.target_image_path = "C:\\test\\forget.png"
        self.sound_file_path = "C:\\test\\find.ogg"
        self.sound_played = False
        self.capture_region = (614, 268, 1316, 407)
        self.setWindowIcon(QIcon('message.ico'))

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇查找的圖片", "C:\\test", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.target_image_path = file_path
            pixmap = QPixmap(file_path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_preview.setPixmap(pixmap)

    def start_detection(self):
        self.sound_played = False
        self.scan_images()

    def scan_images(self):
        screenshot = pyautogui.screenshot(region=self.capture_region)
        screen_np = np.array(screenshot)
        target_img = cv2.imread(self.target_image_path)

        if target_img is None:
            QMessageBox.warning(self, "錯誤", "無法讀取目標圖片！")
            return

        result = cv2.matchTemplate(screen_np, target_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        threshold = self.similarity_slider.value() / 100.0

        if max_val >= threshold:
            self.send_notification()
            if self.send_screenshot_checkbox.isChecked():
                self.send_screenshot_to_discord(screenshot)
            if not self.sound_played:
                self.play_sound()
                self.sound_played = True
        else:
            self.sound_played = False

        QTimer.singleShot(1000, self.scan_images)

    def send_notification(self):
        webhook_url = self.webhook_url_input.text()
        if not webhook_url:
            QMessageBox.warning(self, "錯誤", "請輸入 Discord Webhook URL")
            return

        detection_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        detection_message = f"{detection_time} 偵測到閃光觸發(預計10分後結束)"
        requests.post(webhook_url, data={"content": detection_message})
        
        end_time = datetime.datetime.now() + timedelta(minutes=10)
        end_message = f"{end_time.strftime('%Y-%m-%d %H:%M:%S')} 閃光結束可以進場"
        QTimer.singleShot(600000, lambda: requests.post(webhook_url, data={"content": end_message}))

    def send_screenshot_to_discord(self, screenshot):
        webhook_url = self.webhook_url_input.text()
        if not webhook_url:
            QMessageBox.warning(self, "錯誤", "請輸入 Discord Webhook URL")
            return

        timestamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        image_buffer = BytesIO()
        screenshot.save(image_buffer, format="PNG")
        image_buffer.seek(0)

        response = requests.post(webhook_url, data={"content": f"找到目標圖片！\n時間: {timestamp}"}, files={"file": ("screenshot.png", image_buffer, "image/png")})

        if response.status_code == 200:
            QMessageBox.information(self, "成功", "圖片已發送至 Discord！")
        else:
            QMessageBox.warning(self, "錯誤", f"發送失敗，錯誤碼: {response.status_code}")

    def play_sound(self):
        if os.path.exists(self.sound_file_path):
            pygame.mixer.init()
            pygame.mixer.music.load(self.sound_file_path)
            pygame.mixer.music.play()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenshotApp()
    window.show()
    sys.exit(app.exec())
