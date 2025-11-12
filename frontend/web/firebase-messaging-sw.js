// frontend/web/firebase-messaging-sw.js

// Importa e inicializa los scripts de Firebase
// Estos scripts se obtienen de los paquetes de Flutter (firebase_core, firebase_messaging)
importScripts("flutter-firebase-app.js");
importScripts("flutter-firebase-messaging.js");

// Inicializa la app de Firebase
// La configuración se tomará automáticamente de tu `firebase_options.dart`
firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();

// (Opcional) Manejar notificaciones cuando la app está en segundo plano/cerrada
messaging.onBackgroundMessage((payload) => {
  console.log(
    "[firebase-messaging-sw.js] Received background message ",
    payload,
  );
  // Aquí puedes personalizar el título y cuerpo de la notificación
  const notificationTitle = payload.notification.title || 'Nueva Notificación';
  const notificationOptions = {
    body: payload.notification.body || 'Tienes un nuevo mensaje.',
    icon: '/icons/Icon-192.png' // Icono que se mostrará
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});