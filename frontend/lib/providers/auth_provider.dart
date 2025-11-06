// lib/providers/auth_provider.dart
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../services/api_service.dart';

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
        // Inmediatamente loguear después de registrar
        _token = await ApiService.login(email, password);
      }
      
      await _storage.write(key: 'authToken', value: _token);
      notifyListeners();
    } catch (e) {
      rethrow; // Re-lanza el error para que la UI lo maneje
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
    notifyListeners();
  }

  Future<bool> tryAutoLogin() async {
    final storedToken = await _storage.read(key: 'authToken');
    if (storedToken == null) {
      return false;
    }
    
    // Aquí podrías añadir una lógica para verificar si el token sigue siendo válido
    // (ej. llamando a /users/me), pero por ahora, solo lo cargamos.
    _token = storedToken;
    notifyListeners();
    return true;
  }
}