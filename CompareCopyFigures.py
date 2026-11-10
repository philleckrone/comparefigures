# coding=utf-8
from ScriptureObjects import ScriptureText
from shutil import copyfile
import re
import sys
import os

# CompareCopyFigures.py
# Version 1.3
# Combines CompareFigures.py (v0.3) and CopyFigures.py (v0.7) in one tool.
# The CompareProject option names the source of the figures; the Output
# project (normally the user's own project) is the target.
#   Mode=Compare  writes an HTML report comparing the figures (\fig ...\fig*)
#                 of the Compare project with the Output project, with a
#                 checkbox on each figure. "Copy selection" puts the ticked
#                 references on the clipboard.
#   Mode=Copy     copies the figures listed in FiguresToCopy (the pasted
#                 selection, book codes, or ALL) from the Compare project to
#                 the Output project, and optionally the picture files too.
#                 RemoveAllExisting first strips every figure from the Output
#                 project's chosen books.
# Keep this source ASCII-only.
#__________________________________________________________________________________
# OPTIONS (injected by Paratext as globals; plain top-level guards only --
# a globals()[name] helper silently returns defaults inside Paratext)

def _to_unicode(v):
    if isinstance(v, type(u'')):
        return v
    if not isinstance(v, bytes):
        return unicode(v)
    try:
        return v.decode('utf-8')
    except UnicodeDecodeError:
        return v.decode('mbcs')

try:
    Project
except NameError:
    Project = u''
Project = _to_unicode(Project).strip()

try:
    OutputProject
except NameError:
    OutputProject = u''
OutputProject = _to_unicode(OutputProject).strip()

try:
    SettingsDirectory
except NameError:
    SettingsDirectory = u''
SettingsDirectory = _to_unicode(SettingsDirectory)

try:
    Books
except NameError:
    Books = u''

try:
    Mode
except NameError:
    Mode = u'Compare'

try:
    CompareProject
except NameError:
    CompareProject = u''
CompareProject = _to_unicode(CompareProject).strip()

try:
    RemoveAllExisting
except NameError:
    RemoveAllExisting = u'No'

try:
    OnlyShowDiffs
except NameError:
    OnlyShowDiffs = u'No'

try:
    ShowCaptionList
except NameError:
    ShowCaptionList = u'Yes'

try:
    ShowActualFilename
except NameError:
    ShowActualFilename = u'No'

try:
    ShowThumbnails
except NameError:
    ShowThumbnails = u'Yes'

try:
    FiguresToCopy
except NameError:
    FiguresToCopy = u''

try:
    CopyEvenIfPresent
except NameError:
    CopyEvenIfPresent = u'No'

try:
    ReplaceDifferent
except NameError:
    ReplaceDifferent = u'Yes'

try:
    CopyFilesOverAsWell
except NameError:
    CopyFilesOverAsWell = u'Yes'

try:
    IncludeCaptions
except NameError:
    IncludeCaptions = u'Yes'

try:
    WrapTargetCaption
except NameError:
    WrapTargetCaption = u'Yes'

#__________________________________________________________________________________
# HELPERS

def _yes(v):
    return _to_unicode(v).strip().lower() in (u'yes', u'y', u'true', u'1')

def _out(s):
    # This \noText script never calls checking.setupCheck(), so stdout goes
    # straight to Paratext's list window, which takes unicode as is (as in
    # CopyFigures.py). Encoding to UTF-8 bytes first showed each accented
    # letter as two wrong letters there. The UTF-8 fallback is only for
    # running outside Paratext, where a console may refuse non-ASCII.
    s = _to_unicode(s) + u'\n'
    try:
        sys.stdout.write(s)
    except UnicodeEncodeError:
        sys.stdout.write(s.encode('utf-8'))

def _open_path(path):
    return path.encode('mbcs') if isinstance(path, type(u'')) else path

def _he(s):
    return s.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')

def _attr(s):
    return _he(s).replace(u'"', u'&quot;')

def _file_url(path):
    url = path.replace(u'\\', u'/').replace(u'%', u'%25').replace(u' ', u'%20').replace(u'#', u'%23')
    return u'file:///' + url

# Paratext's canonical book order (book number = index + 1); the Books
# option Paratext passes is a 0/1 string in this order.
BOOK_ORDER = (u'GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM '
              u'EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP '
              u'COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV TOB JDT ESG WIS SIR BAR LJE S3Y SUS '
              u'BEL 1MA 2MA 3MA 4MA 1ES 2ES MAN PS2 ODA PSS JSA JDB TBS SST DNT BLT XXA XXB XXC XXD XXE XXF XXG FRT '
              u'BAK OTH 3ES EZA 5EZ 6EZ INT CNC GLO TDX NDX DAG PS3 2BA LBA JUB ENO 1MQ 2MQ 3MQ REP 4BA LAO').split()
BOOK_INDEX = dict((b, i) for i, b in enumerate(BOOK_ORDER))

def book_list_display(books):
    """The chosen books as codes, with runs of 3+ books shown as ranges,
    e.g. GEN, EXO, LEV and MAT chosen -> 'GEN-LEV, MAT'."""
    s = _to_unicode(books).strip()
    if s and not s.strip(u'01'):
        idx = [i for i, c in enumerate(s) if c == u'1' and i < len(BOOK_ORDER)]
    else:
        idx = sorted(set(BOOK_INDEX[b] for b in s.upper().split() if b in BOOK_INDEX))
    if not idx:
        return s or u'-'
    parts = []
    start = prev = idx[0]
    for i in idx[1:] + [None]:
        if i is not None and i == prev + 1:
            prev = i
            continue
        if prev - start >= 2:
            parts.append(BOOK_ORDER[start] + u'-' + BOOK_ORDER[prev])
        else:
            parts.extend(BOOK_ORDER[j] for j in range(start, prev + 1))
        if i is not None:
            start = prev = i
    return u', '.join(parts)

SFX = u'abcdefghijklmnopqrstuvwxyz'
IMAGE_EXTS = [u'.jpg', u'.jpeg', u'.png', u'.gif', u'.bmp', u'.tif', u'.tiff']
SHOWABLE_EXTS = (u'.jpg', u'.jpeg', u'.png', u'.gif', u'.bmp')

# Known illustration series (e.g. 'HK01234b.tif' and 'hk01234c.jpg' are
# both 'hk01234'), same list as CompareFigures.py's newBase().
SERIES_RE = re.compile(r"(?i)_?((?=ab|cn|co|hk|lb|bk|ba|dy|gt|dh|mh|mn|wa|dn|ib)..\d{5})[abcABC]?$")
TOKEN_RE = re.compile(r'\\v (\d+)|\\fig .*?\\fig\*')
FIG_RE = re.compile(r'\\fig .*?\\fig\*')
CHAP_RE = re.compile(r'^\s*([0-9A-Za-z]{3})\s+(\d+)')
SEL_RE = re.compile(r'([0-9A-Za-z]{3})(?:\s+(\d+)(?::(\d+)([a-zA-Z]?))?)?')

def normalized_name(src):
    stem = os.path.splitext(src)[0]
    cl = SERIES_RE.findall(stem)
    if cl:
        return cl[0].lower()
    return stem

def compare_key(src):
    return src if _yes(ShowActualFilename) else normalized_name(src)

def parse_fig(sFigr):
    """Return (src, caption, loc) for one \\fig ...\\fig*, or None."""
    if u'="' in sFigr:  # USFM3
        m = re.search(r'src="([^"]+)"', sFigr)
        if m is None:
            return None
        cap = re.search(r"\\fig ([^\|]*?)\|", sFigr)
        loc = re.search(r'loc="([^"]+?)"', sFigr)
        return (m.group(1).strip(), cap.group(1) if cap else u'', loc.group(1) if loc else u'')
    # USFM2: \fig DESC|FILE|SIZE|LOC|COPY|CAP|REF\fig*
    fields = sFigr[len(u'\\fig '):-len(u'\\fig*')].split(u'|')
    if len(fields) < 2 or not fields[1].strip():
        return None
    caption = fields[5] if len(fields) >= 7 else (fields[-2] if len(fields) >= 3 else u'')
    loc = fields[3] if len(fields) >= 7 else u''
    return (fields[1].strip(), caption, loc)

def replace_caption(sFigr, newCaption):
    if u'="' in sFigr:  # USFM3: caption is the text before the first |
        bar = sFigr.find(u'|')
        if bar < 0:
            return sFigr
        return u'\\fig ' + newCaption + sFigr[bar:]
    inner = sFigr[len(u'\\fig '):-len(u'\\fig*')]
    fields = inner.split(u'|')
    if len(fields) >= 7:
        fields[5] = newCaption
    elif len(fields) >= 3:
        fields[-2] = newCaption
    else:
        return sFigr
    return u'\\fig ' + u'|'.join(fields) + u'\\fig*'

def ref_sort_key(ref):
    m = re.match(r'^(\S+) (\d+):(\d+)([a-z]?)$', ref)
    if not m:
        return (9999, 0, 0, ref)
    return (BOOK_INDEX.get(m.group(1), 999), int(m.group(2)), int(m.group(3)), m.group(4))

def collect_figures(prj):
    """Return ({ref: fig}, error). ref is e.g. 'GEN 1:3', or 'GEN 1:3b' for
    the second figure in the same verse."""
    figs = {}
    try:
        scr = ScriptureText(prj)
        for reference, text in scr.chapters(Books):
            reference = _to_unicode(reference)
            text = _to_unicode(text)
            cm = CHAP_RE.match(reference)
            if cm is None:
                continue
            book = cm.group(1).upper()
            chapRef = book + u' ' + cm.group(2)
            vrs = u'0'
            perVerse = {}
            for m in TOKEN_RE.finditer(text):
                if m.group(1) is not None:
                    vrs = m.group(1)
                    continue
                sFigr = m.group(0)
                parsed = parse_fig(sFigr)
                if parsed is None:
                    _out(u'Invalid figure found in ' + prj + u' ' + chapRef + u':' + vrs + u': ' + sFigr)
                    continue
                src, caption, loc = parsed
                n = perVerse.get(vrs, 0)
                perVerse[vrs] = n + 1
                ref = chapRef + u':' + vrs + (SFX[n] if 0 < n < len(SFX) else u'')
                figs[ref] = {
                    'prj': prj, 'sFigr': sFigr, 'src': src, 'caption': caption, 'loc': loc,
                    'book': book, 'chapRef': chapRef, 'vrs': vrs, 'ref': ref,
                }
    except Exception, e:
        return (figs, _to_unicode(str(e)))
    return (figs, None)

def project_dir(prj):
    return os.path.join(SettingsDirectory, prj)

_figureIndex = {}
def figures_index(prj):
    """{lowercase filename: full path} for the project's figures folder."""
    if prj not in _figureIndex:
        idx = {}
        d = os.path.join(project_dir(prj), u'figures')
        try:
            for name in os.listdir(d):
                idx[name.lower()] = os.path.join(d, name)
        except Exception:
            pass
        _figureIndex[prj] = idx
    return _figureIndex[prj]

def find_image(prj, src):
    """The picture file for src in prj's figures folder: the exact name,
    otherwise the same name with another image extension (Paratext keeps
    .jpg copies of the .tif files named in \\fig)."""
    idx = figures_index(prj)
    name = os.path.basename(src.replace(u'/', u'\\'))
    if name.lower() in idx:
        return idx[name.lower()]
    stem = os.path.splitext(name)[0].lower()
    for ext in IMAGE_EXTS:
        if stem + ext in idx:
            return idx[stem + ext]
    return None

#__________________________________________________________________________________
# COMPARE MODE

REPORT_CSS = u"""
body{font-family:Segoe UI,Arial,sans-serif;font-size:14px;margin:16px;color:#222}
h1{font-size:20px;margin:0 0 4px}
.meta{color:#555;margin-bottom:12px}
.bar{position:sticky;top:0;background:#f4f6f8;border:1px solid #ccd;padding:8px;margin-bottom:10px;z-index:2}
.bar button{margin:2px 4px 2px 0;padding:4px 10px;cursor:pointer}
.bar textarea{width:100%;box-sizing:border-box;height:44px;margin-top:6px;font-family:Consolas,monospace}
.note{color:#555;font-size:13px;margin-top:4px}
table{border-collapse:collapse}
th,td{border:1px solid #ccc;padding:4px 6px;vertical-align:top;text-align:left}
th{background:#e9edf2;position:sticky;top:0}
td.ref{white-space:nowrap;font-weight:600}
td.missing{background:#fde2e2;color:#999;text-align:center}
td.diff{background:#fff3cd}
.fn{font-family:Consolas,monospace}
.cap{font-style:italic;color:#333;max-width:260px}
.loc{color:#777;font-size:12px}
img.th{display:block;max-width:150px;max-height:110px;margin:4px 0;border:1px solid #ddd}
tr.sel td{outline:2px solid #4a7bd0}
"""

REPORT_JS = u"""
function boxes(){return document.querySelectorAll('input.pick');}
function refresh(){
  var out=[], b=boxes();
  for(var i=0;i<b.length;i++){
    var tr=b[i].parentNode.parentNode;
    if(b[i].checked){out.push(b[i].value); tr.className='sel';} else {tr.className='';}
  }
  document.getElementById('selection').value=out.join(' ');
  document.getElementById('count').innerHTML=out.length;
}
function pick(attr){
  var b=boxes();
  for(var i=0;i<b.length;i++){ if(!b[i].disabled && b[i].getAttribute(attr)=='1'){ b[i].checked=true; } }
  refresh();
}
function pickAll(){ var b=boxes(); for(var i=0;i<b.length;i++){ if(!b[i].disabled){ b[i].checked=true; } } refresh(); }
function clearAll(){ var b=boxes(); for(var i=0;i<b.length;i++){ b[i].checked=false; } refresh(); }
function copySel(){
  refresh();
  var t=document.getElementById('selection');
  t.focus(); t.select();
  var ok=false;
  try{ ok=document.execCommand('copy'); }catch(e){ ok=false; }
  document.getElementById('copied').innerHTML = ok ?
    'Copied. Paste it into the "Figures to copy" option.' :
    'Press Ctrl+C to copy the selected text, then paste it into the "Figures to copy" option.';
}
"""

def target_project():
    # \outputProject normally defaults to the project the tool is run from.
    return OutputProject or Project

def check_projects():
    """Source = CompareProject, target = Output project. Returns an error
    message, or None when the pair can be used."""
    if not CompareProject:
        return (u'Error: choose the project to compare with in the option '
                u'"Project to compare with (copy figures from)".')
    if not target_project():
        return u'Error: no Output project was given.'
    if CompareProject.lower() == target_project().lower():
        return (u'Error: the project to compare with (' + CompareProject +
                u') cannot be the same as the Output project.')
    return None

def run_compare():
    err = check_projects()
    if err:
        _out(err)
        return
    source = CompareProject
    target = target_project()

    srcFigs, err = collect_figures(source)
    if err:
        _out(u'Error reading Scripture books of ' + source + u':\n\t' + err)
        if not srcFigs:
            _out(u'Check the spelling of the project to compare with (the short project name, e.g. WSG).')
            return
    tgtFigs, err = collect_figures(target)
    if err:
        _out(u'Error reading Scripture books of ' + target + u':\n\t' + err)

    refs = sorted(set(srcFigs.keys()) | set(tgtFigs.keys()), key=ref_sort_key)

    showCaps = _yes(ShowCaptionList)
    showThumbs = _yes(ShowThumbnails)
    onlyDiffs = _yes(OnlyShowDiffs)

    def cell_html(prj, f, cls):
        if f is None:
            return u'<td class="missing">-</td>'
        cell = u'<span class="fn">' + _he(compare_key(f['src'])) + u'</span>'
        if showThumbs:
            img = find_image(prj, f['src'])
            if img and os.path.splitext(img)[1].lower() in SHOWABLE_EXTS:
                cell += u'<img class="th" loading="lazy" src="' + _attr(_file_url(img)) + u'" alt="">'
        if showCaps:
            if f['caption']:
                cell += u'<div class="cap">' + _he(f['caption']) + u'</div>'
            if f['loc']:
                cell += u'<div class="loc">loc: ' + _he(f['loc']) + u'</div>'
        return u'<td' + cls + u'>' + cell + u'</td>'

    rows = []
    nMissing = 0
    nDiff = 0
    nShown = 0
    for ref in refs:
        src = srcFigs.get(ref)
        out = tgtFigs.get(ref)
        missingInOut = src is not None and out is None
        diffFromOut = (src is not None and out is not None and
                       compare_key(src['src']) != compare_key(out['src']))
        differs = src is None or out is None or diffFromOut
        if missingInOut:
            nMissing += 1
        if diffFromOut:
            nDiff += 1
        if onlyDiffs and not differs:
            continue
        nShown += 1
        if src is not None:
            box = u'<input type="checkbox" class="pick" value="%s" data-missing="%s" data-diff="%s" onclick="refresh()">' % (
                _attr(ref), u'1' if missingInOut else u'0', u'1' if diffFromOut else u'0')
        else:
            box = u'<input type="checkbox" class="pick" disabled title="Not in %s">' % _attr(source)
        rows.append(u'<tr><td>' + box + u'</td><td class="ref">' + _he(ref) + u'</td>' +
                    cell_html(source, src, u'') +
                    cell_html(target, out, u' class="diff"' if diffFromOut else u'') +
                    u'</tr>')

    html = [
        u'<!DOCTYPE html><html><head><meta charset="utf-8">',
        u'<title>Compare Figures</title><style>' + REPORT_CSS + u'</style>',
        u'<script>' + REPORT_JS + u'</script></head><body>',
        u'<h1>Compare Figures</h1>',
        u'<div class="meta">Copy from: <b>%s</b> &nbsp;&rarr;&nbsp; into: <b>%s</b> &nbsp; Books: %s<br>'
        u'%d figure references: %d missing in %s, %d different; %d shown%s.</div>' % (
            _he(source), _he(target), _he(book_list_display(Books)),
            len(refs), nMissing, _he(target), nDiff, nShown, u' (only differences)' if onlyDiffs else u''),
        u'<div class="bar">',
        u'<button onclick="pick(\'data-missing\')">Select missing in %s</button>' % _he(target),
        u'<button onclick="pick(\'data-diff\')">Select different from %s</button>' % _he(target),
        u'<button onclick="pickAll()">Select all</button>',
        u'<button onclick="clearAll()">Clear</button>',
        u'<button onclick="copySel()"><b>Copy selection</b></button> ',
        u'<span id="count">0</span> selected. <span id="copied"></span>',
        u'<textarea id="selection" readonly></textarea>',
        u'<div class="note">To copy figures from %s into %s: tick them, click <b>Copy selection</b>, '
        u'run this tool again with <b>Mode</b> = <b>Copy</b>, and paste into <b>Figures to copy</b>. '
        u'Choose the same books. Red = missing; yellow = a different picture in %s.</div>' % (
            _he(source), _he(target), _he(target)),
        u'</div>',
        u'<table><tr><th></th><th>Reference</th><th>%s (copy from)</th><th>%s (Output)</th></tr>' % (
            _he(source), _he(target)),
    ]
    html.extend(rows)
    html.append(u'</table></body></html>')

    path = write_report(u''.join(html))
    _out(u'Compare Figures: %s -> %s: %d figure references, %d missing in %s, %d different, %d shown.' % (
        source, target, len(refs), nMissing, target, nDiff, nShown))
    if path:
        _out(u'Report: ' + path)

def write_report(html):
    base = project_dir(Project) if SettingsDirectory and Project else u''
    candidates = []
    if base:
        candidates.append(os.path.join(base, u'local', u'CompareFigures'))
    tmp = os.environ.get('TEMP') or os.environ.get('TMP')
    if tmp:
        candidates.append(_to_unicode(tmp))
    for d in candidates:
        try:
            if not os.path.isdir(d):
                os.makedirs(d)
            path = os.path.join(d, u'CompareFiguresReport.html')
            f = open(_open_path(path), 'wb')
            try:
                f.write(html.encode('utf-8'))
            finally:
                f.close()
        except Exception, e:
            _out(u'Could not write the report in ' + d + u': ' + _to_unicode(str(e)))
            continue
        try:
            os.startfile(_open_path(path))
        except Exception:
            pass
        return path
    return None

#__________________________________________________________________________________
# COPY MODE

def parse_selection(text):
    """Return a list of (token, book, chapter, verseRef) and whether ALL was
    given. verseRef is e.g. '3' or '3b'; chapter/verseRef may be None."""
    sel = []
    for m in SEL_RE.finditer(_to_unicode(text)):
        book = m.group(1).upper()
        if book == u'ALL':
            return ([], True)
        chap = m.group(2)
        vref = None
        if m.group(3) is not None:
            vref = m.group(3) + m.group(4).lower()
        sel.append((m.group(0), book, chap, vref))
    return (sel, False)

def fig_matches(fig, book, chap, vref):
    if fig['book'] != book:
        return False
    if chap is None:
        return True
    if fig['chapRef'] != book + u' ' + chap:
        return False
    if vref is None:
        return True
    # 'GEN 1:3' is the verse's first figure; 'GEN 1:3b' its second.
    return fig['ref'] == book + u' ' + chap + u':' + vref

def place_in_chapter(outText, vrs, figcode):
    """Insert figcode at the end of the first line of verse vrs (or a nearby
    verse, up to 3 away). Returns (newText, verseUsed or None)."""
    try:
        v = int(vrs)
    except ValueError:
        v = 0
    for vint in [v, v - 1, v + 1, v - 2, v + 2, v - 3, v + 3]:
        if vint <= 0:
            continue
        vstry = str(vint)
        pat = re.compile(r'(\\v (' + vstry + r'[ -]|\d+-' + vstry + r' ).+?)(\\(v|c|s|m|p|q|q1|b|pi|l)\b|\r|\n|$)', re.DOTALL)
        m = pat.search(outText)
        if m:
            return (outText[:m.end(1)] + figcode + outText[m.end(1):], vstry)
    return (outText, None)

def target_figcode(fig, includeCaps, wrapCaps):
    caption = fig['caption']
    newCap = caption if includeCaps else u''
    if newCap and wrapCaps:
        newCap = u'[' + newCap + u']'
    if newCap != caption:
        return replace_caption(fig['sFigr'], newCap)
    return fig['sFigr']

def find_or_make_figures_dir(prj):
    d = project_dir(prj)
    for name in (u'figures', u'Figures'):
        p = os.path.join(d, name)
        if os.path.isdir(p):
            return p
    p = os.path.join(d, u'figures')
    os.makedirs(p)
    return p

def remove_all_figures(scrOut, target):
    """Strip every \\fig ...\\fig* from the chosen books of the target.
    Returns the number removed, or None if Paratext refused the write."""
    total = 0
    perBook = {}
    books = []
    for reference, text in scrOut.chapters(Books):
        reference = _to_unicode(reference)
        text = _to_unicode(text)
        cm = CHAP_RE.match(reference)
        if cm is None:
            continue
        chapRef = cm.group(1).upper() + u' ' + cm.group(2)
        (newText, ct) = FIG_RE.subn(u'', text)
        if not ct:
            continue
        try:
            scrOut.putText(chapRef + u':0', newText, 1)
        except ValueError:
            _out(u'Access Denied! Paratext is blocking access to project: ' + target)
            return None
        book = cm.group(1).upper()
        if book not in perBook:
            perBook[book] = 0
            books.append(book)
        perBook[book] += ct
        total += ct
    for book in books:
        _out(u'>> Removed %d existing figure(s) from %s in %s' % (perBook[book], book, target))
    return total

def run_copy():
    err = check_projects()
    if err:
        _out(err)
        return
    source = CompareProject
    target = target_project()
    removeAll = _yes(RemoveAllExisting)
    if not _to_unicode(FiguresToCopy).strip() and not removeAll:
        _out(u'Nothing to copy: the "Figures to copy" option is empty.')
        _out(u'Run with Mode = Compare, tick figures in the report, click "Copy selection" and paste the list into "Figures to copy".')
        return

    sel, copyAll = parse_selection(FiguresToCopy)
    srcFigs, err = collect_figures(source)
    if err:
        _out(u'Error reading Scripture books of ' + source + u':\n\t' + err)
        return
    tgtFigs, err = collect_figures(target)
    if err:
        _out(u'Error reading Scripture books of ' + target + u':\n\t' + err)
        return

    _out(u'Source (Compare) Project=' + source)
    _out(u'Target (Output) Project=' + target)
    _out(u'Figures found in Source: ' + unicode(len(srcFigs)))
    _out(u'RemoveAllExisting=' + _to_unicode(RemoveAllExisting) +
         u'  CopyEvenIfPresent=' + _to_unicode(CopyEvenIfPresent) + u'  ReplaceDifferent=' + _to_unicode(ReplaceDifferent) +
         u'  CopyFilesOverAsWell=' + _to_unicode(CopyFilesOverAsWell) +
         u'  IncludeCaptions=' + _to_unicode(IncludeCaptions) + u'  WrapTargetCaption=' + _to_unicode(WrapTargetCaption))

    chosen = []
    used = set()
    for ref in sorted(srcFigs.keys(), key=ref_sort_key):
        fig = srcFigs[ref]
        if copyAll:
            chosen.append(fig)
            continue
        hits = [i for i, (tok, book, chap, vref) in enumerate(sel) if fig_matches(fig, book, chap, vref)]
        if hits:
            chosen.append(fig)
            used.update(hits)
    if not copyAll:
        for i, (tok, book, chap, vref) in enumerate(sel):
            if i not in used:
                _out(u'Not found in ' + source + u': "' + tok + u'" (check that its book was chosen).')
    _out(u'Figures selected: ' + unicode(len(chosen)))

    # Names of the figures already in each target chapter (for skipping).
    tgtNames = {}
    for f in tgtFigs.values():
        tgtNames.setdefault(f['chapRef'], set()).add(normalized_name(f['src']).lower())

    # Group by chapter, then verse, keeping source order.
    chapters = []
    byChap = {}
    for fig in chosen:
        if fig['chapRef'] not in byChap:
            byChap[fig['chapRef']] = []
            chapters.append(fig['chapRef'])
        byChap[fig['chapRef']].append(fig)

    copyFiles = _yes(CopyFilesOverAsWell)
    includeCaps = _yes(IncludeCaptions)
    wrapCaps = _yes(WrapTargetCaption)
    evenIfPresent = _yes(CopyEvenIfPresent)
    replaceDiff = _yes(ReplaceDifferent)
    figsAdded = 0
    figsReplaced = 0
    figsSkip = 0
    placed = []

    try:
        scrOut = ScriptureText(target)
    except Exception, e:
        _out(u'Could not open the Output project ' + target + u': ' + _to_unicode(str(e)))
        return

    if removeAll:
        removed = remove_all_figures(scrOut, target)
        if removed is None:
            return
        _out(u'Figures removed: ' + unicode(removed))
        tgtFigs = {}
        tgtNames = {}
        if not chosen:
            _out(u'No figures were selected to copy, so only the existing figures were removed.\n ')
            return

    for chapRef in chapters:
        try:
            outText = _to_unicode(scrOut.getText(chapRef + u':0', 1))  # Read the chapter
        except Exception, e:
            _out(chapRef + u'\t>>!! Could not read this chapter in ' + target + u': ' + _to_unicode(str(e)))
            continue
        if not outText:
            _out(chapRef + u'\t>>!! This chapter is empty or missing in ' + target + u'.')
            continue
        verses = []
        byVerse = {}
        chapPlaced = []
        for fig in byChap[chapRef]:
            name = normalized_name(fig['src']).lower()
            figcode = target_figcode(fig, includeCaps, wrapCaps)
            old = tgtFigs.get(fig['ref'])  # figure at the same reference in the target
            if old is not None:
                same = normalized_name(old['src']).lower() == name
                if (same and evenIfPresent) or (not same and replaceDiff):
                    if old['sFigr'] in outText:
                        outText = outText.replace(old['sFigr'], figcode, 1)
                        _out(fig['ref'] + u'\tReplaced ' + old['src'] + u' with: ' + figcode)
                        figsReplaced += 1
                        chapPlaced.append(fig)
                        continue
                elif same:
                    _out(u'Skipping (already in target): ' + fig['ref'] + u'\t' + fig['src'])
                    figsSkip += 1
                    continue
            elif not evenIfPresent and name in tgtNames.get(chapRef, set()):
                _out(u'Skipping (already in target chapter): ' + fig['ref'] + u'\t' + fig['src'])
                figsSkip += 1
                continue
            if fig['vrs'] not in byVerse:
                byVerse[fig['vrs']] = []
                verses.append(fig['vrs'])
            byVerse[fig['vrs']].append((fig, figcode))

        chapAdded = 0
        for vrs in verses:
            codes = [code for (fig, code) in byVerse[vrs]]
            for fig, code in byVerse[vrs]:
                _out(fig['ref'] + u'\t' + code)
            outText, vUsed = place_in_chapter(outText, vrs, u''.join(codes))
            if vUsed is None:
                _out(chapRef + u':' + vrs + u'\t>>!! Could not place \\fig ...\\fig* due to missing precise verse.')
                continue
            if vUsed != vrs:
                _out(chapRef + u':' + vrs + u'\t!! Fuzzy match placed \\fig in verse: ' + vUsed)
            chapAdded += len(codes)
            chapPlaced.extend(fig for (fig, code) in byVerse[vrs])

        if chapPlaced:
            try:
                scrOut.putText(chapRef + u':0', outText, 1)
            except ValueError:
                _out(u'Access Denied! Paratext is blocking access to project: ' + target)
                figsReplaced -= len(chapPlaced) - chapAdded
                break
            figsAdded += chapAdded
            placed.extend(chapPlaced)

    if copyFiles and placed:
        copied = 0
        done = set()
        try:
            tgtDir = find_or_make_figures_dir(target)
        except Exception, e:
            tgtDir = None
            _out(u'Could not create the figures folder of ' + target + u': ' + _to_unicode(str(e)))
        if tgtDir:
            for fig in placed:
                srcPath = find_image(source, fig['src'])
                if srcPath is None:
                    _out(u'Could not find the picture file for ' + fig['src'] + u' in ' + source + u'\\figures.')
                    continue
                name = os.path.basename(srcPath)
                if name.lower() in done:
                    continue
                done.add(name.lower())
                tgtPath = os.path.join(tgtDir, name)
                if os.path.exists(tgtPath):
                    _out(u'Picture file already in target (not overwritten): ' + name)
                    continue
                try:
                    copyfile(srcPath, tgtPath)
                    copied += 1
                    _out(u'Copied picture file: ' + name)
                except Exception, e:
                    _out(u'Could not copy ' + srcPath + u': ' + _to_unicode(str(e)))
        _out(u'Picture files copied: ' + unicode(copied))

    _out(u'Figures added: ' + unicode(figsAdded))
    _out(u'Figures replaced: ' + unicode(figsReplaced))
    _out(u'Figures skipped: ' + unicode(figsSkip) + u'\n ')

# __________________________________________________________________________________
##### MAIN PROGRAM #####

if _to_unicode(Mode).strip().lower().startswith(u'cop'):
    run_copy()
else:
    run_compare()
