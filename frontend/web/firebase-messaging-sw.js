// frontend/web/firebase-messaging-sw.js

// Importar los scripts de Firebase (versión compat, la más estable)
importScripts("https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js");

// --- ¡¡IMPORTANTE!! ---
// Esta configuración la copié de tu archivo 'lib/firebase_options.dart'
// Es la configuración específica para 'web'.
const firebaseConfig = {
  apiKey: "AIzaSyAQgI6RTUTu3LNpspZhFwVV3vdefmCwdDM",
  appId: "1:974695670355:web:00b6a8e7b4ccfc68dd9ca6",
  messagingSenderId: "974695670355",
  projectId: "chatbot-imc-app",
  authDomain: "chatbot-imc-app.firebaseapp.com",
  storageBucket: "chatbot-imc-app.firebasestorage.app",
  measurementId: "G-3G6MM7V2CW"
};
// --- FIN DE LA CONFIGURACIÓN ---

// Inicializar la app de Firebase DENTRO del service worker
firebase.initializeApp(firebaseConfig);

// Obtener la instancia de Messaging
const messaging = firebase.messaging();

// Opcional: Manejar notificaciones cuando la app NO está en primer plano
messaging.onBackgroundMessage((payload) => {
  console.log(
    "[firebase-messaging-sw.js] Mensaje recibido en segundo plano ",
    payload,
  );

  const notificationTitle = payload.notification.title || 'Nueva Notificación';
  const notificationOptions = {
    body: payload.notification.body || 'Tienes un nuevo mensaje.',
    icon: '/icons/Icon-192.png' // Icono que se mostrará
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});