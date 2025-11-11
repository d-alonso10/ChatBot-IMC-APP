// lib/services/api_service.dart
import 'dart:convert';
import 'dart:typed_data'; 
import 'package:http/http.dart' as http;

class ApiService {
  static const baseUrl = 'http://127.0.0.1:8000';

  static Map<String, String> _getAuthHeaders(String token) {
    return {
      'Content-Type': 'application/json; charset=UTF-8',
      'Authorization': 'Bearer $token',
    };
  }

  // --- Endpoints de Auth (sin cambios) ---
  static Future<String> login(String email, String password) async {
    // ... (código existente sin cambios) ...
    final res = await http.post(
      Uri.parse('$baseUrl/token'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': email, 'password': password},
    );
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      return data['access_token'];
    } else {
      throw Exception('Failed to login');
    }
  }

  static Future<void> register(String email, String password) async {
    // ... (código existente sin cambios) ...
    final res = await http.post(
      Uri.parse('$baseUrl/users/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    if (res.statusCode != 200) {
      try {
        final body = jsonDecode(res.body);
        throw Exception(body['detail'] ?? 'Failed to register');
      } catch (e) {
        throw Exception('Failed to register');
      }
    }
  }

  // --- ¡NUEVO ENDPOINT PARA REGISTRAR DISPOSITIVO! ---
  static Future<void> registerDevice(String token, String fcmToken) async {
    final res = await http.post(
      Uri.parse('$baseUrl/users/me/register-device'),
      headers: _getAuthHeaders(token),
      body: jsonEncode({
        'fcm_token': fcmToken,
      }),
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to register FCM token with backend');
    }
  }
  // --- FIN DE LA MODIFICACIÓN ---

  // --- Endpoints de Paciente (sin cambios) ---
  static Future<List<dynamic>> getPacientes(String token) async {
    // ... (código existente sin cambios) ...
    final res = await http.get(
      Uri.parse('$baseUrl/pacientes/me'),
      headers: _getAuthHeaders(token),
    );
    if (res.statusCode == 200) {
      return jsonDecode(utf8.decode(res.bodyBytes));
    } else {
      throw Exception('Failed to load pacientes');
    }
  }

  static Future<Map<String, dynamic>> createPaciente(
      String token, String nombre, String fechaNacimiento, String sexo) async {
    // ... (código existente sin cambios) ...
    final res = await http.post(
      Uri.parse('$baseUrl/pacientes/crear'),
      headers: _getAuthHeaders(token),
      body: jsonEncode({
        'nombre': nombre,
        'fecha_nacimiento': fechaNacimiento,
        'sexo': sexo,
      }),
    );
    if (res.statusCode == 200) {
      return jsonDecode(utf8.decode(res.bodyBytes));
    } else {
      throw Exception('Failed to create paciente');
    }
  }

  // ... (Resto de Endpoints: Historial, Gráficos, PDF, Chat...) ...
  // ... (código existente sin cambios) ...
  static Future<List<dynamic>> getHistorialCalculos(
      String token, int pacienteId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/pacientes/$pacienteId/historial'),
      headers: _getAuthHeaders(token),
    );
    if (res.statusCode == 200) {
      return jsonDecode(utf8.decode(res.bodyBytes));
    }
    if (res.statusCode == 404) {
      return [];
    }
    throw Exception('Failed to load historial');
  }

  static Future<Uint8List> getHistorialGraficoBytes(
      String token, int pacienteId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/pacientes/$pacienteId/historial/grafico'),
      headers: _getAuthHeaders(token),
    );
    if (res.statusCode == 200) {
      return res.bodyBytes;
    }
    if (res.statusCode == 404) {
      throw Exception('404: No hay historial de cálculos');
    }
    throw Exception('Failed to load graph');
  }

  static Future<Uint8List> getGraficoPesoBytes(String token, int pacienteId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/pacientes/$pacienteId/grafico/peso'),
      headers: _getAuthHeaders(token),
    );
    if (res.statusCode == 200) {
      return res.bodyBytes;
    }
    throw Exception('Failed to load peso graph');
  }

  static Future<Uint8List> getGraficoTallaBytes(String token, int pacienteId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/pacientes/$pacienteId/grafico/talla'),
      headers: _getAuthHeaders(token),
    );
    if (res.statusCode == 200) {
      return res.bodyBytes;
    }
    throw Exception('Failed to load talla graph');
  }

  static Future<Uint8List> getPdfBytes(String token, int pacienteId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/pacientes/$pacienteId/exportar-pdf'),
      headers: _getAuthHeaders(token),
    );
    if (res.statusCode == 200) {
      return res.bodyBytes;
    }
    throw Exception('Failed to download PDF');
  }

  static Future<Map<String, dynamic>> enviarMensaje(
      String token, String mensaje, int pacienteId, String? conversationId) async {
    final res = await http.post(
      Uri.parse('$baseUrl/mensaje'),
      headers: _getAuthHeaders(token),
      body: jsonEncode({
        'texto': mensaje,
        'paciente_id': pacienteId,
        'conversation_id': conversationId,
      }),
    );
    if (res.statusCode == 200) {
      return jsonDecode(utf8.decode(res.bodyBytes));
    } else {
      throw Exception('Failed to send message');
    }
  }

  static String getGraficoUrl(String graphId) {
    final cacheBuster = DateTime.now().millisecondsSinceEpoch;
    return '$baseUrl/grafico/$graphId?v=$cacheBuster';
  }
}