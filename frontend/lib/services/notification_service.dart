// lib/services/notification_service.dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:frontend/services/api_service.dart';

// --- PASO 1: Manejador de mensajes en segundo plano ---
// Esto DEBE estar fuera de cualquier clase.
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Es importante inicializar Firebase aquí también si no lo has hecho.
  await Firebase.initializeApp();
  
  print("--- Manejando un mensaje en SEGUNDO PLANO ---");
  print("Título: ${message.notification?.title}");
  print("Cuerpo: ${message.notification?.body}");
  print("Datos: ${message.data}");
}


class NotificationService {
  final _firebaseMessaging = FirebaseMessaging.instance;

  // --- PASO 2: Inicialización principal (en main.dart) ---
  static Future<void> init() async {
    // Escucha mensajes cuando la app está terminada (background)
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
    
    // Aquí puedes añadir lógica para crear canales de notificación en Android
  }

  // --- PASO 3: Pedir permisos (en auth_provider) ---
  Future<void> requestPermission() async {
    NotificationSettings settings = await _firebaseMessaging.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print('Permiso de notificación concedido.');
    } else if (settings.authorizationStatus == AuthorizationStatus.provisional) {
      print('Permiso de notificación provisional concedido.');
    } else {
      print('Permiso de notificación denegado.');
      // Opcional: mostrar un diálogo al usuario
    }
  }

  // --- PASO 4: Obtener token y enviarlo al Backend (en auth_provider) ---
  Future<void> getTokenAndSendToServer(String jwtToken) async {
    try {
      // Obtener el token FCM para este dispositivo
      // Para Web, necesitas pasar el VAPID key de Firebase
      final fcmToken = await _firebaseMessaging.getToken(
        vapidKey: kIsWeb 
            ? "BFwcXE_7Y5z6xyVOKb6V0Bcd7yQ3B9X-TalQ8kPlsmRQAhYDHU5d86dxNAc7Yg5aD7SJszAC_s9Xdj-e-6tw-3c" 
            : null,
      );

      if (fcmToken == null) {
        print('Error: No se pudo obtener el token FCM.');
        return;
      }

      print('--- Token FCM Obtenido ---');
      print(fcmToken);
      print('---------------------------');

      // Enviar el token a nuestro backend FastAPI
      await ApiService.registerDevice(jwtToken, fcmToken);
      print('Token FCM registrado en el backend exitosamente.');

    } catch (e) {
      print('Error al obtener o enviar el token FCM: $e');
    }
  }

  // --- PASO 5: Escuchar mensajes (en auth_provider o main) ---
  void setupForegroundMessageHandler() {
    // Escucha mensajes mientras la app está ABIERTA y en primer plano
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('--- ¡Mensaje recibido en PRIMER PLANO! ---');
      if (message.notification != null) {
        print('Título: ${message.notification?.title}');
        print('Cuerpo: ${message.notification?.body}');
        
        // Aquí podrías mostrar un SnackBar o un diálogo local,
        // ya que las notificaciones "push" no aparecen solas
        // cuando la app está abierta.
      }
    });

    // Escucha cuando el usuario TOCA la notificación y abre la app
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      print('--- Notificación TOCADA (App abierta) ---');
      // Aquí puedes navegar a una pantalla específica si lo deseas
    });
  }
}