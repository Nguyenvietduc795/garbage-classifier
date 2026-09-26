"""
GIAO DIEN DESKTOP HIEN DAI BANG PyQt5 CHO MODEL PHAN LOAI RAC
----------------------------------------------------------------
File nay dung lai cac ham trong phan_loai_rac.py (phai de 2 file
CUNG THU MUC), chi them phan giao dien - khong doi logic AI.

Cai thu vien truoc khi chay:
    pip install torch torchvision opencv-python pillow numpy PyQt5

Chay:
    python giao_dien_pyqt.py
"""

import sys

# QUAN TRONG - PHAI import phan_loai_rac (keo theo torch) TRUOC PyQt5.
# Tren Windows, PyQt5 va torch cung dong goi thu vien Intel MKL/OpenMP.
# Neu PyQt5 nap truoc thi torch khong khoi tao duoc DLL va bao loi:
#   OSError: [WinError 1114] ... Error loading "...\torch\lib\c10.dll"
# Dao thu tu la het. Dung chuyen dong import nay xuong duoi.
from phan_loai_rac import (
    load_model_and_labels,
    predict_trash,
    GOI_Y_XU_LY,
)

import cv2
import numpy as np

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QFileDialog, QMessageBox,
    QProgressBar, QSizePolicy, QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QColor

NGUONG_TIN_CAY = 0.6

# ======================================================================
# BANG MAU & STYLESHEET (QSS) - noi tap trung toan bo phong cach giao dien
# ======================================================================
MAU_CHINH = "#2e7d32"
MAU_CHINH_DAM = "#1b5e20"
MAU_CHINH_NHAT = "#66bb6a"
MAU_NEN = "#eef2ee"
MAU_THE = "#ffffff"
MAU_CANH_BAO = "#ef6c00"

STYLESHEET = f"""
QMainWindow {{
    background-color: {MAU_NEN};
}}
QLabel#tieuDe {{
    color: {MAU_CHINH_DAM};
    font-size: 22px;
    font-weight: 700;
}}
QLabel#phuDe {{
    color: #666;
    font-size: 12px;
}}
QFrame#theVideo, QFrame#theKetQua {{
    background-color: {MAU_THE};
    border-radius: 16px;
}}
QLabel#khungVideo {{
    background-color: #1a1a1a;
    border-radius: 12px;
    color: #aaa;
    font-size: 13px;
}}
QPushButton {{
    background-color: {MAU_CHINH};
    color: white;
    border: none;
    border-radius: 20px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {MAU_CHINH_DAM};
}}
QPushButton:disabled {{
    background-color: #bbb;
}}
QPushButton#nutTat {{
    background-color: {MAU_CANH_BAO};
}}
QPushButton#nutTat:hover {{
    background-color: #b95300;
}}
QLabel#nhanClassTen {{
    color: #333;
    font-size: 12px;
    font-weight: 600;
}}
QLabel#nhanClassPct {{
    color: #666;
    font-size: 12px;
}}
QProgressBar {{
    border: none;
    border-radius: 6px;
    background-color: #e2e8e2;
    height: 12px;
    text-align: center;
}}
QProgressBar::chunk {{
    border-radius: 6px;
    background-color: {MAU_CHINH_NHAT};
}}
QLabel#hopGoiY {{
    background-color: #e8f5e9;
    border-left: 5px solid {MAU_CHINH};
    border-radius: 10px;
    padding: 14px;
    font-size: 13px;
    color: #222;
}}
QLabel#hopGoiYCanhBao {{
    background-color: #fff3e0;
    border-left: 5px solid {MAU_CANH_BAO};
    border-radius: 10px;
    padding: 14px;
    font-size: 13px;
    color: #222;
}}
QLabel#tieuDeKetQua {{
    color: {MAU_CHINH_DAM};
    font-size: 15px;
    font-weight: 700;
}}
QLabel#trangThai {{
    color: #888;
    font-size: 11px;
}}
"""


def lam_moi_style(widget):
    """Bat Qt ve lai style sau khi doi objectName (vi QSS chi ap dung khi widget duoc 'polish' lai)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def them_bong_do(widget, do_mo=25, do_lem=(0, 3)):
    """Them hieu ung do bong nhe cho 1 widget, giup giao dien co chieu sau."""
    bong = QGraphicsDropShadowEffect()
    bong.setBlurRadius(do_mo)
    bong.setOffset(*do_lem)
    bong.setColor(QColor(0, 0, 0, 40))
    widget.setGraphicsEffect(bong)


class TrashClassifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phan loai rac thong minh")
        self.resize(1020, 620)

        self.model = None
        self.class_names = []
        self.cap = None
        self.webcam_dang_chay = False

        self.thanh_do = {}  # ten_class -> (QProgressBar, QLabel phan tram)

        self._xay_dung_giao_dien()

        self.timer_webcam = QTimer()
        self.timer_webcam.timeout.connect(self._cap_nhat_khung_hinh_webcam)

        QTimer.singleShot(100, self._nap_model)

    # ------------------------------------------------------------------
    # XAY DUNG GIAO DIEN
    # ------------------------------------------------------------------
    def _xay_dung_giao_dien(self):
        trung_tam = QWidget()
        self.setCentralWidget(trung_tam)
        layout_goc = QVBoxLayout(trung_tam)
        layout_goc.setContentsMargins(24, 18, 24, 10)
        layout_goc.setSpacing(4)

        # --- Tieu de ---
        nhan_tieu_de = QLabel("\u267b  Phan loai rac thong minh")
        nhan_tieu_de.setObjectName("tieuDe")
        layout_goc.addWidget(nhan_tieu_de)

        nhan_phu_de = QLabel("Mo anh hoac bat webcam de nhan dien loai rac")
        nhan_phu_de.setObjectName("phuDe")
        layout_goc.addWidget(nhan_phu_de)
        layout_goc.addSpacing(12)

        # --- Khung noi dung chinh: 2 cot ---
        layout_noi_dung = QHBoxLayout()
        layout_noi_dung.setSpacing(18)
        layout_goc.addLayout(layout_noi_dung, stretch=1)

        layout_noi_dung.addWidget(self._tao_the_video(), stretch=6)
        layout_noi_dung.addWidget(self._tao_the_ket_qua(), stretch=4)

        # --- Thanh trang thai duoi cung ---
        self.nhan_trang_thai = QLabel("Dang nap model...")
        self.nhan_trang_thai.setObjectName("trangThai")
        layout_goc.addWidget(self.nhan_trang_thai)

    def _tao_the_video(self):
        the = QFrame()
        the.setObjectName("theVideo")
        them_bong_do(the)

        layout = QVBoxLayout(the)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.nhan_video = QLabel("Chua co anh / video")
        self.nhan_video.setObjectName("khungVideo")
        self.nhan_video.setAlignment(Qt.AlignCenter)
        self.nhan_video.setMinimumSize(480, 400)
        self.nhan_video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.nhan_video, stretch=1)

        layout_nut = QHBoxLayout()
        layout_nut.setSpacing(10)
        layout_nut.addStretch()

        self.nut_mo_anh = QPushButton("Mo anh")
        self.nut_mo_anh.setEnabled(False)
        self.nut_mo_anh.clicked.connect(self.mo_anh)
        layout_nut.addWidget(self.nut_mo_anh)

        self.nut_webcam = QPushButton("Bat Webcam")
        self.nut_webcam.setEnabled(False)
        self.nut_webcam.clicked.connect(self.toggle_webcam)
        layout_nut.addWidget(self.nut_webcam)

        layout_nut.addStretch()
        layout.addLayout(layout_nut)

        return the

    def _tao_the_ket_qua(self):
        the = QFrame()
        the.setObjectName("theKetQua")
        them_bong_do(the)

        layout = QVBoxLayout(the)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        nhan_tieu_de = QLabel("Ket qua du doan")
        nhan_tieu_de.setObjectName("tieuDeKetQua")
        layout.addWidget(nhan_tieu_de)
        layout.addSpacing(6)

        self.layout_thanh_do = QVBoxLayout()
        self.layout_thanh_do.setSpacing(10)
        layout.addLayout(self.layout_thanh_do)

        layout.addSpacing(16)

        nhan_tieu_de_goi_y = QLabel("Goi y xu ly")
        nhan_tieu_de_goi_y.setObjectName("tieuDeKetQua")
        layout.addWidget(nhan_tieu_de_goi_y)

        self.nhan_goi_y = QLabel("Chua co du doan nao.")
        self.nhan_goi_y.setObjectName("hopGoiY")
        self.nhan_goi_y.setWordWrap(True)
        layout.addWidget(self.nhan_goi_y)

        layout.addStretch()
        return the

    def _tao_thanh_do_cho_tung_class(self):
        # Xoa cac widget cu (neu co) truoc khi tao lai
        while self.layout_thanh_do.count():
            muc = self.layout_thanh_do.takeAt(0)
            if muc.widget():
                muc.widget().deleteLater()

        self.thanh_do = {}
        for ten in self.class_names:
            hang = QHBoxLayout()
            hang.setSpacing(8)

            nhan_ten = QLabel(ten)
            nhan_ten.setObjectName("nhanClassTen")
            nhan_ten.setFixedWidth(70)
            hang.addWidget(nhan_ten)

            thanh = QProgressBar()
            thanh.setRange(0, 100)
            thanh.setValue(0)
            thanh.setTextVisible(False)
            hang.addWidget(thanh, stretch=1)

            nhan_pct = QLabel("0%")
            nhan_pct.setObjectName("nhanClassPct")
            nhan_pct.setFixedWidth(36)
            hang.addWidget(nhan_pct)

            self.layout_thanh_do.addLayout(hang)
            self.thanh_do[ten] = (thanh, nhan_pct)

    # ------------------------------------------------------------------
    # NAP MODEL
    # ------------------------------------------------------------------
    def _nap_model(self):
        try:
            self.model, self.class_names = load_model_and_labels()
            self._tao_thanh_do_cho_tung_class()
            self.nhan_trang_thai.setText(f"Da nap model - {len(self.class_names)} loai rac")
            self.nut_mo_anh.setEnabled(True)
            self.nut_webcam.setEnabled(True)
        except Exception as loi:
            QMessageBox.critical(self, "Loi nap model",
                                  f"Khong nap duoc model.\nChi tiet: {loi}")
            self.nhan_trang_thai.setText("Loi nap model - xem thong bao")

    # ------------------------------------------------------------------
    # MO 1 ANH TU MAY TINH
    # ------------------------------------------------------------------
    def mo_anh(self):
        if self.webcam_dang_chay:
            self.toggle_webcam()

        duong_dan, _ = QFileDialog.getOpenFileName(
            self, "Chon anh", "", "Anh (*.jpg *.jpeg *.png *.bmp)"
        )
        if not duong_dan:
            return

        frame = cv2.imread(duong_dan)
        if frame is None:
            QMessageBox.warning(self, "Loi", "Khong doc duoc file anh nay.")
            return

        self._du_doan_va_cap_nhat(frame)
        self._hien_anh_len_giao_dien(frame)

    # ------------------------------------------------------------------
    # BAT / TAT WEBCAM
    # ------------------------------------------------------------------
    def toggle_webcam(self):
        if not self.webcam_dang_chay:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.warning(self, "Loi", "Khong mo duoc webcam.")
                return
            self.webcam_dang_chay = True
            self.nut_webcam.setText("Tat Webcam")
            self.nut_webcam.setObjectName("nutTat")
            lam_moi_style(self.nut_webcam)
            self.timer_webcam.start(30)  # ~30 khung hinh/giay
        else:
            self.webcam_dang_chay = False
            self.timer_webcam.stop()
            if self.cap:
                self.cap.release()
            self.nut_webcam.setText("Bat Webcam")
            self.nut_webcam.setObjectName("")
            lam_moi_style(self.nut_webcam)

    def _cap_nhat_khung_hinh_webcam(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if ret:
            self._du_doan_va_cap_nhat(frame)
            self._hien_anh_len_giao_dien(frame)

    # ------------------------------------------------------------------
    # DU DOAN VA CAP NHAT KET QUA
    # ------------------------------------------------------------------
    def _du_doan_va_cap_nhat(self, frame):
        if self.model is None:
            return

        label, confidence, all_preds = predict_trash(frame, self.model, self.class_names)

        for ten, score in zip(self.class_names, all_preds):
            thanh, nhan_pct = self.thanh_do[ten]
            thanh.setValue(int(score * 100))
            nhan_pct.setText(f"{score * 100:.0f}%")

        if confidence >= NGUONG_TIN_CAY:
            goi_y = GOI_Y_XU_LY.get(label, "Chua co goi y cho loai nay.")
            self.nhan_goi_y.setObjectName("hopGoiY")
            self.nhan_goi_y.setText(f"<b>{label} ({confidence * 100:.1f}%)</b><br><br>{goi_y}")
        else:
            self.nhan_goi_y.setObjectName("hopGoiYCanhBao")
            self.nhan_goi_y.setText(
                "Chua chac chan - dua vat gan camera hon hoac chinh anh sang."
            )
        # Ap dung lai stylesheet vi objectName vua doi
        lam_moi_style(self.nhan_goi_y)

    # ------------------------------------------------------------------
    # HIEN THI ANH/VIDEO LEN GIAO DIEN
    # ------------------------------------------------------------------
    def _hien_anh_len_giao_dien(self, frame_bgr):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        anh_qt = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(anh_qt).scaled(
            self.nhan_video.width(), self.nhan_video.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self.nhan_video.setPixmap(pixmap)

    # ------------------------------------------------------------------
    # DONG UNG DUNG
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self.webcam_dang_chay = False
        self.timer_webcam.stop()
        if self.cap:
            self.cap.release()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", 10))

    cua_so = TrashClassifierApp()
    cua_so.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
