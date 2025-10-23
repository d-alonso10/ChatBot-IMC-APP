import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../widgets/message_bubble.dart';
import '../widgets/typing_indicator.dart';
import '../widgets/graph_image.dart';
import '../widgets/chat_input_field.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    // Cargar mensaje de bienvenida
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ChatProvider>().loadWelcomeMessage();
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
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
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.medical_services, color: Colors.white, size: 22),
            ),
            const SizedBox(width: 12),
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
                      const Color(0xFFF8F5FB),
                      const Color(0xFFEDE7F6).withOpacity(0.4),
                    ],
                  ),
                ),
                child: Consumer<ChatProvider>(
                  builder: (context, chatProvider, child) {
                    // Auto-scroll cuando cambian los mensajes
                    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
                    
                    return ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.only(top: 10, bottom: 10),
                      itemCount: chatProvider.messages.length,
                      itemBuilder: (ctx, i) {
                        final msg = chatProvider.messages[i];
                        
                        if (msg.isTyping) {
                          return const TypingIndicator();
                        }
                        
                        if (msg.imageUrl != null) {
                          return GraphImage(imageUrl: msg.imageUrl!);
                        }
                        
                        // Mostrar texto en animación si está escribiendo
                        if (chatProvider.isBotTyping && 
                            i == chatProvider.messages.length - 1 && 
                            chatProvider.typingText.isNotEmpty) {
                          return MessageBubble(
                            text: chatProvider.typingText,
                            isUser: false,
                          );
                        }
                        
                        return MessageBubble(
                          text: msg.text ?? '',
                          isUser: msg.isUser,
                          isError: msg.isError,
                        );
                      },
                    );
                  },
                ),
              ),
            ),
            Consumer<ChatProvider>(
              builder: (context, chatProvider, child) {
                return ChatInputField(
                  onSendMessage: (text) => chatProvider.sendMessage(text),
                  isEnabled: !chatProvider.isBotTyping,
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}