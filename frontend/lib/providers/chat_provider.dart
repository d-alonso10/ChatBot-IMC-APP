// lib/providers/chat_provider.dart
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/paciente_model.dart'; // Importar el modelo

class ChatMessage {
  final String? text;
  final bool isUser;
  final String? imageUrl;
  final bool isTyping;
  final bool isError;

  ChatMessage({
    this.text,
    required this.isUser,
    this.imageUrl,
    this.isTyping = false,
    this.isError = false,
  });
}

class ChatProvider extends ChangeNotifier {
  final List<ChatMessage> _messages = [];
  final Paciente _paciente; // <-- NUEVO
  final String _authToken; // <-- NUEVO
  
  String? _conversationId; // Se mantiene para el flujo del chat
  bool _isBotTyping = false;
  String _typingText = '';
  int _typingIndex = 0;

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isBotTyping => _isBotTyping;
  String get typingText => _typingText;
  Paciente get paciente => _paciente; // Getter para el paciente

  // Constructor modificado
  ChatProvider({required Paciente paciente, required String authToken})
      : _paciente = paciente,
        _authToken = authToken {
    _loadWelcomeMessage(); // Cargar mensaje de bienvenida personalizado
  }

  // Ya no llama a la API, solo añade un mensaje local
  void _loadWelcomeMessage() {
    _messages.add(ChatMessage(
      text: "¡Hola! 👋 Estoy listo para calcular el IMC de ${_paciente.nombre}.\n\n¿Cuál es su PESO actual? (ej: 15.5 kg)",
      isUser: false,
    ));
    notifyListeners();
  }
  
  // --- Funciones de UI (sin cambios) ---
  void addUserMessage(String text) {
    _messages.add(ChatMessage(text: text, isUser: true));
    notifyListeners();
  }

  void startTypingIndicator() {
    _isBotTyping = true;
    _messages.add(ChatMessage(isUser: false, isTyping: true));
    notifyListeners();
  }

  void updateTypingText(String text, int index) {
    _typingText = text;
    _typingIndex = index;
    notifyListeners();
  }

  void finishTyping(String fullText) {
    _isBotTyping = false;
    _typingText = '';
    _typingIndex = 0;
    _messages.removeWhere((msg) => msg.isTyping);
    _messages.add(ChatMessage(text: fullText, isUser: false));
    notifyListeners();
  }

  void addImage(String imageUrl) {
    _messages.add(ChatMessage(isUser: false, imageUrl: imageUrl));
    notifyListeners();
  }

  void _addErrorMessage(String errorText) {
    _isBotTyping = false;
    _messages.removeWhere((msg) => msg.isTyping);
    _messages.add(ChatMessage(
      text: errorText,
      isUser: false,
      isError: true,
    ));
    notifyListeners();
  }

  // --- Lógica de API (MODIFICADA) ---
  Future<void> sendMessage(String text) async {
    if (_isBotTyping || text.trim().isEmpty) return;

    addUserMessage(text);
    startTypingIndicator();

    try {
      // Usar el token, el ID del paciente y el ID de conversación
      final response = await ApiService.enviarMensaje(
        _authToken,
        text,
        _paciente.id, // <-- Pasa el ID del paciente
        _conversationId,
      );

      _conversationId = response['conversation_id']; // Guardar ID de conversación

      if (response['respuesta'] == null) {
        throw Exception('Respuesta inválida del servidor');
      }

      final fullText = response['respuesta'] as String;
      await _animateTyping(fullText);

      if (response['grafico'] == true && response['graph_id'] != null) {
        await Future.delayed(const Duration(milliseconds: 500));
        addImage(ApiService.getGraficoUrl(response['graph_id']));
      }
    } catch (e) {
      _addErrorMessage(
        '❌ Error de conexión con el asistente.\n\n'
        'Por favor verifica tu conexión e intenta de nuevo.\n'
        'Si el problema persiste, escribe "nuevo" para comenzar de nuevo.'
      );
    }
  }

  Future<void> _animateTyping(String fullText) async {
    const typingSpeed = Duration(milliseconds: 30);
    for (int i = 0; i < fullText.length; i++) {
      updateTypingText(fullText.substring(0, i + 1), i);
      await Future.delayed(typingSpeed);
    }
    finishTyping(fullText);
  }
}