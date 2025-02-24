#Dynamic Inventory Generator

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QPushButton, QLabel, QLineEdit,
                             QFormLayout, QDialog, QMessageBox, QComboBox,
                             QGroupBox, QScrollArea, QListWidgetItem, QTableWidget,
                             QTableWidgetItem, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt
import sys
import json
import os

# Gestion des machines et des ports
machines = []  # Stocke les machines (nom, username, password)
sections = []  # Stocke les sections (nom, ports)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(SCRIPT_DIR, "data.json")
INVENTORY_FILE = os.path.join(SCRIPT_DIR, "inventory.ini")


class MachineDialog(QDialog):
    def __init__(self, parent=None, machine=None):
        super().__init__(parent)
        self.machine = machine
        self.setWindowTitle("Ajouter une machine" if not machine else "Modifier une machine")
        layout = QFormLayout()
        self.name_input = QLineEdit(machine["name"] if machine else "")
        self.user_input = QLineEdit(machine["username"] if machine else "")
        self.pass_input = QLineEdit(machine["password"] if machine else "")
        layout.addRow("Nom:", self.name_input)
        layout.addRow("Username:", self.user_input)
        layout.addRow("Password:", self.pass_input)

        self.ok_button = QPushButton("Ajouter" if not machine else "Modifier")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_data(self):
        return self.name_input.text(), self.user_input.text(), self.pass_input.text()

class SectionDialog(QDialog):
    def __init__(self, parent=None, section=None):
        super().__init__(parent)
        self.section = section
        self.setWindowTitle("Ajouter une section" if not section else "Modifier une section")
        layout = QFormLayout()
        self.name_input = QLineEdit(section["name"] if section else "")
        layout.addRow("Nom:", self.name_input)

        self.ok_button = QPushButton("Ajouter" if not section else "Modifier")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_data(self):
        return self.name_input.text()

class PortDialog(QDialog):
    def __init__(self, section_name, parent=None, port=None):
        super().__init__(parent)
        self.port = port
        self.setWindowTitle(f"Ajouter un port à {section_name}" if not port else f"Modifier un port de {section_name}")
        layout = QFormLayout()
        self.name_input = QLineEdit(port["name"] if port else "")
        self.mac_input = QLineEdit(port["mac"] if port else "")
        self.ip_input = QLineEdit(port["ip"] if port else "")
        layout.addRow("Nom:", self.name_input)
        layout.addRow("MAC:", self.mac_input)
        layout.addRow("IP:", self.ip_input)

        self.ok_button = QPushButton("Ajouter" if not port else "Modifier")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_data(self):
        return self.name_input.text(), self.mac_input.text(), self.ip_input.text()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion des Ports et Machines")
        self.setGeometry(100, 100, 1000, 600)

        main_layout = QHBoxLayout()

        # Tableau des machines
        machine_group = QGroupBox("Machines")
        machine_layout = QVBoxLayout()
        self.machine_table = QTableWidget(0, 4)
        self.machine_table.setHorizontalHeaderLabels(["Nom", "Username", "Password", "Actions"])
        self.machine_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.add_machine_btn = QPushButton("Ajouter Machine")
        self.add_machine_btn.clicked.connect(self.add_machine)
        machine_layout.addWidget(self.machine_table)
        machine_layout.addWidget(self.add_machine_btn)
        machine_group.setLayout(machine_layout)
        main_layout.addWidget(machine_group)

        # Liste des sections et ports
        sections_group = QGroupBox("Sections et Ports")
        sections_layout = QVBoxLayout()
        
        self.sections_scroll_area = QScrollArea()
        self.sections_scroll_area.setWidgetResizable(True)
        self.sections_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self.sections_widget = QWidget()
        self.sections_layout = QVBoxLayout()
        self.sections_widget.setLayout(self.sections_layout)

        self.sections_scroll_area.setWidget(self.sections_widget)
        self.add_section_btn = QPushButton("Ajouter Section")
        self.add_section_btn.clicked.connect(self.add_section)

        sections_layout.addWidget(self.sections_scroll_area)
        sections_layout.addWidget(self.add_section_btn)
        sections_group.setLayout(sections_layout)
        main_layout.addWidget(sections_group)

        # Bouton de génération
        self.generate_btn = QPushButton("Générer inventory.ini")
        self.generate_btn.clicked.connect(self.generate_inventory)
        main_layout.addWidget(self.generate_btn)

        self.setLayout(main_layout)

        self.load_data()

    def update_table_height(self, table):
        # On s'assure que les hauteurs de lignes sont à jour
        table.resizeRowsToContents()
        total_height = table.horizontalHeader().height()  # hauteur de l'en-tête horizontal
        for row in range(table.rowCount()):
            total_height += table.rowHeight(row)
        # On ajoute la largeur du cadre (généralement 2*frameWidth)
        table.setFixedHeight(total_height + 2 * table.frameWidth())

    def add_machine(self, machine=None):
        dialog = MachineDialog(self, machine)
        if dialog.exec_():
            name, user, password = dialog.get_data()
            if name and user and password:
                if machine:
                    machine["name"] = name
                    machine["username"] = user
                    machine["password"] = password
                else:
                    machines.append({"name": name, "username": user, "password": password})
                self.update_machine_table()
                self.update_all_port_machine_combos()
                self.save_data()

    def update_machine_table(self):
        self.machine_table.setRowCount(0)
        for row, machine in enumerate(machines):
            self.machine_table.insertRow(row)
            self.machine_table.setItem(row, 0, QTableWidgetItem(machine["name"]))
            self.machine_table.setItem(row, 1, QTableWidgetItem(machine["username"]))
            self.machine_table.setItem(row, 2, QTableWidgetItem(machine["password"]))
            edit_btn = QPushButton("Modifier")
            edit_btn.clicked.connect(lambda _, m=machine: self.add_machine(m))
            delete_btn = QPushButton("Supprimer")
            delete_btn.clicked.connect(lambda _, m=machine: self.delete_machine(m))
            btn_layout = QHBoxLayout()
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(delete_btn)
            btn_widget = QWidget()
            btn_widget.setLayout(btn_layout)
            self.machine_table.setCellWidget(row, 3, btn_widget)

    def delete_machine(self, machine):
        machines.remove(machine)
        self.update_machine_table()
        self.update_all_port_machine_combos()
        self.save_data()

    def add_section(self, section=None):
        dialog = SectionDialog(self, section)
        if dialog.exec_():
            name = dialog.get_data()
            if name:
                if section:
                    section["name"] = name
                else:
                    sections.append({"name": name, "ports": []})
                self.update_sections()
                self.save_data()

    def update_sections(self):
        # Clear existing sections
        for i in reversed(range(self.sections_layout.count())):
            widget = self.sections_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        for section in sections:
            self.add_section_widget(section)

    def add_section_widget(self, section):
        section_group = QGroupBox(section["name"])
        section_layout = QVBoxLayout()

        port_table = QTableWidget(0, 5)
        port_table.setHorizontalHeaderLabels(["Nom", "MAC", "IP", "Machine", "Actions"])
        port_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Supprimer Scrollbar et étendre à l'infini
        port_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        port_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        add_port_btn = QPushButton("Ajouter Port")
        add_port_btn.clicked.connect(lambda: self.add_port(section, port_table))
        edit_section_btn = QPushButton("Modifier Section")
        edit_section_btn.clicked.connect(lambda: self.add_section(section))
        delete_section_btn = QPushButton("Supprimer Section")
        delete_section_btn.clicked.connect(lambda: self.delete_section(section))

        section_layout.addWidget(port_table)
        section_layout.addWidget(add_port_btn)
        section_layout.addWidget(edit_section_btn)
        section_layout.addWidget(delete_section_btn)

        section_group.setLayout(section_layout)
        self.sections_layout.addWidget(section_group)

        self.sections_layout.addStretch(1)

        for port in section["ports"]:
            self.add_port_widget(port_table, port, section)

    def delete_section(self, section):
        sections.remove(section)
        self.update_sections()
        self.save_data()

    def add_port(self, section, port_table, port=None):
        dialog = PortDialog(section["name"], self, port)
        if dialog.exec_():
            name, mac, ip = dialog.get_data()
            if name and mac and ip:
                if port:
                    port["name"] = name
                    port["mac"] = mac
                    port["ip"] = ip
                    self.update_port_widget(port_table, port, section)
                else:
                    port = {"name": name, "mac": mac, "ip": ip, "machine": None}
                    section["ports"].append(port)
                    self.add_port_widget(port_table, port, section)
                self.save_data()
                self.update_sections()

    def add_port_widget(self, port_table, port, section):
        row = port_table.rowCount()
        port_table.insertRow(row)
        port_table.setItem(row, 0, QTableWidgetItem(port["name"]))
        port_table.setItem(row, 1, QTableWidgetItem(port["mac"]))
        port_table.setItem(row, 2, QTableWidgetItem(port["ip"]))
        machine_combo = QComboBox()
        machine_combo.addItem("Aucune")
        for machine in machines:
            machine_combo.addItem(machine["name"])
        machine_combo.setCurrentText(port["machine"] if port["machine"] else "Aucune")
        machine_combo.currentTextChanged.connect(lambda text, p=port: self.update_port_machine(p, text))
        port_table.setCellWidget(row, 3, machine_combo)

        edit_btn = QPushButton("Modifier")
        edit_btn.clicked.connect(lambda _, p=port, t=port_table, s=section: self.modify_port(p, t, s))
        delete_btn = QPushButton("Supprimer")
        delete_btn.clicked.connect(lambda _, p=port, t=port_table: self.delete_port(p, t))
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        port_table.setCellWidget(row, 4, btn_widget)

        self.update_table_height(port_table)

    def modify_port(self, port, port_table, section):
        dialog = PortDialog(section["name"], self, port)
        if dialog.exec_():
            name, mac, ip = dialog.get_data()
            if name and mac and ip:
                port["name"] = name
                port["mac"] = mac
                port["ip"] = ip
                self.update_port_widget(port_table, port, section)
                self.update_sections()
                self.save_data()


    def update_port_widget(self, port_table, port, section):
        for row in range(port_table.rowCount()):
            if port_table.item(row, 0).text() == port["name"]:
                port_table.setItem(row, 1, QTableWidgetItem(port["mac"]))
                port_table.setItem(row, 2, QTableWidgetItem(port["ip"]))
                machine_combo = port_table.cellWidget(row, 3)
                machine_combo.setCurrentText(port["machine"] if port["machine"] else "Aucune")
                break
        
        self.update_table_height(port_table)
        # Mise à jour des QComboBox des machines
        self.update_port_machine_combos()


    def delete_port(self, port, port_table):
        section = next((s for s in sections if port in s["ports"]), None)
        if section:
            section["ports"].remove(port)
            self.update_sections()
            self.save_data()

    def update_all_port_machine_combos(self):
        # Parcours de tous les widgets contenus dans sections_layout
        for i in range(self.sections_layout.count()):
            widget = self.sections_layout.itemAt(i).widget()
            if widget and isinstance(widget, QGroupBox):
                table = widget.findChild(QTableWidget)
                if table:
                    for row in range(table.rowCount()):
                        combo = table.cellWidget(row, 3)
                        if combo and isinstance(combo, QComboBox):
                            # Conserver la valeur actuelle (si valide)
                            current_value = combo.currentText()
                            combo.clear()
                            combo.addItem("Aucune")
                            for machine in machines:
                                combo.addItem(machine["name"])
                            # Restaurer l'ancienne valeur si elle existe dans la nouvelle liste
                            if current_value in [m["name"] for m in machines]:
                                combo.setCurrentText(current_value)
                            else:
                                combo.setCurrentText("Aucune")

    def update_port_machine_combos(self):
        # Pour chaque section et chaque port, nous mettons à jour le QComboBox
        for section in sections:
            for port in section["ports"]:
                for row in range(self.sections_widget.findChild(QTableWidget).rowCount()):
                    # On cherche la ligne correspondant au port
                    if self.sections_widget.findChild(QTableWidget).item(row, 0).text() == port["name"]:
                        machine_combo = self.sections_widget.findChild(QTableWidget).cellWidget(row, 3)
                        if isinstance(machine_combo, QComboBox):
                            current_text = machine_combo.currentText()
                            machine_combo.clear()
                            machine_combo.addItem("Aucune")
                            for machine in machines:
                                machine_combo.addItem(machine["name"])
                            machine_combo.setCurrentText(port["machine"] if port["machine"] else "Aucune")
                        break


    def update_port_machine(self, port, machine_name):
        port["machine"] = machine_name if machine_name != "Aucune" else None
        self.save_data()

    def generate_inventory(self):
        inventory_data = ""
        for section in sections:
            inventory_data += f"[{section['name']}]\n"
            for port in section["ports"]:
                if port["machine"]:
                    machine = next((m for m in machines if m["name"] == port["machine"]), None)
                    if machine:
                        inventory_data += f"{machine['name']} ansible_host={port['ip']} ansible_user={machine['username']} ansible_password={machine['password']} ansible_become_pass={machine['password']} ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n"
        try:
            with open(INVENTORY_FILE, "w") as file:
                file.write(inventory_data)
            QMessageBox.information(self, "Succès", f"inventory.ini généré avec succès dans {INVENTORY_FILE} !")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'écrire le fichier inventory.ini : {e}")


    def save_data(self):
        data = {
            "machines": machines,
            "sections": sections
        }
        with open(SAVE_FILE, "w") as file:
            json.dump(data, file)

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as file:
                data = json.load(file)
                global machines, sections
                machines = data.get("machines", [])
                sections = data.get("sections", [])
                self.update_machine_table()
                self.update_sections()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
