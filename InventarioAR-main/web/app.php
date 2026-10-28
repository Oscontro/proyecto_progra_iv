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
    <script src="js/tema.js"></script>
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
            <header class="acceso-barra">
                <a class="lateral-inicio" href="index.php" title="Ir a la portada">
                    <img class="lateral-logo" src="img/logo.svg" alt="">
                    <span class="lateral-nombre">
                        <strong>Inventario</strong>
                        <small>Equipos de radio</small>
                    </span>
                </a>
                <button type="button" class="btn btn-tema" data-ref="tema"
                        aria-label="Modo oscuro" aria-pressed="false" title="Cambiar entre modo claro y oscuro"></button>
            </header>
            <section class="acceso-panel">
                <!-- El ícono (js/iconos.js) lo agrega js/app.js -->
                <form class="tarjeta acceso-tarjeta" data-ref="form" novalidate>
                    <span class="acceso-icono" data-ref="icono"></span>
                    <h1>Cambiar contraseña</h1>
                    <p class="acceso-leyenda" data-ref="leyenda"></p>
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
            <!-- Los íconos (js/iconos.js) los agrega js/app.js -->
            <aside class="lateral">
                <div class="lateral-marca">
                    <a class="lateral-inicio" href="index.php" title="Ir a la portada">
                        <img class="lateral-logo" src="img/logo.svg" alt="">
                        <span class="lateral-nombre lateral-texto">
                            <strong>Inventario</strong>
                            <small>Equipos de radio</small>
                        </span>
                    </a>
                    <button type="button" class="lateral-colapsar" data-ref="colapsar"
                            aria-label="Achicar el menú" aria-expanded="true"></button>
                    <!-- Solo en pantallas angostas: abre y cierra el menú -->
                    <button type="button" class="lateral-hamburguesa" data-ref="hamburguesa"
                            aria-label="Menú" aria-expanded="false" aria-controls="menu-app"></button>
                </div>

                <div class="lateral-menu" id="menu-app">
                    <p class="lateral-titulo" aria-hidden="true">Menú</p>
                    <nav class="pestanas" role="tablist" aria-label="Secciones" aria-orientation="vertical"
                         data-ref="pestanas"></nav>

                    <div class="lateral-pie">
                        <div class="usuario">
                            <span class="usuario-avatar" data-ref="icono" aria-hidden="true"></span>
                            <span class="usuario-datos lateral-texto">
                                <strong data-ref="nombre"></strong>
                                <small data-ref="rol"></small>
                            </span>
                        </div>
                        <button type="button" class="lateral-accion" data-ref="cambiar-clave" title="Cambiar contraseña">
                            <span class="lateral-texto">Cambiar contraseña</span>
                        </button>
                        <button type="button" class="lateral-accion lateral-salir" data-ref="salir" title="Cerrar sesión">
                            <span class="lateral-texto">Salir</span>
                        </button>
                    </div>
                </div>
            </aside>

            <div class="contenido">
                <header class="contenido-cabecera">
                    <div>
                        <h1 data-ref="saludo"></h1>
                        <p>Sistema de Inventario de Equipos de Radio</p>
                    </div>
                    <div class="contenido-herramientas">
                        <button type="button" class="btn btn-tema" data-ref="tema"
                                aria-label="Modo oscuro" aria-pressed="false" title="Cambiar entre modo claro y oscuro"></button>
                    </div>
                </header>
                <div class="paneles" data-ref="paneles"></div>
            </div>
        </div>
    </template>
</body>
</html>
