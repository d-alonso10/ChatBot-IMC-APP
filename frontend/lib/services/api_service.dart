import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const baseUrl = 'http://127.0.0.1:8000'; // Cambia si corres en Android

  // Enviar mensaje al bot
  static Future<Map<String, dynamic>> enviarMensaje(String mensaje, String? conversationId) async {
    final res = await http.post(
      Uri.parse('$baseUrl/mensaje'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'texto': mensaje,
        'conversation_id': conversationId, // Enviar el ID
      }),
    );
    return jsonDecode(res.body);
  }

  // Obtener gráfico IMC por ID
  static String getGraficoUrl(String graphId) {
    return '$baseUrl/grafico/$graphId';
  }

  // Reiniciar estado conversacional (mantenido por compatibilidad, aunque ahora se usa getBienvenida)
  static Future<void> reiniciar() async {
    await http.get(Uri.parse('$baseUrl/reiniciar'));
  }

  // ✅ Obtener mensaje de bienvenida
  static Future<Map<String, dynamic>> getBienvenida() async {
    final res = await http.get(Uri.parse('$baseUrl/bienvenida'));
    return jsonDecode(res.body); // Ahora esto incluirá el conversation_id
  }
}