<?php
// Contacto: mapa de Google y formulario de consulta. La consulta se guarda
// en la tabla contactos y se envía por correo a CONTACTO_DESTINO (php/config.php):
// con Resend si hay API key, si no con mail() (ver php/correo.php).
require_once __DIR__ . '/inc/inicio.php';
require_once __DIR__ . '/../php/correo.php';

const MENSAJE_MINIMO = 10;
const MENSAJE_MAXIMO = 3000;
const DIRECCION = 'UTN Facultad Regional Haedo, París 532, Haedo, Provincia de Buenos Aires';

$usuario = usuarioActual();
$valores = [
    'nombre'  => $usuario ? trim($usuario['nombre'] . ' ' . $usuario['apellido']) : '',
    'email'   => $usuario['email'] ?? '',
    'asunto'  => '',
    'mensaje' => '',
];
$error = null;

/** Valida la consulta. Devuelve un mensaje de error o null. */
function errorConsulta(array $c): ?string {
    if ($c['nombre'] === '' || mb_strlen($c['nombre']) > 100) return 'Ingresá tu nombre (hasta 100 caracteres).';
    if (!filter_var($c['email'], FILTER_VALIDATE_EMAIL) || mb_strlen($c['email']) > 150) return 'Ingresá un email válido.';
    if ($c['asunto'] === '' || mb_strlen($c['asunto']) > 150) return 'Ingresá el asunto (hasta 150 caracteres).';
    $largo = mb_strlen($c['mensaje']);
    if ($largo < MENSAJE_MINIMO || $largo > MENSAJE_MAXIMO) {
        return 'El mensaje debe tener entre ' . MENSAJE_MINIMO . ' y ' . MENSAJE_MAXIMO . ' caracteres.';
    }
    return null;
}

/** Envía la consulta por correo (Resend o mail(), ver php/correo.php). */
function enviarConsulta(array $c, int $id): bool {
    $cuerpo = "Nueva consulta desde el formulario de contacto

"
            . "Nombre: {$c['nombre']}
Email: {$c['email']}
Fecha: " . date('d/m/Y H:i') . "

"
            . $c['mensaje'] . "
";
    // Responder al correo le contesta directamente a quien hizo la consulta.
    return enviarCorreo(CONTACTO_DESTINO, "[Consulta #$id] " . $c['asunto'], $cuerpo, $c['email']);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    foreach ($valores as $campo => $_) {
        $valores[$campo] = trim((string)($_POST[$campo] ?? ''));
    }
    // El asunto va en una cabecera del correo: sin saltos de línea.
    $valores['asunto'] = preg_replace('/[\r\n]+/', ' ', $valores['asunto']);

    if (!csrfValido($_POST['csrf'] ?? null)) {
        $error = 'El formulario venció. Volvé a enviarlo.';
    } elseif (($_POST['sitio_web'] ?? '') !== '') {
        redirigir('contacto.php');   // campo trampa: robot
    } elseif ($espera = esperaFormulario('contacto', 30)) {
        $error = "Ya enviaste una consulta hace instantes. Esperá $espera segundos.";
    } elseif (!($error = errorConsulta($valores))) {
        bd()->prepare(
            "INSERT INTO contactos (nombre, email, asunto, mensaje, id_usuario, ip) VALUES (?, ?, ?, ?, ?, ?)"
        )->execute([$valores['nombre'], $valores['email'], $valores['asunto'], $valores['mensaje'],
                    $usuario['id'] ?? null, ipCliente()]);
        $id = (int)bd()->lastInsertId();

        $enviado = enviarConsulta($valores, $id);
        bd()->prepare("UPDATE contactos SET mail_enviado = ? WHERE id_contacto = ?")->execute([(int)$enviado, $id]);

        registrarEnvioFormulario('contacto');
        flash('contacto_ok', true);
        redirigir('contacto.php');
    }
}

$enviada = flash('contacto_ok');
$mapa = 'https://maps.google.com/maps?q=' . rawurlencode(DIRECCION) . '&z=16&output=embed';
encabezado('Contacto', 'contacto', [
    'mapa' => true,
    'descripcion' => 'Contacto del ' . NOMBRE_SISTEMA . ': mapa de la UTN Facultad Regional Haedo y formulario de consulta.',
]);
?>
<h1>Contacto</h1>
<div class="contacto">
    <section class="contacto-mapa" aria-labelledby="titulo-ubicacion">
        <h2 id="titulo-ubicacion">Dónde estamos</h2>
        <address>
            <strong>UTN · Facultad Regional Haedo</strong><br>
            París 532, Haedo<br>
            Provincia de Buenos Aires, Argentina
        </address>
        <iframe src="<?= e($mapa) ?>" title="Mapa: <?= e(DIRECCION) ?>" loading="lazy"
                referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </section>

    <section class="contacto-formulario" aria-labelledby="titulo-consulta">
        <h2 id="titulo-consulta">Envianos tu consulta</h2>
        <?php if ($enviada): ?>
            <p class="mensaje-info" role="status">¡Gracias! Recibimos tu consulta.</p>
        <?php endif; ?>
        <?php if ($error): ?>
            <p class="mensaje-error" role="alert"><?= e($error) ?></p>
        <?php endif; ?>
        <form method="post" action="contacto.php" class="formulario-sitio">
            <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">
            <div class="trampa" aria-hidden="true">
                <label for="sitio_web">No completar este campo</label>
                <input type="text" id="sitio_web" name="sitio_web" tabindex="-1" autocomplete="off">
            </div>

            <div class="rejilla-dos">
                <div>
                    <label for="nombre">Nombre</label>
                    <input type="text" id="nombre" name="nombre" value="<?= e($valores['nombre']) ?>" required maxlength="100" autocomplete="name">
                </div>
                <div>
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" value="<?= e($valores['email']) ?>" required maxlength="150" autocomplete="email">
                </div>
            </div>

            <label for="asunto">Asunto</label>
            <input type="text" id="asunto" name="asunto" value="<?= e($valores['asunto']) ?>" required maxlength="150">

            <label for="mensaje">Mensaje</label>
            <textarea id="mensaje" name="mensaje" rows="6" required minlength="<?= MENSAJE_MINIMO ?>" maxlength="<?= MENSAJE_MAXIMO ?>"><?= e($valores['mensaje']) ?></textarea>

            <button type="submit" class="btn btn-primario btn-ancho">Enviar consulta</button>
        </form>
    </section>
</div>
<?php
pie();
