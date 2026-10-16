#!/usr/bin/env bash
# Arma la carpeta y el .zip para subir al hosting (InfinityFree: carpeta htdocs/).
#
# Uso (Git Bash, desde la raíz del repositorio):
#   bash InventarioAR-main/tools/armar_publicacion.sh
#
# Resultado (no se versiona):
#   publicacion/htdocs/        lo que va dentro de htdocs/ del hosting
#   publicacion/htdocs.zip     lo mismo comprimido
#
# Solo incluye lo que el sitio necesita: index.php, .htaccess, web/, php/
# y resources/. Quedan afuera el cliente de escritorio (Python), db/, tools/,
# retirado/, los logs y config.local.php (el de desarrollo).
#
# Si existe InventarioAR-main/php/config.hosting.php (no se versiona: tiene
# la contraseña de la base del hosting) se incluye como php/config.local.php.
set -euo pipefail

ORIGEN="$(cd "$(dirname "$0")/.." && pwd)"
SALIDA="$(cd "$ORIGEN/.." && pwd)/publicacion"
DESTINO="$SALIDA/htdocs"

mkdir -p "$SALIDA"
rm -rf "${SALIDA:?}"/* # se vacía, no se borra: puede estar abierta en el Explorador
mkdir -p "$DESTINO"

cp "$ORIGEN/index.php" "$ORIGEN/.htaccess" "$DESTINO/"
cp -r "$ORIGEN/web" "$ORIGEN/resources" "$DESTINO/"

mkdir -p "$DESTINO/php/logs"
cp "$ORIGEN/php/logs/.htaccess" "$DESTINO/php/logs/"
for archivo in "$ORIGEN"/php/*.php "$ORIGEN"/php/.htaccess; do
    [ -e "$archivo" ] || continue
    case "$(basename "$archivo")" in
        config.local.php|config.hosting.php) ;;
        *) cp "$archivo" "$DESTINO/php/" ;;
    esac
done

if [ -f "$ORIGEN/php/config.hosting.php" ]; then
    cp "$ORIGEN/php/config.hosting.php" "$DESTINO/php/config.local.php"
    echo "Incluido php/config.local.php (desde config.hosting.php)."
else
    echo "AVISO: no existe php/config.hosting.php: hay que crear php/config.local.php en el hosting."
fi

# Nada del cliente de escritorio ni volcados por error.
if find "$DESTINO" \( -name '*.py' -o -name '*.pyc' -o -name '*.sql' -o -name '*.log' -o -name '*.xlsx' \) | grep -q .; then
    echo "ERROR: quedaron archivos que no se publican:" >&2
    find "$DESTINO" \( -name '*.py' -o -name '*.pyc' -o -name '*.sql' -o -name '*.log' -o -name '*.xlsx' \) >&2
    exit 1
fi

# Comprimir: zip si está instalado; si no, PowerShell (Windows).
if command -v zip >/dev/null; then
    (cd "$DESTINO" && zip -qr "$SALIDA/htdocs.zip" .)
else
    # No Compress-Archive: en Windows PowerShell 5.1 guarda las rutas con "\"
    # y en el hosting (Linux) quedan archivos llamados "php\sesion.php" en vez
    # de carpetas. Se arma con .NET y rutas con "/".
    powershell.exe -NoProfile -Command "
        Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
        \$origen = '$(cygpath -w "$DESTINO")'
        \$zip = [IO.Compression.ZipFile]::Open('$(cygpath -w "$SALIDA/htdocs.zip")', 'Create')
        Get-ChildItem -LiteralPath \$origen -Recurse -File -Force | ForEach-Object {
            \$ruta = \$_.FullName.Substring(\$origen.Length + 1).Replace('\\', '/')
            [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile(\$zip, \$_.FullName, \$ruta)
        }
        \$zip.Dispose()"
fi

echo "Listo: $DESTINO ($(find "$DESTINO" -type f | wc -l) archivos) y $SALIDA/htdocs.zip"

# Base de datos para importar en el phpMyAdmin del hosting. Solo tablas y
# datos: el hosting no permite vistas, triggers ni procedimientos (y la base
# ya no los usa). Sin CREATE DATABASE: se importa dentro de la base que da
# el hosting (if0_..._nombre).
MYSQLDUMP="${MYSQLDUMP:-/c/xampp/mysql/bin/mysqldump}"
BASE="${BASE:-inventario_radios}"
if [ -x "$MYSQLDUMP" ] || command -v "$MYSQLDUMP" >/dev/null; then
    "$MYSQLDUMP" -u root --single-transaction --skip-triggers --skip-add-locks \
        --default-character-set=utf8mb4 "$BASE" > "$SALIDA/base_para_hosting.sql"
    if grep -qE 'DEFINER|CREATE (TRIGGER|PROCEDURE|FUNCTION|EVENT)|CREATE .*VIEW' "$SALIDA/base_para_hosting.sql"; then
        echo "ERROR: el volcado tiene vistas, triggers o procedimientos (¿falta aplicar alguna migración?)" >&2
        exit 1
    fi
    echo "Base: $SALIDA/base_para_hosting.sql ($(du -h "$SALIDA/base_para_hosting.sql" | cut -f1)). Tiene datos reales: no compartirla."
else
    echo "AVISO: no se encontró mysqldump ($MYSQLDUMP): exportar la base a mano."
fi
