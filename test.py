import sys
import os
import vtk
import numpy as np
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QMainWindow, QCheckBox, QPushButton, QLabel,
    QVBoxLayout, QWidget
)

import pyvista as pv
from pyvistaqt import QtInteractor


class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, parent, plotter, mesh):
        super().__init__()
        self.plotter = plotter
        self.mesh = mesh
        self.picker = vtk.vtkCellPicker()
        self.left_button_down_pos = None
        self.is_dragging = False
        self.highlight_actor = None
        self.AddObserver("LeftButtonPressEvent", self.left_button_press_event)
        self.AddObserver("LeftButtonReleaseEvent", self.left_button_release_event)
        self.AddObserver("MouseMoveEvent", self.mouse_move_event)
        self.AddObserver("RightButtonPressEvent", self.right_button_press_event)
        self.AddObserver("RightButtonReleaseEvent", self.right_button_release_event)
        self.AddObserver("MouseWheelForwardEvent", self.mouse_wheel_forward_event)
        self.AddObserver("MouseWheelBackwardEvent", self.mouse_wheel_backward_event)
    def get_full_face(self, mesh, start_cell_id, angle_threshold=5.0):
        mesh.compute_normals(cell_normals=True, inplace=True)
        normals = mesh.cell_normals

        start_normal = normals[start_cell_id]
        start_normal = start_normal / np.linalg.norm(start_normal)

        visited = set()
        stack = [start_cell_id]

        face_cells = []

        while stack:
            cid = stack.pop()
            if cid in visited:
                continue
            visited.add(cid)

            normal = normals[cid]
            normal = normal / np.linalg.norm(normal)
            angle = np.degrees(np.arccos(np.clip(np.dot(start_normal, normal), -1.0, 1.0)))

            if angle <= angle_threshold:
                face_cells.append(cid)

                neighbors = mesh.cell_neighbors(cid)
                for n_cid in neighbors:
                    if n_cid not in visited:
                        stack.append(n_cid)

        return mesh.extract_cells(face_cells)

    def left_button_press_event(self, obj, event):
        self.left_button_down_pos = self.plotter.interactor.GetEventPosition()
        self.is_dragging = False

    def mouse_move_event(self, obj, event):
        if self.left_button_down_pos is None:
            self.OnMouseMove()
            return

        curr_pos = self.plotter.interactor.GetEventPosition()
        dx = abs(curr_pos[0] - self.left_button_down_pos[0])
        dy = abs(curr_pos[1] - self.left_button_down_pos[1])
        drag_threshold = 5

        if dx > drag_threshold or dy > drag_threshold:
            self.is_dragging = True
            self.OnMouseMove()
        return

    def left_button_release_event(self, obj, event):
        if not self.is_dragging:
            click_pos = self.plotter.interactor.GetEventPosition()
            self.picker.Pick(click_pos[0], click_pos[1], 0, self.plotter.renderer)
            cell_id = self.picker.GetCellId()
            if cell_id != -1:
                face = self.get_full_face(self.mesh, cell_id, angle_threshold=5.0)

                if self.highlight_actor:
                    self.plotter.remove_actor(self.highlight_actor)

                self.highlight_actor = self.plotter.add_mesh(
                    face, color='red', line_width=5, opacity=0.6, name="highlight"
                )
                self.plotter.render()
        else:
            self.OnLeftButtonUp()

        self.left_button_down_pos = None
        self.is_dragging = False

    def right_button_press_event(self, obj, event):
        self.OnLeftButtonDown()

    def right_button_release_event(self, obj, event):
        self.OnLeftButtonUp()

    def mouse_wheel_forward_event(self, obj, event):
        self.zoom_about_mouse(zoom_in=True)

    def mouse_wheel_backward_event(self, obj, event):
        self.zoom_about_mouse(zoom_in=False)

    def zoom_about_mouse(self, zoom_in=True):
        camera = self.plotter.renderer.GetActiveCamera()
        interactor = self.plotter.interactor
        pos = interactor.GetEventPosition()

        self.picker.Pick(pos[0], pos[1], 0, self.plotter.renderer)
        picked_pos = np.array(self.picker.GetPickPosition())

        if np.allclose(picked_pos, (0, 0, 0)):
            picked_pos = np.array(camera.GetFocalPoint())

        cam_pos = np.array(camera.GetPosition())
        focal = np.array(camera.GetFocalPoint())

        zoom_factor = 1.1 if zoom_in else 1 / 1.1

        cam_to_picked = picked_pos - cam_pos
        focal_to_picked = picked_pos - focal

        new_cam_pos = cam_pos + cam_to_picked * (1 - 1 / zoom_factor)
        new_focal = focal + focal_to_picked * (1 - 1 / zoom_factor)

        camera.SetPosition(*new_cam_pos)
        camera.SetFocalPoint(*new_focal)
        self.plotter.renderer.ResetCameraClippingRange()
        self.plotter.render()


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

        self.saved_label = QLabel("Saved!")
        self.saved_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: green;
                font-weight: bold;
            }
        """)
        self.saved_label.setVisible(False)
        self.overlay_layout.addWidget(self.saved_label)

        self.overlay_widget.setLayout(self.overlay_layout)
        self.overlay_widget.setGeometry(10, 10, 220, 100)

        self.instructions_label = QLabel("🖱 Mouse Controls:\nLeft: Select Face\nRight: Rotate\nMiddle: Pan\nScroll: Zoom", self.plotter.interactor)
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

        self.loading_label = QLabel("Loading model...", self.plotter.interactor)
        self.loading_label.setStyleSheet("""
            QLabel {
                background-color: white;
                color: black;
                padding: 10px;
                font-size: 14px;
                border: 1px solid #aaa;
            }
        """)
        self.loading_label.move(20, 20)
        self.loading_label.show()

        self.mesh = None
        self.actor = None

        self.plotter.add_axes()
        self.plotter.set_background("white")
        self.plotter.camera_position = 'iso'
        self.plotter.show_bounds(grid='back', location='outer', all_edges=True)

        main_layout.addWidget(self.view_container)

        QtCore.QTimer.singleShot(0, lambda: self.load_mesh(stl_path))

    def load_mesh(self, path):
        self.mesh = pv.read(path)
        self.actor = self.plotter.add_mesh(
            self.mesh, color='lightblue', show_edges=False, opacity=1.0
        )

        style = CustomInteractorStyle(self, self.plotter, self.mesh)
        self.plotter.interactor.GetRenderWindow().GetInteractor().SetInteractorStyle(style)

        self.plotter.reset_camera()
        self.plotter.camera.Azimuth(-90)
        self.plotter.render()
        self.loading_label.hide()

    def on_resize(self, event):
        self.instructions_label.move(self.plotter.interactor.width() - 250, 10)
        event.accept()

    def toggle_edges(self, state):
        if self.mesh is None:
            return
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

        self.saved_label.setVisible(True)
        QtCore.QTimer.singleShot(3000, lambda: self.saved_label.setVisible(False))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Set starting folder to Downloads
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    # Use QFileDialog as widget with stricter config
    file_dialog = QtWidgets.QFileDialog(
        None,
        "Select STL File",
        downloads_dir,
        "STL Files (*.stl)"
    )
    file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
    file_dialog.setNameFilter("STL Files (*.stl)")
    file_dialog.setViewMode(QtWidgets.QFileDialog.Detail)
    file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)

    if file_dialog.exec_() == QtWidgets.QDialog.Accepted:
        file_path = file_dialog.selectedFiles()[0]
        viewer = STLViewer(file_path)
        viewer.show()
        sys.exit(app.exec_())
    else:
        print("No STL file selected. Exiting.")
        sys.exit()




