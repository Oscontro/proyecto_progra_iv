<?php
// Portada pública: nombre del proyecto, menú, descripción, registro e ingreso.
require_once __DIR__ . '/inc/inicio.php';

$usuario = usuarioActual();
$salida = isset($_GET['salida']);

encabezado('Inicio', 'inicio');
?>
<section class="portada">
    <div class="portada-texto">
        <h1><?= e(NOMBRE_SISTEMA) ?></h1>
        <p class="portada-bajada">
            Gestión del parque de equipos de radiocomunicación: inventario, ingreso de equipos,
            circuito de reparación en taller, stock de repuestos y estadísticas, en un solo lugar.
        </p>
        <?php if ($salida): ?>
            <p class="mensaje-info" role="status">Cerraste la sesión correctamente.</p>
        <?php endif; ?>
        <div class="portada-acciones">
            <?php if ($usuario): ?>
                <a class="btn btn-primario" href="app.php">Ir al sistema</a>
                <span class="texto-suave">Sesión iniciada como <strong><?= e($usuario['username']) ?></strong></span>
            <?php else: ?>
                <a class="btn btn-primario" href="ingresar.php">Ingresar</a>
                <a class="btn btn-secundario" href="registro.php">Crear una cuenta</a>
            <?php endif; ?>
        </div>
    </div>
    <img class="portada-logo" src="img/logo.svg" alt="" width="180" height="180">
</section>

<section aria-labelledby="titulo-funciones">
    <h2 id="titulo-funciones">¿Qué permite hacer?</h2>
    <ul class="funciones">
        <li>
            <h3>📦 Inventario</h3>
            <p>Consulta de todos los equipos con buscador por número de serie, filtros por tipo, marca,
               modelo, escala, sector y estado, historial de cada equipo y exportación a Excel.</p>
        </li>
        <li>
            <h3>📥 Ingreso de equipos</h3>
            <p>Alta de equipos con su programación de canales (frecuencias TX/RX y codificación),
               imagen del modelo e importación masiva desde Excel.</p>
        </li>
        <li>
            <h3>🛠️ Taller</h3>
            <p>Circuito completo de reparación: envío, recepción, cambios de estado y egreso
               registrando los repuestos utilizados.</p>
        </li>
        <li>
            <h3>🔩 Repuestos</h3>
            <p>Catálogo de repuestos con stock por taller, ingresos, ajustes, reparaciones y bajas.</p>
        </li>
        <li>
            <h3>📊 Estadísticas</h3>
            <p>Resumen del parque, distribución por tipo y modelo, incidencias de taller y consumo de repuestos.</p>
        </li>
        <li>
            <h3>👤 Administración</h3>
            <p>Dos niveles de acceso: los <strong>técnicos</strong> operan el inventario y el taller;
               los <strong>administradores</strong> además gestionan usuarios, aprueban registros,
               responden consultas y realizan las bajas definitivas.</p>
        </li>
    </ul>
</section>

<?php if (!$usuario): ?>
<section aria-labelledby="titulo-acceso" class="pasos">
    <h2 id="titulo-acceso">¿Cómo obtengo acceso?</h2>
    <ol>
        <li><a href="registro.php">Registrate</a> con tu legajo y tus datos.</li>
        <li>Un administrador revisa y aprueba la solicitud.</li>
        <li><a href="ingresar.php">Ingresá</a> con tu usuario y contraseña.</li>
    </ol>
    <p class="texto-suave">¿Dudas? Escribinos desde la página de <a href="contacto.php">contacto</a>.</p>
</section>
<?php endif; ?>
<?php
pie();
