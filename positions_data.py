# -*- coding: utf-8 -*-
"""Posições oficiais dos jogadores (GK/DF/MF/FW) por seleção e número da camisa.

Fonte: listas de escalações oficiais da FIFA WC 2026 (compiladas via Wikipedia,
validadas contra os números de camisa presentes nos arquivos de dados físicos).

Cada string tem 26 posições, na ordem das camisas 1 a 26. O nome da seleção usa
EXATAMENTE a grafia que aparece nos CSVs da FIFA (com acentos), para o
cruzamento por (Team Name + Jersey #) funcionar diretamente.
"""

_RAW = {
    "MEXICO":                  "GK DF DF DF DF MF MF MF FW FW FW GK GK FW DF FW MF MF MF DF FW FW DF MF FW MF",
    "SOUTH AFRICA":            "GK DF DF MF MF DF FW FW FW FW MF FW MF DF FW GK FW DF DF DF DF GK MF DF FW DF",
    "KOREA REPUBLIC":          "GK DF MF DF DF MF FW MF FW MF MF GK DF DF DF DF MF FW MF MF GK DF DF MF MF MF",
    "CZECHIA":                 "GK DF DF DF DF DF DF MF FW FW FW MF FW DF FW GK MF MF FW DF DF MF GK MF MF FW",
    "CANADA":                  "GK DF DF DF DF MF MF MF FW FW MF FW DF MF DF GK FW GK DF FW MF DF DF FW MF FW",
    "BOSNIA AND HERZEGOVINA":  "GK DF DF DF DF MF DF MF FW FW FW GK MF MF MF MF MF DF FW FW DF GK FW DF FW MF",
    "QATAR":                   "GK DF DF DF DF MF FW FW FW FW FW MF DF DF FW DF MF DF FW MF GK GK MF FW DF FW",
    "SWITZERLAND":             "GK DF DF DF DF MF FW MF MF MF FW GK DF MF MF FW FW DF FW MF GK MF FW DF DF FW",
    "BRAZIL":                  "GK MF DF DF MF DF FW MF FW FW FW GK DF DF DF DF MF MF FW MF FW FW GK DF FW FW",
    "HAITI":                   "GK DF DF DF DF MF FW DF FW MF FW GK DF DF FW FW MF FW FW FW FW DF GK DF MF MF",
    "MOROCCO":                 "GK DF DF MF DF MF MF MF FW FW MF GK DF DF MF MF FW DF DF FW FW GK MF MF DF DF",
    "SCOTLAND":                "GK DF DF MF DF DF MF MF FW FW MF GK DF FW DF DF FW FW MF FW GK DF MF DF FW DF",
    "AUSTRALIA":               "GK DF DF DF DF DF FW MF FW FW FW GK MF MF DF DF FW GK DF FW DF MF FW MF DF FW",
    "PARAGUAY":                "GK DF DF DF DF DF MF MF FW MF MF GK DF MF DF MF FW FW FW MF FW GK MF MF FW DF",
    "TÜRKIYE":                 "GK DF DF DF MF MF FW FW FW MF FW GK DF DF DF MF FW DF FW DF FW MF GK FW DF FW",
    "USA":                     "GK DF DF MF DF DF MF MF FW FW FW DF DF MF MF DF MF DF FW FW FW DF DF GK GK FW",
    "CURAÇAO":                 "GK DF DF DF DF MF MF MF FW MF FW FW FW FW MF FW FW DF FW DF MF MF DF DF GK GK",
    "ECUADOR":                 "GK DF DF DF MF DF DF MF FW MF FW GK FW MF MF FW DF MF FW FW MF GK MF FW DF DF",
    "GERMANY":                 "GK DF DF DF MF DF FW MF MF MF FW GK MF FW DF MF MF DF MF MF GK DF MF DF MF FW",
    "CÔTE D'IVOIRE":           "GK DF DF MF DF MF DF MF FW FW FW FW DF FW FW GK DF MF FW DF DF FW GK FW MF MF",
    "JAPAN":                   "GK DF DF DF DF FW MF MF FW MF MF GK MF MF MF DF MF FW FW DF DF DF GK MF DF FW",
    "NETHERLANDS":             "GK DF MF DF DF DF MF MF FW FW FW DF GK MF DF MF FW FW FW MF MF DF GK FW DF MF",
    "SWEDEN":                  "GK DF DF DF DF DF MF DF FW MF FW GK MF DF DF MF FW MF MF DF DF MF GK DF FW FW",
    "TUNISIA":                 "GK DF DF DF DF DF FW FW FW MF MF DF MF MF MF GK MF FW FW DF DF GK DF DF MF MF",
    "CABO VERDE":              "GK DF DF DF DF MF MF MF FW MF MF GK DF MF MF MF MF MF FW FW MF DF GK DF DF MF",
    "SAUDI ARABIA":            "GK DF DF DF DF MF MF FW FW FW FW DF DF DF MF MF FW MF FW FW GK GK MF DF DF DF",
    "SPAIN":                   "GK DF DF DF DF MF FW MF MF FW FW DF GK DF MF MF FW MF FW MF FW DF GK DF FW FW",
    "URUGUAY":                 "GK DF DF DF MF MF MF MF FW MF FW GK DF MF MF DF DF FW FW MF FW MF GK DF MF MF",
    "BELGIUM":                 "GK DF DF DF DF MF MF MF FW FW FW GK GK FW DF DF FW DF MF MF DF MF MF MF DF FW",
    "EGYPT":                   "GK DF DF DF DF DF FW MF FW FW MF FW DF MF DF GK MF MF MF FW MF FW GK DF FW GK",
    "IR IRAN":                 "GK DF DF DF DF MF MF MF FW FW FW GK DF MF MF MF DF FW DF FW MF GK DF FW DF MF",
    "NEW ZEALAND":             "GK DF DF DF DF MF FW MF FW MF MF GK DF MF DF DF FW FW MF MF FW GK MF DF MF DF",
}

# {TEAM_NAME: {jersey_number: position}}
POSITIONS = {
    team: {i + 1: pos for i, pos in enumerate(s.split())}
    for team, s in _RAW.items()
}

POSITION_LABELS = {
    "GK": "Goleiro", "DF": "Defensor", "MF": "Meio-campista", "FW": "Atacante",
}
POSITION_ORDER = ["GK", "DF", "MF", "FW"]


def get_position(team_name, jersey):
    """Retorna GK/DF/MF/FW para (seleção, camisa), ou None se não encontrado."""
    if team_name is None or jersey is None:
        return None
    team = str(team_name).strip().upper()
    try:
        j = int(float(jersey))
    except (ValueError, TypeError):
        return None
    return POSITIONS.get(team, {}).get(j)


# {TEAM_NAME (grafia do CSV): (código de 3 letras, código ISO p/ bandeira)}
TEAM_META = {
    "MEXICO": ("MEX", "mx"), "SOUTH AFRICA": ("RSA", "za"),
    "KOREA REPUBLIC": ("KOR", "kr"), "CZECHIA": ("CZE", "cz"),
    "CANADA": ("CAN", "ca"), "BOSNIA AND HERZEGOVINA": ("BIH", "ba"),
    "QATAR": ("QAT", "qa"), "SWITZERLAND": ("SUI", "ch"),
    "BRAZIL": ("BRA", "br"), "HAITI": ("HAI", "ht"),
    "MOROCCO": ("MAR", "ma"), "SCOTLAND": ("SCO", "gb-sct"),
    "AUSTRALIA": ("AUS", "au"), "PARAGUAY": ("PAR", "py"),
    "TÜRKIYE": ("TUR", "tr"), "USA": ("USA", "us"),
    "CURAÇAO": ("CUW", "cw"), "ECUADOR": ("ECU", "ec"),
    "GERMANY": ("GER", "de"), "CÔTE D'IVOIRE": ("CIV", "ci"),
    "JAPAN": ("JPN", "jp"), "NETHERLANDS": ("NED", "nl"),
    "SWEDEN": ("SWE", "se"), "TUNISIA": ("TUN", "tn"),
    "CABO VERDE": ("CPV", "cv"), "SAUDI ARABIA": ("KSA", "sa"),
    "SPAIN": ("ESP", "es"), "URUGUAY": ("URU", "uy"),
    "BELGIUM": ("BEL", "be"), "EGYPT": ("EGY", "eg"),
    "IR IRAN": ("IRN", "ir"), "NEW ZEALAND": ("NZL", "nz"),
}


def team_code(team_name):
    """Sigla de 3 letras (ex.: 'AUSTRALIA' -> 'AUS'). Fallback: 3 primeiras letras."""
    if team_name is None:
        return "?"
    meta = TEAM_META.get(str(team_name).strip().upper())
    return meta[0] if meta else str(team_name).strip().upper()[:3]


def flag_url(team_name, width=40):
    """URL da bandeira (flagcdn) para a seleção, ou None se desconhecida."""
    if team_name is None:
        return None
    meta = TEAM_META.get(str(team_name).strip().upper())
    return f"https://flagcdn.com/w{width}/{meta[1]}.png" if meta else None
