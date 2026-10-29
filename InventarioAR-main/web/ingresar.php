<?php
// Ingreso al sistema (login) con usuario o email. Verifica la contraseña, abre la
// sesión de PHP y lleva a la aplicación; si algo falla redirige a error.php con el motivo.
require_once __DIR__ . '/inc/inicio.php';

if (usuarioActual()) {
    redirigir('app.php');
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!csrfValido($_POST['csrf'] ?? null)) {
        irAError('csrf');
    }
    $username = trim((string)($_POST['usuario'] ?? ''));
    $clave = (string)($_POST['clave'] ?? '');
    if ($username === '' || $clave === '') {
        irAError('datos');
    }

    $resultado = autenticar(bd(), $username, $clave);
    if (isset($resultado['error'])) {
        irAError($resultado['error']);
    }
    abrirSesion($resultado['usuario']);
    redirigir('app.php');
}

$aviso = flash('aviso');
encabezado('Iniciar sesión', 'ingresar', ['ancho_completo' => true]);
$icono = fn(string $trazos) => '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    . 'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $trazos . '</svg>';
?>
<section class="hero hero-corto" aria-labelledby="titulo-ingresar">
    <div class="hero-imagen" aria-hidden="true">
        <img src="img/portada/inventario-oscuro.webp" alt="" width="1568" height="744" decoding="async">
    </div>
    <div class="contenedor hero-texto">
        <p class="producto"><img src="img/logo.svg" alt="" width="28" height="28"><?= e(NOMBRE_CORTO) ?></p>
        <h1 id="titulo-ingresar">Iniciar sesión</h1>
        <p class="hero-bajada">Accedé al inventario, el taller, los repuestos y las estadísticas del parque de equipos de radio.</p>
        <ul class="hero-enlaces">
            <li><a href="index.php"><?= $icono('<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/>') ?>Conocé el sistema</a></li>
            <li><a href="contacto.php"><?= $icono('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>') ?>¿Problemas para ingresar? Escribinos</a></li>
        </ul>
    </div>
</section>

<div class="seccion seccion-formulario">
<div class="contenedor">
<section class="caja-formulario caja-angosta" aria-labelledby="titulo-caja">
    <h2 id="titulo-caja">Ingresá a tu cuenta</h2>
    <p class="texto-suave">Ingresá con tu usuario o tu email.</p>
    <?php if ($aviso): ?>
        <p class="mensaje-info" role="status"><?= e($aviso) ?></p>
    <?php endif; ?>
    <form method="post" action="ingresar.php" class="formulario-sitio">
        <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">

        <label for="usuario">Usuario o email</label>
        <input type="text" id="usuario" name="usuario" autocomplete="username" required autofocus maxlength="150">

        <div class="etiqueta-con-enlace">
            <label for="clave">Contraseña</label>
            <a href="olvide-clave.php">¿Olvidaste tu contraseña?</a>
        </div>
        <div class="campo-clave">
            <input type="password" id="clave" name="clave" autocomplete="current-password" required>
            <!-- Mostrar/ocultar la contraseña (js/sitio.js); sin JavaScript queda oculto -->
            <button type="button" class="ver-clave" aria-controls="clave" aria-pressed="false" hidden>Mostrar</button>
        </div>

        <button type="submit" class="btn btn-primario btn-ancho">Ingresar</button>
    </form>
    <p class="pie-formulario">¿No tenés cuenta? <a href="registro.php">Creá una</a></p>
</section>
</div>
</div>
<?php
pie();
