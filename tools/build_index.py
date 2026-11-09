#!/usr/bin/env python3
"""Dựng lại index.html (hub tra cứu) từ frontmatter của 132 lesson.md.
Giữ microcopy đã biên tập (tiêu đề/mô tả/ảnh trong thẻ cũ), bổ sung thẻ mới
cho bài tổng quan, tabs phân hệ, chips RADS, dark mode, table view.

Chạy: python3 tools/build_index.py   (từ thư mục gốc repo)
Idempotent: chạy lại vẫn cho kết quả như nhau.
"""
import html
import os
import re
from pathlib import Path

CERT_LABEL = {"tong-hop-y-van": "Tổng hợp y văn",
              "ca-nguyen-van": "Ca nguyên văn",
              "suy-luan": "Suy luận"}
OV_DESC = "📚 Bài tổng quan hệ: bảng DDx bắt buộc + bài liên quan chéo."
REQUIRED_SCORES = ["LI-RADS", "Lung-RADS", "BI-RADS", "O-RADS", "TI-RADS",
                   "PI-RADS", "Bosniak", "ASPECTS", "Atlanta"]
# Nhãn tab gọn: icon + tên chuyên mục; số bài do JS đếm từ thẻ (refreshTabs).
TABS = [("", "🌐 Tất cả"), ("nguc", "🫁 Ngực"), ("bung", "🩺 Bụng"),
        ("thankinh", "🧠 Thần kinh"), ("msk", "🦴 MSK"), ("mat", "👁️ Mắt"),
        ("vu", "🌸 Vú"), ("spk", "🤰 Sản – Phụ khoa"), ("nhi", "👶 Nhi"), ("dauco", "👃 Đầu Cổ"),
        ("tim", "❤️ Tim"), ("canthiep", "🧰 Can thiệp")]


def spec_of(uid):
    try:
        n = int(str(uid))
    except ValueError:
        return "khac"
    return {0: "nguc", 1: "bung", 2: "thankinh", 3: "msk", 4: "mat",
            5: "vuspk", 6: "nhi", 7: "dauco", 8: "tim", 9: "canthiep"}.get(n // 100, "khac")


# ID 4 chữ số là dải tràn (overflow) — gán phân hệ thủ công cho đúng tab.
SPEC_OVERRIDE = {"6104": "nhi", "6105": "nhi", "6107": "nhi", "6108": "nhi", "6110": "nhi", "6134": "nhi", "6111": "nhi", "6112": "nhi", "6113": "nhi", "6114": "nhi", "6115": "nhi", "6116": "nhi", "6117": "nhi", "6120": "nhi", "6118": "nhi", "6121": "nhi", "1601": "vuspk", "1602": "vuspk", "1604": "vuspk", "1605": "vuspk", "1606": "vuspk", "1607": "vuspk", "1608": "bung", "1609": "vuspk", "1628": "vuspk", "1632": "vuspk", "1630": "vuspk", "1610": "vuspk", "1611": "vuspk", "1636": "vuspk", "1780": "nhi", "1801": "bung", "1803": "nhi", "1805": "nhi", "6102": "nhi", "6103": "nhi", "6701": "nhi", "1622": "dauco", "1633": "bung", "1634": "vuspk", "1635": "vuspk", "1637": "vuspk", "3003": "thankinh", "1627": "mat", "1613": "vuspk", "1614": "vuspk", "1600": "vuspk", "1690": "vuspk", "1691": "vuspk", "1692": "vuspk", "1693": "tim", "1408": "mat", "3004": "nhi", "1618": "vuspk", "1901": "bung", "1902": "bung", "1903": "bung", "1904": "bung", "1905": "bung", "1906": "bung", "1907": "bung", "1623": "vuspk", "1615": "msk", "1626": "vuspk", "1664": "vuspk", "1665": "vuspk", "1616": "vuspk", "1782": "nhi", "1420": "mat", "1421": "mat", "1410": "mat", "1795": "nhi", "1620": "vuspk", "1621": "vuspk", "1624": "vuspk", "1625": "nhi", "1640": "vuspk", "1804": "nhi", "1806": "bung", "1807": "bung", "1809": "bung", "1810": "bung", "3001": "nhi", "3002": "thankinh", "3012": "thankinh", "3013": "thankinh", "3014": "thankinh", "3015": "thankinh", "3016": "thankinh", "3017": "msk", "3018": "thankinh", "3019": "msk", "3020": "thankinh", "3021": "thankinh", "3022": "thankinh", "3024": "thankinh", "3025": "thankinh", "3026": "thankinh", "3027": "thankinh", "3030": "thankinh", "3031": "thankinh", "3032": "thankinh", "3033": "thankinh", "3034": "thankinh", "3035": "thankinh", "3036": "thankinh", "3037": "thankinh", "3038": "thankinh", "3039": "thankinh", "3040": "thankinh", "3041": "thankinh", "3043": "thankinh", "3023": "thankinh", "3046": "thankinh", "3005": "nhi", "3006": "nhi", "3009": "nhi", "3010": "nhi", "3047": "nhi", "3048": "nhi", "1703": "nhi", "1802": "nhi", "6101": "nhi", "6119": "nhi", "3050": "thankinh", "3008": "nhi", "1657": "vuspk", "1661": "vuspk", "1717": "vuspk", "1815": "nhi", "1816": "canthiep", "3011": "bung", "3051": "dauco", "3049": "nhi", "3052": "nhi", "3058": "nhi", "3063": "nhi", "3068": "nhi", "3069": "nhi", "3070": "nhi", "3071": "nhi", "1672": "vuspk", "1673": "vuspk", "3080": "nhi", "3085": "bung", "3087": "bung", "3081": "nhi"}


# ── Phân loại bài ID 4 chữ số (dải tràn) ──────────────────────────────────
# Đã rà tay 141 bài từng nằm ở "Khác" (2026-11). Bài mới ID 4 chữ số:
# hoặc thêm vào CLASSIFY_4D, hoặc gắn tag `vung:` khớp VUNG_SPEC; nếu không
# build_index.py sẽ DỪNG và liệt kê bài chưa phân loại (không được để "Khác").
CLASSIFY_4D = {
    "1984": "bung",   # màng ngăn ruột non do NSAID & CMUSE (tiêu hóa, người lớn)
    "3096": "bung",   # BK polyomavirus nephropathy (ghép thận)
    "3097": "bung",   # hội chứng Zinner (tiết niệu – sinh dục nam)
    "1792": "bung",
    "1793": "nhi",
    "1779": "nhi",
    "1848": "canthiep",
    "1840": "bung",
    "1842": "tim",
    "6162": "tim",
    "3076": "thankinh",
    "3079": "nhi",
    "3084": "bung",
    "1884": "tim",    # thủng vách liên thất sau NMCT cấp
    "6163": "bung",   # viêm đĩa đệm + phình ĐMC nhiễm khuẩn (mạch bụng, người lớn)
    "6164": "dauco",  # u nhú đảo ngược tái phát sau mổ (mũi xoang, người lớn)
    "1900": "tim",    # bóc tách động mạch vành tự phát (SCAD)
    "1936": "bung",   # tụ máu bao cơ thẳng bụng (thành bụng)
    "3086": "nhi",    # CAUTI ở trẻ
    "3089": "nhi",    # thiếu B12 sau ileocystoplasty (theo dõi chuyển hóa ở trẻ)
    "3090": "nhi",    # bacteriuria không triệu chứng ở trẻ có bể chứa ruột
    "3099": "msk",    # KHE người lớn & thể sâu (u mô mềm–mạch máu)
    "3100": "nhi",    # quản lý ruột sau mổ ARM (theo dõi chức năng nhi)
    "3101": "thankinh",  # hội chứng CHANTER (opioid, MRI não)
    "3841": "msk",     # chèn ép thần kinh tọa mạn sau chấn thương/mổ
    "1928": "vuspk",   # áp-xe cơ chậu ở thai phụ (sản khoa)
    "1930": "vuspk",   # sỏi mật không biến chứng ở thai phụ (sản khoa)
    "1871": "vuspk",
    "1402": "mat",
    "1403": "mat",
    "1404": "mat",
    "1405": "mat",
    "1406": "mat",
    "1407": "mat",
    "1409": "mat",
    "1411": "mat",
    "1412": "mat",
    "1413": "mat",
    "1414": "mat",
    "1415": "mat",
    "1416": "mat",
    "1417": "mat",
    "1418": "mat",
    "1419": "mat",
    "1422": "bung",
    "1423": "thankinh",
    "1424": "mat",
    "1425": "mat",
    "1426": "mat",
    "1427": "mat",
    "1428": "mat",
    "1429": "mat",
    "1431": "mat",
    "1432": "mat",
    "1433": "mat",
    "1434": "mat",
    "1435": "mat",
    "1437": "mat",
    "1441": "mat",
    "1443": "mat",
    "1444": "mat",
    "1446": "mat",
    "1447": "mat",
    "1450": "mat",
    "1451": "mat",
    "1452": "mat",
    "1445": "mat",
    "1453": "mat",
    "1837": "mat",
    "1864": "mat",
    "1603": "vuspk",
    "1612": "vuspk",
    "1617": "thankinh",
    "1619": "vuspk",
    "1629": "dauco",
    "1631": "vuspk",
    "1638": "vuspk",
    "1639": "msk",
    "1641": "thankinh",
    "1642": "vuspk",
    "1643": "mat",
    "1644": "nhi",
    "1645": "vuspk",
    "1648": "bung",
    "1649": "vuspk",
    "1650": "msk",
    "1651": "msk",
    "1652": "msk",
    "1653": "vuspk",
    "1654": "vuspk",
    "1655": "vuspk",
    "1656": "vuspk",
    "1659": "thankinh",
    "1660": "bung",
    "1662": "bung",
    "1666": "bung",
    "1667": "bung",
    "1668": "nhi",
    "1669": "vuspk",
    "1670": "bung",
    "1671": "vuspk",
    "1675": "thankinh",
    "1680": "bung",
    "1681": "vuspk",
    "1682": "nhi",
    "1735": "nhi",
    "1683": "bung",
    "1686": "vuspk",
    "1687": "vuspk",
    "1694": "bung",
    "1695": "canthiep",
    "1696": "thankinh",
    "1697": "thankinh",
    "1699": "thankinh",
    "1700": "thankinh",
    "1701": "nhi",
    "1702": "nhi",
    "1704": "dauco",
    "1705": "nhi",
    "1706": "nhi",
    "1707": "dauco",
    "1708": "dauco",
    "1709": "thankinh",
    "1710": "thankinh",
    "1722": "thankinh",
    "1716": "dauco",
    "1684": "dauco",
    "1685": "msk",
    "1711": "canthiep",
    "1713": "dauco",
    "1718": "msk",
    "1719": "nhi",
    "1749": "nhi",
    "1720": "nhi",
    "1723": "vuspk",
    "1725": "vuspk",
    "1726": "vuspk",
    "1729": "canthiep",
    "1730": "bung",
    "1731": "nhi",
    "1734": "nhi",
    "1751": "nhi",
    "1752": "nhi",
    "1753": "nhi",
    "1754": "nhi",
    "1755": "nhi",
    "1756": "nhi",
    "1757": "nhi",
    "1758": "mat",
    "1761": "dauco",
    "1769": "dauco",
    "1770": "dauco",
    "1775": "thankinh",
    "1776": "nguc",
    "1790": "bung",
    "1791": "vuspk",
    "1777": "dauco",
    "1764": "dauco",
    "1736": "bung",
    "1737": "bung",
    "1744": "vuspk",
    "1745": "vuspk",
    "1746": "vuspk",
    "1747": "vuspk",
    "1740": "nhi",
    "1778": "nhi",
    "1781": "thankinh",
    "1783": "thankinh",
    "1784": "thankinh",
    "1785": "thankinh",
    "1786": "thankinh",
    "1787": "thankinh",
    "1788": "nguc",
    "1789": "nguc",
    "1794": "vuspk",
    "1796": "vuspk",
    "1797": "thankinh",
    "1798": "thankinh",
    "1799": "nhi",
    "1823": "canthiep",
    "1808": "canthiep",
    "1811": "bung",
    "1812": "nhi",
    "1813": "nhi",
    "1829": "nhi",
    "1830": "nhi",
    "1814": "bung",
    "1817": "bung",
    "1818": "bung",
    "1819": "bung",
    "1820": "bung",
    "1821": "bung",
    "1825": "bung",
    "1828": "thankinh",
    "1822": "canthiep",
    "1831": "canthiep",
    "1832": "canthiep",
    "1833": "canthiep",
    "1834": "canthiep",
    "1839": "bung",
    "1855": "canthiep",
    "1856": "bung",
    "1908": "bung",
    "1912": "bung",
    "1909": "bung",
    "1910": "bung",
    "1913": "bung",
    "1914": "bung",
    "1915": "bung",
    "1916": "bung",
    "3007": "thankinh",
    "3028": "thankinh",
    "3029": "thankinh",
    "3044": "nhi",
    "3045": "nhi",
    "3053": "nhi",
    "3059": "thankinh",
    "3061": "bung",
    "3062": "nhi",
    "3065": "nhi",
    "3066": "dauco",
    "3064": "canthiep",
    "1918": "bung",
    "1919": "bung",
    "3072": "nhi",
    "3073": "nhi",
    "3074": "nhi",
    "3075": "nhi",
    "3078": "bung",
    "3840": "msk",
    "6100": "nhi",
    "6106": "nhi",
    "6109": "nhi",
    "6122": "nhi",
    "6123": "nhi",
    "6124": "nhi",
    "6126": "nhi",
    "6127": "nhi",
    "6128": "nhi",
    "6129": "nhi",
    "6130": "nhi",
    "6131": "nhi",
    "6132": "nhi",
    "6133": "nhi",
    "6135": "nhi",
    "6136": "nhi",
    "6137": "nhi",
    "6142": "nhi",
    "6700": "nhi",
    "6702": "nhi",
    "6703": "nhi",
    "6704": "nhi",
    "6705": "nhi",
    "3095": "canthiep",   # tổn thương ĐM đùi–chậu sau can thiệp nội mạch ở trẻ
    "1845": "nhi",        # bàng quang thần kinh ở trẻ dị tật tủy sống
    "6159": "nhi",        # rò khí quản – động mạch không tên ở trẻ
}

# Rà tay 2026-11: bài Tai–Mũi–Họng nằm lẫn ở Mắt / Thần kinh → Đầu Cổ (TMH)
RECLASS = {
    "205": "dauco", "208": "dauco", "230": "dauco", "233": "dauco", "235": "dauco",
    "236": "dauco", "237": "dauco", "238": "dauco", "244": "dauco",
    "478": "dauco", "497": "dauco", "1649": "spk", "558": "msk",
    # Ưu tiên chuyên ngành MẮT: bài có tổn thương mắt chính (kể cả nhi khoa / thần kinh - nhãn khoa)
    "1641": "mat", "3018": "mat", "3021": "mat", "6104": "mat",
    "6106": "mat", "6131": "mat", "6132": "mat", "658": "mat", "1422": "mat",
    "276": "mat", "278": "mat", "279": "mat",
    # bài vật lý/protocol liều (đi cùng nhóm 932/935/937)
    "9420": "canthiep", "9421": "canthiep", "9422": "canthiep", "1679": "msk", "3054": "nhi", "3023": "dauco", "3046": "dauco", "3050": "dauco",
    # 972 là chủ đề chẩn đoán/hình ảnh tuyến giáp – trung thất (không phải can thiệp) → Đầu Cổ
    "972": "dauco",
}
# Bài "Vú & SPK" cũ → tách: Vú (breast) vs Sản – Phụ khoa
BREAST_TOKENS = {"vu", "num-vu", "hach-nach", "ho-nach", "tuyen-vu", "implant-nguc"}
BREAST_TITLE = r"vú|breast|implant|bi-rads|nhũ|pash|bia-alcl|mammo"


def split_vuspk(uid, tags, title):
    if uid == "500":            # bài tổng quan chung cho cả 2 chuyên khoa
        return "spk"
    toks = set(re.findall(r"vung:([A-Za-z0-9_.-]+)", tags))
    if toks & BREAST_TOKENS or re.search(BREAST_TITLE, title, re.I):
        return "vu"
    return "spk"


VUNG_SPEC = {
    # mắt
    "vong-mac": "mat", "hac-vong-mac": "mat", "vong-mac-hac-mac": "mat", "mat": "mat",
    "hoc-mat": "mat", "nhan-cau": "mat", "nhan-cau-hoc-mat": "mat", "hoang-diem": "mat",
    "giac-mac": "mat", "gai-thi": "mat", "than-kinh-thi": "mat", "the-thuy-tinh": "mat",
    "tien-phong": "mat", "goc-tien-phong": "mat", "hac-mac": "mat", "be-mat-nhan-cau": "mat",
    "cung-mac": "mat", "o-mat": "mat", "mi": "mat", "the-mi": "mat", "dich-kinh": "mat",
    # đầu cổ
    "dau-mat-co": "dauco", "xuong-mat": "dauco", "so-mat": "dauco", "ham-mat": "dauco",
    "ham-duoi": "dauco", "loi-cau-ham-duoi": "dauco", "xuong-ham": "dauco",
    "khop-thai-duong-ham": "dauco", "mui": "dauco", "xoang": "dauco", "tuyen-giap": "dauco",
    "tuyen-bot": "dauco", "tuyen-mang-tai": "dauco", "tuyen-nuoc-bot": "dauco",
    "xuong-thai-duong": "dauco", "xuong-da": "dauco", "tai-giua": "dauco", "tai-trong": "dauco",
    "tai": "dauco", "oc-tai": "dauco", "ong-tai-ngoai": "dauco", "ong-tai-trong": "dauco",
    "co": "dauco", "co-sau": "dauco", "co-canh": "dauco", "mach-co": "dauco",
    "mach-co-dau-co": "dauco", "dau-co": "dauco", "hong": "dauco", "hau-mieng": "dauco",
    "thanh-quan": "dauco", "duong-nuot": "dauco", "duong-tho-tren": "dauco",
    "clivus": "dauco", "xuong-cham": "dauco",
    # tim
    "tim": "tim", "tim-phai": "tim", "cotim": "tim", "vanh": "tim", "van-tim": "tim",
    "mach-tim": "tim", "mong-tim": "tim", "dong-mach-chu-nguc": "tim", "mang-tim": "tim",
    # ngực
    "phoi": "nguc", "phe-quan": "nguc", "trung-that": "nguc", "long-nguc": "nguc",
    "thanh-nguc": "nguc", "mang-phoi": "nguc", "mong-phoi": "nguc", "hoanh": "nguc",
    "co-hoanh": "nguc", "khi-quan": "nguc", "duong-tho": "nguc", "mach-nguc": "nguc",
    "ron-phoi": "nguc", "dong-mach-phoi": "nguc",
    # vú & sản phụ khoa
    "vu": "vuspk", "num-vu": "vuspk", "tu-cung": "vuspk", "co-tu-cung": "vuspk",
    "buong-tu-cung": "vuspk", "seo-tu-cung": "vuspk", "eo-tu-cung": "vuspk",
    "tu-cung-phan-phu": "vuspk", "buong-trung": "vuspk", "phan-phu": "vuspk",
    "thai": "vuspk", "thai-nhi": "vuspk", "thai-ky": "vuspk", "nao-thai": "vuspk",
    "than-thai": "vuspk", "banh-nhau": "vuspk", "nhau-thai": "vuspk", "am-dao": "vuspk",
    "am-ho": "vuspk", "sinh-duc": "vuspk", "sinh-duc-nu": "vuspk", "sinh-mon": "vuspk",
    "san-chau": "vuspk", "day-chau": "vuspk", "manh-oi": "vuspk", "roi": "vuspk",
    "tieu-khung": "vuspk", "chau": "vuspk", "hach-chau": "vuspk", "ho-nach": "vuspk",
    "hach-nach": "vuspk", "duong-vat": "vuspk",
    # bụng – tiêu hóa – gan mật – tụy – tiết niệu
    "gan": "bung", "duong-mat": "bung", "duong-mat-trong-gan": "bung", "gan-mat": "bung",
    "tui-mat": "bung", "tuy": "bung", "tuy-ta-trang": "bung", "ta-trang": "bung",
    "lach": "bung", "ruot": "bung", "ruot-non": "bung", "ruot-thua": "bung",
    "dai-trang": "bung", "da-day": "bung", "thuc-quan": "bung", "phuc-mac": "bung",
    "hau-phuc-mac": "bung", "o-bung": "bung", "o-bung-tren": "bung", "tieu-hoa": "bung",
    "ong-tieu-hoa": "bung", "mach-cua": "bung", "tm-cua": "bung", "tm-gan": "bung",
    "tinh-mach-cua": "bung", "DMC-bung": "bung", "dong-mach-chu-bung": "bung",
    "dong-mach-chu": "bung", "dong-mach-chau": "bung", "tinh-mach-chu-duoi": "bung",
    "tm-chu-duoi": "bung", "than": "bung", "than-ghep": "bung", "tiet-nieu": "bung",
    "nieu-quan": "bung", "bang-quang": "bung", "nieu-dao": "bung",
    "tuyen-tien-liet": "bung", "tien-liet-tuyen": "bung", "truc-trang": "bung",
    "hau-mon": "bung", "truc-trang-hau-mon": "bung", "ho-chau": "bung", "bung": "bung",
    "ben-bung": "bung", "thanh-bung": "bung", "ron-bung": "bung", "sau-phuc-mac": "bung",
    "quanh-manh-ghep": "bung", "dong-mach-gan": "bung", "dong-mach-than": "bung",
    "tinh-mach-lach": "bung", "chuyen-hoa-lipid": "bung", "bung-tiet-nieu": "bung",
    # thần kinh
    "nao": "thankinh", "nao-that": "thankinh", "so-nao": "thankinh", "vo-nao": "thankinh",
    "tieu-nao": "thankinh", "than-nao": "thankinh", "nao-tuy": "thankinh",
    "nen-so": "thankinh", "goc-cau-tieu-nao": "thankinh", "mach-nao": "thankinh",
    "tuy-song": "thankinh", "ong-song": "thankinh", "cot-song": "thankinh",
    "tu": "thankinh", "thoat-vi": "thankinh", "tuyen-yen": "thankinh", "ho-yen": "thankinh",
    "cuong-tuyen-yen": "thankinh", "giao-thoa": "thankinh", "xoang-tinh-mach": "thankinh",
    "xoang-hang": "thankinh", "hach-canh-dmc": "thankinh", "quanh-nao-that": "thankinh",
    "chat-trang": "thankinh", "dam-roi": "thankinh", "dam-roi-canh-tay": "thankinh",
    "than-kinh-ngoai-bien": "thankinh", "ban-cau-dai-nao": "thankinh",
    # cơ xương khớp
    "xuong": "msk", "xuong-tre-em": "msk", "co-xuong": "msk", "co-xuong-khop": "msk",
    "co-xuong-khop-nhi": "msk", "khop": "msk", "co-chan": "msk", "chi-tren": "msk",
    "chi-duoi": "msk", "vai": "msk", "cung-cut": "msk", "xuong-cut": "msk",
    "mo-mem": "msk", "phan-mem": "msk", "da-mo-mem": "msk", "cot-song-that-lung": "msk",
    "tuy-that-lung": "msk", "duoi-ngua": "msk", "xuong-dai": "msk", "xuong-don": "msk",
    "suon": "msk", "dinh-suon": "msk", "khung-chau": "msk", "khop-hang": "msk",
    "khop-goi": "msk", "khop-vai": "msk", "cot-song-cung-cut": "msk",
}
# tag có hậu tố "-nhi" nhưng vùng là của người lớn: bỏ hậu tố rồi tra lại
for _k in list(VUNG_SPEC):
    if _k.endswith("-nhi"):
        VUNG_SPEC.setdefault(_k[:-4], VUNG_SPEC[_k])

SUB_SPEC = [
    ("mat", r"\beye\b|ophthalm"),
    ("vuspk", r"obgyn|breast|gyn|obstetric|sản|vú"),
    ("thankinh", r"neuro"),
    ("nguc", r"\bchest\b|thorac|hô hấp"),
    ("bung", r"abdom|\bGI\b|gastro|hepat|genitourin|transplant|tiêu hóa|gan mật|niệu"),
    ("msk", r"musculoskelet|\bMSK\b|orthop|cơ xương"),
    ("dauco", r"head[_ &]?neck|\bENT\b|otol|salivary|thyroid|tai mũi họng|đầu cổ"),
    ("tim", r"cardi|tim mạch"),
    ("canthiep", r"\bIR\b|interventional|can thiệp"),
    ("nhi", r"pediat|paediat|\bnhi\b|sơ sinh"),
]


def spec_for(uid, tags, title=""):
    """Phân loại chuyên mục: ID 3 số theo dải; ID 4 số theo bảng đã rà / tag vùng / subspecialty.
    Sau cùng tách "vú" ↔ "sản – phụ khoa" (trước đây gộp chung "Vú & SPK")."""
    uid = str(uid)
    if uid in RECLASS:
        spec = RECLASS[uid]
    elif len(uid) <= 3:
        spec = spec_of(uid)
    elif uid in CLASSIFY_4D:
        spec = CLASSIFY_4D[uid]
    elif uid in SPEC_OVERRIDE:
        spec = SPEC_OVERRIDE[uid]
    elif uid.startswith("6"):
        spec = "nhi"
    else:
        spec = ""
        for tok in re.findall(r"vung:([A-Za-z0-9_.-]+)", tags):
            if tok in VUNG_SPEC:
                spec = VUNG_SPEC[tok]
                break
    if spec == "vuspk":
        spec = split_vuspk(uid, tags, title)
    return spec


def frontmatter(path):
    t = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", t, re.S)
    fm, body = m.group(1), m.group(2)
    out = {}
    for key in ("unit_id", "subspecialty", "tags", "certainty"):
        mm = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
        out[key] = (mm.group(1).strip().strip('"') if mm else "")
    h1 = re.search(r"^#\s+(.+)$", body, re.M)
    out["h1"] = h1.group(1).strip() if h1 else Path(path).parent.name
    imgs = re.findall(r"!\[.*?\]\((images/[^)\s]+)\)", body)
    out["thumb"] = next((i for i in imgs if (Path(path).parent / i).exists()), "")
    return out


def curated_copy(index_text):
    """Tiêu đề/mô tả/ảnh đã biên tập trong các thẻ hiện có (neo bằng class ctitle)."""
    cards = {}
    for b in re.split(r'(?=<div class="card")', index_text):
        if not b.startswith('<div class="card"'):
            continue
        m = re.search(r'view\.html\?b=([^&]+)&', b)
        if not m:
            continue
        d = m.group(1)
        mt = re.search(r'class="ctitle"[^>]*>([^<]*)</a>', b)
        if mt:  # định dạng hub mới: neo bằng class ctitle
            mt_text = html.unescape(mt.group(1))
        else:  # định dạng thẻ cũ (trước hub mới): link tiêu đề là anchor có text
            links = re.findall(r'<a href="[^"]+">([^<]*)</a>', b)
            mt_text = next((t for t in links if t and t not in ("Bài học", "Nguồn")), "")
            mt_text = html.unescape(mt_text)
        if mt_text in ("Bài học", "Nguồn"):
            mt_text = ""
        mp = re.search(r'<p>(.*?)</p>', b, re.S)
        mi = re.search(r'<img[^>]+src="([^"]+)" alt="([^"]*)"', b)
        cards[d] = {"title": mt_text,
                    "desc": mp.group(1) if mp else "",
                    "img": (mi.group(1), html.unescape(mi.group(2))) if mi else None}
    return cards


def build_page():
    root = Path(".")
    # Chỉ nhận bài "hoàn chỉnh" (có lesson.md + sources.md theo bất biến repo);
    # bài đang viết dở (chưa có sources.md) sẽ không lên hub tới khi hoàn tất.
    dirs = sorted(d for d in os.listdir(".")
                  if re.match(r"^\d{3,4}-", d) and (root / d / "lesson.md").exists()
                  and (root / d / "sources.md").exists())
    old = root.joinpath("index.html").read_text(encoding="utf-8") if root.joinpath("index.html").exists() else ""
    keep = curated_copy(old)

    recs, card_html, overviews, unclassified = [], [], [], []
    for d in dirs:
        fm = frontmatter(f"{d}/lesson.md")
        tags = [t.strip() for t in fm["tags"].strip("[]").split(",") if t.strip()]
        uid = fm["unit_id"]
        k = keep.get(d, {})
        title = k.get("title") or fm["h1"]
        spec = spec_for(uid, fm["tags"], title)
        if not spec:
            unclassified.append(uid)
        scores = [t.split(":", 1)[1] for t in tags if t.startswith("score:")]
        cert = CERT_LABEL.get(fm["certainty"], fm["certainty"])
        desc = k.get("desc") or OV_DESC
        img = k.get("img") or ((f"{d}/{fm['thumb']}", title) if fm["thumb"] else None)
        search = f"{uid} {title} {' '.join(tags)} {d}"
        spans = " ".join(f'<span class="tag">{html.escape(t)}</span>' for t in tags[:4])
        if len(tags) > 4:
            spans += f' <span class="tag more">+{len(tags) - 4}</span>'
        img_html = (f'<a href="view.html?b={d}&f=lesson.md">'
                    f'<img loading="lazy" src="{img[0]}" alt="{html.escape(img[1])}"></a>' if img else "")
        card_html.append(
            f'<div class="card" data-id="{html.escape(uid)}" data-spec="{spec}" '
            f'data-scores="{html.escape(" ".join(scores))}" data-cert="{html.escape(fm["certainty"])}" '
            f'data-tags="{html.escape(" ".join(tags))}" data-search="{html.escape(search)}">{img_html}'
            f'<div class="cid">{html.escape(uid)} · {spec.upper()}</div>'
            f'<a class="ctitle" href="view.html?b={d}&f=lesson.md">{html.escape(title)}</a><br>'
            f'{spans}<span class="cert">{html.escape(cert)}</span><p>{desc}</p>'
            f'<a href="view.html?b={d}&f=lesson.md">Bài học</a> · '
            f'<a href="view.html?b={d}&f=sources.md" target="_blank" rel="noopener">Nguồn</a> '
            f'<button class="learn" data-learn="{html.escape(uid)}" '
            f'title="Đánh dấu bài này đã học (lưu trong trình duyệt của bạn)">✓ Đã học</button></div>')
        recs.append((uid, tags))
        if "tong-quan" in d or "overview" in d:
            vi = fm["h1"].split(" / ")[0].strip()
            vi = re.sub(r"^\d{3}\s*[—–-]\s*", "", vi)
            vi = re.sub(r"^Tổng quan\s+", "", vi, flags=re.I).split(":")[0].strip()
            vi = vi[:1].upper() + vi[1:]
            overviews.append((uid, d, f"{uid} · {vi}"))

    if unclassified:
        print("BUILD_INDEX FAIL: chưa phân loại chuyên mục cho:", ", ".join(unclassified))
        print("  → thêm ID vào CLASSIFY_4D trong tools/build_index.py (hoặc gắn tag vung: hợp lệ)")
        return None, 0, 0, []

    ov_options = ['<option value="">📚 Bài tổng quan hệ (' + str(len(overviews)) + ")</option>"]
    ov_options += [f'<option value="view.html?b={d}&f=lesson.md">{html.escape(label)}</option>'
                   for _, d, label in sorted(overviews)]
    ov_select = '<select id="fOverview" title="Nhảy nhanh tới bài tổng quan của từng hệ">' \
                + "".join(ov_options) + "</select>"

    present = sorted({s for _, tags in recs for t in tags
                      for s in ([t.split(":", 1)[1]] if t.startswith("score:") else [])})
    # Nút "Tất cả" + nút mở rộng nằm trong template; ở đây chỉ sinh chip score.
    chips = [f'<button class="chip" data-score="{s}">{s}</button>'
             for s in REQUIRED_SCORES if s in present]
    chips += [f'<button class="chip extra" data-score="{s}">{s}</button>'
              for s in present if s not in REQUIRED_SCORES]
    tabs = "".join(f'<button class="tab{" on" if not v else ""}" data-spec="{v}">{lab}</button>'
                   for v, lab in TABS)

    page = Path("tools/hub_template.html").read_text(encoding="utf-8")
    page = (page.replace("__TABS__", tabs).replace("__CHIPS__", "\n".join(chips))
                .replace("__OVSELECT__", ov_select).replace("__CARDS__", "\n".join(card_html))
                .replace("__N__", str(len(card_html))))
    return page, len(card_html), len(chips), present


def main(argv=None):
    import sys
    argv = sys.argv[1:] if argv is None else argv
    page, ncards, nchips, present = build_page()
    if page is None:
        return 1
    target = Path("index.html")
    if "--check" in argv:
        cur = target.read_text(encoding="utf-8") if target.exists() else ""
        if cur != page:
            print("BUILD_INDEX FAIL: index.html KHÔNG khớp tools/hub_template.html")
            print("  → chạy: python3 tools/build_index.py  (và không sửa tay index.html)")
            return 1
        print(f"BUILD_INDEX OK: index.html khớp template ({ncards} thẻ, {nchips} chips)")
        return 0
    target.write_text(page, encoding="utf-8")
    print(f"index.html: {ncards} thẻ, {nchips} chips, score tags: {present}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
