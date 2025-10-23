
let todasLasCotizaciones = [];
let cotizacionesFiltradas = [];
let paginaActual = 1;
let registrosPorPagina = 50;
let ordenActual = 'fecha_desc';
let usuarioActual = '';

  // Cargar cotizaciones al iniciar
  document.addEventListener("DOMContentLoaded", function () {
    cargarCotizaciones();
    configurarEventListeners();
});

function configurarEventListeners() {
    // Configurar buscador
    document.getElementById('buscador').addEventListener('input', aplicarFiltros);
    
    // Configurar filtros avanzados
    document.getElementById('fechaDesde').addEventListener('change', aplicarFiltros);
    document.getElementById('fechaHasta').addEventListener('change', aplicarFiltros);
    document.getElementById('filtroUsuario').addEventListener('change', aplicarFiltros);
    document.getElementById('filtroDistrito').addEventListener('change', aplicarFiltros);
    document.getElementById('montoMin').addEventListener('input', aplicarFiltros);
    document.getElementById('montoMax').addEventListener('input', aplicarFiltros);
    document.getElementById('filtroEstadoCuotas').addEventListener('change', aplicarFiltros);
    
    // Configurar controles
    document.getElementById('registrosPorPaginaSelect').addEventListener('change', cambiarRegistrosPorPagina);
    document.getElementById('ordenarPor').addEventListener('change', cambiarOrden);
    
    // Configurar botones de paginación
    document.getElementById("btnAnterior").addEventListener("click", function () {
      if (paginaActual > 1) {
        paginaActual--;
        mostrarCotizaciones();
        actualizarPaginacion();
      }
    });
    
    document.getElementById('btnSiguiente').addEventListener('click', function() {
        const totalPaginas = Math.ceil(cotizacionesFiltradas.length / registrosPorPagina);
        if (paginaActual < totalPaginas) {
            paginaActual++;
            mostrarCotizaciones();
            actualizarPaginacion();
        }
    });
    
    // Configurar ordenamiento por columnas por fecha 
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', function() {
            const column = this.getAttribute('data-column');
            cambiarOrdenamiento(column);
        });
    });
}

  // Cargar lista de cotizaciones desde el backend
  function cargarCotizaciones() {
    fetch("../api/lista-cotizaciones/")
      .then((response) => response.json())
      .then((data) => {
        todasLasCotizaciones = data;
        
        // El backend ya calcula el estado, solo necesitamos mapear los nombres
        todasLasCotizaciones.forEach(cotizacion => {
            // Mapear estados del backend al frontend
            if (cotizacion.estado_cuotas === 'proxima_vencer') {
                cotizacion.estadoCuotas = 'proxima_vencer';
            } else {
                cotizacion.estadoCuotas = cotizacion.estado_cuotas;
            }
            cotizacion.diasRestantes = cotizacion.dias_restantes || 0;
        });
        
        // Obtener usuario actual desde la primera cotización (asumiendo que todas tienen el mismo usuario)
        if (data.length > 0) {
            usuarioActual = data[0].user_username;
        }
        llenarFiltroDistritos();
        llenarFiltroUsuarios();
        aplicarFiltros();
        mostrarResumenCuotas();
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensajeError('Error al cargar las cotizaciones');
    });
}

// Mostrar resumen de cuotas (venccidas, críticas, próximas a vencer, al día)
function mostrarResumenCuotas() {
    const contador = {
        al_dia: 0,
        proximas_vencer: 0,
        criticas: 0,
        vencidas: 0
    };
    
    todasLasCotizaciones.forEach(cotizacion => {
        const estado = cotizacion.estadoCuotas;
        if (estado === 'proxima_vencer') {
            contador.proximas_vencer++;
        } else if (estado === 'critica') {
            contador.criticas++;
        } else if (estado === 'vencida') {
            contador.vencidas++;
        } else {
            contador.al_dia++;
        }
    });
    
    document.getElementById('countProximas').textContent = contador.proximas_vencer;
    document.getElementById('countCriticas').textContent = contador.criticas;
    document.getElementById('countVencidas').textContent = contador.vencidas;
    document.getElementById('countAlDia').textContent = contador.al_dia;
    
    // Mostrar alertas solo si hay filtros avanzados activos
    const filtrosActivos = document.getElementById('filtrosAvanzados').style.display !== 'none';
    if (filtrosActivos) {
        document.getElementById('alertasCuotas').style.display = 'flex';
    }
}

// Obtener badge de estado de cuotas
function obtenerBadgeEstadoCuotas(cotizacion) {
    const estado = cotizacion.estadoCuotas;
    const dias = cotizacion.diasRestantes;
    
    switch(estado) {
        case 'vencida':
            return `<span class="badge bg-dark" title="Vencida hace ${dias} días">
                      <i class="fas fa-times-circle"></i> Vencida (${dias}d)
                    </span>`;
        case 'critica':
            return `<span class="badge bg-danger" title="Crítica - ${dias} días restantes">
                      <i class="fas fa-exclamation-triangle"></i> Crítica (${dias}d)
                    </span>`;
        case 'proxima_vencer':
            return `<span class="badge bg-warning text-dark" title="Próxima a vencer - ${dias} días restantes">
                      <i class="fas fa-clock"></i> Próxima (${dias}d)
                    </span>`;
        default:
            return `<span class="badge bg-success" title="Al día">
                      <i class="fas fa-check-circle"></i> Al día
                    </span>`;
    }
}

// Llenar el filtro de distritos
function llenarFiltroDistritos() {
    const distritos = [...new Set(todasLasCotizaciones.map(c => c.distrito))].sort();
    const select = document.getElementById('filtroDistrito');
    select.innerHTML = '<option value="">Todos los distritos</option>';
    distritos.forEach(distrito => {
        if (distrito) {
            select.innerHTML += `<option value="${distrito}">${distrito}</option>`;
        }
    });
}

// Llenar el filtro de usuarios
function llenarFiltroUsuarios() {
    const usuarios = [...new Set(todasLasCotizaciones.map(c => c.user_id))].sort();
    const select = document.getElementById('filtroUsuario');
    select.innerHTML = '<option value="">Todos los usuarios</option>';
    usuarios.forEach(usuario => {
        if (usuario) {
            select.innerHTML += `<option value="${usuario}">${usuario}</option>`;
        }
    });
}

// Aplicar todos los filtros
function aplicarFiltros() {
    const textoBusqueda = document.getElementById('buscador').value.toLowerCase().trim();
    const fechaDesde = document.getElementById('fechaDesde').value;
    const fechaHasta = document.getElementById('fechaHasta').value;
    const usuario = document.getElementById('filtroUsuario').value;
    const distrito = document.getElementById('filtroDistrito').value;
    const montoMin = parseFloat(document.getElementById('montoMin').value) || 0;
    const montoMax = parseFloat(document.getElementById('montoMax').value) || Infinity;
    const estadoCuotas = document.getElementById('filtroEstadoCuotas').value;
    const ordenSeleccionado = document.getElementById('ordenarPor').value;
    
    // Determinar si se muestran solo las cotizaciones del usuario actual o todas las cotizaciones según el filtr
    let mostrarSoloMias = false;
    if (ordenSeleccionado === 'mis_cotizaciones') {
        mostrarSoloMias = true;
    }
    
    cotizacionesFiltradas = todasLasCotizaciones.filter(cotizacion => {
        // Filtro principal: Mis cotizaciones vs Todas
        if (mostrarSoloMias && cotizacion.user_username !== usuarioActual) {
            return false;
        }
        
        // Filtro de texto
        const cumpleTexto = textoBusqueda === '' || 
            cotizacion.cliente.toLowerCase().includes(textoBusqueda) ||
            cotizacion.dni.toLowerCase().includes(textoBusqueda) ||
            cotizacion.distrito.toLowerCase().includes(textoBusqueda) ||
            cotizacion.nivel_predio.toLowerCase().includes(textoBusqueda) ||
            cotizacion.user_id.toLowerCase().includes(textoBusqueda) ||
            cotizacion.id.toString().includes(textoBusqueda);
        
        // Filtro de fecha
        const fechaCotizacion = new Date(cotizacion.fecha);
        const cumpleFecha = (!fechaDesde || fechaCotizacion >= new Date(fechaDesde)) &&
                           (!fechaHasta || fechaCotizacion <= new Date(fechaHasta));
        
        // Filtro de usuario
        const cumpleUsuario = !usuario || cotizacion.user_id === usuario;
        
        // Filtro de distrito
        const cumpleDistrito = !distrito || cotizacion.distrito === distrito;
        
        // Filtro de monto
        const total = parseFloat(cotizacion.total);
        const cumpleMonto = total >= montoMin && total <= montoMax;
        
        // Filtro de estado de cuotas
        const cumpleEstadoCuotas = !estadoCuotas || cotizacion.estadoCuotas === estadoCuotas || 
                                  (estadoCuotas === 'proximas_vencer' && cotizacion.estadoCuotas === 'proxima_vencer');
        
        return cumpleTexto && cumpleFecha && cumpleUsuario && cumpleDistrito && cumpleMonto && cumpleEstadoCuotas;
    });
    
    // Solo aplicar ordenamiento si no es una opción de filtro especial
    if (!['mis_cotizaciones', 'todas_cotizaciones'].includes(ordenSeleccionado)) {
        ordenActual = ordenSeleccionado;
    }
    
    ordenarCotizaciones();
    paginaActual = 1;
    mostrarCotizaciones();
    actualizarPaginacion();
    actualizarInfoRegistros();
}

// Ordenar cotizaciones
function ordenarCotizaciones() {
    if (ordenActual === 'cuotas_urgentes') {
        // Ordenamiento especial por urgencia de cuotas
        cotizacionesFiltradas.sort((a, b) => {
            const prioridadA = obtenerPrioridadUrgencia(a.estadoCuotas);
            const prioridadB = obtenerPrioridadUrgencia(b.estadoCuotas);
            
            if (prioridadA !== prioridadB) {
                return prioridadB - prioridadA; // Mayor prioridad primero
            }
            
            // Si tienen la misma prioridad, ordenar por días restantes
            return a.diasRestantes - b.diasRestantes;
        });
        return;
    }
    
    const [campo, direccion] = ordenActual.split('_');
    
    cotizacionesFiltradas.sort((a, b) => {
        let valorA, valorB;
        
        switch(campo) {
            case 'fecha':
                valorA = new Date(a.fecha);
                valorB = new Date(b.fecha);
                break;
            case 'total':
                valorA = parseFloat(a.total);
                valorB = parseFloat(b.total);
                break;
            case 'id':
                valorA = parseInt(a.id);
                valorB = parseInt(b.id);
                break;
            default:
                valorA = a[campo] ? a[campo].toLowerCase() : '';
                valorB = b[campo] ? b[campo].toLowerCase() : '';
        }
        
        if (direccion === 'asc') {
            return valorA > valorB ? 1 : -1;
        } else {
            return valorA < valorB ? 1 : -1;
        }
    });
}

// Obtener prioridad de urgencia para ordenamiento
function obtenerPrioridadUrgencia(estado) {
    switch(estado) {
        case 'vencida': return 4;
        case 'critica': return 3;
        case 'proxima_vencer': return 2;
        case 'al_dia': return 1;
        default: return 0;
    }
}

// Cambiar ordenamiento por columna
function cambiarOrdenamiento(columna) {
    const [campoActual, direccionActual] = ordenActual.split('_');
    
    if (campoActual === columna) {
        // Si es la misma columna, cambiar dirección
        ordenActual = `${columna}_${direccionActual === 'asc' ? 'desc' : 'asc'}`;
    } else {
        // Si es diferente columna, empezar con ascendente
        ordenActual = `${columna}_asc`;
    }
    
    aplicarFiltros();
}

// Cambiar número de registros por página
function cambiarRegistrosPorPagina() {
    const valor = document.getElementById('registrosPorPaginaSelect').value;
    registrosPorPagina = parseInt(valor);
    paginaActual = 1;
    mostrarCotizaciones();
    actualizarPaginacion();
}

// Cambiar orden
function cambiarOrden() {
    aplicarFiltros();
}

  // Mostrar cotizaciones de la página actual
  function mostrarCotizaciones() {
    const tbody = document.getElementById("cotizacionesTableBody");
    tbody.innerHTML = "";

    if (cotizacionesFiltradas.length === 0) {
      tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center text-muted py-4">
                    <i class="fas fa-search fa-2x mb-2 d-block"></i>
                    No se encontraron cotizaciones
                </td>
            </tr>
        `;
      return;
    }

    const inicio = (paginaActual - 1) * registrosPorPagina;
    const fin = Math.min(inicio + registrosPorPagina, cotizacionesFiltradas.length);
    const cotizacionesPagina = cotizacionesFiltradas.slice(inicio, fin);

    cotizacionesPagina.forEach((cotizacion) => {
      const row = `
            <tr>
                <td><span class="badge bg-secondary">${cotizacion.id}</span></td>
                <td><span class="badge bg-info text-dark">${cotizacion.user_id}</span></td>
                <td>${formatearFecha(cotizacion.fecha)}</td>
                <td><strong>${cotizacion.cliente}</strong></td>
                <td><code>${cotizacion.dni}</code></td>
                <td>${cotizacion.distrito}</td>
                <td>${cotizacion.nivel_predio}</td>
                <td><strong class="text-success">S/ ${parseFloat(cotizacion.total).toFixed(2)}</strong></td>
                <td>${obtenerBadgeEstadoCuotas(cotizacion)}</td>
                <td class="text-center">
                    <button class="btn btn-info btn-sm me-1" onclick="verCuotas(${cotizacion.id})" title="Ver cuotas">
                        <i class="bi bi-eye"></i>
                    </button>
                    <a class="btn btn-warning btn-sm me-1" href="editar/${cotizacion.id}" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button class="btn btn-danger btn-sm" onclick="eliminarCotizacion(${cotizacion.id})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
      tbody.innerHTML += row;
    });
  }

// Actualizar información de registros
function actualizarInfoRegistros() {
    const info = document.getElementById('infoRegistros');
    const ordenSeleccionado = document.getElementById('ordenarPor').value;
    
    if (ordenSeleccionado === 'mis_cotizaciones') {
        info.textContent = `Mostrando ${cotizacionesFiltradas.length} de mis cotizaciones`;
    } else {
        info.textContent = `Mostrando ${cotizacionesFiltradas.length} de ${todasLasCotizaciones.length} registros`;
    }
}

  // Actualizar controles de paginación
  function actualizarPaginacion() {
    const totalPaginas = Math.ceil(cotizacionesFiltradas.length / registrosPorPagina);
    const btnAnterior = document.getElementById("btnAnterior");
    const btnSiguiente = document.getElementById("btnSiguiente");
    const infoPaginacion = document.getElementById("infoPaginacion");

    // Actualizar botones
    btnAnterior.disabled = paginaActual <= 1;
    btnSiguiente.disabled = paginaActual >= totalPaginas;

    // Actualizar información
    if (totalPaginas > 0) {
      infoPaginacion.textContent = `Página ${paginaActual} de ${totalPaginas}`;
    } else {
      infoPaginacion.textContent = "Sin páginas";
    }
}

// Toggle filtros avanzados
function toggleFiltrosAvanzados() {
    const filtros = document.getElementById('filtrosAvanzados');
    const alertas = document.getElementById('alertasCuotas');
    
    if (filtros.style.display === 'none') {
        filtros.style.display = 'flex';
        alertas.style.display = 'flex';
    } else {
        filtros.style.display = 'none';
        alertas.style.display = 'none';
    }
}

// Limpiar búsqueda
function limpiarBusqueda() {
    document.getElementById('buscador').value = '';
    document.getElementById('fechaDesde').value = '';
    document.getElementById('fechaHasta').value = '';
    document.getElementById('filtroUsuario').value = '';
    document.getElementById('filtroDistrito').value = '';
    document.getElementById('montoMin').value = '';
    document.getElementById('montoMax').value = '';
    document.getElementById('filtroEstadoCuotas').value = '';
    document.getElementById('ordenarPor').value = 'fecha_desc';
    aplicarFiltros();
}

// Obtener estado de cuota individual
function obtenerEstadoCuota(fechaCuota) {
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const fecha = new Date(fechaCuota + 'T00:00:00');
    const diferenciaDias = Math.ceil((fecha - hoy) / (1000 * 60 * 60 * 24));
    
    if (diferenciaDias < 0) {
        return {
            estado: 'vencida',
            badge: '<span class="badge bg-dark"><i class="fas fa-times-circle"></i> Vencida</span>',
            dias: Math.abs(diferenciaDias)
        };
    } else if (diferenciaDias <= 3) {
        return {
            estado: 'critica',
            badge: '<span class="badge bg-danger"><i class="fas fa-exclamation-triangle"></i> Crítica</span>',
            dias: diferenciaDias
        };
    } else if (diferenciaDias <= 7) {
        return {
            estado: 'proxima',
            badge: '<span class="badge bg-warning text-dark"><i class="fas fa-clock"></i> Próxima</span>',
            dias: diferenciaDias
        };
    } else {
        return {
            estado: 'al_dia',
            badge: '<span class="badge bg-success"><i class="fas fa-check-circle"></i> Al día</span>',
            dias: diferenciaDias
        };
    }
}

  // Ver cuotas en modal
  function verCuotas(id) {
    fetch(`../api/detalle-cuotas/${id}/`)
      .then((response) => response.json())
      .then((data) => {
        const tbody = document.getElementById("cuotasModalBody");
        tbody.innerHTML = "";

        data.forEach((cuota, index) => {
            const estadoCuota = obtenerEstadoCuota(cuota.fecha);
            const row = `
                <tr>
                    <td><span class="badge bg-primary">${index + 1}</span></td>
                    <td><strong class="text-success">S/ ${parseFloat(cuota.monto).toFixed(2)}</strong></td>
                    <td>${formatearFecha(cuota.fecha)}</td>
                    <td>${estadoCuota.badge}</td>
                    <td>${cuota.descripcion}</td>
                </tr>
            `;
          tbody.innerHTML += row;
        });

        new bootstrap.Modal(document.getElementById("cuotasModal")).show();
      })
      .catch((error) => {
        console.error("Error:", error);
        mostrarMensajeError("Error al cargar las cuotas");
      });
  }


// Eliminar cotización con modal de confirmación
function eliminarCotizacion(id) {
    const confirmBtn = document.getElementById('confirmBtn');
    confirmBtn.onclick = function() {
        fetch(`../api/cotizaciones/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            if (response.ok) {
                mostrarMensajeExito('Cotización eliminada exitosamente');
                cargarCotizaciones();
                bootstrap.Modal.getInstance(document.getElementById('confirmModal')).hide();
            } else {
                mostrarMensajeError('Error al eliminar la cotización');
            }
        })
        .catch((error) => {
          console.error("Error:", error);
          mostrarMensajeError("Error de conexión");
        });
    };
    
    new bootstrap.Modal(document.getElementById('confirmModal')).show();
}

  // Formatear fecha
  function formatearFecha(fechaStr) {
    const fecha = new Date(fechaStr + "T00:00:00");
    return fecha.toLocaleDateString("es-PE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  // Mostrar mensajes de éxito
  function mostrarMensajeExito(mensaje) {
    const alert = document.createElement("div");
    alert.className = "alert alert-success alert-dismissible fade show position-fixed";
    alert.style.top = "20px";
    alert.style.right = "20px";
    alert.style.zIndex = "9999";
    alert.innerHTML = `
        <i class="fas fa-check-circle"></i> ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);

    setTimeout(() => alert.remove(), 3000);
  }

  // Mostrar mensajes de error
  function mostrarMensajeError(mensaje) {
    const alert = document.createElement("div");
    alert.className = "alert alert-danger alert-dismissible fade show position-fixed";
    alert.style.top = "20px";
    alert.style.right = "20px";
    alert.style.zIndex = "9999";
    alert.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i> ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);

    setTimeout(() => alert.remove(), 5000);
  }

  // Obtener cookie CSRF
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
