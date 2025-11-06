// lib/services/api_service.dart
import 'dart:typed_data'; // <-- AÑADIR ESTE IMPORT
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // ¡RECUERDA CAMBIAR ESTO SI PRUEBAS EN MÓVIL!
  static const baseUrl = 'http://127.0.0.1:8000';

  // --- NUEVO: Helper para Headers ---
  static Map<String, String> _getAuthHeaders(String token) {
    return {
      'Content-Type': 'application/json; charset=UTF-8', // <-- CORREGIDO (era UTF-OCHO)
      'Authorization': 'Bearer $token',
    };
  }

  // --- NUEVO: Endpoints de Auth ---
  static Future<String> login(String email, String password) async {
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
    final res = await http.post(
      Uri.parse('$baseUrl/users/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (res.statusCode != 200) {
       // Intenta decodificar el error del backend
      try {
        final body = jsonDecode(res.body);
        throw Exception(body['detail'] ?? 'Failed to register');
      } catch (e) {
        throw Exception('Failed to register');
      }
    }
  }

  // --- NUEVO: Endpoints de Paciente ---
  static Future<List<dynamic>> getPacientes(String token) async {
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

  static Future<Map<String, dynamic>> createPaciente(String token, String nombre, String fechaNacimiento, String sexo) async {
     final res = await http.post(
      Uri.parse('$baseUrl/pacientes/crear'),
      headers: _getAuthHeaders(token), // <-- Esta función causaba el error
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

  // --- NUEVO: Endpoints de Historial ---
  static Future<List<dynamic>> getHistorialCalculos(String token, int pacienteId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/pacientes/$pacienteId/historial'),
      headers: _getAuthHeaders(token),
    );
    if (res.statusCode == 200) {
      return jsonDecode(utf8.decode(res.bodyBytes));
    }
    // Manejo de error si no hay historial
    if (res.statusCode == 404) {
      return []; // Devuelve lista vacía si no hay historial
    }
    throw Exception('Failed to load historial');
  }

  static Future<Uint8List> getHistorialGraficoBytes(String token, int pacienteId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/pacientes/$pacienteId/historial/grafico'),
      headers: _getAuthHeaders(token),
    );
    if (res.statusCode == 200) {
      return res.bodyBytes;
    }
    throw Exception('Failed to load graph');
  }

  // --- MODIFICADO: Endpoint de Chat ---
  static Future<Map<String, dynamic>> enviarMensaje(String token, String mensaje, int pacienteId, String? conversationId) async {
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

  // --- Endpoint de Gráfico (sin cambios) ---
  static String getGraficoUrl(String graphId) {
    return '$baseUrl/grafico/$graphId';
  }
}