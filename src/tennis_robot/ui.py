from __future__ import annotations

import sys

import cv2
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from .config import load_config
from .pipeline import TennisRobotPipeline


class RobotConsole(QMainWindow):
    def __init__(self, config_path: str = "config/default.yaml"):
        super().__init__()
        self.config = load_config(config_path)
        self.pipeline = TennisRobotPipeline(self.config)
        self.capture = cv2.VideoCapture(int(self.config.source) if self.config.source.isdigit() else self.config.source)
        self.setWindowTitle("Tennis Collection Robot | Vision Console")
        self.resize(1280, 760)
        self.video = QLabel("等待视频源")
        self.video.setMinimumSize(860, 560)
        self.video.setStyleSheet("background:#101820; color:#d6e2e8; font-size:20px;")
        self.video.setAlignment(Qt.AlignCenter)
        self.status = QLabel("READY")
        self.status.setStyleSheet("font-size:18px; font-weight:700; color:#37d39c;")
        self.stats = QLabel("检测数量: 0\n路径长度: 0.00\n推理延迟: 0 ms")
        self.start_button = QPushButton("开始采集")
        self.start_button.clicked.connect(self.toggle)
        layout = QHBoxLayout()
        layout.addWidget(self.video, 3)
        side = QVBoxLayout()
        side.addWidget(QLabel("运行状态"))
        side.addWidget(self.status)
        side.addWidget(QLabel("实时指标"))
        side.addWidget(self.stats)
        side.addStretch()
        side.addWidget(self.start_button)
        layout.addLayout(side, 1)
        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.running = False

    def toggle(self):
        self.running = not self.running
        self.start_button.setText("停止采集" if self.running else "开始采集")
        self.status.setText("RUNNING" if self.running else "READY")
        if self.running:
            self.timer.start(30)
        else:
            self.timer.stop()

    def next_frame(self):
        ok, frame = self.capture.read()
        if not ok:
            self.running = False
            self.status.setText("SOURCE OFFLINE")
            self.timer.stop()
            return
        result = self.pipeline.process(frame)
        rgb = cv2.cvtColor(result.frame, cv2.COLOR_BGR2RGB)
        image = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888)
        self.video.setPixmap(QPixmap.fromImage(image).scaled(self.video.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.stats.setText(f"检测数量: {len(result.detections)}\n路径长度: {result.route_length:.2f}\n推理延迟: {result.latency_ms:.1f} ms")

    def closeEvent(self, event):
        self.timer.stop()
        self.capture.release()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = RobotConsole()
    window.show()
    return app.exec()
