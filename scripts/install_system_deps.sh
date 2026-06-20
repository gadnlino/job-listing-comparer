#!/usr/bin/env bash
# Install native libraries required for WeasyPrint PDF generation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

has_gobject() {
  for libdir in /opt/homebrew/lib /usr/local/lib; do
    if [ -f "$libdir/libgobject-2.0.0.dylib" ] || [ -f "$libdir/libgobject-2.0.dylib" ]; then
      return 0
    fi
  done
  if ldconfig -p 2>/dev/null | grep -q 'libgobject-2.0.so'; then
    return 0
  fi
  return 1
}

install_macos() {
  if has_gobject; then
    echo "✓ WeasyPrint system libraries already present"
    return 0
  fi

  if ! command -v brew >/dev/null 2>&1; then
    echo "⚠ Homebrew not found — install from https://brew.sh for PDF support"
    echo "  Then run: brew install glib pango cairo gdk-pixbuf libffi"
    return 1
  fi

  echo "→ Installing WeasyPrint system libraries via Homebrew..."
  brew install glib pango cairo gdk-pixbuf libffi
  echo "✓ WeasyPrint system libraries installed"
}

install_linux() {
  if has_gobject; then
    echo "✓ WeasyPrint system libraries already present"
    return 0
  fi

  if command -v apt-get >/dev/null 2>&1; then
    echo "→ Installing WeasyPrint system libraries via apt..."
    if [ "$(id -u)" -eq 0 ]; then
      apt-get update -qq
      DEBIAN_FRONTEND=noninteractive apt-get install -y \
        libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev libcairo2 \
        libglib2.0-0 shared-mime-info
    elif command -v sudo >/dev/null 2>&1; then
      sudo apt-get update -qq
      DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
        libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev libcairo2 \
        libglib2.0-0 shared-mime-info
    else
      echo "⚠ Run as root or with sudo to install PDF libraries:"
      echo "  sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev libcairo2 libglib2.0-0 shared-mime-info"
      return 1
    fi
    echo "✓ WeasyPrint system libraries installed"
    return 0
  fi

  if command -v dnf >/dev/null 2>&1; then
    echo "→ Installing WeasyPrint system libraries via dnf..."
    if [ "$(id -u)" -eq 0 ]; then
      dnf install -y pango cairo gdk-pixbuf2 libffi glib2 shared-mime-info
    elif command -v sudo >/dev/null 2>&1; then
      sudo dnf install -y pango cairo gdk-pixbuf2 libffi glib2 shared-mime-info
    else
      echo "⚠ Run with sudo to install PDF libraries:"
      echo "  sudo dnf install -y pango cairo gdk-pixbuf2 libffi glib2 shared-mime-info"
      return 1
    fi
    echo "✓ WeasyPrint system libraries installed"
    return 0
  fi

  echo "⚠ Unknown Linux distro — install WeasyPrint system deps manually:"
  echo "  https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
  return 1
}

main() {
  case "$(uname -s)" in
    Darwin) install_macos ;;
    Linux) install_linux ;;
    *)
      echo "⚠ Unsupported OS for automatic PDF library install"
      echo "  https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
      return 1
      ;;
  esac
}

main "$@"
