// lib/providers/auth_provider.dart
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../services/api_service.dart';
// --- ¡NUEVA IMPORTACIÓN! ---
import '../services/notification_service.dart';

class AuthProvider extends ChangeNotifier {
  String? _token;
  final _storage = const FlutterSecureStorage();

  bool get isAuth => _token != null;
  String? get token => _token;

  Future<void> _authenticate(String email, String password, bool isLogin) async {
    try {
      if (isLogin) {
        _token = await ApiService.login(email, password);
      } else {
        await ApiService.register(email, password);
        _token = await ApiService.login(email, password);
      }
      
      await _storage.write(key: 'authToken', value: _token);

      // --- ¡LÓGICA DE NOTIFICACIONES AÑADIDA! ---
      // Si el login/registro fue exitoso, registrar el dispositivo.
      if (_token != null) {
        try {
          final notificationService = NotificationService();
          await notificationService.requestPermission();
          await notificationService.getTokenAndSendToServer(_token!);
          // Escuchar mensajes solo cuando el usuario está logueado
          notificationService.setupForegroundMessageHandler();
        } catch (e) {
          // Es importante NO detener el flujo de login si las notificaciones fallan.
          // Solo lo registramos en la consola.
          print("Error al registrar el dispositivo para notificaciones: $e");
        }
      }
      // --- FIN DE LA LÓGICA AÑADIDA ---

      notifyListeners();
    } catch (e) {
      rethrow; 
    }
  }

  Future<void> login(String email, String password) async {
    return _authenticate(email, password, true);
  }

  Future<void> register(String email, String password) async {
    return _authenticate(email, password, false);
  }

  Future<void> logout() async {
    _token = null;
    await _storage.delete(key: 'authToken');
    // Opcional: También podrías tener una API para "des-registrar" el token FCM
    notifyListeners();
  }

  Future<bool> tryAutoLogin() async {
    final storedToken = await _storage.read(key: 'authToken');
    if (storedToken == null) {
      return false;
    }
    
    _token = storedToken;

    // --- ¡LÓGICA DE NOTIFICACIONES AÑADIDA! ---
    // Si re-logueamos automáticamente, también configurar el 
    // manejador de notificaciones. No necesitamos volver a registrar el token
    // si ya lo hicimos (el backend lo tiene), pero sí necesitamos escuchar.
    try {
      final notificationService = NotificationService();
      // Solo escuchamos, no volvemos a pedir permiso ni a enviar token
      notificationService.setupForegroundMessageHandler();
    } catch (e) {
      print("Error al configurar notificaciones en auto-login: $e");
    }
    // --- FIN DE LA LÓGICA AÑADIDA ---

    notifyListeners();
    return true;
  }
}