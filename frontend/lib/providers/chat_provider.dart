import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

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
  bool _isBotTyping = false;
  String _typingText = '';
  int _typingIndex = 0;

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isBotTyping => _isBotTyping;
  String get typingText => _typingText;

  Future<void> loadWelcomeMessage() async {
    try {
      final response = await ApiService.getBienvenida();
      _messages.add(ChatMessage(
        text: response['respuesta'],
        isUser: false,
      ));
      notifyListeners();
    } catch (e) {
      _addErrorMessage('Error al cargar el mensaje de bienvenida. Verifica tu conexión.');
    }
  }

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
    
    // Remover indicador de typing
    _messages.removeWhere((msg) => msg.isTyping);
    
    // Agregar mensaje completo
    _messages.add(ChatMessage(text: fullText, isUser: false));
    notifyListeners();
  }

  void addImage(String imageUrl) {
    _messages.add(ChatMessage(
      isUser: false,
      imageUrl: imageUrl,
    ));
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

  Future<void> sendMessage(String text) async {
    if (_isBotTyping || text.trim().isEmpty) return;

    addUserMessage(text);
    startTypingIndicator();

    try {
      final response = await ApiService.enviarMensaje(text);

      if (response == null || response['respuesta'] == null) {
        throw Exception('Respuesta inválida del servidor');
      }

      // Simular animación de escritura
      final fullText = response['respuesta'] as String;
      await _animateTyping(fullText);

      // Mostrar gráfico si está disponible
      if (response['grafico'] == true && response['graph_id'] != null) {
        await Future.delayed(const Duration(milliseconds: 500));
        addImage(ApiService.getGraficoUrl(response['graph_id']));
      }
    } catch (e) {
      _addErrorMessage(
        '❌ Error de conexión con el asistente.\n\n'
        'Por favor verifica tu conexión a internet e intenta de nuevo.\n'
        'Si el problema persiste, escribe "reiniciar" para comenzar de nuevo.'
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

  void clearMessages() {
    _messages.clear();
    _isBotTyping = false;
    _typingText = '';
    _typingIndex = 0;
    notifyListeners();
  }
}
