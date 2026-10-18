<?php
// Página de error del acceso: a dónde redirige el login fallido y la
// aplicación cuando no hay una sesión válida.
require_once __DIR__ . '/inc/inicio.php';

// código => [estado HTTP, título, mensaje, [texto del enlace, destino]]
const ERRORES = [
    'credenciales'   => [401, 'Usuario o contraseña incorrectos',
                         'Verificá los datos e intentá de nuevo. Después de 5 intentos fallidos la cuenta se bloquea 15 minutos.',
                         ['Volver a intentar', 'ingresar.php']],
    'datos'          => [400, 'Faltan datos', 'Completá el usuario y la contraseña.', ['Volver a intentar', 'ingresar.php']],
    'bloqueada'      => [429, 'Cuenta bloqueada temporalmente',
                         'Hubo demasiados intentos fallidos. Esperá 15 minutos o pedí a un administrador que resetee tu contraseña.',
                         ['Volver al inicio', 'index.php']],
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
encabezado($titulo, '', ['noindex' => true]);
?>
<section class="caja-formulario caja-error" role="alert">
    <p class="error-icono" aria-hidden="true">⚠️</p>
    <h1><?= e($titulo) ?></h1>
    <p><?= e($mensaje) ?></p>
    <p><a class="btn btn-primario" href="<?= e($destino) ?>"><?= e($enlace) ?></a></p>
</section>
<?php
pie();
