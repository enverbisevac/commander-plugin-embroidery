# Embroidery Viewer for Commander

A small, cross-platform [Commander](../zig/commander) protocol-v1 plugin that previews
machine-embroidery files as scalable, color stitch paths. It supports PES, PEC, DST,
JEF, EXP, VP3, XXX, and SEW through
[pyembroidery](https://github.com/EmbroidePy/pyembroidery).

The plugin also renders design thumbnails in Commander's grid/gallery views and
adds embroidery targets to the Convert dialog. PES, PEC, DST, JEF, EXP, VP3, XXX,
and SEW can be read; pyembroidery's writable machine formats (all except SEW),
plus PNG and SVG image exports, are offered as conversion targets.

The project is deliberately compact: it is both a useful viewer and a reference for
people building their own Commander plugins.

## Install

Python 3.9 or newer is recommended.

```sh
./install.sh
```

Restart Commander, then select a supported design and open Quick View or press F3.
The viewer reads local files only. Large designs are sampled for a responsive preview;
the original file is never changed.

Switch a pane to Thumbnails or Gallery to see stitch previews. To convert a design,
select it and open Commander's Convert action; the plugin's output formats appear
alongside built-in targets.

To install manually, run `python3 -m pip install -r requirements.txt`, then copy this
directory to Commander's user plugin folder:

- macOS: `~/Library/Application Support/Commander/plugins/embroidery-viewer`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/commander/plugins/embroidery-viewer`
- Windows: `%APPDATA%\Commander\plugins\embroidery-viewer`

## Test and develop

The rendering tests do not require an embroidery sample or third-party package:

```sh
python3 -m unittest discover -s tests -v
```

Test a real design directly after installing dependencies:

```sh
python3 embroidery_viewer.py viewer.render '{"path":"/absolute/path/design.pes"}'
```

The program writes exactly one JSON reply to stdout. Diagnostics belong on stderr.
A handled problem returns exit status 0 with `{"ok":false,"error":"..."}`, allowing
Commander to fall back safely.

## Use this as your plugin template

1. Copy the repository and rename the plugin in `plugin.json`.
2. Change `exec` and the extension list under `capabilities.viewer`.
3. Implement `viewer.render` in any language. Commander passes the method in argument
   1 and a JSON object containing `path` and `maxBytes` in argument 2.
4. Return one of Commander's viewer kinds: `text`, `table`, `tables`, `html`, or
   `image`. Keep stdout machine-readable and put logs on stderr.
5. Run the plugin directly, then copy it into the user plugin folder and test with F3.

Optional capabilities follow the same one-shot protocol. `thumbnail.render` returns
base64 PNG/SVG data for `{path, px}`; `converter.convert` receives
`{src, dst, from, to}`, writes `dst`, and returns `{ok:true}`.

Minimal success reply:

```json
{"ok":true,"kind":"text","text":"Hello from my plugin","lang":"txt"}
```

Commander runs plugins as one-shot subprocesses, so avoid relying on state between
requests. Treat file paths as untrusted input, honor `maxBytes` where applicable, and
never emit active script content in an HTML preview.

## Packaging

Create a zip with `plugin.json` and the executable at its root. A marketplace entry
can then point at the archive and its SHA-256 checksum. See Commander's
`docs/plugins.md` for the catalog schema and full wire protocol.

## License

MIT. The `pyembroidery` dependency is distributed separately under its own license.
