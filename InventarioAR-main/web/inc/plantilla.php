<?php
// Encabezado (marca + menú de navegación) y pie comunes a las páginas públicas.

const NOMBRE_SISTEMA = 'Sistema de Inventario de Equipos de Radio';
const NOMBRE_CORTO = 'InventarioAR';
const DESCRIPCION_SISTEMA = 'Aplicación web para gestionar equipos de radiocomunicación: inventario con canales, '
    . 'reparaciones en taller, stock de repuestos y estadísticas.';

/** URL absoluta de la carpeta web/ (para la URL canónica, Open Graph y el sitemap). */
function urlBase(): string {
    $https = ($_SERVER['HTTPS'] ?? '') === 'on' || ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https';
    $host = preg_replace('/[^A-Za-z0-9.:-]/', '', $_SERVER['HTTP_HOST'] ?? 'localhost');
    $carpeta = rtrim(str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'] ?? '/')), '/');
    return ($https ? 'https' : 'http') . "://$host$carpeta/";
}

/**
 * Abre la página.
 *   $activa: id del ítem del menú resaltado (inicio, contacto, registro, ingresar).
 *   $opciones['mapa']: permite el iframe de Google Maps (página de contacto).
 *   $opciones['descripcion']: meta description (por defecto, la del sistema).
 *   $opciones['titulo_completo']: <title> tal cual, sin agregarle el nombre del sistema.
 *   $opciones['jsonld']: datos estructurados schema.org (array) para buscadores.
 *   $opciones['noindex']: pide a los buscadores que no indexen la página.
 *   $opciones['ancho_completo']: el contenido arma sus propias secciones a todo el ancho.
 */
function encabezado(string $titulo, string $activa = '', array $opciones = []): void {
    $marcos = !empty($opciones['mapa']) ? "https://www.google.com https://maps.google.com" : "'none'";
    header('Content-Type: text/html; charset=utf-8');
    header("Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; "
         . "script-src 'self'; frame-src $marcos; form-action 'self'; base-uri 'self'; "
         . "object-src 'none'; frame-ancestors 'none'");

    $usuario = usuarioActual();
    $items = [['inicio', 'index.php', 'Inicio'], ['contacto', 'contacto.php', 'Contacto']];
    if (!$usuario) {
        $items[] = ['ingresar', 'ingresar.php', 'Ingresar'];
        $items[] = ['registro', 'registro.php', 'Crear cuenta'];
    }
    $tituloPagina = $opciones['titulo_completo'] ?? "$titulo · " . NOMBRE_SISTEMA;
    $descripcion = $opciones['descripcion'] ?? DESCRIPCION_SISTEMA;
    $pagina = basename($_SERVER['SCRIPT_NAME'] ?? 'index.php');
    $canonica = urlBase() . ($pagina === 'index.php' ? '' : $pagina);
    ?>
<!DOCTYPE html>
<html lang="es-AR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= e($tituloPagina) ?></title>
    <meta name="description" content="<?= e($descripcion) ?>">
    <?php if (!empty($opciones['noindex'])): ?>
    <meta name="robots" content="noindex, nofollow">
    <?php else: ?>
    <link rel="canonical" href="<?= e($canonica) ?>">
    <?php endif; ?>
    <meta name="theme-color" content="#1565c0">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="es_AR">
    <meta property="og:site_name" content="<?= e(NOMBRE_SISTEMA) ?>">
    <meta property="og:title" content="<?= e($tituloPagina) ?>">
    <meta property="og:description" content="<?= e($descripcion) ?>">
    <meta property="og:url" content="<?= e($canonica) ?>">
    <link rel="icon" href="img/logo.svg" type="image/svg+xml">
    <link rel="preload" href="fonts/plex-sans-400.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="fonts/plex-sans-700.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="stylesheet" href="css/app.css">
    <link rel="stylesheet" href="css/sitio.css">
    <script src="js/menu.js" defer></script>
    <?php if (!empty($opciones['jsonld'])): ?>
    <script type="application/ld+json"><?= json_encode($opciones['jsonld'], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP) ?></script>
    <?php endif; ?>
</head>
<body class="sitio">
    <a class="saltar" href="#contenido">Saltar al contenido</a>
    <header class="sitio-cabecera">
        <div class="sitio-cabecera-interior">
            <a class="sitio-marca" href="index.php">
                <img src="img/logo.svg" alt="" width="40" height="40">
                <span>
                    <strong><?= e(NOMBRE_CORTO) ?></strong>
                    <small>Equipos de radio</small>
                </span>
            </a>
            <button type="button" class="menu-boton" aria-expanded="false" aria-controls="menu-principal" hidden>
                <svg class="menu-icono-abrir" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
                <svg class="menu-icono-cerrar" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>
                <span class="solo-lectores">Menú</span>
            </button>
            <nav class="sitio-menu" id="menu-principal" aria-label="Menú principal">
                <ul>
                    <?php foreach ($items as [$id, $url, $texto]): ?>
                        <li><a href="<?= e($url) ?>"<?= $id === 'registro' ? ' class="menu-destacado"' : ($id === 'ingresar' ? ' class="menu-borde"' : '') ?><?= $id === $activa ? ' aria-current="page"' : '' ?>><?= e($texto) ?></a></li>
                    <?php endforeach; ?>
                    <?php if ($usuario): ?>
                        <li><a class="menu-destacado" href="app.php">Ir al sistema</a></li>
                        <li>
                            <form method="post" action="salir.php" class="form-salir">
                                <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">
                                <button type="submit">Salir (<?= e($usuario['username']) ?>)</button>
                            </form>
                        </li>
                    <?php endif; ?>
                </ul>
            </nav>
        </div>
    </header>
    <main class="<?= !empty($opciones['ancho_completo']) ? 'sitio-portada' : 'sitio-contenido' ?>" id="contenido">
<?php
}

function pie(): void {
    ?>
    </main>
    <footer class="sitio-pie">
        <div class="pie-interior">
            <div class="pie-columnas">
                <div>
                    <strong class="pie-marca"><?= e(NOMBRE_CORTO) ?></strong>
                    <p><?= e(NOMBRE_SISTEMA) ?>. Proyecto Integrador de Programación IV.</p>
                </div>
                <nav aria-label="Sitio">
                    <strong>Sitio</strong>
                    <a href="index.php#funciones">Funciones</a>
                    <a href="index.php#taller">Circuito de taller</a>
                    <a href="index.php#preguntas">Preguntas frecuentes</a>
                </nav>
                <nav aria-label="Cuenta">
                    <strong>Cuenta</strong>
                    <a href="ingresar.php">Ingresar</a>
                    <a href="registro.php">Crear cuenta</a>
                </nav>
                <address>
                    <strong>Contacto</strong>
                    <span>UTN Facultad Regional Haedo</span>
                    <span>París 532, Haedo, Buenos Aires</span>
                    <a href="contacto.php">Formulario de contacto</a>
                </address>
            </div>
            <p class="pie-legal">© <?= date('Y') ?> · Proyecto Integrador · Programación IV · UTN FRH</p>
        </div>
    </footer>
</body>
</html>
<?php
}
