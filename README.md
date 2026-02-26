# gex

A Gauntlet II arcade ROM tile, stamp, and maze extractor. Originally written as a golang project, now ported to python courtesy of Claude Code. Original project at https://github.com/alinsavix/gex

Extracts and renders tiles, stamps, floors, walls, items, monsters, and complete mazes from Gauntlet II arcade ROMs as PNG images.

## Requirements

- Python 3.12+
- Gauntlet II ROM files (not included)

## Installation

```bash
pip install gex
```

Or install from source:

```bash
pip install .
```

## ROM Setup

Place your Gauntlet II ROM files in a directory called `ROMs/` in your current
working directory, or set the `GEX_ROM_DIR` environment variable to point at
the directory containing the ROM files.

```bash
export GEX_ROM_DIR=/path/to/your/ROMs
```

## Usage

```bash
# Extract a maze
gex maze0

# Extract an item
gex item-key

# Extract a monster sprite
gex ghost-walk-up

# Extract a floor tile with options
gex floor0-c5-var1

# Extract a wall tile
gex wall0-c3

# Extract a specific tile by hex number
gex -t 1a -x 2 -y 2

# Specify output file
gex -o maze42.png maze42

# Show maze metadata
gex -v maze0-meta
```

## Tested ROMs

| File | Size | sha1sum |
|------|------|---------|
| 136037-112.1b | 32kB | 5dfaaf54ee2b3c0eaf35e8c17558313db9791616 |
| 136037-114.1mn | 32kB | 91e1465af6505b35cd97434c13d2b4d40a085946 |
| 136037-116.2b | 32kB | 729b7561d59d94ef33874a134b97bcd37573dfa6 |
| 136037-118.2mn | 32kB | 683d900ab7591ee661218be2406fb375a12e435c |
| 136037-1307.9a | 32kB | d5fa19e028a2f43658330c67c10e0c811d332780 |
| 136037-1308.9b | 32kB | 7467b2ec21b1b4fcc18ff9387ce891495f4b064c |
| 136043-1104.6p | 8kB | 4a9542bc8ede305e7e8f860eb4b47ca2f3017275 |
| 136043-1105.10a | 16kB | a9a03150f5a0ad6ce62c5cfdffb4a9f54340590c |
| 136043-1106.10b | 16kB | d2df4e5b036500dcc537a1e0025abb2a8c730bdd |
| 136043-1109.7a | 32kB | 7f51184840e3c96574836b8a00bfb4a7a5f508d0 |
| 136043-1110.7b | 32kB | dfce027ea50188659907be698aeb26f9d8bfab23 |
| 136043-1111.1a | 32kB | 726984275c6a338c12ec0c4cc449f92f4a7a138c |
| 136043-1113.1l | 32kB | e0757ee0120de2d38be44f8dc8702972c35b87b3 |
| 136043-1115.2a | 32kB | 244e108668eaef6b64c6ff733b08b9ee6b7a2d2b |
| 136043-1117.2l | 32kB | e9b513089eaf3bec269058b437fefe7075a3fd6f |
| 136043-1119.16s | 32kB | 6d0d8493609974bd5a63be858b045fe4db35d8df |
| 136043-1120.16r | 16kB | 045ad571db34ef870b1bf003e77eea403204f55b |
| 136043-1121.6a | 32kB | 3d93236aaffe6ef692e5073b1828633e8abf0ce4 |
| 136043-1122.6b | 32kB | 378c582c360440b808820bcd3be78ec6e8800c34 |
| 136043-1123.1c | 16kB | a24bece3196d13c38e4acdbf62783860253ba67d |
| 136043-1124.1p | 16kB | 3b4ce96da0d178b4bc2d05b5b51b42c7ec461113 |
| 136043-1125.2c | 16kB | 185e38c75c06b6ca131a17ee3a46098279bfe17e |
| 136043-1126.2p | 16kB | abe801dff7bb3f2712e2189c2b91f172d941fccd |


## License

GPL-3.0 -- see [LICENSE](../LICENSE).
