<?php
// Página de error del acceso: a dónde redirige el login fallido y la
// aplicación cuando no hay una sesión válida.
require_once __DIR__ . '/inc/inicio.php';

// código => [estado HTTP, título, mensaje, [texto del enlace, destino]]
const ERRORES = [
    'credenciales'   => [401, 'Usuario o contraseña incorrectos',
                         'Verificá los datos e intentá de nuevo. Después de 5 intentos fallidos la cuenta se bloquea 15 minutos. '
                         . 'Si no la recordás, podés restablecerla desde «¿Olvidaste tu contraseña?».',
                         ['Volver a intentar', 'ingresar.php']],
    'datos'          => [400, 'Faltan datos', 'Completá el usuario o email y la contraseña.', ['Volver a intentar', 'ingresar.php']],
    'bloqueada'      => [429, 'Cuenta bloqueada temporalmente',
                         'Hubo demasiados intentos fallidos. Esperá 15 minutos o restablecé tu contraseña por correo.',
                         ['Recuperar contraseña', 'olvide-clave.php']],
    'pendiente'      => [403, 'Tu cuenta todavía no fue aprobada',
                         'Un administrador tiene que aprobar tu registro antes de que puedas ingresar.',
                         ['Volver al inicio', 'index.php']],
    'inactiva'       => [403, 'Tu cuenta está desactivada',
                         'Comunicate con un administrador para reactivarla.', ['Ir a contacto', 'contacto.php']],
    'sin_sesion'     => [401, 'Acceso restringido',
                         'Tenés que iniciar sesión para acceder al sistema.', ['Ingresar', 'ingresar.php']],
    'sesion_vencida' => [401, 'Tu sesión venció',
                         'Por seguridad la sesión se cierra tras un tiempo sin actividad. Volvé a ingresar.', ['Ingresar', 'ingresar.php']],
    'csrf'           => [400, 'El formulario venció',
                         'La página estuvo abierta demasiado tiempo. Volvé a intentarlo.', ['Volver al inicio', 'index.php']],
];

$codigo = (string)($_GET['codigo'] ?? '');
[$estado, $titulo, $mensaje, [$enlace, $destino]] = ERRORES[$codigo]
    ?? [400, 'Ocurrió un error', 'No se pudo completar la operación.', ['Volver al inicio', 'index.php']];

http_response_code($estado);
encabezado($titulo, '', ['noindex' => true, 'ancho_completo' => true]);
$icono = fn(string $trazos) => '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    . 'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $trazos . '</svg>';
?>
<section class="hero hero-corto hero-error" aria-labelledby="titulo-error">
    <div class="hero-imagen" aria-hidden="true">
        <img src="img/portada/inventario-oscuro.webp" alt="" width="1568" height="744" decoding="async">
    </div>
    <div class="contenedor hero-texto" role="alert">
        <p class="producto"><img src="img/logo.svg" alt="" width="28" height="28"><?= e(NOMBRE_CORTO) ?> <span class="insignia-etiqueta">Error <?= $estado ?></span></p>
        <h1 id="titulo-error"><?= e($titulo) ?></h1>
        <p class="hero-bajada"><?= e($mensaje) ?></p>
        <div class="hero-acciones">
            <a class="boton boton-contorno" href="<?= e($destino) ?>"><?= e($enlace) ?>
                <?= $icono('<path d="M5 12h14M13 6l6 6-6 6"/>') ?></a>
        </div>
        <ul class="hero-enlaces">
            <?php if ($destino !== 'index.php'): ?>
                <li><a href="index.php"><?= $icono('<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/>') ?>Volver al inicio</a></li>
            <?php endif; ?>
            <?php if ($destino !== 'contacto.php'): ?>
                <li><a href="contacto.php"><?= $icono('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>') ?>¿Necesitás ayuda? Escribinos</a></li>
            <?php endif; ?>
        </ul>
    </div>
</section>
<?php
pie();
