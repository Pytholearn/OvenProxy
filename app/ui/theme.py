"""Dark, Fluent-inspired colour palette and global stylesheet."""

from __future__ import annotations

COLORS: dict[str, str] = {
    "bg": "#16161a",
    "surface": "#1f1f25",
    "surface_alt": "#26262e",
    "surface_hover": "#2d2d37",
    "border": "#34343f",
    "text": "#e8e8ee",
    "text_muted": "#9a9aa6",
    "accent": "#4cc2ff",
    "accent_hover": "#6fcfff",
    "accent_press": "#3aa9e0",
    "success": "#3ad29f",
    "warning": "#ffcf6b",
    "error": "#ff6b6b",
}

LEVEL_COLORS: dict[str, str] = {
    "DEBUG": COLORS["text_muted"],
    "INFO": COLORS["text"],
    "SUCCESS": COLORS["success"],
    "WARNING": COLORS["warning"],
    "ERROR": COLORS["error"],
    "CRITICAL": COLORS["error"],
}


def build_stylesheet() -> str:
    """Return the application-wide Qt Style Sheet."""
    c = COLORS
    return f"""
    * {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
        color: {c['text']};
    }}
    QWidget#Root, QMainWindow {{ background-color: {c['bg']}; }}
    QStackedWidget {{ background-color: {c['bg']}; }}

    /* ---- Sidebar ---- */
    QWidget#Sidebar {{
        background-color: {c['surface']};
        border-right: 1px solid {c['border']};
    }}
    QLabel#AppTitle {{ font-size: 20px; font-weight: 700; color: {c['text']}; }}
    QLabel#AppSubtitle {{ font-size: 11px; color: {c['text_muted']}; }}
    QLabel#StatusLabel {{ font-size: 11px; color: {c['text_muted']}; padding: 6px 4px; }}
    QPushButton#NavButton {{
        text-align: left;
        padding: 10px 14px;
        border: none;
        border-radius: 10px;
        color: {c['text_muted']};
        background-color: transparent;
        font-size: 13px;
    }}
    QPushButton#NavButton:hover {{ background-color: {c['surface_hover']}; color: {c['text']}; }}
    QPushButton#NavButton:checked {{
        background-color: {c['surface_alt']};
        color: {c['accent']};
        font-weight: 600;
    }}

    /* ---- Cards ---- */
    QFrame#Card, QFrame#StatCard {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 14px;
    }}
    QLabel#PageTitle {{ font-size: 22px; font-weight: 700; }}
    QLabel#PageSubtitle {{ font-size: 12px; color: {c['text_muted']}; }}
    QLabel#CardTitle {{ font-size: 12px; color: {c['text_muted']}; font-weight: 600; }}
    QLabel#StatValue {{ font-size: 26px; font-weight: 700; }}
    QLabel#StatCaption {{ font-size: 11px; color: {c['text_muted']}; }}
    QLabel#SectionTitle {{ font-size: 14px; font-weight: 600; }}

    /* ---- Buttons ---- */
    QPushButton {{
        background-color: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 9px;
        padding: 8px 16px;
        color: {c['text']};
    }}
    QPushButton:hover {{ background-color: {c['surface_hover']}; }}
    QPushButton:pressed {{ background-color: {c['border']}; }}
    QPushButton:disabled {{ color: {c['text_muted']}; background-color: {c['surface']}; }}
    QPushButton#Primary {{
        background-color: {c['accent']};
        border: none;
        color: #06222f;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{ background-color: {c['accent_hover']}; }}
    QPushButton#Primary:pressed {{ background-color: {c['accent_press']}; }}
    QPushButton#Primary:disabled {{ background-color: {c['border']}; color: {c['text_muted']}; }}
    QPushButton#Danger {{ background-color: transparent; border: 1px solid {c['error']}; color: {c['error']}; }}
    QPushButton#Danger:hover {{ background-color: rgba(255,107,107,0.12); }}

    /* ---- Inputs ---- */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {{
        background-color: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 7px 10px;
        selection-background-color: {c['accent']};
        selection-color: #06222f;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {{
        border: 1px solid {c['accent']};
    }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background-color: {c['surface_alt']};
        border: 1px solid {c['border']};
        selection-background-color: {c['surface_hover']};
        outline: none;
    }}
    QCheckBox {{ spacing: 8px; }}
    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border: 1px solid {c['border']};
        border-radius: 5px;
        background-color: {c['surface_alt']};
    }}
    QCheckBox::indicator:checked {{ background-color: {c['accent']}; border-color: {c['accent']}; }}

    /* ---- Table ---- */
    QTableView {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        gridline-color: {c['border']};
        selection-background-color: {c['surface_hover']};
        selection-color: {c['text']};
        alternate-background-color: {c['surface_alt']};
    }}
    QTableView::item {{ padding: 4px 6px; }}
    QHeaderView::section {{
        background-color: {c['surface_alt']};
        color: {c['text_muted']};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {c['border']};
        font-weight: 600;
    }}
    QTableCornerButton::section {{ background-color: {c['surface_alt']}; border: none; }}

    /* ---- Progress ---- */
    QProgressBar {{
        background-color: {c['surface_alt']};
        border: none;
        border-radius: 7px;
        height: 14px;
        text-align: center;
        color: {c['text']};
        font-size: 10px;
    }}
    QProgressBar::chunk {{ background-color: {c['accent']}; border-radius: 7px; }}

    /* ---- Lists ---- */
    QListWidget {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{ padding: 8px; border-radius: 8px; }}
    QListWidget::item:hover {{ background-color: {c['surface_hover']}; }}
    QListWidget::item:selected {{ background-color: {c['surface_alt']}; color: {c['accent']}; }}

    /* ---- Scrollbars ---- */
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {c['border']}; border-radius: 5px; min-width: 28px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

    QToolTip {{
        background-color: {c['surface_alt']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 4px 8px;
    }}

    /* ---- Update banner ---- */
    QFrame#UpdateBanner {{
        background-color: rgba(76, 194, 255, 0.16);
        border: none;
        border-bottom: 1px solid {c['accent']};
    }}
    QLabel#BannerText {{ font-weight: 600; color: {c['text']}; }}

    QTextBrowser {{
        background-color: {c['surface']};
        border: none;
    }}
    """
