import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/message_bubble.dart';

class ChatScreen extends StatefulWidget {
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final _controller = TextEditingController();
  final _scrollController = ScrollController(); // Añadido para auto-scroll
  final List<Map<String, dynamic>> _messages = [];
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  late AnimationController _typingController;
  bool _isBotTyping = false;
  String _typingText = '';
  int _typingIndex = 0;
  Timer? _typingTimer;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 200),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.9).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut)
    );
    
    _typingController = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 1500),
    )..addStatusListener((status) {
        if (status == AnimationStatus.completed) {
          _typingController.reverse();
        } else if (status == AnimationStatus.dismissed) {
          _typingController.forward();
        }
      });
    
    _cargarMensajeInicial();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _typingController.dispose();
    _typingTimer?.cancel();
    _scrollController.dispose(); // No olvidar limpiar el controller
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _startTypingAnimation(String fullText) {
    _typingTimer?.cancel();
    _typingIndex = 0;
    _typingText = '';
    
    _typingTimer = Timer.periodic(Duration(milliseconds: 30), (timer) {
      if (_typingIndex < fullText.length) {
        setState(() {
          _typingText = fullText.substring(0, _typingIndex + 1);
          _typingIndex++;
        });
        _scrollToBottom(); // Auto-scroll mientras escribe
      } else {
        timer.cancel();
        setState(() {
          _isBotTyping = false;
          _messages.removeLast();
          _messages.add({'text': fullText, 'isUser': false});
        });
        _scrollToBottom(); // Auto-scroll al finalizar
      }
    });
  }

  void _enviarMensaje() async {
    if (_isBotTyping) return; // Evitar doble envío
    
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    _animationController.forward().then((_) => _animationController.reverse());

    setState(() {
      _messages.add({'text': text, 'isUser': true});
      _controller.clear();
      _isBotTyping = true;
      _messages.add({'typing': true, 'isUser': false});
    });
    _scrollToBottom();

    try {
      final response = await ApiService.enviarMensaje(text);
      
      if (response == null || response['respuesta'] == null) {
        throw Exception('Respuesta inválida');
      }

      _startTypingAnimation(response['respuesta']);

      if (response['grafico'] == true && response['graph_id'] != null) {
        final graphId = response['graph_id'];
        Future.delayed(Duration(milliseconds: response['respuesta'].length * 30 + 500), () {
          setState(() {
            _messages.add({'image': ApiService.getGraficoUrl(graphId), 'isUser': false});
          });
          _scrollToBottom();
        });
      }
    } catch (e) {
      setState(() {
        _isBotTyping = false;
        _messages.removeLast(); // Remover el indicador de typing
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Error de conexión con el asistente."),
          backgroundColor: Colors.red[400],
        ),
      );
    }
  }

  void _cargarMensajeInicial() async {
    final bienvenida = await ApiService.getBienvenida();
    setState(() {
      _messages.add({'text': bienvenida['respuesta'], 'isUser': false});
    });
    _scrollToBottom();
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
              constraints: const BoxConstraints(maxWidth: 280),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [const Color(0xFFEDE7F6), const Color(0xFFF3E5F5)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(20),
                  topRight: const Radius.circular(20),
                  bottomLeft: Radius.circular(4),
                  bottomRight: Radius.circular(20),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 6,
                    offset: Offset(0, 3),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF7E57C2)),
                    ),
                  ),
                  SizedBox(width: 12),
                  Text(
                    'Escribiendo...',
                    style: TextStyle(
                      color: Color(0xFF7E57C2),
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F5FB),
      appBar: AppBar(
        backgroundColor: const Color(0xFF7E57C2),
        elevation: 8,
        shadowColor: Colors.deepPurple.withOpacity(0.3),
        centerTitle: false,
        title: Row(
          children: [
            Container(
              padding: EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.medical_services, color: Colors.white, size: 22),
            ),
            SizedBox(width: 12),
            const Text(
              "Asistente IMC Pediátrico",
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
                color: Colors.white,
              ),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Color(0xFFF8F5FB),
                      Color(0xFFEDE7F6).withOpacity(0.4),
                    ],
                  ),
                ),
                child: ListView.builder(
                  controller: _scrollController, // Añadido para auto-scroll
                  padding: const EdgeInsets.only(top: 10, bottom: 10),
                  itemCount: _messages.length,
                  itemBuilder: (ctx, i) {
                    final msg = _messages[i];
                    
                    if (msg.containsKey("typing")) {
                      return _buildTypingIndicator();
                    }
                    
                    if (msg.containsKey("image")) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(20),
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(20),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.1),
                                  blurRadius: 8,
                                  offset: Offset(0, 3),
                                ),
                              ],
                            ),
                            child: Image.network(
                              msg['image'],
                              fit: BoxFit.cover,
                              loadingBuilder: (context, child, loadingProgress) {
                                if (loadingProgress == null) return child;
                                return Center(
                                  child: CircularProgressIndicator(
                                    value: loadingProgress.expectedTotalBytes != null
                                        ? loadingProgress.cumulativeBytesLoaded /
                                            loadingProgress.expectedTotalBytes!
                                        : null,
                                    color: Color(0xFF7E57C2),
                                  ),
                                );
                              },
                            ),
                          ),
                        ),
                      );
                    }
                    
                    if (_isBotTyping && i == _messages.length - 1 && _typingText.isNotEmpty) {
                      return MessageBubble(
                        text: _typingText,
                        isUser: false,
                      );
                    }
                    
                    return MessageBubble(
                      text: msg['text'],
                      isUser: msg['isUser'],
                    );
                  },
                ),
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 12,
                    offset: Offset(0, -4),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: const Color(0xFFF0F0F0),
                        borderRadius: BorderRadius.circular(30),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.05),
                            blurRadius: 4,
                            offset: Offset(0, 2),
                          ),
                        ],
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: TextField(
                        controller: _controller,
                        maxLength: 150, // Límite de caracteres
                        decoration: const InputDecoration(
                          hintText: "Escribe tu mensaje...",
                          border: InputBorder.none,
                          hintStyle: TextStyle(color: Colors.grey),
                          counterText: "", // Ocultar contador
                        ),
                        style: const TextStyle(fontSize: 16),
                        onSubmitted: (_) => _enviarMensaje(),
                      ),
                    ),
                  ),
                  SizedBox(width: 12),
                  ScaleTransition(
                    scale: _scaleAnimation,
                    child: GestureDetector(
                      onTap: _enviarMensaje,
                      onTapDown: (_) => _animationController.forward(),
                      onTapUp: (_) => _animationController.reverse(),
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              Color(0xFF7E57C2),
                              Color(0xFF9575CD),
                            ],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: Color(0xFF7E57C2).withOpacity(0.3),
                              blurRadius: 8,
                              offset: Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Icon(
                          Icons.send_rounded,
                          color: Colors.white,
                          size: 24,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}