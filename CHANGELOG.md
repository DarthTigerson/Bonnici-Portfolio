# Changelog

All notable changes to the Bonnici Portfolio project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-03-23

### Changed
- Complete admin panel rewrite as a React/TypeScript SPA (Vite + shadcn/ui)
- Redesigned frontend with upgraded background and hero animations
- Improved Jinja2 templating structure in the frontend

### Fixed
- Duplicate page H1 headings in admin panel (page name already shown in breadcrumb)
- Tab naming inconsistencies
- "What I'm Doing" section bugs

## [0.4.2] - 2025-04-28

### Added
- Initialization notification in portfolio
- Wallpaper mode toggle
- Version display on login page
- Enhanced SEO tracking and meta data descriptions

### Fixed
- Portfolio appearing in mobile navbar even when disabled
- "Flag as new" UI bug
- Project page issues:
  - Options buttons stopping work after deleting a project
  - Double confirmation when attempting to delete a project
- Inconsistency in SVG images showing on mobile view
- Added error messages when attempting to upload unsupported image formats (HEIC/HEIF)
- Fixed bug where some SVG colors don't change to match site color scheme

### Changed
- Improved save button UI that flashes and changes colors when changes are detected
- Cleaned up project samples
- Added support for GIF files in projects