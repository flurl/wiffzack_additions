from html.parser import HTMLParser
from typing import TypeAlias, cast

from escpos.capabilities import Profile
import escpos.printer


TagAttrs: TypeAlias = list[tuple[str, str | None]]


class EscPosHTMLParser(HTMLParser):

    def __init__(self, profile: str) -> None:
        HTMLParser.__init__(self)
        # a list of (tag, attrs) tuples
        self.tags: list[tuple[str, TagAttrs]] = []
        # Create a dummy self.printer object
        self.printer = escpos.printer.Dummy(profile=profile)
        self.printer.hw("RESET")

    def handle_starttag(self, tag: str, attrs: TagAttrs) -> None:
        # print "Encountered a start tag:", tag
        self.tags.append((tag, attrs))

        # use the align attribute as an universal
        # attribute that might be attached to every tag
        for name, value in attrs:
            if name == 'align':
                if value == 'right':
                    self.printer.set(align='right')
                elif value == 'center':
                    self.printer.set(align='center')
                else:
                    self.printer.set(align='left')

        if tag == 'p':
            pass
        elif tag == 'u':
            self.printer.set(underline=1)
        elif tag == 'b':
            self.printer.set(bold=True)
        elif tag == 'center':
            self.printer.set(align='center')
        # font tag
        elif tag == 'font':
            # the font tag itself does nothing
            # the attributes are the important part
            for name, value in attrs:
                if name == 'face':
                    self.printer.set(font=value)
                    p: Profile = cast(
                        Profile, self.printer.profile)  # type: ignore
                    self.max_chars: int = p.get_columns(value)  # type: ignore
                elif name == 'size':
                    assert value is not None
                    self.printer.set(custom_size=True, width=int(
                        value), height=int(value))
                elif name == 'spacing':
                    if value is not None:
                        value = int(value)
                    self.printer.line_spacing(value)
        # qr code
        elif tag == 'qr':
            pass
        # barcode
        elif tag == 'bar':
            pass

    def handle_endtag(self, tag: str) -> None:
        # print "Encountered  an end tag:", tag
        if tag == 'p':
            self.printer.ln()
        elif tag == 'u':
            self.printer.set(underline=0)
        elif tag == 'b':
            self.printer.set(bold=False)
        elif tag == 'center':
            self.printer.set(align='left')
        elif tag == 'qr':
            pass
        elif tag == 'bar':
            pass

        # if an alignment was specified, reset to left alignment
        attrs: list[tuple[str, str | None]] = self.tags.pop()[1]
        for name, _ in attrs:
            if name == 'align':
                self.printer.set(align='left')
                break

    def handle_startendtag(self, tag: str, attrs: TagAttrs) -> None:
        # print "Encountered  an startend tag:", tag
        if tag == 'br':
            # print "adding newline"
            self.printer.ln()
        elif tag == 'hr':
            for name, value in attrs:
                if name == 'size' and value == '2':
                    self.printer.textln("="*self.max_chars)
                    return
                elif name == 'class' and value == 'paper_full_cut':
                    self.printer.cut()
                    return
            self.printer.textln('-'*self.max_chars)

    def handle_data(self, data: str) -> None:
        # print "Encountered some data:", repr(data):
        # data = data.encode('utf-8')
        # print "BP1 Encountered   some data:", repr(data)
        try:
            # print "BP2", self._tags[-1][0]
            if self.tags[-1][0] == 'qr':
                # print "BP2.5"
                self.printer.qr(data)  # type: ignore
            elif self.tags[-1][0] == 'bar':
                # print "BP2.5"
                self.printer.barcode(data, "EAN13")  # type: ignore
            # do nothing on empty strings, line feeds, etc - skip the styles tags
            elif data.strip() and not self.tags[-1][0] == 'style':
                self.printer.text(data)
        except IndexError:
            # print "BP3", "Error", self._tags
            pass

    @property
    def output(self) -> bytes:
        return self.printer.output
