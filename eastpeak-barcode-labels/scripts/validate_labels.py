#!/usr/bin/env python3
"""Decode actual single-label PDF pixels against an authoritative SKU/UPC map."""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def checksum_ok(value):
    return (isinstance(value, str) and re.fullmatch(r'[0-9]{12}', value) is not None
            and sum(int(n) * (3 if i % 2 == 0 else 1)
                    for i, n in enumerate(value)) % 10 == 0)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def load_expected(path):
    data = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if not isinstance(data, dict) or not data:
        raise ValueError('Expected a nonempty JSON object: SKU -> UPC string')
    seen = set()
    for sku, upc in data.items():
        if not sku or sku in ('.', '..') or any(c in sku for c in '/\\\x00'):
            raise ValueError(f'SKU must be a filename stem: {sku!r}')
        if not checksum_ok(upc):
            raise ValueError(f'{sku}: expected 12-digit string with valid UPC-A checksum')
        if upc in seen:
            raise ValueError(f'{sku}: duplicate UPC assignment {upc}; resolve source mapping')
        seen.add(upc)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', type=Path, required=True)
    parser.add_argument('--pdf-dir', type=Path, required=True)
    parser.add_argument('--lsc-dir', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--dpi', type=int, default=300,
                        help='Render resolution; default 300. Lower values are stress tests.')
    args = parser.parse_args()
    report = {'dpi': args.dpi, 'decoder': 'ZXing-C++', 'results': [], 'passed': False}
    try:
        if args.dpi <= 0:
            raise ValueError('DPI must be positive')
        expected = load_expected(args.expected)
        inputs = [(args.pdf_dir / (sku + '.pdf')).resolve() for sku in expected]
        inputs += [(args.lsc_dir / (sku + '.lsc')).resolve() for sku in expected] if args.lsc_dir else []
        if args.report.resolve() in inputs + [args.expected.resolve()]:
            raise ValueError('Report path must not overwrite an input')
        from PIL import Image
        from pypdf import PdfReader
        import zxingcpp
        with tempfile.TemporaryDirectory(prefix='upc-scan-') as scratch:
            for i, (sku, upc) in enumerate(expected.items()):
                result = {'sku': sku, 'expected_upc': upc, 'scans': [], 'passed': False}
                try:
                    pdf = args.pdf_dir / (sku + '.pdf')
                    reader = PdfReader(pdf)
                    if len(reader.pages) != 1:
                        raise ValueError('Expected exactly one label page')
                    box = reader.pages[0].mediabox
                    result['page_inches'] = [float(box.width)/72, float(box.height)/72]
                    if args.lsc_dir:
                        doc = json.loads((args.lsc_dir / (sku + '.lsc')).read_text())
                        codes = [o['config']['text'] for o in doc['canvasRecord']['objects']
                                 if o.get('type') == 'ELEMENT_BARCODE']
                        if codes != [upc]:
                            raise ValueError(f'Native barcode data mismatch: {codes!r}')
                        result['native_data_matches'] = True
                    prefix = Path(scratch) / str(i)
                    subprocess.run(['pdftoppm', '-r', str(args.dpi), '-singlefile', '-png',
                                    str(pdf), str(prefix)], check=True, capture_output=True,
                                   text=True, timeout=120)
                    with Image.open(str(prefix) + '.png') as original:
                        image = original.convert('RGB')
                    for angle in (0, 90, 180, 270):
                        decoded = zxingcpp.read_barcodes(image.rotate(angle, expand=True))
                        raw = [c.text for c in decoded]
                        good = (len(decoded) == 1 and decoded[0].valid
                                and decoded[0].format in (zxingcpp.BarcodeFormat.UPCA, zxingcpp.BarcodeFormat.EAN13)
                                and decoded[0].text in (upc, '0' + upc))
                        result['scans'].append({'rotation': angle, 'raw_decoded': raw,
                                                'formats': [str(c.format) for c in decoded],
                                                'passed': bool(good)})
                    result['passed'] = all(s['passed'] for s in result['scans'])
                except Exception as exc:
                    result['error'] = str(exc)
                report['results'].append(result)
                print(f"{sku}: {'PASS' if result['passed'] else 'FAIL'}")
        report['passed'] = bool(report['results']) and all(r['passed'] for r in report['results'])
    except Exception as exc:
        report['error'] = str(exc)
    # Never overwrite inputs, including after an input-path validation failure.
    protected = [args.expected.resolve()]
    for folder, suffix in ((args.pdf_dir, '.pdf'), (args.lsc_dir, '.lsc')):
        if folder:
            protected.extend(p.resolve() for p in folder.glob('*' + suffix))
    if args.report.resolve() in protected:
        print(json.dumps(report, indent=2), file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    if report.get('error'):
        print(report['error'], file=sys.stderr)
    print(f"{'PASS' if report['passed'] else 'FAIL'} — report: {args.report}")
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
