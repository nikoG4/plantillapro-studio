from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem


class DataTableWidget(QTableWidget):
    def set_rows(self, rows: list[dict[str, str]]) -> None:
        columns = sorted({key for row in rows for key in row.keys()})
        if "nombre" in columns:
            columns.remove("nombre")
            columns.insert(0, "nombre")
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, name in enumerate(columns):
                self.setItem(r, c, QTableWidgetItem(str(row.get(name, ""))))
        self.resizeColumnsToContents()

    def rows(self) -> list[dict[str, str]]:
        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount())]
        data: list[dict[str, str]] = []
        for r in range(self.rowCount()):
            row = {}
            for c, header in enumerate(headers):
                item = self.item(r, c)
                row[header] = item.text() if item else ""
            if any(value.strip() for value in row.values()):
                data.append(row)
        return data

    def add_empty_row(self) -> None:
        if self.columnCount() == 0:
            self.setColumnCount(1)
            self.setHorizontalHeaderLabels(["nombre"])
        self.insertRow(self.rowCount())

    def delete_selected_rows(self) -> None:
        for row in sorted({index.row() for index in self.selectedIndexes()}, reverse=True):
            self.removeRow(row)

