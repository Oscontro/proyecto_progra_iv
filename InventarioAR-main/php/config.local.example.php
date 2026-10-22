<?php
// Copiar como config.local.php y ajustar. Solo hace falta incluir las
// claves que difieren de los valores por defecto de config.php.
//
// Para el hosting: guardarlo como config.hosting.php (no se versiona) y
// tools/armar_publicacion.sh lo incluye en el paquete como config.local.php.
// En InfinityFree los datos están en el panel, sección "MySQL Databases":
// host sqlNNN.infinityfree.com, usuario if0_NNNNNNNN, base if0_NNNNNNNN_nombre
// y la contraseña es la de la cuenta de hosting (panel > "Account Details").
return [
    // 'db_host'          => 'sqlNNN.infinityfree.com',
    // 'db_user'          => 'if0_NNNNNNNN',
    // 'db_pass'          => 'cambiar-esta-clave',
    // 'db_name'          => 'if0_NNNNNNNN_inventario',
    // 'api_debug'        => true,   // solo en desarrollo
    // 'contacto_destino' => 'consultas@inventario-radios.test',
    // 'mail_remitente'   => 'no-responder@tu-dominio',

    // ═══ CORREO CON RESEND ═══════════════════════════════════════════════
    // 👉 Pegá acá tu API key (https://resend.com/api-keys, empieza con "re_").
    //    Sin key, el sistema usa mail() como antes.
    // 'resend_api_key'   => 're_xxxxxxxxxxxxxxxxxxxxxxxx',
    //
    // 👉 Con el remitente de prueba onboarding@resend.dev, Resend solo envía al
    //    email con el que creaste la cuenta: ponelo como destino de las consultas.
    // 'contacto_destino' => 'el-email-de-tu-cuenta-de-resend@ejemplo.com',
    //
    // Si verificás un dominio propio en Resend (panel > Domains), podés usar
    // un remitente de ese dominio y enviar a cualquier dirección:
    // 'resend_remitente' => 'Inventario de Radios <no-responder@tu-dominio.com>',
];
