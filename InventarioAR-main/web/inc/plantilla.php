<?php
// Encabezado (marca + menú de navegación) y pie comunes a las páginas públicas.

const NOMBRE_SISTEMA = 'Sistema de Inventario de Equipos de Radio';

/**
 * Abre la página.
 *   $activa: id del ítem del menú resaltado (inicio, contacto, registro, ingresar).
 *   $opciones['mapa']: permite el iframe de Google Maps (página de contacto).
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
        $items[] = ['registro', 'registro.php', 'Registrarse'];
        $items[] = ['ingresar', 'ingresar.php', 'Ingresar'];
    }
    ?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= e($titulo) ?> · <?= e(NOMBRE_SISTEMA) ?></title>
    <link rel="icon" href="img/logo.svg" type="image/svg+xml">
    <link rel="stylesheet" href="css/app.css">
    <link rel="stylesheet" href="css/sitio.css">
</head>
<body class="sitio">
    <a class="saltar" href="#contenido">Saltar al contenido</a>
    <header class="sitio-cabecera">
        <a class="sitio-marca" href="index.php">
            <img src="img/logo.svg" alt="" width="44" height="44">
            <span><?= e(NOMBRE_SISTEMA) ?></span>
        </a>
        <nav class="sitio-menu" aria-label="Menú principal">
            <ul>
                <?php foreach ($items as [$id, $url, $texto]): ?>
                    <li><a href="<?= e($url) ?>"<?= $id === $activa ? ' aria-current="page"' : '' ?>><?= e($texto) ?></a></li>
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
    </header>
    <main class="sitio-contenido" id="contenido">
<?php
}

function pie(): void {
    ?>
    </main>
    <footer class="sitio-pie">
        <p><?= e(NOMBRE_SISTEMA) ?> · Proyecto Integrador · Programación IV · <?= date('Y') ?></p>
        <p><a href="contacto.php">Contacto</a></p>
    </footer>
</body>
</html>
<?php
}
