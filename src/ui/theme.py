from PySide6.QtGui import QColor, QPalette

def create_dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(35, 39, 46))
    palette.setColor(QPalette.WindowText, QColor(245, 246, 250))
    palette.setColor(QPalette.Base, QColor(42, 46, 56))
    palette.setColor(QPalette.AlternateBase, QColor(45, 49, 58))
    palette.setColor(QPalette.ToolTipBase, QColor(42, 46, 56))
    palette.setColor(QPalette.ToolTipText, QColor(245, 246, 250))
    palette.setColor(QPalette.Text, QColor(245, 246, 250))
    palette.setColor(QPalette.Button, QColor(58, 63, 75))
    palette.setColor(QPalette.ButtonText, QColor(245, 246, 250))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(68, 74, 86))
    palette.setColor(QPalette.HighlightedText, QColor(245, 246, 250))
    return palette
