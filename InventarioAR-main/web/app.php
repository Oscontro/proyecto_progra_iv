<?php
// Aplicación (zona protegida). Solo se muestra con una sesión de PHP válida:
// sin sesión redirige a la página de error (como pide la consigna).
// El contenido lo arma js/app.js consultando la API (php/*.php).
require_once __DIR__ . '/inc/inicio.php';

if (!usuarioActual()) {
    irAError('sin_sesion');
}
session_write_close();   // la API usa la misma sesión: no dejarla bloqueada

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
header("Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
     . "connect-src 'self'; base-uri 'self'; form-action 'self'; object-src 'none'; frame-ancestors 'none'");
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sistema · <?= e(NOMBRE_SISTEMA) ?></title>
    <link rel="icon" href="img/logo.svg" type="image/svg+xml">
    <link rel="stylesheet" href="css/app.css">
    <script type="module" src="js/app.js"></script>
</head>
<body>
    <main id="app" aria-live="polite">
        <div class="pantalla-centro">
            <p class="cargando">Cargando…</p>
        </div>
    </main>

    <div id="avisos" class="avisos"></div>

    <noscript>
        <p class="noscript">Esta aplicación necesita JavaScript habilitado.</p>
    </noscript>

    <!-- ─────────────── Vistas ─────────────── -->

    <template id="tpl-cargando">
        <div class="pantalla-centro">
            <p class="cargando">Cargando…</p>
        </div>
    </template>

    <template id="tpl-error-inicio">
        <div class="pantalla-centro">
            <div class="tarjeta tarjeta-chica">
                <h1>No se pudo iniciar la aplicación</h1>
                <p class="mensaje-error" data-ref="mensaje"></p>
                <button type="button" class="btn btn-primario" data-ref="reintentar">Reintentar</button>
            </div>
        </div>
    </template>

    <template id="tpl-cambio-clave">
        <div class="acceso">
            <aside class="acceso-marca">
                <div class="acceso-icono" aria-hidden="true">🔒</div>
                <p class="acceso-sistema" data-ref="leyenda"></p>
            </aside>
            <section class="acceso-panel">
                <form class="tarjeta" data-ref="form" novalidate>
                    <h1>Cambiar contraseña</h1>
                    <p class="mensaje-info" data-ref="aviso" hidden>
                        Tu cuenta tiene una contraseña temporal. Para continuar, elegí una nueva.
                    </p>
                    <p class="mensaje-error" data-ref="error" role="alert" hidden></p>

                    <label for="clave-actual">Contraseña actual</label>
                    <input id="clave-actual" name="actual" type="password" autocomplete="current-password" required>

                    <label for="clave-nueva">Nueva contraseña</label>
                    <input id="clave-nueva" name="nueva" type="password" autocomplete="new-password"
                           minlength="8" aria-describedby="clave-nueva-ayuda" required>
                    <small id="clave-nueva-ayuda" class="ayuda">Mínimo 8 caracteres.</small>

                    <label for="clave-repetir">Repetir nueva contraseña</label>
                    <input id="clave-repetir" name="repetir" type="password" autocomplete="new-password" required>

                    <div class="acciones">
                        <button type="button" class="btn btn-secundario" data-ref="cancelar"></button>
                        <button type="submit" class="btn btn-primario">Guardar</button>
                    </div>
                </form>
            </section>
        </div>
    </template>

    <template id="tpl-principal">
        <div class="principal">
            <header class="barra">
                <a class="barra-inicio" href="index.php" title="Ir a la portada">
                    <img class="barra-logo" src="img/logo.svg" alt="Portada">
                </a>
                <h1 class="barra-titulo">Sistema de Inventario de Equipos de Radio</h1>
                <div class="barra-usuario">
                    <span class="barra-icono" data-ref="icono" aria-hidden="true"></span>
                    <span>
                        <strong data-ref="nombre"></strong>
                        <small data-ref="rol"></small>
                    </span>
                </div>
                <button type="button" class="btn btn-barra" data-ref="cambiar-clave">Cambiar contraseña</button>
                <button type="button" class="btn btn-peligro" data-ref="salir">🚪 Salir</button>
            </header>
            <nav class="pestanas" role="tablist" aria-label="Secciones" data-ref="pestanas"></nav>
            <div class="paneles" data-ref="paneles"></div>
        </div>
    </template>
</body>
</html>
