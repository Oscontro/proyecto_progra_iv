import requests # type: ignore
import direcciones # type: ignore
import pandas as pd # type: ignore
from PyQt6.QtWidgets import ( # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QAbstractItemView, QDialog, QScrollArea,
    QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt # type: ignore
from PyQt6.QtGui import QFont, QColor, QBrush # type: ignore
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

class APILoader:
    @staticmethod
    def llenar_combo(endpoint, combo, campo_json, incluir_todos=False, inclir_escriba=False):
        
        """
        api_url: URL base (ej. http://api.com)
        endpoint: Archivo PHP (ej. marcas.php)
        combo: El objeto QComboBox
        campo_json: El nombre de la clave en el JSON (ej. 'marca')
        incluir_todos: Si agrega el item "Todos"
        """
        api_url = direcciones.URL.API_BASE_URL
        try:
            response = requests.get(f"{api_url}/{endpoint}")
            response.raise_for_status()
            data = response.json()
            
            # Extraemos la lista de valores
            items = [str(obj[campo_json]) for obj in data]
            
            combo.clear()
            if incluir_todos:
                combo.addItem("Todos")
            elif inclir_escriba:
                combo.addItem("Escriba o seleccione")
            
            combo.addItems(items)
            
        except requests.exceptions.HTTPError as errh:
        # Errores de tipo 404 (No encontrado), 401 (No autorizado), 500 (Error de servidor)
            print(f"Error HTTP: El servidor respondió con código {response.status_code}. Detalle: {errh}")

        data = []
        return data
            
    def llenar_tabla(endpoint):
        api_url = direcciones.URL.API_BASE_URL
        try:
            response = requests.get(f"{api_url}/{endpoint}", timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as errh:
        # Errores de tipo 404 (No encontrado), 401 (No autorizado), 500 (Error de servidor)
            print(f"Error HTTP: El servidor respondió con código {response.status_code}. Detalle: {errh}")

        return []
    
    def generar_excel(self, datos_exportar, nombre_archivo):
        
        datos_a_excel = datos_exportar
        df1 = pd.DataFrame(datos_a_excel)
        
        """Genera reporte Excel"""
        archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte Excel",
            f"{nombre_archivo}",
            "Archivos Excel (*.xlsx)"
        )

        if archivo:
            df1.to_excel(archivo, index=False)
            wb = load_workbook(archivo)
            ws=wb.active
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 5)
                ws.column_dimensions[column].width = adjusted_width
            
            wb.save(archivo)
            QMessageBox.information(self, "Excel Generado",
                                    f"Reporte generado correctamente:\n\n{archivo}")