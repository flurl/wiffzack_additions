from html.parser import HTMLParser
from math import ceil
from typing import Any, Literal, TypeAlias

from .EscPosConstants import *
import pyqrcode

TagAttrs: TypeAlias = list[tuple[str, str | None]]

NEWLINE = CTL_LF + CTL_CR
MAXCHARS = 56

TESTCODE = """011111110010100110011111110
010000010001000001010000010
010111010110110100010111010
010111010100000010010111010
010111010011101010010111010
010000010010000110010000010
011111110101010101011111110
000000000011011010000000000
000011011010100001000011000
010011001010111000001111100
000010111000000110111010010
010011000101001001010011110
000100111011110101111000010
010001001100011100000100100
011100011010110010100011110
010101101101011100001101010
010010111111000011111101100
000000000101000111000100100
011111110101111001010110010
010000010001010011000100000
010111010100000011111110100
010111010101101001111010010
010111010011110100101101110
010000010000110100011101110
011111110001000001010010010
000000000000000000000000000
000000000000000000000000000
000000000000000000000000000
000000000000000000000000000
000000000000000000000000000
000000000000000000000000000
000000000000000000000000000"""


class EscPosHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        # a list of (tag, attrs) tuples
        self.tags: list[tuple[str, TagAttrs]] = []
        self.code: str = HW_INIT + ESC + '\x21'+'\x01'  # ''
        self.code += SET_LINE_SPACE_10

    def handle_starttag(self, tag: str, attrs: TagAttrs) -> None:
        # print "Encountered a start tag:", tag
        self.tags.append((tag, attrs))

        for name, value in attrs:
            if name == 'align':
                if value == 'right':
                    self.code += TXT_ALIGN_RT
                elif value == 'center':
                    self.code += TXT_ALIGN_CT
                else:
                    self.code += TXT_ALIGN_LT

        if tag == 'p':
            pass
        elif tag == 'u':
            self.code += TXT_UNDERL_ON
        elif tag == 'b':
            self.code += TXT_BOLD_ON
        elif tag == 'center':
            self.code += TXT_ALIGN_CT
        # qr code
        elif tag == 'qr':
            pass
        # barcode
        elif tag == 'bar':
            for name, value in attrs:
                if name == 'height' and value is not None:
                    self.code += BARCODE_HEIGHT+chr(int(value))
            pass

    def handle_endtag(self, tag: str) -> None:
        # print "Encountered  an end tag:", tag
        if tag == 'p':
            self.code += NEWLINE
        elif tag == 'u':
            self.code += TXT_UNDERL_OFF
        elif tag == 'b':
            self.code += TXT_BOLD_OFF
        elif tag == 'center':
            self.code += TXT_ALIGN_LT
        elif tag == 'qr':
            pass
        elif tag == 'bar':
            pass

        # if an alignment was specified, reset to left alignment
        attrs: list[tuple[str, str | None]] = self.tags.pop()[1]
        for name, _ in attrs:
            if name == 'align':
                self.code += TXT_ALIGN_LT

    def handle_startendtag(self, tag: str, attrs: TagAttrs) -> None:
        # print "Encountered  an startend tag:", tag
        if tag == 'br':
            # print "adding newline"
            self.code += NEWLINE
        elif tag == 'hr':
            for name, value in attrs:
                if name == 'size' and value == '2':
                    self.code += ('='*MAXCHARS) + NEWLINE
                    return
                elif name == 'class' and value == 'paper_full_cut':
                    self.code += PAPER_FULL_CUT
                    return
            self.code += ('-'*MAXCHARS) + NEWLINE

    def handle_data(self, data: str) -> None:
        # print "Encountered some data:", repr(data):
        # data = data.encode('utf-8')
        # print "BP1 Encountered   some data:", repr(data)

        try:
            # print "BP2", self._tags[-1][0]
            if self.tags[-1][0] == 'qr':
                # print "BP2.5"
                self.code += self.mk_QR_code(data)
            elif self.tags[-1][0] == 'bar':
                # print "BP2.5"
                self.code += self.mk_bar_code(data)
            # do nothing on empty strings, line feeds, etc - skip the styles tags
            elif data.strip() and not self.tags[-1][0] == 'style':
                self.code += data
        except IndexError:
            # print "BP3", "Error", self._tags
            pass

    def mk_bar_code(self, data: str):
        escPosCode: str = BARCODE_CODE39+str(data)+'\x00'
        return escPosCode

    def mk_QR_code(self, data: str):

        def safe_list_get(l: list[Any], idx: int) -> Any | Literal['0']:
            try:
                return l[idx]
            except IndexError:
                return '0'

        code: pyqrcode.QRCode = pyqrcode.create(  # type: ignore
            data, error='L')  # type: ignore
        qr_text: str = str(code.text(quiet_zone=1))  # type: ignore
        line_len: int = qr_text.find("\n")
        # print qrText
        esc_pos_code: str = ''
        # escPosCode += "Linelen: %s" % lineLen
        esc_pos_code += SET_LINE_SPACE_24

        qr_text = qr_text.replace('\n', '').replace('\r', '')
        # escPosCode += NEWLINE + "LenQrText: %s" % len(qrText)
        for i in range(0, ceil((len(qr_text)/line_len)), 8):
            try:
                # this would double the size of the qr code
                double = False
                if double:
                    # print "i", i
                    line = NEWLINE
                    line2 = NEWLINE

                    line += BIT_IMAGE_MODE + '\x00' + chr(line_len*4) + '\x00'
                    line2 += BIT_IMAGE_MODE + '\x00' + chr(line_len*4) + '\x00'
                    for j in range(line_len):
                        byte = 0 if safe_list_get(
                            qr_text, j+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text,
                                                   j+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text,
                                                   j+line_len+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text,
                                                   j+line_len+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*2+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*2+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*3+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*3+i*line_len) == '0' else 0x1
                        line += chr(byte)*4

                        byte = 0 if safe_list_get(
                            qr_text, j+line_len*4+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*4+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*5+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*5+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*6+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*6+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*7+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*7+i*line_len) == '0' else 0x1
                        line2 += chr(byte)*4
                    # print repr(escPosCode*40)
                    esc_pos_code += line
                    esc_pos_code += line2
                else:
                    line = NEWLINE
                    line += BIT_IMAGE_MODE + '\x00' + chr(line_len*2) + '\x00'
                    for j in range(line_len):
                        byte = 0 if safe_list_get(
                            qr_text, j+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text,
                                                   j+line_len+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*2+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*3+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*4+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*5+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*6+i*line_len) == '0' else 0x1
                        byte = byte << 1
                        byte += 0 if safe_list_get(qr_text, j +
                                                   line_len*7+i*line_len) == '0' else 0x1

                        # completly inacceptable workarround
                        # somehow the tm-t88 don't like a byte with value 0x0A
                        # so we replace it with 0x0B and hope for the best and the QR's error correction
                        if byte == 0x0A:
                            byte = 0x0B
                        line += chr(byte)*2
                    # print repr(escPosCode*40)
                    esc_pos_code += line
                # escPosCode += NEWLINE

                # print repr(escPosCode)
            except IndexError:
                pass

        # print repr(escPosCode)

        esc_pos_code += NEWLINE

        return esc_pos_code
