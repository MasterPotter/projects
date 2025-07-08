import sys
import os
import vtk
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QMainWindow, QCheckBox, QPushButton, QLabel,
    QVBoxLayout, QWidget
)

import pyvista as pv
from pyvistaqt import QtInteractor

class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        super().__init__()
        self.AddObserver("RightButtonPressEvent", self.right_button_press_event)
        self.AddObserver("RightButtonReleaseEvent", self.right_button_release_event)

    def right_button_press_event(self, obj, event):
        self.OnLeftButtonDown()
        return

    def right_button_release_event(self, obj, event):
        self.OnLeftButtonUp()
        return


class STLViewer(QMainWindow):
    def __init__(self, stl_path):
        super().__init__()

        self.setWindowTitle("STL Viewer")
        self.setGeometry(100, 100, 1000, 800)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        main_layout = QVBoxLayout(self.main_widget)

        self.view_container = QWidget()
        self.view_container.setLayout(QVBoxLayout())
        self.view_container.layout().setContentsMargins(0, 0, 0, 0)

        self.plotter = QtInteractor(self.view_container)
        self.view_container.layout().addWidget(self.plotter.interactor)

        style = CustomInteractorStyle()
        self.plotter.interactor.GetRenderWindow().GetInteractor().SetInteractorStyle(style)

        self.overlay_widget = QWidget(self.plotter.interactor)
        self.overlay_layout = QVBoxLayout()
        self.overlay_layout.setContentsMargins(10, 10, 10, 10)
        self.overlay_layout.setSpacing(10)

        self.edge_checkbox = QCheckBox("Show Triangle Edges")
        self.edge_checkbox.setChecked(False)
        self.edge_checkbox.stateChanged.connect(self.toggle_edges)
        self.edge_checkbox.setStyleSheet("""
            QCheckBox {
                background-color: black;
                color: white;
                padding: 5px;
                border-radius: 5px;
            }
        """)
        self.overlay_layout.addWidget(self.edge_checkbox)

        self.screenshot_button = QPushButton("Take Screenshot")
        self.screenshot_button.clicked.connect(self.take_screenshot)
        self.screenshot_button.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        self.overlay_layout.addWidget(self.screenshot_button)

        self.overlay_widget.setLayout(self.overlay_layout)
        self.overlay_widget.setGeometry(10, 10, 220, 100)

        self.instructions_label = QLabel("🖱 Mouse Controls:\nLeft / Right: Rotate\nMiddle: Pan\nScroll: Zoom", self.plotter.interactor)
        self.instructions_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                padding: 6px;
                border-radius: 6px;
            }
        """)
        self.instructions_label.adjustSize()
        self.instructions_label.move(self.width() - 250, 10)
        self.plotter.interactor.resizeEvent = self.on_resize

        self.mesh = pv.read(stl_path)
        self.actor = self.plotter.add_mesh(
            self.mesh, color='lightblue', show_edges=False, opacity=1.0
        )

        self.plotter.add_axes()
        self.plotter.set_background("white")
        self.plotter.camera_position = 'iso'
        self.plotter.show_bounds(grid='back', location='outer', all_edges=True)

        main_layout.addWidget(self.view_container)

    def on_resize(self, event):
        self.instructions_label.move(self.plotter.interactor.width() - 250, 10)
        event.accept()

    def toggle_edges(self, state):
        show_edges = state == 2
        self.plotter.remove_actor(self.actor)
        self.actor = self.plotter.add_mesh(
            self.mesh, color='lightblue', show_edges=show_edges, opacity=1.0
        )
        self.plotter.render()

    def take_screenshot(self):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(desktop_path, f"stl_screenshot_{timestamp}.png")
        self.plotter.screenshot(filename)
        QtWidgets.QMessageBox.information(self, "Screenshot", f"Saved to:\n{filename}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    viewer = STLViewer("/Users/zoebizzi/Downloads/trophy.stl")
    viewer.show()
    sys.exit(app.exec_())
