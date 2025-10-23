var colorMapping = {
  Presentado: "#00a7a4",
  Reingresado: "#1d58b4",
  Apelado: "#ef8e00",
  "En proceso": "#b4b4b4",
  "En calificación": "#5a2071",
  Inscrito: "#89be21",
  Reservado: "#575756",
  Distribuido: "#f31c53",
  Liquidado: "#006633",
  Prorrogado: "#80d0ff",
  Observado: "red",
  Suspendido: "#981622",
  Tachado: "black",
  "Res. Tribunal": "black",
  "Res. Procedente": "#006633",
  "Res. Improcedente": "black",
  Anotado: "#7eb3d5",
  Finalizado: "#89be21",
};

// Función para crear y mostrar los toasts
function mostrarToast(extra, headerClass, headerText, message, fecha, diasRestantes) {
  let toastHtml = `
      <div class="toast custom-slide fade show" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="toast-header ${headerClass} text-white"">
              <strong class="me-auto text-truncate">${headerText}</strong>
              <small class="ms-4 text-nowrap">${extra} ${
    diasRestantes === 0 ? "Hoy" : diasRestantes === 1 ? "Mañana" : `En ${diasRestantes} días`
  }</small>
              <button type="button" class="ms-2 mb-1 btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
          <div class="toast-body">
              ${message}
          </div>
      </div>`;
  $(".toast-container").append(toastHtml); // Agregar la notificación al contenedor
}

// Función para agregar notificaciones al DOM sin repetir estructura
function agregarNotificacion(titulo, subtitulo, iconBg, iconClass) {
  $("#notifications-container").append(`
      <a href="javascript:void(0);" class="dropdown-item p-0 notify-item card unread-noti shadow-none mb-2">
          <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                  <div class="notify-icon ${iconBg}">
                      <i class="mdi ${iconClass}"></i>
                  </div>
                </div>
                <div class="flex-grow-1 text-truncate ms-2">
                  <h5 class="noti-item-title fw-semibold font-14">${titulo}</h5>
                  <small class="noti-item-subtitle text-muted">${subtitulo}</small>
                </div>
              </div>
          </div>
      </a>
  `);
}

function jqueryToast(titulo = "¡Bien Hecho!", mensaje, posicion = "bottom-right", tipo = "success", duracion = 3000) {
  $.toast({
    heading: titulo,
    text: mensaje,
    position: posicion,
    icon: tipo, // warning, success, error, info
    loaderBg: "rgba(0,0,0,0.2)",
    hideAfter: duracion,
  });
}
