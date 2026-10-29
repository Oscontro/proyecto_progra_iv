<?php
// Registro de usuarios "generales" (perfil Técnico). La cuenta queda
// pendiente: un administrador la aprueba desde la pestaña Administración.
// No se pide legajo: se genera uno (WEB-XXXXXX) porque la tabla lo exige y
// Administración identifica las cuentas por legajo.
require_once __DIR__ . '/inc/inicio.php';
require_once __DIR__ . '/../php/usuarios_validacion.php';

if (usuarioActual()) {
    redirigir('app.php');
}

$valores = ['nombre' => '', 'apellido' => '', 'email' => '', 'username' => ''];
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    foreach ($valores as $campo => $_) {
        $valores[$campo] = trim((string)($_POST[$campo] ?? ''));
    }
    if (!csrfValido($_POST['csrf'] ?? null)) {
        $error = 'El formulario venció. Volvé a enviarlo.';
    } elseif (($_POST['sitio_web'] ?? '') !== '') {
        // Campo trampa invisible: solo lo completan los robots.
        redirigir('registro.php');
    } elseif ($espera = esperaFormulario('registro', 60)) {
        $error = "Ya enviaste una solicitud hace instantes. Esperá $espera segundos.";
    } else {
        $legajo = 'WEB-' . strtoupper(bin2hex(random_bytes(3)));
        [$datos, $error] = validarDatosPersonales($valores + ['legajo' => $legajo], true);
        $error ??= errorClave((string)($_POST['clave'] ?? ''), (string)($_POST['repetir'] ?? ''));
        $error ??= buscarDuplicado(bd(), $datos['legajo'], $datos['username']);
        $error ??= emailEnUso(bd(), $datos['email']);
        if (!$error && empty($_POST['acepto'])) {
            $error = 'Tenés que aceptar que un administrador revise tu solicitud.';
        }

        if (!$error) {
            bd()->prepare(
                "INSERT INTO usuarios
                    (legajo, username, nombre, apellido, email, password_hash,
                     es_administrador, debe_cambiar_clave, activo, pendiente_aprobacion)
                 VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 1)"
            )->execute([$datos['legajo'], $datos['username'], $datos['nombre'], $datos['apellido'],
                        $datos['email'], password_hash((string)$_POST['clave'], PASSWORD_DEFAULT)]);
            registrarEnvioFormulario('registro');
            flash('registro_ok', $datos['username']);
            redirigir('registro.php');
        }
    }
}

$registrado = flash('registro_ok');
encabezado('Registrarse', 'registro', [
    'descripcion' => 'Creá tu cuenta en el ' . NOMBRE_SISTEMA . '. Un administrador aprueba la solicitud antes del primer ingreso.',
    'ancho_completo' => true,
]);
$icono = fn(string $trazos) => '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    . 'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $trazos . '</svg>';
?>
<section class="hero hero-corto" aria-labelledby="titulo-registro">
    <div class="hero-imagen" aria-hidden="true">
        <img src="img/portada/repuestos-oscuro.webp" alt="" width="1568" height="744" decoding="async">
    </div>
    <div class="contenedor hero-texto">
        <p class="producto"><img src="img/logo.svg" alt="" width="28" height="28"><?= e(NOMBRE_CORTO) ?></p>
        <h1 id="titulo-registro">Crear una cuenta</h1>
        <p class="hero-bajada">Solicitá tu acceso al sistema. Las cuentas nuevas tienen perfil <strong>Técnico</strong> y quedan pendientes hasta que un administrador las aprueba.</p>
        <ul class="hero-enlaces">
            <li><a href="index.php#acceso"><?= $icono('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>') ?>Cómo funciona la aprobación</a></li>
            <li><a href="contacto.php"><?= $icono('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>') ?>Hacé una consulta</a></li>
        </ul>
    </div>
</section>

<div class="seccion seccion-formulario">
<div class="contenedor">
<section class="caja-formulario" aria-labelledby="titulo-caja">
    <?php if ($registrado): ?>
        <h2 id="titulo-caja">¡Solicitud enviada!</h2>
        <p class="mensaje-info" role="status">
            La cuenta <strong><?= e($registrado) ?></strong> quedó registrada y pendiente de aprobación.
            Cuando un administrador la apruebe vas a poder ingresar con tu usuario y contraseña.
        </p>
        <p><a class="btn btn-primario" href="index.php">Volver al inicio</a></p>
    <?php else: ?>
        <h2 id="titulo-caja">Tus datos</h2>
        <p class="texto-suave">Completá el formulario para enviar tu solicitud.</p>
        <?php if ($error): ?>
            <p class="mensaje-error" role="alert"><?= e($error) ?></p>
        <?php endif; ?>
        <form method="post" action="registro.php" class="formulario-sitio">
            <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">
            <div class="trampa" aria-hidden="true">
                <label for="sitio_web">No completar este campo</label>
                <input type="text" id="sitio_web" name="sitio_web" tabindex="-1" autocomplete="off">
            </div>

            <div class="rejilla-dos">
                <div>
                    <label for="nombre">Nombre</label>
                    <input type="text" id="nombre" name="nombre" value="<?= e($valores['nombre']) ?>" required maxlength="100" autocomplete="given-name" autofocus>
                </div>
                <div>
                    <label for="apellido">Apellido</label>
                    <input type="text" id="apellido" name="apellido" value="<?= e($valores['apellido']) ?>" required maxlength="100" autocomplete="family-name">
                </div>
            </div>

            <label for="email">Email</label>
            <input type="email" id="email" name="email" value="<?= e($valores['email']) ?>" required maxlength="150" autocomplete="email" aria-describedby="email-ayuda">
            <small id="email-ayuda" class="ayuda">Lo usamos para recuperar tu contraseña. También podés ingresar con él.</small>

            <label for="username">Nombre de usuario</label>
            <input type="text" id="username" name="username" value="<?= e($valores['username']) ?>" required maxlength="100" autocomplete="username" pattern="\S+" title="Sin espacios">

            <div class="rejilla-dos">
                <div>
                    <label for="clave">Contraseña</label>
                    <div class="campo-clave">
                        <input type="password" id="clave" name="clave" required minlength="<?= CLAVE_MINIMO ?>" autocomplete="new-password" aria-describedby="clave-ayuda">
                        <button type="button" class="ver-clave" aria-controls="clave" aria-pressed="false" hidden>Mostrar</button>
                    </div>
                    <small id="clave-ayuda" class="ayuda">Mínimo <?= CLAVE_MINIMO ?> caracteres.</small>
                </div>
                <div>
                    <label for="repetir">Repetir contraseña</label>
                    <input type="password" id="repetir" name="repetir" required autocomplete="new-password">
                </div>
            </div>

            <label class="casilla">
                <input type="checkbox" name="acepto" value="1" required>
                <span>Entiendo que un administrador debe aprobar mi cuenta antes del primer ingreso.</span>
            </label>

            <button type="submit" class="btn btn-primario btn-ancho">Crear cuenta</button>
        </form>
        <p class="pie-formulario">¿Ya tenés cuenta? <a href="ingresar.php">Iniciá sesión</a></p>
    <?php endif; ?>
</section>
</div>
</div>
<?php
pie();
