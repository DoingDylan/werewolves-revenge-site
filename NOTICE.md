# Notice: Mixed Licensing

This repository contains two distinct categories of content, licensed
differently:

## 1. Website source code — open source (MIT)

Everything that makes up the website itself is open source under the
[MIT License](./LICENSE):

- `src/` (Astro pages, layouts, components, styles, data-loading code,
  `export_roles.py`, the faction/class color systems, etc.)
- `astro.config.mjs`, `tsconfig.json`, `package.json`, and other tooling
  config
- `public/fonts/` and any other non-game UI assets bundled with the site

You're free to fork, reuse, and adapt this code under the terms of the MIT
license.

## 2. Werewolves Revenge game assets — all rights reserved

The following are **not** covered by the MIT license and remain the
exclusive property of Studio Serene, © 2026 Studio Serene. All rights
reserved:

- All role artwork and portraits in `public/images/roles/`
- The role, faction, and class names, descriptions, and any other game data
  in `src/data/roles.json`
- The Werewolves Revenge name, logo, and `public/images/WW.png`

These assets are included in this repository so the website can be built
and run as-is, but no license is granted to copy, redistribute, modify, or
reuse them outside of running this website. If you fork this project to
build your own site, replace this content with your own.
