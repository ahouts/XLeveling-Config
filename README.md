# XLeveling Config

This repository tracks editable JSONC configuration files for the Vintage Story
XLeveling mod.

Edit the root-level `*.jsonc` files, then build strict JSON files for the mod:

```sh
python3 scripts/build.py
```

The build writes pure JSON to `dist/*.json`. Generated files preserve the source
formatting as closely as possible while removing JSONC comments and trailing
commas. Copy or symlink the files from `dist/` into the mod's config location.
