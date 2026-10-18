<?php
// Portada pública: nombre del proyecto, menú, descripción, registro e ingreso.
// Pensada para buscadores (SEO) y motores con IA (GEO): un único h1, respuesta
// directa a "¿qué es?", preguntas frecuentes y datos estructurados schema.org.
require_once __DIR__ . '/inc/inicio.php';

$usuario = usuarioActual();
$salida = isset($_GET['salida']);

// Las mismas preguntas se muestran en la página y se publican como FAQPage.
$preguntas = [
    ['¿Puedo importar mi inventario desde Excel?',
     'Sí. La pestaña Ingreso de equipos permite cargar equipos en forma masiva desde una planilla de Excel, '
     . 'y el inventario se puede exportar a Excel con los filtros aplicados.'],
    ['¿Por qué mi cuenta figura como pendiente?',
     'Todas las cuentas nuevas quedan pendientes hasta que un administrador aprueba la solicitud. '
     . 'Una vez aprobada, ya podés ingresar con tu usuario y contraseña.'],
    ['¿Qué diferencia hay entre técnico y administrador?',
     'El técnico opera el inventario, el taller, los repuestos y la papelera. El administrador además gestiona '
     . 'usuarios, aprueba registros, responde consultas y realiza las bajas definitivas.'],
    ['¿Se pierde un equipo si lo elimino?',
     'No. Los equipos eliminados van a la papelera, desde donde se pueden restaurar. '
     . 'Solo un administrador puede darlos de baja en forma definitiva.'],
    ['¿Mis datos están protegidos?',
     'Las contraseñas se guardan encriptadas y el acceso a la aplicación requiere una sesión iniciada; '
     . 'sin ella, el sistema redirige a la página de error.'],
];

$url = urlBase();
$jsonld = [
    '@context' => 'https://schema.org',
    '@graph' => [
        [
            '@type' => 'WebApplication',
            '@id' => $url . '#aplicacion',
            'name' => NOMBRE_SISTEMA,
            'alternateName' => NOMBRE_CORTO,
            'url' => $url,
            'description' => DESCRIPCION_SISTEMA,
            'applicationCategory' => 'BusinessApplication',
            'operatingSystem' => 'Web',
            'inLanguage' => 'es-AR',
            'featureList' => [
                'Inventario con buscador, filtros, historial y exportación a Excel',
                'Ingreso de equipos con programación de canales e importación desde Excel',
                'Circuito de reparación en taller',
                'Stock de repuestos por taller',
                'Estadísticas del parque de equipos',
                'Administración de usuarios con dos niveles de acceso',
            ],
            'creator' => ['@id' => $url . '#utn-frh'],
        ],
        [
            '@type' => 'CollegeOrUniversity',
            '@id' => $url . '#utn-frh',
            'name' => 'Universidad Tecnológica Nacional · Facultad Regional Haedo',
            'address' => [
                '@type' => 'PostalAddress',
                'streetAddress' => 'París 532',
                'addressLocality' => 'Haedo',
                'addressRegion' => 'Provincia de Buenos Aires',
                'addressCountry' => 'AR',
            ],
        ],
        [
            '@type' => 'FAQPage',
            'mainEntity' => array_map(fn($p) => [
                '@type' => 'Question',
                'name' => $p[0],
                'acceptedAnswer' => ['@type' => 'Answer', 'text' => $p[1]],
            ], $preguntas),
        ],
    ],
];

encabezado('Inicio', 'inicio', [
    'titulo_completo' => NOMBRE_SISTEMA . ' · Taller y repuestos',
    'jsonld' => $jsonld,
    'ancho_completo' => true,
]);

$icono = fn(string $trazos) => '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    . 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $trazos . '</svg>';
$tilde = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
    . 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 5 5 9-10"/></svg>';
?>
<section class="seccion seccion-blanca hero" aria-labelledby="titulo-portada">
    <div class="contenedor hero-grilla">
        <div class="hero-texto">
            <p class="etiqueta-chip">Proyecto Integrador · Programación IV · UTN FRH</p>
            <h1 id="titulo-portada">Inventario de equipos de radio, del alta al taller.</h1>
            <p class="hero-bajada">
                El <strong><?= e(NOMBRE_SISTEMA) ?></strong> es una aplicación web para gestionar un parque
                de equipos de radiocomunicación: inventario con programación de canales, circuito de reparación
                en taller, stock de repuestos por taller y estadísticas, en un solo lugar.
            </p>
            <?php if ($salida): ?>
                <p class="mensaje-info" role="status">Cerraste la sesión correctamente.</p>
            <?php endif; ?>
            <div class="hero-acciones">
                <?php if ($usuario): ?>
                    <a class="boton boton-primario" href="app.php">Ir al sistema</a>
                    <span class="texto-suave">Sesión iniciada como <strong><?= e($usuario['username']) ?></strong></span>
                <?php else: ?>
                    <a class="boton boton-primario" href="registro.php">Solicitar acceso
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg></a>
                    <a class="boton boton-borde" href="ingresar.php">Ya tengo cuenta</a>
                <?php endif; ?>
            </div>
            <ul class="hero-ventajas">
                <li><?= $tilde ?>Importación y exportación a Excel</li>
                <li><?= $tilde ?>Historial de cada equipo</li>
                <li><?= $tilde ?>Roles de técnico y administrador</li>
            </ul>
        </div>

        <figure class="maqueta">
            <div class="maqueta-marco" aria-hidden="true">
                <div class="maqueta-puntos"><span></span><span></span><span></span></div>
                <div class="maqueta-pantalla">
                    <div class="maqueta-pestanas">
                        <span class="activa">Inventario</span><span>Ingreso</span><span>Taller</span><span>Repuestos</span><span>Estadísticas</span>
                    </div>
                    <div class="maqueta-cuerpo">
                        <div class="maqueta-buscador">Buscar por número de serie…</div>
                        <table class="maqueta-tabla">
                            <thead><tr><th>N.º de serie</th><th>Tipo</th><th>Estado</th></tr></thead>
                            <tbody>
                                <tr><td class="mono">EJ-0001</td><td>Portátil</td><td><span class="pildora pildora-verde">Operativo</span></td></tr>
                                <tr><td class="mono">EJ-0002</td><td>Móvil</td><td><span class="pildora pildora-ambar">En reparación</span></td></tr>
                                <tr><td class="mono">EJ-0003</td><td>Base</td><td><span class="pildora pildora-verde">Operativo</span></td></tr>
                            </tbody>
                        </table>
                        <div class="maqueta-canales">
                            <strong>Programación de canales</strong>
                            <span>CH 01 · TX / RX · codificación</span>
                            <span>CH 02 · TX / RX · codificación</span>
                        </div>
                    </div>
                </div>
            </div>
            <figcaption>Ejemplo ilustrativo de la pestaña Inventario: buscador, estados y programación de canales.</figcaption>
        </figure>
    </div>
</section>

<section class="seccion" aria-labelledby="titulo-que-es">
    <div class="contenedor dos-columnas">
        <div class="encabezado-seccion">
            <p class="sobretitulo">En pocas palabras</p>
            <h2 id="titulo-que-es">¿Qué es el <?= e(NOMBRE_SISTEMA) ?>?</h2>
            <p>Es una aplicación web que centraliza el registro de los equipos de radiocomunicación de una
               organización —portátiles, móviles y bases— junto con su programación de canales, su paso por el
               taller de reparación y los repuestos consumidos. Reemplaza planillas sueltas por una base de datos
               única con buscador, historial de cambios y dos niveles de acceso.</p>
        </div>
        <dl class="datos-clave">
            <div><dt>Para quién</dt><dd>Técnicos de radiocomunicaciones y administradores del parque de equipos.</dd></div>
            <div><dt>Qué gestiona</dt><dd>Equipos, canales (TX/RX y codificación), reparaciones, repuestos por taller y usuarios.</dd></div>
            <div><dt>Acceso</dt><dd>Registro con aprobación de un administrador; ingreso con usuario y contraseña.</dd></div>
            <div><dt>Tecnologías</dt><dd>HTML5, CSS, JavaScript, PHP 8 y MySQL/MariaDB.</dd></div>
        </dl>
    </div>
</section>

<section id="funciones" class="seccion seccion-blanca" aria-labelledby="titulo-funciones">
    <div class="contenedor">
        <div class="encabezado-seccion">
            <p class="sobretitulo">Funciones</p>
            <h2 id="titulo-funciones">Todo el ciclo de vida del equipo, en seis módulos</h2>
        </div>
        <ul class="tarjetas-funcion">
            <li>
                <span class="icono-funcion"><?= $icono('<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>') ?></span>
                <h3>Inventario</h3>
                <p>Buscador por número de serie, filtros por tipo, marca, modelo, escala, sector y estado, historial de cada equipo y exportación a Excel.</p>
            </li>
            <li>
                <span class="icono-funcion"><?= $icono('<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M4 17v3h16v-3"/>') ?></span>
                <h3>Ingreso de equipos</h3>
                <p>Alta con programación de canales (frecuencias TX/RX y codificación), imagen del modelo e importación masiva desde Excel.</p>
            </li>
            <li>
                <span class="icono-funcion"><?= $icono('<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>') ?></span>
                <h3>Taller</h3>
                <p>Circuito completo de reparación: envío, recepción, cambios de estado y egreso registrando los repuestos utilizados.</p>
            </li>
            <li>
                <span class="icono-funcion"><?= $icono('<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>') ?></span>
                <h3>Repuestos</h3>
                <p>Catálogo de repuestos con stock por taller: ingresos, ajustes, consumo en reparaciones y bajas.</p>
            </li>
            <li>
                <span class="icono-funcion"><?= $icono('<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>') ?></span>
                <h3>Estadísticas</h3>
                <p>Resumen del parque, distribución por tipo y modelo, incidencias de taller y consumo de repuestos.</p>
            </li>
            <li>
                <span class="icono-funcion"><?= $icono('<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M19 8v6M16 11h6"/>') ?></span>
                <h3>Administración</h3>
                <p>Gestión de usuarios, aprobación de registros, reseteo de claves y respuesta a las consultas del formulario de contacto.</p>
            </li>
        </ul>
    </div>
</section>

<section id="taller" class="seccion seccion-oscura" aria-labelledby="titulo-taller">
    <div class="contenedor">
        <div class="encabezado-seccion">
            <p class="sobretitulo">Circuito de taller</p>
            <h2 id="titulo-taller">Cada reparación queda registrada, paso por paso</h2>
            <p>El equipo cambia de estado en el inventario a medida que avanza, y los repuestos usados se
               descuentan del stock del taller que lo reparó.</p>
        </div>
        <ol class="flujo">
            <li><span class="flujo-numero">01</span><h3>Envío</h3><p>Desde el inventario se envía el equipo al taller indicando la falla.</p></li>
            <li><span class="flujo-numero">02</span><h3>Recepción</h3><p>El taller confirma que recibió el equipo y queda a su cargo.</p></li>
            <li><span class="flujo-numero">03</span><h3>Reparación</h3><p>Los cambios de estado quedan en el historial del equipo.</p></li>
            <li><span class="flujo-numero">04</span><h3>Egreso</h3><p>Se registra la salida con los repuestos utilizados y el equipo vuelve al servicio.</p></li>
        </ol>
    </div>
</section>

<section class="seccion" aria-labelledby="titulo-roles">
    <div class="contenedor">
        <div class="encabezado-seccion">
            <p class="sobretitulo">Roles</p>
            <h2 id="titulo-roles">Dos niveles de acceso</h2>
            <p>Los técnicos operan el inventario y el taller; los administradores, además, gestionan usuarios y
               realizan las bajas definitivas.</p>
        </div>
        <div class="tabla-roles">
            <table>
                <caption class="solo-lectores">Permisos por rol</caption>
                <thead><tr><th scope="col">Módulo</th><th scope="col">Técnico</th><th scope="col">Administrador</th></tr></thead>
                <tbody>
                    <tr><th scope="row">Ingreso de equipos e Inventario</th><td>Sí</td><td>Sí</td></tr>
                    <tr><th scope="row">Taller y Estadísticas</th><td>Sí</td><td>Sí</td></tr>
                    <tr><th scope="row">Repuestos</th><td>Sí</td><td>Sí, incluidas las bajas</td></tr>
                    <tr><th scope="row">Papelera</th><td>Restaurar</td><td>Restaurar y baja definitiva</td></tr>
                    <tr><th scope="row">Usuarios y consultas</th><td class="no">No</td><td>Sí</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</section>

<?php if (!$usuario): ?>
<section id="acceso" class="seccion seccion-blanca" aria-labelledby="titulo-acceso">
    <div class="contenedor">
        <div class="encabezado-seccion">
            <p class="sobretitulo">Acceso</p>
            <h2 id="titulo-acceso">¿Cómo obtengo acceso?</h2>
        </div>
        <ol class="pasos-acceso">
            <li><span class="paso-numero">1</span><h3>Registrate</h3><p>Completá el <a href="registro.php">formulario de registro</a> con tu legajo y tus datos.</p></li>
            <li><span class="paso-numero">2</span><h3>Esperá la aprobación</h3><p>Un administrador revisa la solicitud; hasta entonces la cuenta queda pendiente.</p></li>
            <li><span class="paso-numero">3</span><h3>Ingresá</h3><p><a href="ingresar.php">Iniciá sesión</a> con tu usuario y contraseña y accedé al sistema.</p></li>
        </ol>
    </div>
</section>
<?php endif; ?>

<section id="preguntas" class="seccion" aria-labelledby="titulo-preguntas">
    <div class="contenedor dos-columnas">
        <div class="encabezado-seccion">
            <p class="sobretitulo">Preguntas frecuentes</p>
            <h2 id="titulo-preguntas">Lo que suelen preguntarnos</h2>
            <p>¿No encontrás tu respuesta? Escribinos desde la página de <a href="contacto.php">contacto</a>.</p>
        </div>
        <div class="preguntas">
            <?php foreach ($preguntas as $i => [$pregunta, $respuesta]): ?>
                <details<?= $i === 0 ? ' open' : '' ?>>
                    <summary><?= e($pregunta) ?><span class="mas" aria-hidden="true"></span></summary>
                    <p><?= e($respuesta) ?></p>
                </details>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<?php if (!$usuario): ?>
<section class="seccion seccion-final" aria-labelledby="titulo-final">
    <div class="contenedor">
        <div class="llamado">
            <div>
                <h2 id="titulo-final">Empezá a ordenar tu parque de equipos</h2>
                <p>Creá tu cuenta y un administrador la habilitará.</p>
            </div>
            <div class="llamado-acciones">
                <a class="boton boton-blanco" href="registro.php">Crear cuenta</a>
                <a class="boton boton-contorno-claro" href="contacto.php">Hacer una consulta</a>
            </div>
        </div>
    </div>
</section>
<?php endif; ?>
<?php
pie();
