// lib/services/notification_service.dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:frontend/services/api_service.dart';

// --- PASO 1: Manejador de mensajes en segundo plano ---
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
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
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
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
    }
  }

  // --- PASO 4: Obtener token y enviarlo al Backend (CORREGIDO) ---
  Future<void> getTokenAndSendToServer(String jwtToken) async {
    try {
      
      // --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
      // La VAPID key SÍ es necesaria para Web y debe pasarse manualmente.
      // No se obtiene de firebase_options.dart.
      final fcmToken = await _firebaseMessaging.getToken(
        vapidKey: kIsWeb 
            ? "PEGA_TU_CLAVE_PÚBLICA_VAPID_AQUÍ" 
            : null,
      );
      // --- FIN DE LA CORRECCIÓN ---

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
      // relanzar el error para que el auth_provider lo vea
      rethrow;
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
      }
    });

    // Escucha cuando el usuario TOCA la notificación y abre la app
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      print('--- Notificación TOCADA (App abierta) ---');
    });
  }
}